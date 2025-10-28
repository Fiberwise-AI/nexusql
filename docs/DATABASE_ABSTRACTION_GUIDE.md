# Database Abstraction Layer Implementation Guide

## Overview

Successfully implemented a pluggable database abstraction layer for ia_modules that allows seamless switching between **NexusQL** and **SQLAlchemy** backends.

## Architecture

### Adapter Pattern

```
┌─────────────────────────────────────────────┐
│           Your Application Code             │
│    (Uses DatabaseInterface methods)         │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │ DatabaseInterface │ (Abstract)
         └──────┬────────────┘
                │
       ┌────────┴────────┐
       │                 │
┌──────▼──────┐   ┌─────▼──────────┐
│   NexusQL   │   │  SQLAlchemy    │
│   Adapter   │   │    Adapter     │
└──────┬──────┘   └─────┬──────────┘
       │                │
┌──────▼──────┐   ┌─────▼──────────┐
│   nexusql   │   │  sqlalchemy    │
│   package   │   │    package     │
└─────────────┘   └────────────────┘
```

## File Structure

```
ia_modules/database/
├── __init__.py                    # Public API
├── README.md                      # Comprehensive documentation
├── examples.py                    # Working examples
├── interfaces.py                  # DatabaseInterface + QueryResult
├── factory.py                     # get_database() factory
└── adapters/
    ├── __init__.py
    ├── nexusql_adapter.py         # NexusQL wrapper
    └── sqlalchemy_adapter.py      # SQLAlchemy wrapper
```

## Quick Start

### Installation

```bash
# Install NexusQL (default)
pip install nexusql

# Install SQLAlchemy (optional)
pip install sqlalchemy

# Install both
pip install nexusql sqlalchemy
```

### Basic Usage

```python
from ia_modules.database import get_database

# Uses NexusQL by default
db = get_database("sqlite:///app.db")
db.connect()

# Standard interface works with both backends
users = db.execute("SELECT * FROM users WHERE id = :id", {"id": 1})
user = db.fetch_one("SELECT * FROM users WHERE email = :email", {"email": "test@example.com"})

db.disconnect()
```

### Switching Backends

```python
# Method 1: Explicit
db = get_database("sqlite:///app.db", backend="sqlalchemy")

# Method 2: Environment variable
import os
os.environ["IA_DATABASE_BACKEND"] = "sqlalchemy"
db = get_database("sqlite:///app.db")

# Method 3: Global default
from ia_modules.database import set_default_backend, DatabaseBackend
set_default_backend(DatabaseBackend.SQLALCHEMY)
db = get_database("sqlite:///app.db")
```

## Interface

### DatabaseInterface (Abstract Base Class)

All adapters implement these methods:

```python
class DatabaseInterface(ABC):
    # Connection
    def connect() -> bool
    def disconnect()
    async def close()

    # Queries
    def execute(query: str, params: Dict) -> List[Dict]
    async def execute_async(query: str, params: Dict) -> Any
    def fetch_one(query: str, params: Dict) -> Optional[Dict]
    def fetch_all(query: str, params: Dict) -> List[Dict]

    # Utilities
    def table_exists(table_name: str) -> bool
    async def execute_script(script: str) -> QueryResult
    async def initialize(apply_schema: bool, app_migration_paths: List[str]) -> bool

    # Context manager
    def __enter__()
    def __exit__()
```

## Backend Comparison

| Feature | NexusQL | SQLAlchemy |
|---------|---------|------------|
| **Installation** | `pip install nexusql` | `pip install sqlalchemy` |
| **Multi-database** | ✅ Built-in (4 DBs) | ✅ Via dialects (30+ DBs) |
| **SQL Translation** | ✅ PostgreSQL → All | ❌ Manual per DB |
| **ORM Support** | ❌ Raw SQL only | ✅ Full ORM with relationships |
| **Migrations** | ✅ Built-in system | ⚠️ Use Alembic separately |
| **Connection Pooling** | ⚠️ Basic | ✅ Advanced production-ready |
| **Query Complexity** | 🟢 Simple CRUD | 🟡 Complex joins, subqueries |
| **Performance** | ⚡ Fast (no ORM) | ⚡ Fast (with tuning) |
| **Learning Curve** | 🟢 Easy | 🟡 Moderate |
| **Ecosystem** | 🟡 New (2024) | 🟢 Mature (15+ years) |
| **Best Use Case** | Simple queries, multi-DB | Complex models, ORM needs |

