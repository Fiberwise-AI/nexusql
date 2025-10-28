"""Pytest configuration for NexusQL tests"""
import pytest
import os
from pathlib import Path


@pytest.fixture
def temp_db_path(tmp_path):
    """Provide a temporary database path"""
    return str(tmp_path / "test.db")


@pytest.fixture
def sqlite_url(temp_db_path):
    """Provide a SQLite database URL"""
    return f"sqlite:///{temp_db_path}"


# PostgreSQL test configuration
@pytest.fixture
def postgresql_url():
    """Get PostgreSQL test URL from environment"""
    return os.getenv("TEST_POSTGRESQL_URL", "postgresql://testuser:testpass@localhost:5432/nexusql_test")


# MySQL test configuration
@pytest.fixture
def mysql_url():
    """Get MySQL test URL from environment"""
    return os.getenv("TEST_MYSQL_URL", "mysql://testuser:testpass@localhost:3306/nexusql_test")


# MSSQL test configuration
@pytest.fixture
def mssql_url():
    """Get MSSQL test URL from environment"""
    return os.getenv("TEST_MSSQL_URL", "mssql://sa:TestPass123!@localhost:1433/master")


@pytest.fixture
def skip_if_no_postgresql(postgresql_url):
    """Skip test if PostgreSQL is not available"""
    try:
        from nexusql import DatabaseManager
        db = DatabaseManager(postgresql_url)
        if not db.connect():
            pytest.skip("PostgreSQL not available")
        db.disconnect()
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")


@pytest.fixture
def skip_if_no_mysql(mysql_url):
    """Skip test if MySQL is not available"""
    try:
        from nexusql import DatabaseManager
        db = DatabaseManager(mysql_url)
        if not db.connect():
            pytest.skip("MySQL not available")
        db.disconnect()
    except Exception as e:
        pytest.skip(f"MySQL not available: {e}")


@pytest.fixture
def skip_if_no_mssql(mssql_url):
    """Skip test if MSSQL is not available"""
    try:
        from nexusql import DatabaseManager
        db = DatabaseManager(mssql_url)
        if not db.connect():
            pytest.skip("MSSQL not available")
        db.disconnect()
    except Exception as e:
        pytest.skip(f"MSSQL not available: {e}")


@pytest.fixture
def db_config(request, sqlite_url, postgresql_url, mysql_url, mssql_url):
    """Provide a ConnectionConfig for the requested database type"""
    from nexusql import ConnectionConfig

    db_type = request.param if hasattr(request, 'param') else 'sqlite'

    url_map = {
        'sqlite': sqlite_url,
        'postgresql': postgresql_url,
        'mysql': mysql_url,
        'mssql': mssql_url
    }

    db_url = url_map.get(db_type, sqlite_url)
    return ConnectionConfig.from_url(db_url)


@pytest.fixture
def db_manager(request, sqlite_url, postgresql_url, mysql_url, mssql_url):
    """Provide a DatabaseManager for the requested database type"""
    from nexusql import DatabaseManager

    db_type = request.param if hasattr(request, 'param') else 'sqlite'

    url_map = {
        'sqlite': sqlite_url,
        'postgresql': postgresql_url,
        'mysql': mysql_url,
        'mssql': mssql_url
    }

    db_url = url_map.get(db_type, sqlite_url)
    db = DatabaseManager(db_url)

    # For MSSQL, ensure test database exists first
    if db_type == 'mssql':
        from urllib.parse import urlparse
        parsed = urlparse(mssql_url)
        db_name = parsed.path.lstrip('/')

        # Build master URL preserving all query parameters
        master_url = f"{parsed.scheme}://{parsed.netloc}/master"
        if parsed.query:
            master_url += f"?{parsed.query}"

        master_db = DatabaseManager(master_url)
        try:
            if not master_db.connect():
                pytest.skip("MSSQL master database not available")

            # Create test database if it doesn't exist
            master_db._connection.autocommit = True
            master_db.execute(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{db_name}') CREATE DATABASE {db_name}")
            master_db._connection.autocommit = False
            master_db.disconnect()
        except Exception as e:
            pytest.skip(f"Cannot create MSSQL test database: {e}")

    # Try to connect, skip if not available
    try:
        if not db.connect():
            pytest.skip(f"{db_type} not available")
    except Exception as e:
        pytest.skip(f"{db_type} not available: {e}")

    yield db

    # Cleanup
    try:
        db.disconnect()
    except:
        pass
