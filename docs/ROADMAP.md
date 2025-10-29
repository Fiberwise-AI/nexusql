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

## ✅ **Recently Resolved Issues**

### ✅ Issue #1: execute_script() SQL Splitting is Fragile - **FIXED**

**Location**: `nexusql/manager.py:792-935`

**Problem**: For non-SQLite databases, `execute_script()` was using naive `;` splitting which failed on SQL containing semicolons in string literals or function bodies.

**Solution**: Implemented robust SQL statement parser `_split_sql_statements()` that properly handles:
- Single-quoted strings with escaped quotes (`'a''b'`)
- Double-quoted identifiers with escaped quotes (`"table""name"`)
- Dollar-quoted strings for PostgreSQL functions (`$$`, `$tag$`)
- Single-line comments (`--`)
- Multi-line comments (`/* */`)
- Comment-only statements are filtered out to prevent empty query errors

**Tests Added**:
- Unit tests: [tests/unit/test_sql_splitting.py](../tests/unit/test_sql_splitting.py) - 14 test cases
- Integration tests: [tests/integration/test_execute_script.py](../tests/integration/test_execute_script.py) - 35 test cases across PostgreSQL, MySQL, and MSSQL

**Test Results**: ✅ All 49 tests passing across all database backends

### ✅ Issue #2: Binary/BLOB Parameter Handling - **FIXED**

**Location**: No code changes required - binary data already handled correctly by `_convert_params()`

**Problem**: No tests existed to verify that binary data (bytes) can be passed as parameters and retrieved correctly across different database backends.

**Solution**: Created comprehensive test suite demonstrating that binary data handling works correctly without code modifications. The existing parameter conversion system properly handles `bytes` objects.

**Database-Specific Types Tested**:
- SQLite: BLOB
- PostgreSQL: BYTEA
- MySQL: LONGBLOB (for larger data)
- MSSQL: VARBINARY(MAX)

**Tests Added**:
- Integration tests: [tests/integration/test_binary_data.py](../tests/integration/test_binary_data.py) - 60 test cases covering:
  - Basic binary INSERT/SELECT operations
  - Empty bytes and NULL handling
  - All byte values (0-255)
  - Special sequences (PNG headers, null bytes, high-entropy data)
  - Various sizes (1KB, 64KB, 1MB)
  - Multiple rows and UPDATE operations
  - Edge cases (SQL injection patterns, repeated bytes)

**Test Results**: ✅ All 60 tests passing across SQLite, PostgreSQL, MySQL, and MSSQL

---

## 🔴 **Outstanding Issues**

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

### Phase 1: Connection Pooling/Concurrency (Low Priority)

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

### Phase 2: Auto-increment ID Support (Future Enhancement)

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
| ~~execute_script() splitting~~ | 🔴 High | ~~4-6h~~ | ✅ **Completed** |
| ~~Binary/BLOB support~~ | 🟡 Medium | ~~3-4h~~ | ✅ **Completed** |
| Concurrency docs/tests | 🟢 Low | 2-3h | Not Started |
| Auto-increment ID | 🔵 Future | 8-12h | Deferred |

**Total Remaining Effort**: 2-3 hours for remaining priority items

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

### ✅ Phase 1: Fix Critical Issues - **COMPLETE**
1. ✅ Execute_script() SQL splitting - **DONE**
2. ✅ Binary/BLOB support - **DONE**
3. Concurrency documentation - **TODO**

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
