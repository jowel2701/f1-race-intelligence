#Configuracion base para extraccón de datos

YEARS = [2024, 2025, 2026]

BASE_URL = "https://api.openf1.org/v1"

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

SELECTED_SESSION_NAMES = [
    "Qualifying",
    "Sprint Qualifying",
    "Race",
    "Sprint",
]

REQUEST_DELAY_SECONDS = 2
RATE_LIMIT_WAIT_SECONDS = 90
MAX_RETRIES = 5