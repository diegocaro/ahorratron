import os
import zoneinfo

from dotenv import load_dotenv

load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

TZ = os.getenv("TZ", "America/Santiago")
DEFAULT_TIMEZONE = zoneinfo.ZoneInfo(TZ)

RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))
RETRY_BACKOFF_SECONDS = float(os.getenv("RETRY_BACKOFF_SECONDS", "1.0"))
