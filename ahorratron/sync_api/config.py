import os
import zoneinfo

from dotenv import load_dotenv

load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

TZ = os.getenv("TZ", "America/Santiago")
DEFAULT_TIMEZONE = zoneinfo.ZoneInfo(TZ)
