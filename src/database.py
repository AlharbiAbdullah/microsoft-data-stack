"""Database connection utilities for SQL Server."""

import os
from contextlib import contextmanager
from typing import Generator

import pyodbc
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def get_connection_string() -> str:
    """Build SQL Server connection string from environment variables."""
    host = os.getenv("SQLSERVER_HOST", "localhost")
    port = os.getenv("SQLSERVER_PORT", "1433")
    user = os.getenv("SQLSERVER_USER", "sa")
    password = os.getenv("SQLSERVER_PASSWORD", "")
    database = os.getenv("SQLSERVER_DATABASE", "datawarehouse")

    return (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host},{port};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
    )


def get_sqlalchemy_url() -> str:
    """Build SQLAlchemy connection URL."""
    host = os.getenv("SQLSERVER_HOST", "localhost")
    port = os.getenv("SQLSERVER_PORT", "1433")
    user = os.getenv("SQLSERVER_USER", "sa")
    password = os.getenv("SQLSERVER_PASSWORD", "")
    database = os.getenv("SQLSERVER_DATABASE", "datawarehouse")

    return (
        f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}"
        f"?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )


def get_engine() -> Engine:
    """Create SQLAlchemy engine for SQL Server."""
    return create_engine(get_sqlalchemy_url(), echo=False)


@contextmanager
def get_connection() -> Generator[pyodbc.Connection, None, None]:
    """Context manager for database connections."""
    conn = pyodbc.connect(get_connection_string())
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_cursor() -> Generator[pyodbc.Cursor, None, None]:
    """Context manager for database cursors."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()


def execute_query(query: str, params: tuple | None = None) -> list[dict]:
    """Execute a SELECT query and return results as list of dicts."""
    with get_cursor() as cursor:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def execute_non_query(query: str, params: tuple | None = None) -> int:
    """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
    with get_cursor() as cursor:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.rowcount


def test_connection() -> bool:
    """Test database connectivity."""
    try:
        with get_cursor() as cursor:
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
