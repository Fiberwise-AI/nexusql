# NexusQL

Multi-database abstraction layer with unified API for PostgreSQL, MySQL, SQLite, and MSSQL.

## Features

- ✅ **Unified API** - Same code works across 4 databases (PostgreSQL, MySQL, SQLite, MSSQL)
- ✅ **Named Parameters** - Safe from SQL injection with `:param` syntax
- ✅ **Auto-migrations** - Versioned schema management with automatic translation
- ✅ **SQL Translation** - Write PostgreSQL canonical syntax, automatically translates to all databases
- ✅ **Type Safety** - Full typing support with Python 3.10+
- ✅ **Async Ready** - Async/await compatible API
- ✅ **Production Ready** - Comprehensive test coverage

## Installation

```bash
# SQLite only (no additional dependencies)
pip install nexusql

# With PostgreSQL support
pip install nexusql[postgresql]

# With MySQL support
pip install nexusql[mysql]

# With MSSQL support
pip install nexusql[mssql]

# With all database drivers
pip install nexusql[all]

# For development (includes all drivers and testing tools)
pip install nexusql[dev]
```

## Quick Start

```python
from nexusql import DatabaseManager

# SQLite (no server needed)
db = DatabaseManager("sqlite:///app.db")

# PostgreSQL
db = DatabaseManager("postgresql://user:pass@localhost:5432/mydb")

# MySQL
db = DatabaseManager("mysql://user:pass@localhost:3306/mydb")

# MSSQL
db = DatabaseManager("mssql+pyodbc://user:pass@localhost:1433/mydb")

# Initialize with schema migrations
await db.initialize(apply_schema=True)

# Execute queries with named parameters (safe from SQL injection)
users = db.execute(
    "SELECT * FROM users WHERE email = :email",
    {"email": "user@example.com"}
)

# Fetch single row
user = db.fetch_one(
    "SELECT * FROM users WHERE id = :id",
    {"id": 123}
)

# Fetch all rows
all_users = db.fetch_all(
    "SELECT * FROM users WHERE active = :active",
    {"active": True}
)

# Execute INSERT/UPDATE/DELETE
db.execute(
    "INSERT INTO users (email, name) VALUES (:email, :name)",
    {"email": "new@example.com", "name": "John Doe"}
)
```

## SQL Translation

NexusQL uses PostgreSQL as the canonical SQL syntax and automatically translates to other databases:

```python
# Write once in PostgreSQL syntax
create_table_sql = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
)
"""

# Works on all databases! NexusQL translates:
# - SERIAL → INTEGER AUTOINCREMENT (SQLite)
# - SERIAL → INT AUTO_INCREMENT (MySQL)
# - SERIAL → INT IDENTITY(1,1) (MSSQL)
# - BOOLEAN → INTEGER (SQLite), TINYINT(1) (MySQL), BIT (MSSQL)
# - JSONB → TEXT (SQLite), JSON (MySQL), NVARCHAR(MAX) (MSSQL)
# - NOW() → CURRENT_TIMESTAMP (SQLite), GETDATE() (MSSQL)

db.execute(create_table_sql)
```

## Migrations

NexusQL includes a built-in migration system:

```python
from nexusql import DatabaseManager
from pathlib import Path

db = DatabaseManager("sqlite:///app.db")

# Run system migrations + app-specific migrations
await db.initialize(
    apply_schema=True,
    app_migration_paths=[
        "path/to/your/migrations"
    ]
)
```

Migration files follow the pattern `V001__description.sql`:

```sql
-- V001__create_users_table.sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

## Named Parameters

NexusQL enforces named parameters for security and clarity:

```python
# ✅ Good - Named parameters
db.execute(
    "SELECT * FROM users WHERE email = :email AND status = :status",
    {"email": "user@example.com", "status": "active"}
)

# ❌ Bad - Don't do string concatenation
# db.execute(f"SELECT * FROM users WHERE email = '{email}'")  # SQL injection risk!
```

## Connection Management

```python
# Context manager (auto-connect and disconnect)
with DatabaseManager("sqlite:///app.db") as db:
    users = db.execute("SELECT * FROM users")

# Manual connection management
db = DatabaseManager("postgresql://user:pass@localhost:5432/mydb")
db.connect()
try:
    users = db.execute("SELECT * FROM users")
finally:
    db.disconnect()

# Async close
await db.close()
```

## Checking Table Existence

```python
if db.table_exists("users"):
    print("Users table exists")
else:
    db.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL
        )
    """)
```

## Advanced Features

### Running SQL Scripts

```python
# Execute multiple statements at once
script = """
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id),
    name VARCHAR(255) NOT NULL
);
"""

result = await db.execute_script(script)
if result.success:
    print("Script executed successfully")
```

### Custom Migration Paths

```python
# Run migrations from multiple directories
await db.initialize(
    apply_schema=True,
    app_migration_paths=[
        "migrations/core",
        "migrations/features",
        "migrations/plugins"
    ]
)
```

## Supported Data Types

| PostgreSQL (Canonical) | SQLite | MySQL | MSSQL |
|------------------------|--------|-------|-------|
| SERIAL | INTEGER AUTOINCREMENT | INT AUTO_INCREMENT | INT IDENTITY(1,1) |
| BOOLEAN | INTEGER | TINYINT(1) | BIT |
| VARCHAR(n) | TEXT | VARCHAR(n) | NVARCHAR(n) |
| TEXT | TEXT | TEXT | NVARCHAR(MAX) |
| JSONB | TEXT | JSON | NVARCHAR(MAX) |
| JSON | TEXT | JSON | NVARCHAR(MAX) |
| UUID | TEXT | CHAR(36) | UNIQUEIDENTIFIER |
| TIMESTAMP | TEXT | TIMESTAMP | DATETIME2 |

## Supported Functions

| PostgreSQL (Canonical) | SQLite | MySQL | MSSQL |
|------------------------|--------|-------|-------|
| NOW() | CURRENT_TIMESTAMP | NOW() | GETDATE() |
| gen_random_uuid() | hex(randomblob(16)) | UUID() | NEWID() |
| CURRENT_TIMESTAMP | CURRENT_TIMESTAMP | CURRENT_TIMESTAMP | GETDATE() |

## API Reference

### DatabaseManager

#### `__init__(database_url_or_config)`
Initialize with database URL string or ConnectionConfig object.

#### `connect() -> bool`
Connect to the database.

#### `disconnect()`
Disconnect from the database.

#### `async initialize(apply_schema=True, app_migration_paths=None) -> bool`
Initialize database and optionally apply migrations.

#### `execute(query, params=None) -> List[Dict]`
Execute query with named parameters. Returns list of dicts for SELECT, empty list for INSERT/UPDATE/DELETE.

#### `fetch_one(query, params=None) -> Optional[Dict]`
Fetch single row with named parameters.

#### `fetch_all(query, params=None) -> List[Dict]`
Fetch all rows with named parameters.

#### `table_exists(table_name) -> bool`
Check if table exists.

#### `async execute_script(script) -> QueryResult`
Execute multiple SQL statements.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nexusql --cov-report=html

# Run specific test file
pytest tests/unit/test_manager.py -v
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

MIT

## Credits

NexusQL was extracted from the [ia_modules](https://github.com/yourusername/ia_modules) project to provide a standalone, reusable database abstraction layer.
