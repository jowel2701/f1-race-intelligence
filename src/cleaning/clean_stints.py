import os
import pandas as pd
from config import BASE_URL, MAX_RETRIES, RATE_LIMIT_WAIT_SECONDS, RAW_DIR, PROCESSED_DIR, REQUEST_DELAY_SECONDS, YEARS, SELECTED_SESSION_NAMES

INPUT = os.path.join(RAW_DIR, "stints_raw.csv")
LAPS = os.path.join(RAW_DIR, "laps_raw.csv")
OUTPUT = os.path.join(PROCESSED_DIR, "stints_clean.csv")

# Mismo mapeo de naming
LOCATION_MAP = {
    "Miami Gardens": "Miami",
    "Monte Carlo": "Monaco",
    "Yas Marina": "Yas Island",
    "Bahrain": "Sakhir",
}


def clean_stints(df: pd.DataFrame, laps: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates()

    # Normalizar nombres de circuitoS
    df["location_name"] = df["location_name"].replace(LOCATION_MAP)

    # unificar nulos y UNKNOWN en una sola
    df["compound"] = df["compound"].fillna("UNKNOWN")
    df["compound"] = df["compound"].astype(str)

    #si es el primer stint y lap_start es NaN, debe ser 1
    mask_first_stint = (df["stint_number"] == 1) & (df["lap_start"].isnull())
    df.loc[mask_first_stint, "lap_start"] = 1

    # lap_end: recuperar desde laps_raw cuando es NaN, usando la última
    # vuelta registrada de ese piloto en esa sesión.
    laps = laps[["session_key", "driver_number", "lap_number"]]

    max_lap_by_driver_session = (
        laps.groupby(["session_key", "driver_number"])["lap_number"]
        .max()
        .reset_index()
        .rename(columns={"lap_number": "max_lap"})
    )

    df = df.merge(max_lap_by_driver_session, on=["session_key", "driver_number"], how="left")

    mask_end_null = df["lap_end"].isnull()
    df.loc[mask_end_null, "lap_end"] = df.loc[mask_end_null, "max_lap"]

    df = df.drop(columns=["max_lap"])

    # Tipos
    df["lap_start"] = df["lap_start"].astype("Int64")
    df["lap_end"] = df["lap_end"].astype("Int64")
    df["date_start_session"] = pd.to_datetime(df["date_start_session"], utc=True)
    df["date_end_session"] = pd.to_datetime(df["date_end_session"], utc=True)

    return df


def main() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    df = pd.read_csv(INPUT)
    laps = pd.read_csv(LAPS)

    print(f"Filas originales: {len(df)}")

    df_clean = clean_stints(df, laps)
    print(f"Filas tras limpieza: {len(df_clean)}")

    print("\nValores nulos restantes:")
    print(df_clean.isnull().sum()[df_clean.isnull().sum() > 0])

    print("\ncompound tras limpieza:")
    print(df_clean["compound"].value_counts())

    print("\nCircuitos (location_name) tras normalizar:")
    print(sorted(df_clean["location_name"].unique()))

    df_clean.to_csv(OUTPUT, index=False)
    print(f"\nGuardado: {OUTPUT}")


if __name__ == "__main__":
    main()
