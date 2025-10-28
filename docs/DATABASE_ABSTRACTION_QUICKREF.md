# Database Abstraction Layer - Quick Reference

## 🎯 Bottom Line

**Your queries don't change. Period.**

Same SQL. Same parameters. Same results. Just more flexibility.

## 📊 Impact Assessment

| Aspect | Impact | Notes |
|--------|--------|-------|
| **SQL Syntax** | ✅ No change | Identical queries |
| **Parameters** | ✅ No change | Same `:param` format |
| **Return Format** | ✅ No change | Still `List[Dict]` |
| **SELECT queries** | ✅ No change | 100% identical |
| **INSERT queries** | ✅ No change | 100% identical |
| **UPDATE queries** | ✅ No change | 100% identical |
| **DELETE queries** | ✅ No change | 100% identical |
| **Code changes** | ✅ Minimal | Just import line |

## 🚀 Quick Start

### Simplest Migration (Keep NexusQL)

**Before:**
```python
from nexusql import DatabaseManager
db = DatabaseManager("sqlite:///app.db")
```

**After:**
```python
from ia_modules.database import get_database
db = get_database("sqlite:///app.db")  # Uses NexusQL by default
```

**That's it!** All queries stay the same.

### To Switch Backends Later

```python
# One line change - zero query changes
db = get_database("sqlite:///app.db", backend="sqlalchemy")
```

## 📝 Query Examples (Work with Both)

```python
# All these are IDENTICAL regardless of backend

# SELECT
users = db.execute("SELECT * FROM users WHERE id = :id", {"id": 1})

# INSERT
db.execute(
    "INSERT INTO users (name, email) VALUES (:name, :email)",
    {"name": "Alice", "email": "alice@example.com"}
)

# UPDATE
db.execute(
    "UPDATE users SET email = :email WHERE id = :id",
    {"email": "new@example.com", "id": 1}
)

# DELETE
db.execute("DELETE FROM users WHERE id = :id", {"id": 1})

# FETCH ONE
user = db.fetch_one("SELECT * FROM users WHERE email = :email", {"email": "test@example.com"})

# FETCH ALL
all_users = db.fetch_all("SELECT * FROM users")
```

## 🔧 Configuration Options

### Option 1: Explicit (Recommended)
```python
db = get_database(url, backend="nexusql")     # Explicit NexusQL
db = get_database(url, backend="sqlalchemy")  # Explicit SQLAlchemy
```

### Option 2: Environment Variable
```bash
export IA_DATABASE_BACKEND=sqlalchemy
```
```python
db = get_database(url)  # Uses environment variable
```

### Option 3: Global Default
```python
from ia_modules.database import set_default_backend, DatabaseBackend
set_default_backend(DatabaseBackend.SQLALCHEMY)
db = get_database(url)  # Uses global default
```

## ⚖️ When to Use Which

### Use NexusQL When:
- ✅ Building multi-database apps
- ✅ Need SQL translation (PostgreSQL → all DBs)
- ✅ Want lightweight, simple database access
- ✅ Don't need ORM features

### Use SQLAlchemy When:
- ✅ Need ORM (object-relational mapping)
- ✅ Have complex data models with relationships
- ✅ Want advanced query builder
- ✅ Need production-grade connection pooling
- ✅ Already using SQLAlchemy ecosystem

### Use the Abstraction When:
- ✅ Want flexibility for the future
- ✅ Testing different backends
- ✅ Migrating between ORMs
- ✅ Supporting multiple deployment scenarios

## 🎁 What You Get

### With NexusQL Backend (Default)
```python
db = get_database("sqlite:///app.db", backend="nexusql")

# Bonus: SQL Translation
db.execute("""
    CREATE TABLE products (
        id SERIAL PRIMARY KEY,        -- Works on SQLite!
        name VARCHAR(255),             -- Auto-translated
        active BOOLEAN DEFAULT TRUE    -- Auto-translated
    )
""")
```

### With SQLAlchemy Backend (Optional)
```python
db = get_database("postgresql://localhost/db", backend="sqlalchemy")

# Bonus: ORM Access
session = db.session
user = session.query(User).filter_by(id=1).first()

# Bonus: Connection Pooling
db = get_database(url, backend="sqlalchemy", pool_size=10, max_overflow=20)
```

## ✅ Checklist

- [x] Queries are 100% identical ✅
- [x] Parameters are 100% identical ✅
- [x] Return format is 100% identical ✅
- [x] Can switch backends anytime ✅
- [x] No code rewrite needed ✅
- [x] Tested and verified ✅

## 📚 More Info

- **Full Guide**: [DATABASE_ABSTRACTION_GUIDE.md](DATABASE_ABSTRACTION_GUIDE.md)
- **Query Comparison**: [QUERY_COMPARISON_GUIDE.md](QUERY_COMPARISON_GUIDE.md)
- **Examples**: `python ia_modules/database/compare_backends.py`
- **Documentation**: [ia_modules/database/README.md](ia_modules/database/README.md)

## 🎯 Key Takeaway

**The abstraction layer gives you OPTIONS, not OBLIGATIONS.**

- Your queries don't change
- You're not locked into one backend
- Switch anytime with zero rewrites
- Best of both worlds available when you need it

**It's all upside, no downside!** 🚀
