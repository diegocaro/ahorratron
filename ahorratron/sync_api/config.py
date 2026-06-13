import os

from dotenv import load_dotenv

load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
