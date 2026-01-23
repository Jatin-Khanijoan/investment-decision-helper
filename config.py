"""
Centralized path configuration for the project.
All file paths should reference this module.
"""
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Data directories
DATA_DIR = BASE_DIR / "data"
NIFTY_DATA_DIR = DATA_DIR / "nifty"
USER_DATA_DIR = DATA_DIR / "user"

# Database directory
DB_DIR = BASE_DIR / "db"

# Logs directory
LOGS_DIR = BASE_DIR / "logs"

# Documentation directory
DOCS_DIR = BASE_DIR / "docs"

# Scripts directory
SCRIPTS_DIR = BASE_DIR / "scripts"

# Specific file paths
USER_PROFILE_FILE = USER_DATA_DIR / "user_profile.json"
STOCKS_FILE = USER_DATA_DIR / "stocks.json"
PRODUCTION_DB = DB_DIR / "kautilya_production.db"
BACKTEST_DB = DB_DIR / "backtest_full.db"

# NIFTY data files
NIFTY_CSV_FILES = [
    NIFTY_DATA_DIR / "NIFTY 50-22-01-2021-to-22-01-2022.csv",
    NIFTY_DATA_DIR / "NIFTY 50-22-01-2022-to-22-01-2023.csv",
    NIFTY_DATA_DIR / "NIFTY 50-22-01-2023-to-22-01-2024.csv",
    NIFTY_DATA_DIR / "NIFTY 50-22-01-2024-to-22-01-2025.csv",
    NIFTY_DATA_DIR / "NIFTY 50-23-01-2025-to-23-01-2026.csv",
]
