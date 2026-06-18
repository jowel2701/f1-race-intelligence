import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from streamlit_image_coordinates import streamlit_image_coordinates

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from src.dashboard.data_loader import load_all_data
from src.dashboard.utils import global_style

#Configuración de página
st.set_page_config(page_title="Engineer Mode", layout="wide")
global_style()

###Helpers
def metric_flip_card(title: str, front_value: str, back_title: str, back_value: str) -> None:
    st.markdown(
        f"""
        <div class="flip-card">
            <div class="flip-card-inner">
                <div class="flip-card-front">
                    <p class="card-title">{title}</p>
                    <h2>{front_value}</h2>
                </div>
                <div class="flip-card-back">
                    <p class="card-title">{back_title}</p>
                    <h2>{back_value}</h2>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

PLOTLY_BASE = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    margin=dict(l=20, r=20, t=20, b=20),
)

#Datos
data = load_all_data()

laps     = data["laps"]
stints   = data["stints"]
car_data = data["car_data"]
location = data["location"]
drivers  = data["drivers"]
weather  = data["weather"]

# Merge name_acronym a laps para usarlo como variable predictora en el modelo
driver_cols = ["session_key", "driver_number", "name_acronym", "team_name"]
laps = laps.merge(drivers[driver_cols], on=["session_key", "driver_number"], how="left")

#=============Sidebar Filtros===========================
st.sidebar.header("Filtros")

available_sessions = laps[
    ["season", "country_name", "session_name", "session_key"]
].drop_duplicates()

season = st.sidebar.selectbox("Season", sorted(available_sessions["season"].unique()))
sessions_season = available_sessions[available_sessions["season"] == season]

country = st.sidebar.selectbox("Grand Prix", sorted(sessions_season["country_name"].unique()))
sessions_country = sessions_season[sessions_season["country_name"] == country]

session = st.sidebar.selectbox("Session", sorted(sessions_country["session_name"].unique()))
session_key = sessions_country[
    sessions_country["session_name"] == session
]["session_key"].iloc[0]

session_drivers = drivers[drivers["session_key"] == session_key]
driver_options  = session_drivers[["driver_number", "name_acronym"]].drop_duplicates()

if driver_options.empty:
    st.warning("No hay pilotos disponibles para esta sesión.")
    st.stop()

selected_driver = st.sidebar.selectbox("Driver", sorted(driver_options["name_acronym"]))
driver_number   = driver_options[
    driver_options["name_acronym"] == selected_driver
]["driver_number"].iloc[0]

driver_car      = car_data[(car_data["session_key"] == session_key) & (car_data["driver_number"] == driver_number)].copy()
driver_stints   = stints[(stints["session_key"] == session_key) & (stints["driver_number"] == driver_number)].copy()
driver_location = location[(location["session_key"] == session_key) & (location["driver_number"] == driver_number)].copy()

has_telemetry = not driver_car.empty and not driver_location.empty

st.title("Engineer Mode")
st.caption(f"{country} · {season} · {session} · {selected_driver}")

##TABS
tab_diagnostico, tab_lap_pred, tab_braking = st.tabs([
    "Diagnóstico del coche",
    "Predicción de vuelta",
    "Punto óptimo de frenada",
])

#TAB1
with tab_diagnostico:
    if not has_telemetry:
        st.info("No hay telemetría disponible para esta combinación de sesión y piloto.")
    else:
        IMAGE_PATH = ROOT_DIR / "app" / "assets" / "Car_AMR26.png"

        if not IMAGE_PATH.exists():
            st.error(f"Imagen no encontrada en: {IMAGE_PATH}")
        else:
            if "module" not in st.session_state:
                st.session_state.module = "Engine"

            coords = streamlit_image_coordinates(str(IMAGE_PATH), key="car_click", width=900)

            if coords:
                x, y = coords["x"], coords["y"]
                if   250 <= x <= 450 and 220 <= y <= 450: st.session_state.module = "Front Tyres"
                elif 660 <= x <= 740 and 235 <= y <= 320: st.session_state.module = "Rear Tyres"
                elif 550 <= x <= 600 and 215 <= y <= 320: st.session_state.module = "Engine"
                elif  50 <= x <= 250 and 300 <= y <= 500: st.session_state.module = "Aero"
                elif 650 <= x <= 850 and 196 <= y <= 213: st.session_state.module = "DRS"
                elif 380 <= x <= 520 and 180 <= y <= 280: st.session_state.module = "Driver"

            selected_module = st.session_state.module
            st.subheader(f"Sistema seleccionado: {selected_module}")

            col1, col2, col3, col4 = st.columns(4)

            if selected_module == "Engine":
                with col1:
                    metric_flip_card("Velocidad punta", f"{driver_car['speed'].max():.0f} km/h", "Media", f"{driver_car['speed'].mean():.0f} km/h")
                with col2:
                    metric_flip_card("RPM máxima", f"{driver_car['rpm'].max():.0f}", "RPM media", f"{driver_car['rpm'].mean():.0f}")
                with col3:
                    metric_flip_card("Marcha máxima", f"{int(driver_car['n_gear'].max())}", "Marcha media", f"{driver_car['n_gear'].mean():.1f}")
                with col4:
                    metric_flip_card("% a plena potencia", f"{(driver_car['throttle'] >= 90).mean()*100:.1f}%", "Throttle medio", f"{driver_car['throttle'].mean():.0f}%")
                st.markdown(
                    """<div class="insight-box">El motor se evalúa por velocidad punta, RPM y uso de marchas.
                    Un RPM máximo alto con velocidad punta elevada indica buen aprovechamiento en rectas.
                    La marcha media refleja el tipo de circuito: valores altos = circuito rápido.</div>""",
                    unsafe_allow_html=True,
                )

            elif selected_module == "DRS":
                drs_pct       = (driver_car["drs"] >= 10).mean() * 100
                drs_count     = (driver_car["drs"] >= 10).sum()
                drs_top_speed = driver_car.loc[driver_car["drs"] >= 10, "speed"].max()
                drs_gain      = driver_car.loc[driver_car["drs"] >= 10, "speed"].mean() - driver_car.loc[driver_car["drs"] < 10, "speed"].mean()
                with col1:
                    metric_flip_card("Uso de DRS", f"{drs_pct:.1f}%", "Muestras activas", f"{drs_count:,}")
                with col2:
                    metric_flip_card("Velocidad punta DRS", f"{drs_top_speed:.0f} km/h" if pd.notna(drs_top_speed) else "N/A", "Estado máximo", str(int(driver_car["drs"].max())))
                with col3:
                    metric_flip_card("Sin DRS (media)", f"{driver_car.loc[driver_car['drs'] < 10, 'speed'].mean():.0f} km/h", "Con DRS (media)", f"{driver_car.loc[driver_car['drs'] >= 10, 'speed'].mean():.0f} km/h")
                with col4:
                    metric_flip_card("Ganancia media DRS", f"+{drs_gain:.1f} km/h" if not np.isnan(drs_gain) else "N/A", "Zonas DRS", f"{int((driver_car['drs'].diff().fillna(0) > 0).sum())}")
                st.markdown(
                    """<div class="insight-box">El DRS abre el alerón trasero para reducir la resistencia aerodinámica.
                    Solo se activa cuando el piloto está a menos de 1 segundo del coche delante en la zona de detección.
                    La ganancia media muestra cuántos km/h aporta el DRS en las zonas donde está activo.</div>""",
                    unsafe_allow_html=True,
                )

            elif selected_module in ("Front Tyres", "Rear Tyres"):
                if driver_stints.empty:
                    st.warning("No hay datos de stints para este piloto.")
                else:
                    last_stint = driver_stints.sort_values("stint_number").iloc[-1]
                    stint_laps = int(last_stint["lap_end"] - last_stint["lap_start"] + 1)
                    total_stints = int(driver_stints["stint_number"].max())
                    with col1:
                        metric_flip_card("Compuesto actual", last_stint["compound"], "Stint", str(int(last_stint["stint_number"])))
                    with col2:
                        metric_flip_card("Vueltas del stint", str(stint_laps), "Vuelta inicio", str(int(last_stint["lap_start"])))
                    with col3:
                        metric_flip_card("Edad del neumático", f"{int(last_stint['tyre_age_at_start'])} vueltas", "Al inicio del stint", "Vueltas acumuladas")
                    with col4:
                        metric_flip_card("Stints totales", str(total_stints), "Paradas en boxes", str(total_stints - 1))
                    st.markdown(
                        f"""<div class="insight-box">Los neumáticos <strong>{last_stint['compound']}</strong> del último stint
                        tenían <strong>{int(last_stint['tyre_age_at_start'])} vueltas</strong> de vida al inicio.
                        El piloto realizó <strong>{total_stints - 1} parada{'s' if total_stints > 2 else ''}</strong> en boxes.</div>""",
                        unsafe_allow_html=True,
                    )

            elif selected_module == "Aero":
                avg_speed    = driver_car["speed"].mean()
                top_speed    = driver_car["speed"].max()
                avg_throttle = driver_car["throttle"].mean()
                drs_usage    = (driver_car["drs"] >= 10).mean() * 100
                with col1:
                    metric_flip_card("Velocidad media", f"{avg_speed:.0f} km/h", "Velocidad punta", f"{top_speed:.0f} km/h")
                with col2:
                    metric_flip_card("Throttle medio", f"{avg_throttle:.0f}%", "% a plena potencia", f"{(driver_car['throttle'] >= 90).mean()*100:.1f}%")
                with col3:
                    metric_flip_card("Uso de DRS", f"{drs_usage:.1f}%", "Tipo circuito", "Alta carga" if avg_speed < 200 else "Baja carga")
                with col4:
                    metric_flip_card("Frenada media", f"{driver_car['brake'].mean():.1f}%", "% tiempo frenando", f"{(driver_car['brake'] > 0).mean()*100:.1f}%")
                st.markdown(
                    """<div class="insight-box">La aerodinámica equilibra carga (agarre en curva) y resistencia (velocidad en recta).
                    Throttle medio alto y poco DRS → circuito de alta carga aerodinámica.
                    DRS frecuente y velocidades punta altas → configuración de baja carga.</div>""",
                    unsafe_allow_html=True,
                )

            elif selected_module == "Driver":
                driver_laps_diag = laps[
                    (laps["session_key"] == session_key) & (laps["driver_number"] == driver_number)
                ]
                if driver_laps_diag.empty:
                    st.warning("No hay vueltas registradas para este piloto.")
                else:
                    fastest_lap = driver_laps_diag["lap_duration"].min()
                    avg_lap     = driver_laps_diag["lap_duration"].mean()
                    best_s1     = driver_laps_diag["duration_sector_1"].min() if "duration_sector_1" in driver_laps_diag.columns else None
                    with col1:
                        metric_flip_card("Vuelta rápida", f"{fastest_lap:.3f}s", "Media", f"{avg_lap:.3f}s")
                    with col2:
                        metric_flip_card("Vueltas completadas", str(int(driver_laps_diag["lap_number"].max())), "Consistencia", f"{driver_laps_diag['lap_duration'].std():.3f}s std")
                    with col3:
                        metric_flip_card("Mejor S1", f"{best_s1:.3f}s" if best_s1 else "N/A", "Gap rápida vs media", f"+{avg_lap - fastest_lap:.3f}s")
                    with col4:
                        metric_flip_card("Piloto", selected_driver, "Equipo", drivers[drivers["driver_number"] == driver_number]["team_name"].iloc[0] if not drivers[drivers["driver_number"] == driver_number].empty else "—")
                    st.markdown(
                        f"""<div class="insight-box">Cuanto menor es la diferencia entre vuelta rápida y media,
                        más consistente es el piloto. Un gap de <strong>{avg_lap - fastest_lap:.3f}s</strong>
                        indica {'alta consistencia' if avg_lap - fastest_lap < 1 else 'variabilidad en el rendimiento'}.</div>""",
                        unsafe_allow_html=True,
                    )

            st.caption(
                "Haz clic sobre el motor, los neumáticos, el alerón, el DRS o el cockpit "
                "para inspeccionar cada sistema del monoplaza."
            )

#TAB2
with tab_lap_pred:
    st.subheader("Predicción de tiempo de vuelta")
    st.caption(
        "Modelo predictivo sobre vueltas válidas, usando condiciones climáticas, "
        "compuesto de neumático y desgaste como variables predictoras."
    )

    valid_laps = laps[
        laps["lap_duration"].notna()
        & (laps["is_pit_out_lap"] == False)
        & (laps["is_outlier_lap"] == False)
    ].copy()

    stints_expand = stints.copy()
    stints_expand["lap_start"] = stints_expand["lap_start"].astype(float)
    stints_expand["lap_end"] = stints_expand["lap_end"].astype(float)

    def attach_stint_info(laps_df: pd.DataFrame, stints_df: pd.DataFrame) -> pd.DataFrame:
        merged_rows = []

        for (sk, dn), group in laps_df.groupby(["session_key", "driver_number"]):
            s = stints_df[
                (stints_df["session_key"] == sk) &
                (stints_df["driver_number"] == dn)
            ]

            g = group.copy()
            g["compound"] = "UNKNOWN"
            g["tyre_age_at_start"] = np.nan

            if not s.empty:
                for _, stint_row in s.iterrows():
                    mask = (
                        (g["lap_number"] >= stint_row["lap_start"]) &
                        (g["lap_number"] <= stint_row["lap_end"])
                    )
                    g.loc[mask, "compound"] = stint_row["compound"]
                    g.loc[mask, "tyre_age_at_start"] = stint_row["tyre_age_at_start"]

            merged_rows.append(g)

        return pd.concat(merged_rows, ignore_index=True)

    with st.spinner("Preparando dataset de entrenamiento..."):
        laps_with_stint = attach_stint_info(valid_laps, stints_expand)

    weather_small = weather[
        ["session_key", "date", "air_temperature", "track_temperature", "humidity", "rainfall"]
    ].copy()

    laps_with_stint["date_start"] = pd.to_datetime(
        laps_with_stint["date_start"], utc=True, format="mixed"
    )
    weather_small["date"] = pd.to_datetime(
        weather_small["date"], utc=True, format="mixed"
    )

    laps_with_stint = laps_with_stint.dropna(subset=["date_start"]).sort_values("date_start")
    weather_small = weather_small.dropna(subset=["date"]).sort_values("date")

    model_df = pd.merge_asof(
        laps_with_stint,
        weather_small,
        left_on="date_start",
        right_on="date",
        by="session_key",
        direction="nearest",
    ).dropna(
        subset=[
            "lap_duration",
            "air_temperature",
            "track_temperature",
            "humidity",
            "tyre_age_at_start",
            "compound",
            "name_acronym",
        ]
    )

    tyre_life_map = {
        "SOFT": 25,
        "MEDIUM": 35,
        "HARD": 45,
        "INTERMEDIATE": 25,
        "WET": 20,
        "UNKNOWN": 30,
    }

    tyre_temp_window = {
        "SOFT": 85,
        "MEDIUM": 95,
        "HARD": 110,
        "INTERMEDIATE": 70,
        "WET": 60,
        "UNKNOWN": 90,
    }

    degradation_rate = {
        "SOFT": 0.10,
        "MEDIUM": 0.05,
        "HARD": 0.02,
        "INTERMEDIATE": 0.08,
        "WET": 0.06,
        "UNKNOWN": 0.05,
    }

    initial_advantage = {
        "SOFT": 1.0,
        "MEDIUM": 0.5,
        "HARD": 0.0,
        "INTERMEDIATE": 0.0,
        "WET": 0.0,
        "UNKNOWN": 0.3,
    }

    model_df["tyre_life_max"] = model_df["compound"].map(tyre_life_map)
    model_df["tyre_degradation"] = model_df["tyre_age_at_start"] / model_df["tyre_life_max"]
    model_df["temp_vs_optimal"] = model_df["track_temperature"] - model_df["compound"].map(tyre_temp_window)
    model_df["rain_wrong_tyre"] = (
        (model_df["rainfall"] == 1) &
        (model_df["compound"].isin(["SOFT", "MEDIUM", "HARD"]))
    ).astype(int)
    model_df["deg_rate"] = model_df["compound"].map(degradation_rate)
    model_df["initial_advantage"] = model_df["compound"].map(initial_advantage)
    model_df["tyre_performance"] = (
        model_df["initial_advantage"] - model_df["deg_rate"] * model_df["tyre_age_at_start"]
    )
    model_df["crossover_lap"] = model_df.apply(
        lambda r: r["initial_advantage"] / (r["deg_rate"] - 0.02)
        if r["deg_rate"] > 0.02 else 999,
        axis=1,
    )
    model_df["past_crossover"] = (
        model_df["tyre_age_at_start"] > model_df["crossover_lap"]
    ).astype(int)

    st.caption(f"Dataset de entrenamiento: **{len(model_df)} vueltas válidas**.")

    if "lap_model_bundle" not in st.session_state:
        st.session_state.lap_model_bundle = None

    if len(model_df) < 30:
        st.warning("No hay suficientes datos para entrenar un modelo fiable (mínimo ~30 vueltas).")
    else:
        col_train1, col_train2 = st.columns([1, 1])
        with col_train1:
            train_model_clicked = st.button("Entrenar modelo de predicción")
        with col_train2:
            if st.button("Resetear modelo"):
                st.session_state.lap_model_bundle = None
                st.rerun()

        if train_model_clicked:
            try:
                with st.spinner("Entrenando modelo de predicción..."):
                    features_num = [
                        "air_temperature",
                        "track_temperature",
                        "humidity",
                        "tyre_age_at_start",
                        "rainfall",
                        "tyre_degradation",
                        "temp_vs_optimal",
                        "rain_wrong_tyre",
                        "tyre_performance",
                        "crossover_lap",
                        "past_crossover",
                    ]
                    features_cat = ["compound", "name_acronym"]

                    model_df_train = model_df.dropna(
                        subset=features_num + features_cat + ["lap_duration"]
                    ).copy()

                    X = model_df_train[features_num + features_cat]
                    y = model_df_train["lap_duration"]

                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=0.2, random_state=42
                    )

                    preprocessor = ColumnTransformer(
                        transformers=[
                            ("cat", OneHotEncoder(handle_unknown="ignore"), features_cat)
                        ],
                        remainder="passthrough",
                    )

                    pipeline = Pipeline(steps=[
                        ("prep", preprocessor),
                        ("reg", RandomForestRegressor( 
                            n_estimators=200, ##poblacion del forest para mejor modelo pred
                            random_state=42,
                            max_depth=12,
                            min_samples_leaf=4,
                            n_jobs=-1,
                        )),
                    ])

                    pipeline.fit(X_train, y_train)
                    y_pred = pipeline.predict(X_test)

                    r2 = r2_score(y_test, y_pred)
                    mae = mean_absolute_error(y_test, y_pred)

                    y_floor = float(y_train.quantile(0.05))
                    y_ceiling = float(y_train.quantile(0.95))

                    st.session_state.lap_model_bundle = {
                        "pipeline": pipeline,
                        "r2": r2,
                        "mae": mae,
                        "y_floor": y_floor,
                        "y_ceiling": y_ceiling,
                        "train_rows": len(model_df_train),
                    }

            except Exception as e:
                st.error(f"Error en el entrenamiento: {type(e).__name__}: {e}")

        if st.session_state.lap_model_bundle is not None:
            bundle = st.session_state.lap_model_bundle
            pipeline = bundle["pipeline"]
            r2 = bundle["r2"]
            mae = bundle["mae"]
            y_floor = bundle["y_floor"]
            y_ceiling = bundle["y_ceiling"]
            train_rows = bundle["train_rows"]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("R² del modelo", f"{r2:.3f}")
                st.caption("Cuanto más cerca de 1.0, mejor predice el modelo.")
            with col2:
                st.metric("Error medio", f"±{mae:.3f}s")
                st.caption("El modelo se equivoca en media esta cantidad por vuelta.")
            with col3:
                st.metric("Vueltas analizadas", f"{train_rows:,}")
                st.caption("Vueltas válidas usadas para construir el modelo.")

            st.divider()
            st.markdown("##### Simula condiciones para predecir el tiempo de vuelta")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                sim_air = st.slider(
                    "Temperatura aire (°C)",
                    15.0, 45.0,
                    float(model_df["air_temperature"].mean())
                )
                sim_track = st.slider(
                    "Temperatura pista (°C)",
                    15.0, 60.0,
                    float(model_df["track_temperature"].mean())
                )
            with col_b:
                sim_humidity = st.slider(
                    "Humedad (%)",
                    0.0, 100.0,
                    float(model_df["humidity"].mean())
                )
                sim_rain = st.checkbox("Lluvia", value=False)
            with col_c:
                sim_compound = st.selectbox(
                    "Compuesto",
                    sorted(model_df["compound"].dropna().unique())
                )
                sim_tyre_age = st.slider("Edad del neumático (vueltas)", 0, 40, 5)

            _life_max = tyre_life_map.get(sim_compound, 30)
            _deg_rate = degradation_rate.get(sim_compound, 0.05)
            _init_adv = initial_advantage.get(sim_compound, 0.0)
            _temp_opt = tyre_temp_window.get(sim_compound, 90)
            _crossover = _init_adv / (_deg_rate - 0.02) if _deg_rate > 0.02 else 999

            sim_input = pd.DataFrame([{
                "air_temperature": sim_air,
                "track_temperature": sim_track,
                "humidity": sim_humidity,
                "tyre_age_at_start": sim_tyre_age,
                "rainfall": int(sim_rain),
                "tyre_degradation": sim_tyre_age / _life_max,
                "temp_vs_optimal": sim_track - _temp_opt,
                "rain_wrong_tyre": int(sim_rain and sim_compound in ["SOFT", "MEDIUM", "HARD"]),
                "tyre_performance": _init_adv - _deg_rate * sim_tyre_age,
                "crossover_lap": _crossover,
                "past_crossover": int(sim_tyre_age > _crossover),
                "compound": sim_compound,
                "name_acronym": selected_driver,
            }])

            if sim_rain and sim_compound in ["SOFT", "MEDIUM", "HARD"]:
                st.warning(
                    f"Con lluvia y compuesto {sim_compound} de seco, la predicción no será realista. "
                    f"Usa Intermedio o WET."
                )

            if sim_tyre_age > _crossover and sim_compound != "HARD":
                st.warning(
                    f"Con {sim_tyre_age} vueltas en {sim_compound}, el HARD ya sería más rápido. "
                    f"El crossover se produce en la vuelta {_crossover:.0f}."
                )

            if sim_track >= 45 and sim_compound == "SOFT" and sim_tyre_age >= 15:
                st.warning(
                    f"Condición extrema: {sim_compound} con {sim_tyre_age} vueltas y {sim_track:.0f}°C de pista. "
                    f"El neumático está en una zona de degradación severa."
                )
            ##NECESARIO PARA QUE NO SUPERE LIMITES FÍSICOS EN BASE A LOS COMPUESTO
            physical_penalty = 0.0

            if sim_compound == "SOFT":
                if sim_track > 45:
                    physical_penalty += ((sim_track - 45) ** 1.3) * 0.10
                if sim_tyre_age > 15:
                    physical_penalty += ((sim_tyre_age - 15) ** 1.2) * 0.14

            if sim_compound == "MEDIUM":
                if sim_track > 48:
                    physical_penalty += ((sim_track - 48) ** 1.2) * 0.06
                if sim_tyre_age > 22:
                    physical_penalty += ((sim_tyre_age - 22) ** 1.1) * 0.05

            if sim_compound == "HARD":
                if sim_track > 52:
                    physical_penalty += ((sim_track - 52) ** 1.1) * 0.03
                if sim_tyre_age > 30:
                    physical_penalty += ((sim_tyre_age - 30) ** 1.05) * 0.02

            if sim_rain and sim_compound in ["SOFT", "MEDIUM", "HARD"]:
                physical_penalty += 8.0

            try:
                raw_pred = float(pipeline.predict(sim_input)[0]) + physical_penalty
                sim_pred = float(np.clip(raw_pred, y_floor, y_ceiling))

                col_pred1, col_pred2, col_pred3 = st.columns(3)
                with col_pred1:
                    st.metric("Tiempo estimado", f"{sim_pred:.3f}s")
                with col_pred2:
                    st.metric("Mejor caso", f"{max(y_floor, sim_pred - mae):.3f}s")
                with col_pred3:
                    st.metric("Peor caso", f"{min(y_ceiling, sim_pred + mae):.3f}s")

                st.caption(
                    f"El modelo predice **{sim_pred:.3f}s** con un margen de error de ±{mae:.3f}s. "
                    f"Penalización física aplicada: +{physical_penalty:.3f}s. "
                    f"Un R² de {r2:.3f} significa que el modelo explica el {r2*100:.1f}% de la variabilidad."
                )
            except Exception as e:
                st.error(f"Error en la simulación: {type(e).__name__}: {e}")
        else:
            st.info("Pulsa 'Entrenar modelo de predicción' para generar el modelo una vez y reutilizarlo en la simulación.")

#TAB3
with tab_braking:
    st.subheader("Punto óptimo de frenada")
    st.caption(
        "Relación entre la velocidad de entrada a una curva y la distancia "
        "recorrida desde el fin de recta hasta el inicio real de la frenada."
    )

    if not has_telemetry:
        st.warning("Selecciona una sesión y piloto con telemetría disponible.")
    else:
        loc = driver_location.sort_values("date").reset_index(drop=True)
        car = driver_car.sort_values("date").reset_index(drop=True)

        loc["date"] = pd.to_datetime(loc["date"], utc=True, format="mixed")
        car["date"] = pd.to_datetime(car["date"], utc=True, format="mixed")

        track = pd.merge_asof(
            loc, car[["date", "speed", "brake", "throttle"]],
            on="date", direction="nearest",
        ).reset_index(drop=True)

        # Distancia acumulada aproximada por coordenadas
        track["dist"] = np.sqrt(
            track["x"].diff()**2 + track["y"].diff()**2
        ).fillna(0).cumsum()

        # Detectar inicio de zonas de frenada
        track["braking_start"] = (track["brake"].diff().fillna(0) > 0) & (track["brake"] > 0)
        brake_events = track[track["braking_start"]].copy()

        if len(brake_events) < 5:
            st.warning("No se detectaron suficientes zonas de frenada para analizar.")
        else:
            # Velocidad de entrada = máxima en los 5 puntos previos al frenado
            entry_speeds = []
            for idx in brake_events.index:
                window = track.iloc[max(0, idx - 5):idx]
                entry_speeds.append(
                    window["speed"].max() if not window.empty else track.loc[idx, "speed"]
                )
            brake_events["entry_speed"] = entry_speeds

            # Distancia de frenada desde el pico de velocidad local hasta el inicio del frenado
            braking_distances = []
            for idx in brake_events.index:
                window = track.iloc[max(0, idx - 8):idx]
                if window.empty:
                    braking_distances.append(np.nan)
                    continue
                peak_idx = window["speed"].idxmax()
                braking_distances.append(track.loc[idx, "dist"] - track.loc[peak_idx, "dist"])
            brake_events["braking_distance"] = braking_distances

            brake_events = (
                brake_events
                .dropna(subset=["entry_speed", "braking_distance"])
                .pipe(lambda df: df[df["braking_distance"] <= 500])  # filtrar outliers físicamente imposibles
            )

            st.caption(f"{len(brake_events)} zonas de frenada detectadas.")

            # Modelo lineal: velocidad de entrada → distancia de frenada
            X_brake = brake_events[["entry_speed"]]
            y_brake = brake_events["braking_distance"]

            reg_brake = LinearRegression()
            reg_brake.fit(X_brake, y_brake)
            r2_brake  = reg_brake.score(X_brake, y_brake)
            mae_brake = mean_absolute_error(y_brake, reg_brake.predict(X_brake))

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Zonas de frenada", str(len(brake_events)))
                st.caption(f"Velocidad media de entrada: {brake_events['entry_speed'].mean():.0f} km/h")
            with col2:
                st.metric("R² del ajuste", f"{r2_brake:.3f}")
                st.caption("Relación entre velocidad de entrada y distancia de frenada.")
            with col3:
                st.metric("Error medio", f"±{mae_brake:.1f}m")
                st.caption(f"Distancia media de frenada: {brake_events['braking_distance'].mean():.0f}m")

            st.divider()

            # Scatter + línea de regresión
            x_range = np.linspace(brake_events["entry_speed"].min(), brake_events["entry_speed"].max(), 50)
            y_line  = reg_brake.predict(x_range.reshape(-1, 1))
            y_upper = y_line + mae_brake
            y_lower = y_line - mae_brake

            fig_scatter = go.Figure()
            # Banda de confianza
            fig_scatter.add_trace(go.Scatter(
                x=np.concatenate([x_range, x_range[::-1]]),
                y=np.concatenate([y_upper, y_lower[::-1]]),
                fill="toself",
                fillcolor="rgba(0,210,190,0.1)",
                line=dict(color="rgba(0,0,0,0)"),
                name=f"Margen ±{mae_brake:.1f}m",
                showlegend=True,
            ))
            # Puntos de frenada
            fig_scatter.add_trace(go.Scatter(
                x=brake_events["entry_speed"],
                y=brake_events["braking_distance"],
                mode="markers",
                marker=dict(size=9, color="#00D2BE", opacity=0.85),
                name="Zona de frenada",
            ))
            # Línea de regresión
            fig_scatter.add_trace(go.Scatter(
                x=x_range, y=y_line,
                mode="lines",
                line=dict(color="white", dash="dash", width=2),
                name="Ajuste lineal",
            ))

            fig_scatter.update_layout(
                **PLOTLY_BASE,
                height=420,
                xaxis=dict(title="Velocidad de entrada (km/h)", gridcolor="rgba(0,210,190,0.12)"),
                yaxis=dict(title="Distancia de frenada (m)", gridcolor="rgba(0,210,190,0.12)"),
                legend=dict(font=dict(color="white"), bgcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

            st.divider()

            # Simulador
            st.markdown("##### Simula una velocidad de entrada")
            sim_speed = st.slider(
                "Velocidad de entrada (km/h)",
                float(brake_events["entry_speed"].min()),
                float(brake_events["entry_speed"].max()),
                float(brake_events["entry_speed"].mean()),
            )
            sim_dist = reg_brake.predict([[sim_speed]])[0]

            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("Distancia estimada", f"{sim_dist:.0f}m")
            with col_s2:
                st.metric("Mejor caso", f"{max(0, sim_dist - mae_brake):.0f}m")
            with col_s3:
                st.metric("Peor caso", f"{sim_dist + mae_brake:.0f}m")

            st.divider()

            # Mapa del circuito con zonas de frenada
            st.markdown("##### Zonas de frenada sobre el trazado")

            fig_map = go.Figure()
            # Borde exterior
            fig_map.add_trace(go.Scatter(
                x=track["x"], y=track["y"], mode="lines",
                line=dict(color="rgba(180,180,180,0.9)", width=16),
                hoverinfo="skip", showlegend=False,
            ))
            # Asfalto interior
            fig_map.add_trace(go.Scatter(
                x=track["x"], y=track["y"], mode="lines",
                line=dict(color="rgba(10,10,10,1)", width=10),
                hoverinfo="skip", showlegend=False,
            ))
            # Puntos de inicio de frenada
            fig_map.add_trace(go.Scatter(
                x=brake_events["x"], y=brake_events["y"],
                mode="markers",
                marker=dict(
                    size=11,
                    color=brake_events["entry_speed"],
                    colorscale=[[0, "#FFF200"], [0.5, "#FF6B00"], [1, "#E10600"]],
                    colorbar=dict(title="Velocidad entrada (km/h)", tickfont=dict(color="white")),
                    line=dict(color="white", width=1),
                ),
                hovertemplate=(
                    "Velocidad entrada: %{marker.color:.0f} km/h<extra></extra>"
                ),
                name="Inicio de frenada",
            ))
            fig_map.update_layout(
                **PLOTLY_BASE,
                height=520,
                xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
                yaxis=dict(visible=False),
                showlegend=False,
            )
            st.plotly_chart(fig_map, use_container_width=True)

            st.caption(
                "Cada punto rojo marca el inicio de una frenada. "
                "El color indica la velocidad de entrada: amarillo = velocidad baja, rojo = velocidad alta. "
                "Los puntos más rojos son las frenadas más exigentes del circuito."
            )