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