## Use Cases

### When to Use NexusQL

✅ **Use NexusQL when:**
- Building multi-database applications
- Need automatic SQL translation
- Want simple, lightweight database access
- Don't need ORM features
- Working with straightforward CRUD operations
- Building microservices with simple data models

**Example:**
```python
# Write once, works on all databases
db = get_database("sqlite:///app.db", backend="nexusql")
db.execute("""
    CREATE TABLE products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        active BOOLEAN DEFAULT TRUE,
        metadata JSONB
    )
""")
# NexusQL translates PostgreSQL → SQLite automatically
```

### When to Use SQLAlchemy

✅ **Use SQLAlchemy when:**
- Building applications with complex data models
- Need ORM features (relationships, lazy loading)
- Working with an existing SQLAlchemy codebase
- Require advanced query capabilities
- Need production-grade connection pooling
- Using Flask, FastAPI, or other SQLAlchemy-integrated frameworks

**Example:**
```python
db = get_database("postgresql://localhost/db", backend="sqlalchemy")
db.connect()

# Access ORM features
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    posts = relationship("Post", back_populates="user")

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="posts")
```

## Advanced Features

### NexusQL-Specific

```python
db = get_database("sqlite:///app.db", backend="nexusql")
db.connect()

# Access underlying NexusQL instance
nexusql = db.nexusql

# Get database type
db_type = db.database_type  # DatabaseType.SQLITE

# Get configuration
config = db.config  # ConnectionConfig object
```

### SQLAlchemy-Specific

```python
db = get_database("postgresql://localhost/db", backend="sqlalchemy")
db.connect()

# Access underlying SQLAlchemy components
engine = db.engine      # SQLAlchemy engine
session = db.session    # Current session

# Create new session
new_session = db.get_new_session()

# Transaction management
with db.begin_transaction():
    db.execute("INSERT INTO users (name) VALUES (:name)", {"name": "Alice"})
    # Auto-commit on success, rollback on exception

# Manual transaction control
db.commit()
db.rollback()
```

## Testing

### Testing with Both Backends

```python
import pytest
from ia_modules.database import get_database

@pytest.fixture(params=["nexusql", "sqlalchemy"])
def db(request):
    """Test with both backends"""
    backend = request.param
    database = get_database("sqlite:///:memory:", backend=backend)
    database.connect()
    yield database
    database.disconnect()

def test_user_operations(db):
    """This test runs twice: once with NexusQL, once with SQLAlchemy"""
    db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    db.execute("INSERT INTO users (name) VALUES (:name)", {"name": "Alice"})
    user = db.fetch_one("SELECT * FROM users WHERE name = :name", {"name": "Alice"})
    assert user["name"] == "Alice"
```

## Migration Path

### Option 1: Keep NexusQL (Current State)

No changes needed! Everything works as-is:

```python
from nexusql import DatabaseManager

db = DatabaseManager("sqlite:///app.db")
# Continue using NexusQL directly
```

### Option 2: Use Abstraction Layer with NexusQL

```python
from ia_modules.database import get_database

# Uses NexusQL by default
db = get_database("sqlite:///app.db")
# or explicitly
db = get_database("sqlite:///app.db", backend="nexusql")
```

### Option 3: Switch to SQLAlchemy

```python
from ia_modules.database import get_database

# One line change
db = get_database("sqlite:///app.db", backend="sqlalchemy")
```

### Option 4: Support Both (Recommended)

