"""
Configuration settings for the Auto Article Publisher
"""

import os
from pathlib import Path

# Application settings
APP_TITLE = "Auto Article Publisher"
APP_ICON = "👑"
APP_DESCRIPTION = "Aplikasi untuk mengelola posting artikel otomatis ke GitHub repository"

# Directory structure
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
KEYWORDS_DIR = BASE_DIR / "keywords"
GENERAL_DIR = BASE_DIR / ".general"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
KEYWORDS_DIR.mkdir(exist_ok=True)

# Default settings
DEFAULT_SETTINGS = {
    'articles_per_run': 5,
    'auto_run_interval': 60,  # minutes
    'github_rate_limit_delay': 10,  # seconds
    'batch_processing_delay': 2,  # seconds between articles
    'max_retries': 3,
    'target_folder': '_posts',
    'image_folder': 'assets/image'
}

# GitHub API settings
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com"

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# File patterns
PROCESSED_SUBJECTS_PATTERN = "{repo_name}_processed_subjects.json"
KEYWORDS_FILE_PATTERN = "{repo_name}.txt"

# Streamlit configuration
STREAMLIT_CONFIG = {
    'page_title': APP_TITLE,
    'page_icon': APP_ICON,
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# Article generation settings
ARTICLE_SETTINGS = {
    'min_word_count': 3500,
    'max_word_count': 5000,
    'target_headings': 15,
    'language': 'Indonesian',
    'images_per_article': 2,
    'enable_internal_linking': True,
    'enable_auto_images': True
}

# Scheduler settings
SCHEDULER_SETTINGS = {
    'min_interval': 30,  # minimum minutes between runs
    'max_interval': 180,  # maximum minutes between runs
    'default_interval': 60,  # default interval in minutes
    'max_concurrent_articles': 10
}