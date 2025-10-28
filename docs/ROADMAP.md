# Remaining Database Issues and Implementation Plan

This document tracks remaining issues that need attention and provides an implementation plan for fixes and tests.

## ✅ **Resolved Issues**

The following issues have been **fixed and tested**:

1. ✅ **fetch_one() MSSQL dict conversion** - Fixed in [manager.py:692-694](../nexusql/manager.py#L692-L694)
2. ✅ **fetch_all() MSSQL dict conversion** - Fixed in [manager.py:715-717](../nexusql/manager.py#L715-L717)
3. ✅ **NULL parameter handling** - Tested in [test_database_edge_cases.py:24](../tests/integration/test_database_edge_cases.py#L24)
4. ✅ **Datetime parameter handling** - Tested in [test_database_edge_cases.py:53](../tests/integration/test_database_edge_cases.py#L53)
5. ✅ **Empty string vs NULL** - Tested in [test_database_edge_cases.py:82](../tests/integration/test_database_edge_cases.py#L82)
6. ✅ **Boolean parameters** - Tested in [test_database_edge_cases.py:110](../tests/integration/test_database_edge_cases.py#L110)
7. ✅ **Unicode/special characters** - Tested in [test_database_edge_cases.py:140](../tests/integration/test_database_edge_cases.py#L140)
8. ✅ **Multiple NULLs in query** - Tested in [test_database_edge_cases.py:246](../tests/integration/test_database_edge_cases.py#L246)
9. ✅ **Quotes and special SQL chars** - Tested in [test_database_edge_cases.py:282](../tests/integration/test_database_edge_cases.py#L282)
10. ✅ **Large string parameters** - Tested in [test_database_edge_cases.py:318](../tests/integration/test_database_edge_cases.py#L318)
11. ✅ **Numeric parameter types** - Tested in [test_database_edge_cases.py:346](../tests/integration/test_database_edge_cases.py#L346)

---

## 🔴 **Outstanding Issues**

### Issue #1: execute_script() SQL Splitting is Fragile

**Location**: `nexusql/manager.py:765-778`

**Problem**: For non-SQLite databases, `execute_script()` uses naive `;` splitting which will fail on SQL containing semicolons in string literals or function bodies.

```python
if self.config.database_type == DatabaseType.SQLITE:
    self._connection.executescript(translated_script)
else:
    # ❌ Naive split - will break on: INSERT INTO t VALUES ('a;b');
    statements = [s.strip() for s in script.split(';') if s.strip()]
    for statement in statements:
        self.execute(statement)
```

**Example Failure Case**:
```sql
INSERT INTO users (name, bio) VALUES ('John', 'Loves SQL; enjoys programming');
CREATE TABLE posts (id INT, content TEXT);
```

This will incorrectly split into 3 statements instead of 2.

---

### Issue #2: Binary/BLOB Parameter Handling

**Problem**: No tests verify that binary data (bytes) can be passed as parameters and retrieved correctly.

**Use Case**:
```python
db.execute("INSERT INTO files (name, data) VALUES (:name, :data)", {
    'name': 'image.png',
    'data': b'\x89PNG\r\n\x1a\n...'  # Binary image data
})
```

**Risks**:
- Different databases may require different binary encoding
- SQLite uses BLOB type
- PostgreSQL uses BYTEA type
- MySQL uses BLOB/BINARY types
- MSSQL uses VARBINARY type

---

### Issue #3: Connection Pooling/Concurrent Access

**Problem**: No tests for thread safety or concurrent database access.

**Risks**:
- Multiple threads using the same `DatabaseManager` instance
- Race conditions on connection state
- Transaction isolation issues

---

### Issue #4: Auto-increment ID Retrieval

**Problem**: After INSERT with auto-increment primary key, different databases return the ID differently.

**Database-Specific Behavior**:
- SQLite: `cursor.lastrowid`
- PostgreSQL: `RETURNING id` clause or `currval()`
- MySQL: `LAST_INSERT_ID()`
- MSSQL: `SCOPE_IDENTITY()` or `OUTPUT` clause

---

## 📋 **Implementation Plan**

### Phase 1: Fix execute_script() (High Priority)

**Goal**: Properly parse multi-statement SQL scripts for all databases.

**Approach**:
1. Implement proper SQL statement parser that respects:
   - String literals (single and double quotes)
   - Comments (-- and /* */)
   - Stored procedures/functions (BEGIN...END blocks)
   - Dollar-quoted strings in PostgreSQL

2. Use `sqlparse` library for robust parsing:
```python
import sqlparse

def execute_script(self, script: str):
    translated_script = self.translate_sql(script)

    if self.config.database_type == DatabaseType.SQLITE:
        self._connection.executescript(translated_script)
    else:
        # Proper SQL parsing
        statements = sqlparse.split(translated_script)
        for statement in statements:
            if statement.strip():
                self.execute(statement)
```

**Test Cases to Add**:
```python
def test_execute_script_with_semicolons_in_strings(db):
    """Test script with semicolons inside string literals"""
    script = """
        CREATE TABLE test (id INT, value TEXT);
        INSERT INTO test VALUES (1, 'Hello; World');
        INSERT INTO test VALUES (2, 'Uses ; multiple; times');
    """
    db.execute_script(script)
    results = db.fetch_all("SELECT * FROM test ORDER BY id")
    assert len(results) == 2
    assert results[0]['value'] == 'Hello; World'

def test_execute_script_with_comments(db):
    """Test script with SQL comments"""
    script = """
        -- Create table
        CREATE TABLE test (id INT);
        /* Multi-line
           comment */
        INSERT INTO test VALUES (1);
    """
    db.execute_script(script)
```

**Implementation Steps**:
1. Add `sqlparse` to dependencies in `pyproject.toml`
2. Implement improved `execute_script()` in `manager.py`
3. Add test file: `tests/integration/test_execute_script.py`
4. Run tests across all database backends

**Estimated Effort**: 4-6 hours

---

### Phase 2: Binary/BLOB Support (Medium Priority)

**Goal**: Support binary data as parameters across all databases.

**Implementation Steps**:

1. Add binary type handling in `_convert_params()`:
```python
def _convert_params(self, query: str, params: Dict) -> Tuple[str, Union[Dict, Tuple]]:
    # ... existing code ...

    for key, value in params.items():
        # Handle binary data
        if isinstance(value, bytes):
            if self.config.database_type == DatabaseType.MSSQL:
                # MSSQL may need special handling
                param_list.append(value)
            else:
                param_list.append(value)
        # ... rest of conversions ...
```

2. Add test file: `tests/integration/test_binary_data.py`:
```python
import pytest

def test_binary_insert_and_retrieve(db):
    """Test storing and retrieving binary data"""
    db.execute("""
        CREATE TABLE files (
            id INTEGER PRIMARY KEY,
            filename TEXT,
            data BLOB
        )
    """)

    # Small binary data
    test_data = b'\x00\x01\x02\x03\xff\xfe\xfd'
    db.execute(
        "INSERT INTO files (id, filename, data) VALUES (:id, :name, :data)",
        {'id': 1, 'name': 'test.bin', 'data': test_data}
    )

    result = db.fetch_one("SELECT * FROM files WHERE id = :id", {'id': 1})
    assert result['data'] == test_data

def test_large_binary_data(db):
    """Test large binary data (1MB)"""
    large_data = bytes(range(256)) * 4096  # 1MB
    # ... similar test with large data ...

def test_image_like_binary(db):
    """Test PNG-like binary header"""
    png_header = b'\x89PNG\r\n\x1a\n'
    # ... test with realistic binary data ...
```

**Implementation Steps**:
1. Research database-specific binary handling requirements
2. Implement binary parameter conversion
3. Create comprehensive test suite
4. Test with various binary sizes (1KB, 100KB, 1MB)

**Estimated Effort**: 3-4 hours

---

### Phase 3: Connection Pooling/Concurrency (Low Priority)

**Goal**: Document thread safety limitations and add concurrency tests.

**Implementation Steps**:

1. Add documentation to `README.md`:
```markdown
## Thread Safety

`DatabaseManager` is **not thread-safe**. Each thread should create its own
`DatabaseManager` instance:

```python
# ❌ Don't share across threads
db = DatabaseManager(url)
thread1.start(lambda: db.execute(...))  # UNSAFE

# ✅ Create per-thread instances
def worker():
    db = DatabaseManager(url)
    db.connect()
    db.execute(...)
    db.disconnect()

thread1.start(worker)  # SAFE
```

2. Add test file: `tests/unit/test_concurrency.py`:
```python
import pytest
import threading
import concurrent.futures

def test_multiple_instances_concurrent(db_url):
    """Test multiple DatabaseManager instances work concurrently"""
    def insert_worker(worker_id):
        db = DatabaseManager(db_url)
        db.connect()
        for i in range(10):
            db.execute(
                "INSERT INTO test (worker, value) VALUES (:w, :v)",
                {'w': worker_id, 'v': i}
            )
        db.disconnect()

    # Run 5 concurrent workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(insert_worker, i) for i in range(5)]
        concurrent.futures.wait(futures)

    # Verify all 50 rows inserted
    db = DatabaseManager(db_url)
    db.connect()
    results = db.fetch_all("SELECT COUNT(*) as cnt FROM test")
    assert results[0]['cnt'] == 50
```

**Estimated Effort**: 2-3 hours

---

### Phase 4: Auto-increment ID Support (Future Enhancement)

**Goal**: Provide consistent API for retrieving auto-generated IDs.

**Proposed API**:
```python
result = db.execute(
    "INSERT INTO users (name) VALUES (:name)",
    {'name': 'John'},
    return_id=True  # New parameter
)
# result will contain the auto-generated ID
```

**Implementation**: Requires significant research into database-specific behavior. Defer until user demand justifies the complexity.

---

## 📊 **Summary and Priorities**

| Issue | Priority | Effort | Status |
|-------|----------|--------|--------|
| execute_script() splitting | 🔴 High | 4-6h | Not Started |
| Binary/BLOB support | 🟡 Medium | 3-4h | Not Started |
| Concurrency docs/tests | 🟢 Low | 2-3h | Not Started |
| Auto-increment ID | 🔵 Future | 8-12h | Deferred |

**Total Estimated Effort**: 9-13 hours for high/medium priority items

---

## 🔮 **Forward-Looking Features** (From FORWARD_LOOKING_DATABASE_REQUIREMENTS.md)

The following features are **not yet implemented** but may be needed for future use cases:

### 🔴 High Priority (Production Readiness)
| Feature | Description | Effort | Priority |
|---------|-------------|--------|----------|
| **Connection Pooling** | Pool of reusable connections for high-concurrency apps | 12-16h | High |
| **Transaction Management** | Explicit BEGIN/COMMIT/ROLLBACK with savepoints | 8-12h | High |
| **Streaming Results** | Yield large result sets in chunks (avoid memory issues) | 6-8h | High |
| **Query Performance Tools** | Slow query logging, EXPLAIN analysis | 4-6h | High |

### 🟡 Medium Priority (Advanced Features)
| Feature | Description | Effort | Priority |
|---------|-------------|--------|----------|
| **Row-Level Security** | Multi-tenancy support with automatic filtering | 8-12h | Medium |
| **Migration Rollback** | Down migrations for production safety | 6-8h | Medium |
| **Backup/Recovery** | Database backup, restore, point-in-time recovery | 10-14h | Medium |
| **Full-Text Search** | Full-text indexes, search ranking, fuzzy matching | 12-16h | Medium |

### 🟢 Low Priority (Scale & Advanced)
| Feature | Description | Effort | Priority |
|---------|-------------|--------|----------|
| **Sharding/Partitioning** | Horizontal scaling across multiple databases | 20-30h | Low |
| **Change Data Capture** | Track all changes for audit/event sourcing | 16-20h | Low |
| **Encryption/Compliance** | Column-level encryption, PII masking, GDPR | 12-16h | Low |
| **Query Builder/ORM** | Type-safe query builder for better DX | 16-24h | Low |
| **Test Fixtures** | Data factories, snapshots for testing | 8-12h | Low |
| **Schema Validation** | Runtime type checking and validation | 10-14h | Low |

### ❌ Not Applicable / Out of Scope
- **Analytics/OLAP** - Use dedicated analytics databases (ClickHouse, BigQuery)
- **Graph Queries** - Use graph databases (Neo4j)
- **Time-Series** - Use specialized databases (InfluxDB, TimescaleDB)

**Total Estimated Effort for All Forward-Looking Features**: ~140-200 hours

---

## 🎯 **Recommended Implementation Order**

### Phase 1: Fix Critical Issues (9-13 hours)
1. Execute_script() SQL splitting
2. Binary/BLOB support
3. Concurrency documentation

### Phase 2: Production Readiness (30-42 hours)
4. Connection pooling
5. Transaction management (BEGIN/COMMIT/ROLLBACK/savepoints)
6. Streaming query results
7. Slow query logging

### Phase 3: Advanced Features (36-50 hours)
8. Row-level security helpers
9. Migration rollback support
10. Backup/restore utilities
11. Full-text search support

### Phase 4: Scale & Enterprise (80-120 hours)
12. Database sharding framework
13. Change data capture
14. Encryption/compliance
15. Query builder API
16. Test data factories
17. Schema validation

---

## 📝 **Dependencies to Add**

Update `pyproject.toml`:
```toml
dependencies = [
    "sqlparse>=0.4.0"  # For execute_script() SQL parsing
]

[project.optional-dependencies]
# Future dependencies for advanced features
pooling = [
    "sqlalchemy>=2.0.0"  # For connection pooling
]
search = [
    "whoosh>=2.7.0"  # For full-text search
]
validation = [
    "pydantic>=2.0.0"  # For schema validation
]
testing = [
    "faker>=20.0.0"  # For test data generation
]
```
