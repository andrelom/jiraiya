import os
import io
import sys
import logging

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Python
    environment: str                = "development"
    # Jira
    jira_url: str                    = ""
    jira_email: str                  = ""
    jira_api_token: str              = ""
    jira_sprint_id: str              = ""
    jira_output_folder: str          = ""

    class Config:
        # Ignore extra fields in the environment.
        extra = "ignore"
        # Conditionally load the .env file only if not in production.
        env_file = ".env" if os.getenv("ENVIRONMENT", "development") != "production" else None

# Set stdout to utf-8 to avoid encoding issues.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set logging level to INFO.
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Instantiate the settings object.
settings = Settings()
