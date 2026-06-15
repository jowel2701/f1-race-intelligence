import os
import pandas as pd

from config import BASE_URL, MAX_RETRIES, RATE_LIMIT_WAIT_SECONDS, RAW_DIR, PROCESSED_DIR, REQUEST_DELAY_SECONDS, YEARS, SELECTED_SESSION_NAMES

INPUT = os.path.join(RAW_DIR, "car_data_fast_lap_raw.csv")
OUTPUT = os.path.join(PROCESSED_DIR, "car_data_fast_lap_clean.csv")

LOCATION_MAP = {
    "Miami Gardens": "Miami",
    "Monte Carlo": "Monaco",
    "Yas Marina": "Yas Island",
    "Bahrain": "Sakhir",
}

# Rangos físicos
VALID_RANGES = {
    "speed": (0, 400),
    "rpm": (0, 15000),
    "n_gear": (0, 8),
    "throttle": (0, 100),
    "drs": (0,14),
    "brake": (0, 100),
}


def clean_car_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates()

    # Normalizar nombres de circuito 
    df["location_name"] = df["location_name"].replace(LOCATION_MAP)

    # 104 = placeholder de la API cuando el coche está parado/sin dato
    # (speed=0, n_gear=0). Se recodifica a 0.
    stopped_car = (df["speed"] == 0) & (df["rpm"] == 0) & (df["n_gear"] == 0)
    df.loc[stopped_car & (df["throttle"] == 104), "throttle"] = 0
    df.loc[stopped_car & (df["brake"] == 104), "brake"] = 0

    # Convertir fechas a datetime
    for col in ["date", "lap_start"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True)

    return df


def validate_ranges(df: pd.DataFrame) -> None:
    for col, (lo, hi) in VALID_RANGES.items():
        if col not in df.columns:
            continue
        out_of_range = ~df[col].between(lo, hi)
        if out_of_range.any():
            print(f"AVISO: {out_of_range.sum()} filas con '{col}' fuera de rango [{lo},{hi}]")
        else:
            print(f"OK: '{col}' dentro de rango [{lo},{hi}]")


def main() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    df = pd.read_csv(INPUT)
    print(f"Filas originales: {len(df)}")

    df_clean = clean_car_data(df)
    print(f"Filas tras limpieza: {len(df_clean)}")

    print("\nValidación de rangos físicos:")
    validate_ranges(df_clean)

    print("\nValores nulos restantes:")
    print(df_clean.isnull().sum()[df_clean.isnull().sum() > 0])

    print("\nCircuitos tras normalizar:")
    print(sorted(df_clean["location_name"].unique()))

    print(f"\nSesiones: {df_clean['session_key'].nunique()}")

    df_clean.to_csv(OUTPUT, index=False)
    print(f"\nGuardado: {OUTPUT}")


if __name__ == "__main__":
    main()
