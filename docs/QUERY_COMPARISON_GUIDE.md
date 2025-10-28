# Query Comparison: NexusQL vs SQLAlchemy

## TL;DR - Do Your Queries Change?

**Short answer: NO** - If you use the DatabaseInterface methods, your queries are **100% identical**.

**Both backends use the same query syntax:**
- Named parameters: `:param_name`
- Same SQL strings
- Same parameter dictionaries
- Same return format (List[Dict])

## Side-by-Side Comparison

### Example 1: Simple SELECT

**With NexusQL:**
```python
from ia_modules.database import get_database

db = get_database("sqlite:///app.db", backend="nexusql")
db.connect()

users = db.execute(
    "SELECT * FROM users WHERE id = :id",
    {"id": 1}
)
# Returns: [{'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}]
```

**With SQLAlchemy:**
```python
from ia_modules.database import get_database

db = get_database("sqlite:///app.db", backend="sqlalchemy")
db.connect()

users = db.execute(
    "SELECT * FROM users WHERE id = :id",
    {"id": 1}
)
# Returns: [{'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}]
```

**Result: IDENTICAL** ✅

### Example 2: INSERT with Parameters

**With NexusQL:**
```python
db.execute(
    "INSERT INTO users (name, email) VALUES (:name, :email)",
    {"name": "Bob", "email": "bob@example.com"}
)
```

**With SQLAlchemy:**
```python
db.execute(
    "INSERT INTO users (name, email) VALUES (:name, :email)",
    {"name": "Bob", "email": "bob@example.com"}
)
```

**Result: IDENTICAL** ✅

### Example 3: UPDATE

**With NexusQL:**
```python
db.execute(
    "UPDATE users SET email = :email WHERE id = :id",
    {"email": "newemail@example.com", "id": 1}
)
```

**With SQLAlchemy:**
```python
db.execute(
    "UPDATE users SET email = :email WHERE id = :id",
    {"email": "newemail@example.com", "id": 1}
)
```

**Result: IDENTICAL** ✅

### Example 4: Complex JOIN

**With NexusQL:**
```python
results = db.execute("""
    SELECT u.name, p.title, p.created_at
    FROM users u
    JOIN posts p ON u.id = p.user_id
    WHERE u.status = :status
    ORDER BY p.created_at DESC
""", {"status": "active"})
```

**With SQLAlchemy:**
```python
results = db.execute("""
    SELECT u.name, p.title, p.created_at
    FROM users u
    JOIN posts p ON u.id = p.user_id
    WHERE u.status = :status
    ORDER BY p.created_at DESC
""", {"status": "active"})
```

**Result: IDENTICAL** ✅

## The ONLY Difference: Advanced Features

The **basic queries are identical**. The difference is in **advanced features** you can optionally use.

### What NexusQL Adds (Optional)

#### 1. Automatic SQL Translation

Write PostgreSQL syntax, works on all databases:

```python
db = get_database("sqlite:///app.db", backend="nexusql")

# PostgreSQL syntax
db.execute("""
    CREATE TABLE products (
        id SERIAL PRIMARY KEY,           -- Auto-translated to INTEGER AUTOINCREMENT
        name VARCHAR(255),                -- Works on SQLite as TEXT
        active BOOLEAN DEFAULT TRUE,      -- Translated to INTEGER
        metadata JSONB,                   -- Translated to TEXT
        created_at TIMESTAMP DEFAULT NOW() -- Translated to TEXT
    )
""")

# This SAME query works on:
# - SQLite
# - PostgreSQL
# - MySQL
# - MSSQL
```

With SQLAlchemy, you'd need to write database-specific SQL.

#### 2. Built-in Migrations

```python
db = get_database("sqlite:///app.db", backend="nexusql")
await db.initialize(
    apply_schema=True,
    app_migration_paths=["migrations/"]
)
# Automatically tracks and runs migrations
```

### What SQLAlchemy Adds (Optional)

#### 1. ORM (Object-Relational Mapping)

**You can optionally use the ORM instead of raw SQL:**

```python
db = get_database("postgresql://localhost/db", backend="sqlalchemy")
db.connect()

# Option A: Use raw SQL (same as NexusQL)
users = db.execute("SELECT * FROM users WHERE id = :id", {"id": 1})

# Option B: Use SQLAlchemy ORM (advanced feature)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)

# ORM query (SQLAlchemy-specific)
session = db.session
user = session.query(User).filter(User.id == 1).first()
print(user.name)  # Access via attributes
```

**Note:** ORM is **optional**. You can keep using raw SQL.

#### 2. Advanced Query Builder

```python
# Option A: Raw SQL (works with both)
db.execute("SELECT * FROM users WHERE name LIKE :pattern", {"pattern": "A%"})

# Option B: SQLAlchemy query builder (SQLAlchemy-specific)
from sqlalchemy import select, Table, MetaData
metadata = MetaData()
users = Table('users', metadata, autoload_with=db.engine)
stmt = select(users).where(users.c.name.like('A%'))
result = db.session.execute(stmt)
```

#### 3. Connection Pooling

```python
# SQLAlchemy handles connection pooling automatically
db = get_database(
    "postgresql://localhost/db",
    backend="sqlalchemy",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

## Migration Impact Assessment

### Scenario 1: You Only Use Raw SQL

**Current Code:**
```python
from nexusql import DatabaseManager

db = DatabaseManager("sqlite:///app.db")
db.connect()
users = db.execute("SELECT * FROM users WHERE id = :id", {"id": 1})
```

**With Abstraction Layer (NexusQL):**
```python
from ia_modules.database import get_database

db = get_database("sqlite:///app.db", backend="nexusql")
db.connect()
users = db.execute("SELECT * FROM users WHERE id = :id", {"id": 1})
```

**Impact:** ✅ **Zero query changes** - Just different import

**With Abstraction Layer (SQLAlchemy):**
```python
from ia_modules.database import get_database

