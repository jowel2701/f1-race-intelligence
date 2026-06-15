import os
import pandas as pd
from config import BASE_URL, MAX_RETRIES, RATE_LIMIT_WAIT_SECONDS, RAW_DIR, PROCESSED_DIR, REQUEST_DELAY_SECONDS, YEARS, SELECTED_SESSION_NAMES

INPUT = os.path.join(RAW_DIR, "drivers_raw.csv")
OUTPUT = os.path.join(PROCESSED_DIR, "drivers_clean.csv")

# Mapeo de naming
LOCATION_MAP = {
    "Miami Gardens": "Miami",
    "Monte Carlo": "Monaco",
    "Yas Marina": "Yas Island",
}


def clean_drivers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates()

    # Normalizar nombres de circuito
    df["location_name"] = df["location_name"].replace(LOCATION_MAP)

    # Convertir fechas a datetime
    df["date_start_session"] = pd.to_datetime(df["date_start_session"], utc=True, format="mixed")
    df["date_end_session"] = pd.to_datetime(df["date_end_session"], utc=True, format="mixed")

    return df


def main() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    df = pd.read_csv(INPUT)
    print(f"Filas originales: {len(df)}")

    df_clean = clean_drivers(df)
    print(f"Filas tras limpieza: {len(df_clean)}")

    print("\nValores nulos restantes:")
    print(df_clean.isnull().sum()[df_clean.isnull().sum() > 0])

    print("\nCircuitos (location_name) tras normalizar:")
    print(sorted(df_clean["location_name"].unique()))

    df_clean.to_csv(OUTPUT, index=False)
    print(f"\nGuardado: {OUTPUT}")


if __name__ == "__main__":
    main()
