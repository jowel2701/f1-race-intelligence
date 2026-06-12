import os
import time
from typing import Optional

import pandas as pd
import requests
from tqdm import tqdm

from config import BASE_URL, MAX_RETRIES, RATE_LIMIT_WAIT_SECONDS, RAW_DIR, REQUEST_DELAY_SECONDS, YEARS, SELECTED_SESSION_NAMES


os.makedirs(RAW_DIR, exist_ok=True)


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

        data = response.json()
        return pd.DataFrame(data)

    print(f"No se pudo extraer {endpoint} con params={params}")
    return pd.DataFrame()


def save_csv(dataframes: list[pd.DataFrame], filename: str) -> None:
    if not dataframes:
        print(f"No hay datos para {filename}")
        return

    output_path = os.path.join(RAW_DIR, filename)
    pd.concat(dataframes, ignore_index=True).to_csv(
        output_path,
        index=False,
        encoding="utf-8",
    )

    print(f"Guardado: {output_path}")

def add_session_context(
    dataframe: pd.DataFrame,
    session_row: pd.Series,
    year: int,
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe

    dataframe = dataframe.copy()

    dataframe["season"] = year
    dataframe["meeting_key"] = session_row["meeting_key"]
    dataframe["country_name"] = session_row["country_name"]
    dataframe["location_name"] = session_row["location"]
    dataframe["session_name"] = session_row["session_name"]
    dataframe["session_type"] = session_row["session_type"]
    dataframe["date_start_session"] = session_row["date_start"]
    dataframe["date_end_session"] = session_row["date_end"]

    return dataframe


def main() -> None:
    all_sessions = []
    all_drivers = []
    all_laps = []
    all_stints = []
    all_weather = []
    all_race_control = []

    for year in YEARS:
        print(f"\n===== Temporada {year} =====")

        sessions = fetch_openf1("sessions", {"year": year})

        if sessions.empty:
            print(f"No hay sesiones para {year}")
            continue

        sessions["season"] = year
        all_sessions.append(sessions)

        selected_sessions = sessions[
            sessions["session_name"].isin(SELECTED_SESSION_NAMES)
        ].copy()

        print(f"Sesiones seleccionadas para {year}: {len(selected_sessions)}")

        for _, session_row in tqdm(
            selected_sessions.iterrows(),
            total=len(selected_sessions),
            desc=f"Metadata {year}",
        ):
            session_key = session_row["session_key"]

            print(
                f"\nExtrayendo {year} - "
                f"{session_row['country_name']} - "
                f"{session_row['session_name']} "
                f"(session_key={session_key})"
            )

            drivers = fetch_openf1("drivers", {"session_key": session_key})
            laps = fetch_openf1("laps", {"session_key": session_key})
            stints = fetch_openf1("stints", {"session_key": session_key})
            weather = fetch_openf1("weather", {"session_key": session_key})
            race_control = fetch_openf1("race_control", {"session_key": session_key})

            drivers = add_session_context(drivers, session_row, year)
            laps = add_session_context(laps, session_row, year)
            stints = add_session_context(stints, session_row, year)
            weather = add_session_context(weather, session_row, year)
            race_control = add_session_context(race_control, session_row, year)

            all_drivers.append(drivers)
            all_laps.append(laps)
            all_stints.append(stints)
            all_weather.append(weather)
            all_race_control.append(race_control)

            save_csv(all_sessions, "sessions_raw.csv")
            save_csv(all_drivers, "drivers_raw.csv")
            save_csv(all_laps, "laps_raw.csv")
            save_csv(all_stints, "stints_raw.csv")
            save_csv(all_weather, "weather_raw.csv")
            save_csv(all_race_control, "race_control_raw.csv")

    print("\nExtracción de metadata completada.")


if __name__ == "__main__":
    main()