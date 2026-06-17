from pathlib import Path

import pandas as pd
import streamlit as st


# Todas las páginas importan desde aquí, no leen CSVs directamente.

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "processed"

# Columnas de fecha por dataset para parsear automáticamente al cargar
_DATE_COLUMNS: dict[str, list[str]] = {
    "laps_clean.csv": ["date_start"],
    "sessions_clean.csv": ["date_start", "date_end"],
    "weather_clean.csv": ["date"],
    "race_control_clean.csv": ["date"],
    "car_data_fast_lap_clean.csv": ["date"],
    "location_fast_lap_clean.csv": ["date"],
}


@st.cache_data(show_spinner=False)
def load_csv(filename: str) -> pd.DataFrame:
  
    #Carga un CSV desde data/processed/ y lo devuelve como DataFrame.
    path = DATA_DIR / filename

    if not path.exists():
        st.error(f"Archivo no encontrado: {path}")
        return pd.DataFrame()

    parse_dates = _DATE_COLUMNS.get(filename, False)

    try:
        df = pd.read_csv(path, parse_dates=parse_dates)
    except Exception as e:
        st.error(f"Error al leer {filename}: {e}")
        return pd.DataFrame()

    return df


@st.cache_data(show_spinner="Cargando datos de la sesión...")
def load_all_data() -> dict[str, pd.DataFrame]:
    
    ##Carga todos los datasets del proyecto en un único dict.
    #Así Streamlit comparte la caché entre páginas durante la misma sesión.
    
    datasets = {
        "laps":         "laps_clean.csv",
        "drivers":      "drivers_clean.csv",
        "sessions":     "sessions_clean.csv",
        "stints":       "stints_clean.csv",
        "car_data":     "car_data_fast_lap_clean.csv",
        "location":     "location_fast_lap_clean.csv",
        "weather":      "weather_clean.csv",
        "race_control": "race_control_clean.csv",
    }

    return {key: load_csv(filename) for key, filename in datasets.items()}


def get_sessions_for(
    laps: pd.DataFrame,
    season: int | str,
    country: str,
) -> list[str]:
    
    ##Devuelve las sesiones disponibles para una temporada y GP concretos.
    mask = (laps["season"] == season) & (laps["country_name"] == country)
    return sorted(laps.loc[mask, "session_name"].dropna().unique().tolist())


def filter_valid_laps(laps: pd.DataFrame) -> pd.DataFrame:
    
    #Filtra vueltas inválidas: elimina nulos en lap_duration,
    return laps[
        laps["lap_duration"].notna()
        & (laps["is_outlier_lap"] == False)
        & (laps["is_pit_out_lap"] == False)
    ].copy()