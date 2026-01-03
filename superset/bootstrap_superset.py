"""Bootstrap script to configure Superset with SQL Server connection."""

import os

from superset import app, db
from superset.models.core import Database


def create_database_connection():
    """Create the SQL Server database connection in Superset."""
    with app.app_context():
        # Check if connection already exists
        existing = db.session.query(Database).filter_by(
            database_name="Microsoft Data Stack"
        ).first()

        if existing:
            print("Database connection 'Microsoft Data Stack' already exists")
            return

        # Build connection string
        host = os.getenv("SQLSERVER_HOST", "sqlserver")
        port = os.getenv("SQLSERVER_PORT", "1433")
        user = os.getenv("SQLSERVER_USER", "sa")
        password = os.getenv("SQLSERVER_PASSWORD", "")
        database = os.getenv("SQLSERVER_DATABASE", "datawarehouse")

        sqlalchemy_uri = (
            f"mssql+pymssql://{user}:{password}@{host}:{port}/{database}"
        )

        # Create database connection
        new_database = Database(
            database_name="Microsoft Data Stack",
            sqlalchemy_uri=sqlalchemy_uri,
            expose_in_sqllab=True,
            allow_run_async=True,
            allow_ctas=False,
            allow_cvas=False,
            allow_dml=False,
            extra='{"metadata_params": {}, "engine_params": {}}',
        )

        db.session.add(new_database)
        db.session.commit()

        print("Successfully created database connection 'Microsoft Data Stack'")
        print(f"Connected to: {host}:{port}/{database}")


if __name__ == "__main__":
    create_database_connection()
