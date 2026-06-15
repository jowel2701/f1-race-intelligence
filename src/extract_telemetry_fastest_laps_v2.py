import os
import time
from datetime import timedelta
from typing import Optional

import pandas as pd
import requests
from tqdm import tqdm

from config import BASE_URL, MAX_RETRIES, RATE_LIMIT_WAIT_SECONDS, RAW_DIR, REQUEST_DELAY_SECONDS

os.makedirs(RAW_DIR, exist_ok=True)

CAR_DATA = os.path.join(RAW_DIR, "car_data_fast_lap_raw.csv")
LOCATION_DATA = os.path.join(RAW_DIR, "location_fast_lap_raw.csv")

# Orden fijo de columnas para evitar desalineación al hacer append.
CAR_COLUMNS = [
    "date",
    "session_key",
    "throttle",
    "brake",
    "rpm",
    "speed",
    "meeting_key",
    "driver_number",
    "n_gear",
    "drs",
    "season",
    "country_name",
    "location_name",
    "session_name",
    "session_type",
    "lap_number",
    "lap_duration",
    "lap_start",
]

LOCATION_COLUMNS = [
    "date",
    "session_key",
    "x",
    "z",
    "meeting_key",
    "driver_number",
    "y",
    "season",
    "country_name",
    "location_name",
    "session_name",
    "session_type",
    "lap_number",
    "lap_duration",
    "lap_start",
]

# Rangos físicos válidos por columna validados con Openf1
VALID_RANGES = {
    "speed": (0, 400),
    "rpm": (0, 15000),
    "n_gear": (0, 8),
    "throttle": (0, 104),
    "drs": (0, 14),
    "brake": (0, 104),
}


def fetch_openf1(endpoint: str, params: Optional[dict] = None) -> pd.DataFrame:
    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.get(
            f"{BASE_URL}/{endpoint}",
            params=params,
            timeout=90,
        )

        print(f"{endpoint} | {response.url} | {response.status_code}")

        if response.status_code == 404:
            print(f"No hay datos para {endpoint} con params={params}. Se omite.")
            time.sleep(REQUEST_DELAY_SECONDS)
            return pd.DataFrame()

        if response.status_code == 429:
            wait_time = RATE_LIMIT_WAIT_SECONDS * attempt
            print(f"Rate limit alcanzado. Esperando {wait_time} segundos...")
            time.sleep(wait_time)
            continue

        response.raise_for_status()
        time.sleep(REQUEST_DELAY_SECONDS)

        return pd.DataFrame(response.json())

    print(f"No se pudo extraer {endpoint} con params={params}")
    return pd.DataFrame()


def get_fast_laps(laps: pd.DataFrame) -> pd.DataFrame:
    laps_w_time = laps[laps["lap_duration"].notna()].copy()

    if laps_w_time.empty:
        return pd.DataFrame()

    idx_fast_lap = (laps_w_time.groupby(["session_key", "driver_number"])["lap_duration"].idxmin())
    fastest_laps = laps_w_time.loc[idx_fast_lap].copy()

    return fastest_laps


def windows_fast_lap(dataframe: pd.DataFrame, fast_lap: pd.Series) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe

    lap_start = pd.to_datetime(fast_lap["date_start"], format="mixed", utc=True)
    lap_end = lap_start + timedelta(seconds=float(fast_lap["lap_duration"]))

    dataframe = dataframe.copy()

    dataframe["date"] = pd.to_datetime(dataframe["date"], format="mixed", utc=True)

    return dataframe[(dataframe["date"] >= lap_start) & (dataframe["date"] <= lap_end)].copy()


def save_incremental_csv(dataframe: pd.DataFrame, output_path: str, columns: list[str],) -> None:
    if dataframe.empty:
        return

    exists_file = os.path.exists(output_path)

    # Fuerza siempre el mismo orden/conjunto de columnas, evitando
    dataframe = dataframe.reindex(columns=columns)

    dataframe.to_csv(output_path, mode="a", header=not exists_file, index=False, encoding="utf-8",)

#Verificamos que sea información válida
def is_car_data_valid(group: pd.DataFrame) -> bool:
    for col, (lo, hi) in VALID_RANGES.items():
        if col not in group.columns:
            continue
        if not group[col].between(lo, hi).all():
            return False
    return True


def main() -> None:
    laps_path = os.path.join(RAW_DIR, "laps_raw.csv")

    if not os.path.exists(laps_path):
        raise FileNotFoundError(
            "No existe data/raw/laps_raw.csv. "
            "Ejecuta primero src/extract_metadata.py"
        )

    # si existen versiones corruptas, se eliminan
    for path in [CAR_DATA, LOCATION_DATA]:
        if os.path.exists(path):
            os.remove(path)
            print(f"Eliminado archivo previo: {path}")

    laps = pd.read_csv(laps_path)
    fast_laps = get_fast_laps(laps)
    fast_laps = fast_laps[
        fast_laps["session_name"].isin(["Qualifying", "Race"])
    ].copy()

    print(f"Vueltas más rápidas detectadas: {len(fast_laps)}")

    sessions_with_invalid_data = []

    for _, fastest_lap in tqdm(
        fast_laps.iterrows(),
        total=len(fast_laps),
        desc="Extrayendo telemetría",
    ):
        session_key = int(fastest_lap["session_key"])
        driver_number = int(fastest_lap["driver_number"])
        lap_number = int(fastest_lap["lap_number"])

        print(f"\nSession {session_key} | Driver {driver_number} | Lap {lap_number}")

        car_data = fetch_openf1(
            "car_data",
            {"session_key": session_key, "driver_number": driver_number},
        )

        location = fetch_openf1(
            "location",
            {"session_key": session_key, "driver_number": driver_number},
        )

        car_data_fastest_lap = windows_fast_lap(car_data, fastest_lap)
        location_fastest_lap = windows_fast_lap(location, fastest_lap)

        for dataframe in [car_data_fastest_lap, location_fastest_lap]:
            if dataframe.empty:
                continue

            dataframe["season"] = fastest_lap.get("season", None)
            dataframe["country_name"] = fastest_lap.get("country_name", None)
            dataframe["location_name"] = fastest_lap.get("location_name", None)
            dataframe["session_name"] = fastest_lap.get("session_name", None)
            dataframe["session_type"] = fastest_lap.get("session_type", None)
            dataframe["session_key"] = session_key
            dataframe["driver_number"] = driver_number
            dataframe["lap_number"] = lap_number
            dataframe["lap_duration"] = fastest_lap.get("lap_duration", None)
            dataframe["lap_start"] = fastest_lap.get("date_start", None)

        # Verificación de rangos físicos antes de guardar
        if not car_data_fastest_lap.empty and not is_car_data_valid(car_data_fastest_lap):
            print(f"  -> ATENCIÓN: session {session_key} con valores fuera de rango físico.")
            sessions_with_invalid_data.append(session_key)

        save_incremental_csv(car_data_fastest_lap, CAR_DATA, CAR_COLUMNS)
        save_incremental_csv(location_fastest_lap, LOCATION_DATA, LOCATION_COLUMNS)

    print("\nTelemetría completada.")
    print(f"Guardado: {CAR_DATA}")
    print(f"Guardado: {LOCATION_DATA}")

    if sessions_with_invalid_data:
        print(f"\nSesiones con valores fuera de rango físico ({len(sessions_with_invalid_data)}):")
        print(sessions_with_invalid_data)
    else:
        print("\nTodas las sesiones tienen valores dentro de rangos físicos válidos.")


if __name__ == "__main__":
    main()
