"""
NexusQL - Multi-database abstraction layer with unified API
"""

from .manager import DatabaseManager
from .interfaces import (
    ConnectionConfig,
    DatabaseType,
    QueryResult,
    DatabaseInterface,
    create_query_result,
    create_error_result
)

__version__ = "0.1.0"
__all__ = [
    'DatabaseManager',
    'ConnectionConfig',
    'DatabaseType',
    'QueryResult',
    'DatabaseInterface',
    'create_query_result',
    'create_error_result'
]