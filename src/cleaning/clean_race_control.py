import os
import pandas as pd

from config import BASE_URL, MAX_RETRIES, RATE_LIMIT_WAIT_SECONDS, RAW_DIR, PROCESSED_DIR, REQUEST_DELAY_SECONDS, YEARS, SELECTED_SESSION_NAMES

INPUT = os.path.join(RAW_DIR, "race_control_raw.csv")
OUTPUT = os.path.join(PROCESSED_DIR, "race_control_clean.csv")

LOCATION_MAP = {
    "Miami Gardens": "Miami",
    "Monte Carlo": "Monaco",
    "Yas Marina": "Yas Island",
    "Bahrain": "Sakhir",
}

# Según el tipo de evento pueden verse nulos
NULL_COLUMNS = ["driver_number", "lap_number", "sector", "qualifying_phase"]


def clean_race_control(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates()

    # Normalizar nombres de circuito inconsistentes entre temporadas
    df["location_name"] = df["location_name"].replace(LOCATION_MAP)

    # Convertir fechas a datetime
    for col in ["date", "date_start_session", "date_end_session"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", utc=True, errors="coerce")

    # driver_number, lap_number, sector, qualifying_phase: float con NaN
    # -> Int64. Los nulos se mantienen, son legítimos
    for col in NULL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("Int64")

    return df


def main() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    df = pd.read_csv(INPUT)
    print(f"Filas originales: {len(df)}")

    df_clean = clean_race_control(df)
    print(f"Filas tras limpieza: {len(df_clean)}")

    print("\nValores nulos (legítimos según 'category'):")
    print(df_clean.isnull().sum()[df_clean.isnull().sum() > 0])

    print("\ncategory:")
    print(df_clean["category"].value_counts())

    print("\nCircuitos tras normalizar:")
    print(sorted(df_clean["location_name"].unique()))

    df_clean.to_csv(OUTPUT, index=False)
    print(f"\nGuardado: {OUTPUT}")


if __name__ == "__main__":
    main()
