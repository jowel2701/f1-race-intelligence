import os
import pandas as pd

from config import BASE_URL, MAX_RETRIES, RATE_LIMIT_WAIT_SECONDS, RAW_DIR, PROCESSED_DIR, REQUEST_DELAY_SECONDS, YEARS, SELECTED_SESSION_NAMES


INPUT_PATH = os.path.join(RAW_DIR, "weather_raw.csv")
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "weather_clean.csv")

LOCATION_MAP = {
    "Miami Gardens": "Miami",
    "Monte Carlo": "Monaco",
    "Yas Marina": "Yas Island",
    "Bahrain": "Sakhir",
}


def clean_weather(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates()

    # Normalizar nombres de circuito inconsistentes entre temporadas
    df["location_name"] = df["location_name"].replace(LOCATION_MAP)

    # Convertir fechas a datetime
    for col in ["date", "date_start_session", "date_end_session"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True)

    # rainfall: 0/1 -> booleano
    df["rainfall"] = df["rainfall"].astype(bool)

    return df


def main() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    df = pd.read_csv(INPUT_PATH)
    print(f"Filas originales: {len(df)}")

    df_clean = clean_weather(df)
    print(f"Filas tras limpieza: {len(df_clean)}")

    print("\nValores nulos restantes:")
    print(df_clean.isnull().sum()[df_clean.isnull().sum() > 0])

    print("\nCircuitos tras normalizar:")
    print(sorted(df_clean["location_name"].unique()))

    print("\nLluvia:")
    print(df_clean["rainfall"].value_counts())

    df_clean.to_csv(OUTPUT_PATH, index=False)
    print(f"\nGuardado: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