```python
# config.py
DATABASE_URL = "postgresql://localhost/db"
DATABASE_BACKEND = os.getenv("DB_BACKEND", "nexusql")  # Default to nexusql

# app.py
from ia_modules.database import get_database
from config import DATABASE_URL, DATABASE_BACKEND

db = get_database(DATABASE_URL, backend=DATABASE_BACKEND)
```

Now you can switch backends via environment variable:
```bash
# Use NexusQL
export DB_BACKEND=nexusql
python app.py

# Use SQLAlchemy
export DB_BACKEND=sqlalchemy
python app.py
```

## Real-World Example

### Simple Blog Application

```python
from ia_modules.database import get_database
import os

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///blog.db")
DATABASE_BACKEND = os.getenv("DB_BACKEND", "nexusql")

# Initialize database
db = get_database(DATABASE_URL, backend=DATABASE_BACKEND)
db.connect()

# Create schema
db.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        content TEXT,
        author VARCHAR(100),
        published BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")

# Create post
def create_post(title: str, content: str, author: str):
    return db.execute(
        """
        INSERT INTO posts (title, content, author)
        VALUES (:title, :content, :author)
        """,
        {"title": title, "content": content, "author": author}
    )

# Get post
def get_post(post_id: int):
    return db.fetch_one(
        "SELECT * FROM posts WHERE id = :id",
        {"id": post_id}
    )

# List posts
def list_posts(published_only: bool = True):
    query = "SELECT * FROM posts"
    if published_only:
        query += " WHERE published = :published"
        return db.fetch_all(query, {"published": True})
    return db.fetch_all(query)

# Publish post
def publish_post(post_id: int):
    return db.execute(
        "UPDATE posts SET published = :published WHERE id = :id",
        {"published": True, "id": post_id}
    )

# Usage
create_post("Hello World", "My first blog post!", "Alice")
posts = list_posts()
print(f"Found {len(posts)} published posts")

db.disconnect()
```

Now you can run this with either backend:

```bash
# Development with NexusQL + SQLite
export DATABASE_URL="sqlite:///blog.db"
export DB_BACKEND="nexusql"
python blog.py

# Production with SQLAlchemy + PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost/blog"
export DB_BACKEND="sqlalchemy"
python blog.py
```

## Benefits

1. **Flexibility**: Switch backends without code changes
2. **Future-proofing**: Easy to migrate between ORMs
3. **Testing**: Test with SQLite locally, PostgreSQL in production
4. **Best of Both**: Use NexusQL for simplicity, SQLAlchemy for complexity
5. **Gradual Migration**: Migrate parts of your app at a time
6. **Vendor Independence**: Not locked into one database abstraction

## Performance Considerations

### NexusQL
- Faster for simple queries (no ORM overhead)
- Lower memory usage
- Better for microservices and simple APIs

### SQLAlchemy
- Optimized for complex queries with relationships
- Connection pooling improves throughput
- Better for applications with complex data models

## Next Steps

1. **Try the examples**: Run `python ia_modules/database/examples.py`
2. **Read the docs**: See `ia_modules/database/README.md`
3. **Choose your backend**: Start with NexusQL, migrate to SQLAlchemy if needed
4. **Write backend-agnostic code**: Use DatabaseInterface methods only
5. **Test both backends**: Use parametrized fixtures

## Summary

✅ **Implemented:**
- DatabaseInterface abstract base class
- NexuSQLAdapter wrapping nexusql
- SQLAlchemyAdapter wrapping sqlalchemy
- Factory pattern with get_database()
- Multiple configuration methods
- Comprehensive documentation and examples

✅ **Key Features:**
- Pluggable backends (NexusQL, SQLAlchemy)
- Unified interface for both
- Easy backend switching
- Access to backend-specific features
- Production-ready

✅ **Use Cases:**
- Use NexusQL: Simple queries, multi-database, SQL translation
- Use SQLAlchemy: Complex models, ORM features, mature ecosystem
- Use abstraction: Future flexibility, gradual migration
