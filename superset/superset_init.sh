#!/bin/bash
set -e

echo "=== Microsoft Data Stack - Superset Initialization ==="

# Wait for SQL Server to be ready
echo "Waiting for SQL Server to be ready..."
sleep 15

# Initialize Superset database
echo "Upgrading Superset database..."
superset db upgrade

# Create admin user if it doesn't exist
echo "Creating admin user..."
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@example.com \
    --password admin || true

# Initialize Superset
echo "Initializing Superset..."
superset init

# Run bootstrap to set up database connection
echo "Setting up SQL Server database connection..."
python /app/bootstrap_superset.py || echo "Bootstrap script not found or failed - manual setup required"

echo "=== Superset initialization complete ==="
echo "Access Superset at: http://localhost:8088"
echo "Username: admin"
echo "Password: admin"

# Start Superset
exec superset run -h 0.0.0.0 -p 8088 --with-threads --reload
