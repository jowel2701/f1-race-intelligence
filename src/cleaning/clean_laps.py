import os
import pandas as pd

from config import BASE_URL, MAX_RETRIES, RATE_LIMIT_WAIT_SECONDS, RAW_DIR, PROCESSED_DIR, REQUEST_DELAY_SECONDS, YEARS, SELECTED_SESSION_NAMES

INPUT = os.path.join(RAW_DIR, "laps_raw.csv")
OUTPUT = os.path.join(PROCESSED_DIR, "laps_clean.csv")

# Mismo mapeo de naming
LOCATION_MAP = {
    "Miami Gardens": "Miami",
    "Monte Carlo": "Monaco",
    "Yas Marina": "Yas Island",
    "Bahrain": "Sakhir",
}

OUTLIER_SECONDS = 300

SEGMENTS = ["segments_sector_1", "segments_sector_2", "segments_sector_3"]


def clean_laps(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates()

    # Normalizar nombres de circuito 
    df["location_name"] = df["location_name"].replace(LOCATION_MAP)

    # Eliminar vueltas sin lap_duration 
    before = len(df)
    df = df[df["lap_duration"].notna()].copy()
    print(f"Filas eliminadas por lap_duration nulo: {before - len(df)}")

    # Flag de outlier: vueltas >300s (banderas rojas / interrupciones),
    df["is_outlier_lap"] = df["lap_duration"] > OUTLIER_SECONDS
    print(f"Vueltas marcadas como outlier (>300s): {df['is_outlier_lap'].sum()}")

    # segments_sector_X no se usan en el dashboard
    df = df.drop(columns=[c for c in SEGMENTS if c in df.columns])
    
    # Convertir fechas a datetime
    for col in ["date_start", "date_start_session", "date_end_session"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True)

    return df


def main() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    df = pd.read_csv(INPUT)
    print(f"Filas originales: {len(df)}")

    df_clean = clean_laps(df)
    print(f"Filas tras limpieza: {len(df_clean)}")

    print("\nValores nulos restantes:")
    print(df_clean.isnull().sum()[df_clean.isnull().sum() > 0])

    print("\nCircuitos tras normalizar:")
    print(sorted(df_clean["location_name"].unique()))

    df_clean.to_csv(OUTPUT, index=False)
    print(f"\nGuardado: {OUTPUT}")


if __name__ == "__main__":
    main()
