"""Superset configuration for Microsoft Data Stack."""

import os

# Superset specific config
ROW_LIMIT = 5000
SUPERSET_WEBSERVER_PORT = 8088

# Secret key for session management
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "supersecretkey123")

# Database connection for Superset metadata
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"

# Feature flags
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_NATIVE_FILTERS_SET": True,
    "ALERT_REPORTS": False,
}

# Cache configuration
CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}

# SQL Lab configuration
SQL_MAX_ROW = 10000
DISPLAY_MAX_ROW = 1000

# Theme
APP_NAME = "Microsoft Data Stack"

# Enable SQL Lab
ENABLE_SQLLAB = True

# Allow CSV upload
CSV_EXTENSIONS = ["csv", "tsv"]
EXCEL_EXTENSIONS = ["xls", "xlsx"]
ALLOWED_EXTENSIONS = set(CSV_EXTENSIONS + EXCEL_EXTENSIONS)

# Time zone
BABEL_DEFAULT_LOCALE = "en"
BABEL_DEFAULT_FOLDER = "superset/translations"

# WTF CSRF
WTF_CSRF_ENABLED = False

# Data source settings
SQLALCHEMY_TRACK_MODIFICATIONS = False
