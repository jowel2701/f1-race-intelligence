import os
import pandas as pd

from config import BASE_URL, MAX_RETRIES, RATE_LIMIT_WAIT_SECONDS, RAW_DIR, PROCESSED_DIR, REQUEST_DELAY_SECONDS, YEARS, SELECTED_SESSION_NAMES

INPUT = os.path.join(RAW_DIR, "location_fast_lap_raw.csv")
OUTPUT = os.path.join(PROCESSED_DIR, "location_fast_lap_clean.csv")

LOCATION_MAP = {
    "Miami Gardens": "Miami",
    "Monte Carlo": "Monaco",
    "Yas Marina": "Yas Island",
    "Bahrain": "Sakhir",
}


def clean_location(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates()

    # Normalizar nombres de circuito 
    df["location_name"] = df["location_name"].replace(LOCATION_MAP)

    # Convertir fechas a datetime
    for col in ["date", "lap_start"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", utc=True, errors="coerce")

    return df


def main() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    df = pd.read_csv(INPUT)
    print(f"Filas originales: {len(df)}")

    df_clean = clean_location(df)
    print(f"Filas tras limpieza: {len(df_clean)}")

    print("\nValores nulos restantes:")
    print(df_clean.isnull().sum()[df_clean.isnull().sum() > 0])

    print("\nRangos x/y/z:")
    print(df_clean[["x", "y", "z"]].describe())

    print("\nCircuitos tras normalizar:")
    print(sorted(df_clean["location_name"].unique()))

    print(f"\nSesiones: {df_clean['session_key'].nunique()}")

    df_clean.to_csv(OUTPUT, index=False)
    print(f"\nGuardado: {OUTPUT}")


if __name__ == "__main__":
    main()