db = get_database("sqlite:///app.db", backend="sqlalchemy")
db.connect()
users = db.execute("SELECT * FROM users WHERE id = :id", {"id": 1})
```

**Impact:** ✅ **Zero query changes** - Identical code!

### Scenario 2: You Use CREATE TABLE Statements

**Current Code (NexusQL):**
```python
db.execute("""
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        active BOOLEAN DEFAULT TRUE
    )
""")
```

**With NexusQL Backend:**
```python
db = get_database("sqlite:///app.db", backend="nexusql")
db.execute("""
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        active BOOLEAN DEFAULT TRUE
    )
""")
# ✅ Works! Auto-translates to SQLite syntax
```

**With SQLAlchemy Backend:**
```python
db = get_database("sqlite:///app.db", backend="sqlalchemy")
db.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,  -- ⚠️ Use SQLite syntax
        name TEXT,                -- ⚠️ Use TEXT not VARCHAR
        active INTEGER DEFAULT 1  -- ⚠️ Use INTEGER not BOOLEAN
    )
""")
# ⚠️ Need to use database-specific syntax
```

**Impact:** ⚠️ **CREATE TABLE statements need database-specific syntax with SQLAlchemy**

**Solution:** Keep using NexusQL for schema creation, or use SQLAlchemy's declarative models.

### Scenario 3: You Want to Use ORM (Optional)

**With SQLAlchemy (NEW capability):**
```python
db = get_database("postgresql://localhost/db", backend="sqlalchemy")

# Define ORM model
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)

# Use ORM
session = db.session
user = session.query(User).filter_by(id=1).first()
user.name = "New Name"
session.commit()
```

**Impact:** ✅ **NEW feature** - Optionally available with SQLAlchemy

## Real-World Example

Let's say you have a user management module:

### Current Code (Direct NexusQL)

```python
from nexusql import DatabaseManager

class UserService:
    def __init__(self, db_url: str):
        self.db = DatabaseManager(db_url)
        self.db.connect()

    def get_user(self, user_id: int):
        return self.db.fetch_one(
            "SELECT * FROM users WHERE id = :id",
            {"id": user_id}
        )

    def create_user(self, name: str, email: str):
        return self.db.execute(
            "INSERT INTO users (name, email) VALUES (:name, :email)",
            {"name": name, "email": email}
        )

    def list_active_users(self):
        return self.db.fetch_all(
            "SELECT * FROM users WHERE active = :active",
            {"active": True}
        )
```

### With Abstraction Layer (No Query Changes)

```python
from ia_modules.database import get_database

class UserService:
    def __init__(self, db_url: str, backend: str = "nexusql"):
        self.db = get_database(db_url, backend=backend)
        self.db.connect()

    def get_user(self, user_id: int):
        # ✅ EXACT SAME QUERY
        return self.db.fetch_one(
            "SELECT * FROM users WHERE id = :id",
            {"id": user_id}
        )

    def create_user(self, name: str, email: str):
        # ✅ EXACT SAME QUERY
        return self.db.execute(
            "INSERT INTO users (name, email) VALUES (:name, :email)",
            {"name": name, "email": email}
        )

    def list_active_users(self):
        # ✅ EXACT SAME QUERY
        return self.db.fetch_all(
            "SELECT * FROM users WHERE active = :active",
            {"active": True}
        )
```

**Difference:** Only the initialization! All queries are identical.

**Now you can switch backends:**
```python
# Development
service = UserService("sqlite:///dev.db", backend="nexusql")

# Production
service = UserService("postgresql://prod/db", backend="sqlalchemy")
```

## Query Impact Summary

| Query Type | NexusQL → NexusQL Adapter | NexusQL → SQLAlchemy Adapter |
|------------|---------------------------|------------------------------|
| **SELECT** | ✅ No change | ✅ No change |
| **INSERT** | ✅ No change | ✅ No change |
| **UPDATE** | ✅ No change | ✅ No change |
| **DELETE** | ✅ No change | ✅ No change |
| **JOIN** | ✅ No change | ✅ No change |
| **WHERE with params** | ✅ No change | ✅ No change |
| **CREATE TABLE (PostgreSQL syntax)** | ✅ Auto-translates | ⚠️ Need DB-specific syntax |
| **Migrations** | ✅ Built-in | ⚠️ Use Alembic separately |

## Recommendations

### Keep It Simple (Recommended)

**Use the abstraction layer with raw SQL:**

```python
from ia_modules.database import get_database

# Your choice of backend
db = get_database(DATABASE_URL, backend=BACKEND)

# All your queries stay the same
users = db.execute("SELECT * FROM users")
db.execute("INSERT INTO users (name) VALUES (:name)", {"name": "Alice"})
```

**Impact:** ✅ **Zero query changes**

### Advanced Usage (Optional)

**When you need ORM features:**

```python
db = get_database(DATABASE_URL, backend="sqlalchemy")

# Most queries stay the same
users = db.execute("SELECT * FROM users")

# Advanced queries can use ORM
session = db.session
user = session.query(User).filter_by(id=1).first()
```

**Impact:** ✅ **Most queries unchanged**, ORM is optional addition

## Bottom Line

**Your queries DON'T change** when using the DatabaseInterface methods:
- ✅ Same SQL strings
- ✅ Same parameter format (`:param_name`)
- ✅ Same return format (`List[Dict]`)
- ✅ Works with both backends

**The only differences are:**
1. **NexusQL** auto-translates SQL dialects (useful for CREATE TABLE)
2. **SQLAlchemy** offers optional ORM features (if you want them)

**You get flexibility without breaking your code!**
