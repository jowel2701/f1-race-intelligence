import os
import pandas as pd
from config import BASE_URL, MAX_RETRIES, RATE_LIMIT_WAIT_SECONDS, RAW_DIR, PROCESSED_DIR, REQUEST_DELAY_SECONDS, YEARS, SELECTED_SESSION_NAMES

INPUT_PATH = os.path.join(RAW_DIR, "sessions_raw.csv")
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "sessions_clean.csv")


# Mapeo de naming
LOCATION_MAP = {
    "Miami Gardens": "Miami",
    "Monte Carlo": "Monaco",
    "Yas Marina": "Yas Island",
    "Bahrain": "Sakhir",
}


def clean_sessions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Normalizar nombres de circuito inconsistentes entre temporadas
    df["location"] = df["location"].replace(LOCATION_MAP)

    # Convertir fechas a datetime
    df["date_start"] = pd.to_datetime(df["date_start"], utc=True)
    df["date_end"] = pd.to_datetime(df["date_end"], utc=True)

    return df


def main() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    df = pd.read_csv(INPUT_PATH)
    print(f"Filas originales: {len(df)}")

    df_clean = clean_sessions(df)
    print(f"Filas tras limpieza: {len(df_clean)}")

    print("\nSesiones canceladas:")
    print(df_clean["is_cancelled"].value_counts())

    print("\nCircuitos (location) tras normalizar:")
    print(sorted(df_clean["location"].unique()))

    df_clean.to_csv(OUTPUT_PATH, index=False)
    print(f"\nGuardado: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
