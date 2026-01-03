FROM apache/superset:3.1.0

USER root

# Install system dependencies for SQL Server connectivity
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    unixodbc \
    unixodbc-dev \
    freetds-dev \
    freetds-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER superset

# Install SQL Server drivers for Superset
RUN pip install --no-cache-dir pymssql

# Copy configuration files
COPY superset_config.py /app/superset_config.py
COPY bootstrap_superset.py /app/bootstrap_superset.py
COPY superset_init.sh /app/superset_init.sh

# Set Superset config path
ENV SUPERSET_CONFIG_PATH=/app/superset_config.py

USER root
RUN chmod +x /app/superset_init.sh

USER superset

# Set entrypoint
ENTRYPOINT ["/app/superset_init.sh"]
