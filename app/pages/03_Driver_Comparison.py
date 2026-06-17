import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from src.dashboard.data_loader import load_all_data
from src.dashboard.utils import global_style

#Configuración de página
st.set_page_config(page_title="Driver Comparison", layout="wide")
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


def get_fastest_lap(driver_laps: pd.DataFrame) -> pd.Series | None:
    valid_driver_laps = driver_laps.dropna(subset=["lap_duration"])
    if valid_driver_laps.empty:
        return None
    return valid_driver_laps.sort_values("lap_duration").iloc[0]

##Datos
data = load_all_data()

laps = data["laps"]
drivers = data["drivers"]
car_data = data["car_data"]
location = data["location"]

# Columnas de drivers que necesitamos en todos los datasets
driver_cols = [
    "session_key", "driver_number", "full_name", "last_name",
    "name_acronym", "team_name", "team_colour",
]

laps     = laps.merge(drivers[driver_cols], on=["session_key", "driver_number"], how="left")
car_data = car_data.merge(drivers[driver_cols], on=["session_key", "driver_number"], how="left")
location = location.merge(drivers[driver_cols], on=["session_key", "driver_number"], how="left")

#=============Sidebar Filtros===========================
st.sidebar.header("Filtros")

available_sessions = car_data[
    ["season", "country_name", "session_name", "session_key"]
].drop_duplicates()

season = st.sidebar.selectbox(
    "Season",
    sorted(available_sessions["season"].dropna().unique()),
)

sessions_season = available_sessions[available_sessions["season"] == season]

country = st.sidebar.selectbox(
    "Grand Prix",
    sorted(sessions_season["country_name"].dropna().unique()),
)

sessions_country = sessions_season[sessions_season["country_name"] == country]

session = st.sidebar.selectbox(
    "Session",
    sorted(sessions_country["session_name"].dropna().unique()),
)

session_options = sessions_country[
    sessions_country["session_name"] == session
]["session_key"].unique()
session_key = session_options[0]

session_car = car_data[car_data["session_key"] == session_key]
session_location = location[location["session_key"] == session_key]
session_laps = laps[laps["session_key"] == session_key]

available_drivers = (
    session_car[["driver_number", "full_name", "name_acronym", "team_name"]]
    .dropna(subset=["full_name"])
    .drop_duplicates()
    .sort_values("name_acronym")
)

driver_labels = {
    f"{row['name_acronym']} - {row['full_name']}": row["driver_number"]
    for _, row in available_drivers.iterrows()
}

col_a, col_b = st.sidebar.columns(2)
with col_a:
    driver_a_label = st.selectbox("Piloto A", list(driver_labels.keys()), index=0)
with col_b:
    driver_b_label = st.selectbox(
        "Piloto B",
        list(driver_labels.keys()),
        index=1 if len(driver_labels) > 1 else 0,
    )

driver_a = driver_labels[driver_a_label]
driver_b = driver_labels[driver_b_label]

#=================Guards============
st.title("Comparativa de vuelta rápida")
st.caption(f"{country} · {season} · {session}")

if driver_a == driver_b:
    st.warning("Selecciona dos pilotos diferentes.")
    st.stop()

lap_a = get_fastest_lap(session_laps[session_laps["driver_number"] == driver_a])
lap_b = get_fastest_lap(session_laps[session_laps["driver_number"] == driver_b])

if lap_a is None or lap_b is None:
    st.warning("Selecciona dos pilotos con al menos una vuelta válida.")
    st.stop()

st.divider()

##=========1ª DIVISION====
# Filtramos telemetría solo por la vuelta rápida de cada piloto
lap_number_a = int(lap_a["lap_number"])
lap_number_b = int(lap_b["lap_number"])

car_a = session_car[
    (session_car["driver_number"] == driver_a) &
    (session_car["lap_number"] == lap_number_a)
].sort_values("date").reset_index(drop=True)

car_b = session_car[
    (session_car["driver_number"] == driver_b) &
    (session_car["lap_number"] == lap_number_b)
].sort_values("date").reset_index(drop=True)

loc_a = session_location[
    (session_location["driver_number"] == driver_a) &
    (session_location["lap_number"] == lap_number_a)
].sort_values("date").reset_index(drop=True)

loc_b = session_location[
    (session_location["driver_number"] == driver_b) &
    (session_location["lap_number"] == lap_number_b)
].sort_values("date").reset_index(drop=True)

acr_a = lap_a["last_name"]
acr_b = lap_b["last_name"]
delta_lap = lap_a["lap_duration"] - lap_b["lap_duration"]
time_gap = abs(delta_lap)
faster_driver = acr_a if delta_lap < 0 else acr_b

driver_colors = {
    acr_a: f"#{lap_a['team_colour']}" if pd.notna(lap_a.get("team_colour")) else "#00D2BE",
    acr_b: f"#{lap_b['team_colour']}" if pd.notna(lap_b.get("team_colour")) else "#E10600",
}

#==============Vuelta más rápida===============
st.subheader("¿Cuál fue la referencia entre ambos pilotos?")

col1, col2, col3 = st.columns(3)
with col1:
    metric_flip_card(
        f"{acr_a} · Best lap",
        f"{lap_a['lap_duration']:.3f}s",
        "Vuelta",
        f"Lap {int(lap_a['lap_number'])}" if pd.notna(lap_a.get("lap_number")) else acr_a,
    )
with col2:
    metric_flip_card(
        f"{acr_b} · Best lap",
        f"{lap_b['lap_duration']:.3f}s",
        "Vuelta",
        f"Lap {int(lap_b['lap_number'])}" if pd.notna(lap_b.get("lap_number")) else acr_b,
    )
with col3:
    metric_flip_card(
        "Delta total",
        f"{delta_lap:+.3f}s",
        "Más rápido",
        faster_driver,
    )

st.caption(
    f"{faster_driver} fue la referencia de la sesión, con una ventaja total de {time_gap:.3f}s sobre su rival directo."
)

st.divider()

#==============2ª Division=========================
st.subheader("¿Dónde se gana o se pierde tiempo?")

sector_table = pd.DataFrame(
    {
        "Sector": ["S1", "S2", "S3"],
        acr_a: [
            lap_a["duration_sector_1"],
            lap_a["duration_sector_2"],
            lap_a["duration_sector_3"],
        ],
        acr_b: [
            lap_b["duration_sector_1"],
            lap_b["duration_sector_2"],
            lap_b["duration_sector_3"],
        ],
    }
)

sector_table["Delta"] = sector_table[acr_a] - sector_table[acr_b]
worst_sector = sector_table.iloc[sector_table["Delta"].abs().idxmax()]

def compact_sector_text(delta_value):
    if pd.isna(delta_value):
        return "—"
    return f"{acr_a} · {delta_value:+.3f}s"

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    st.metric("S1", compact_sector_text(sector_table.iloc[0]["Delta"]))

with col2:
    st.metric("S2", compact_sector_text(sector_table.iloc[1]["Delta"]))

with col3:
    st.metric("S3", compact_sector_text(sector_table.iloc[2]["Delta"]))

with col4:
    st.metric("Mayor pérdida", worst_sector["Sector"])

sector_long = sector_table.melt(
    id_vars="Sector",
    value_vars=[acr_a, acr_b],
    var_name="Piloto",
    value_name="Tiempo",
)

fig_sector = px.bar(
    sector_long,
    x="Sector",
    y="Tiempo",
    color="Piloto",
    barmode="group",
    color_discrete_map=driver_colors,
    labels={
        "Tiempo": "Tiempo por sector (s)",
        "Sector": "Sector",
        "Piloto": "Piloto",
    },
)

fig_sector.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    height=420,
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="white")),
)

st.plotly_chart(fig_sector, use_container_width=True)

st.caption(
    f"Los valores muestran la diferencia de {acr_a} respecto a {acr_b}: "
    f"La mayor diferencia estuvo en {worst_sector['Sector']}."
)

st.divider()
#==============3ª Division=========================
st.subheader("¿Cómo cambia la telemetría a lo largo de la vuelta?")

telemetry_columns = ["speed", "throttle", "brake", "rpm"]
telemetry_a = car_a[telemetry_columns].copy()
telemetry_b = car_b[telemetry_columns].copy()

telemetry_a["sample"] = np.linspace(0, 100, len(telemetry_a)) if not telemetry_a.empty else []
telemetry_b["sample"] = np.linspace(0, 100, len(telemetry_b)) if not telemetry_b.empty else []
telemetry_a["Piloto"] = acr_a
telemetry_b["Piloto"] = acr_b

telemetry = pd.concat([telemetry_a, telemetry_b], ignore_index=True)

telemetry_metric = st.radio(
    "Métrica de telemetría",
    ["speed", "throttle", "brake", "rpm"],
    horizontal=True,
    format_func={
        "speed": "Velocidad",
        "throttle": "Acelerador",
        "brake": "Freno",
        "rpm": "RPM",
    }.get,
)

fig_telemetry = px.line(
    telemetry,
    x="sample",
    y=telemetry_metric,
    color="Piloto",
    color_discrete_map=driver_colors,
    labels={
        "sample": "Progreso de vuelta (%)",
        telemetry_metric: telemetry_metric,
        "Piloto": "Piloto",
    },
)

fig_telemetry.update_yaxes(gridcolor="rgba(0, 210, 190, 0.12)")
fig_telemetry.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    height=440,
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(
        title=None,
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
        font=dict(size=14, color="white"),
        bgcolor="rgba(0,0,0,0)"
    ),
)
st.plotly_chart(fig_telemetry, use_container_width=True)

st.caption(
    "La vuelta se normaliza del 0% al 100% para comparar mejor velocidad, frenada, acelerador y régimen de motor."
)

st.divider()

#==============4ª Division=========================
st.subheader("¿Dónde está la diferencia en pista?")

loc_a_map = loc_a.copy()
loc_b_map = loc_b.copy()
car_a_map = car_a.copy()
car_b_map = car_b.copy()

loc_a_map["date"] = pd.to_datetime(loc_a_map["date"], format="mixed", utc=True, errors="coerce")
loc_b_map["date"] = pd.to_datetime(loc_b_map["date"], format="mixed", utc=True, errors="coerce")
car_a_map["date"] = pd.to_datetime(car_a_map["date"], format="mixed", utc=True, errors="coerce")
car_b_map["date"] = pd.to_datetime(car_b_map["date"], format="mixed", utc=True, errors="coerce")

loc_a_map = (
    loc_a_map[["date", "x", "y"]]
    .dropna(subset=["date", "x", "y"])
    .sort_values("date")
    .reset_index(drop=True)
)

loc_b_map = (
    loc_b_map[["date", "x", "y"]]
    .dropna(subset=["date", "x", "y"])
    .sort_values("date")
    .reset_index(drop=True)
)

car_a_map = (
    car_a_map[["date", "speed", "throttle", "brake"]]
    .dropna(subset=["date"])
    .sort_values("date")
    .reset_index(drop=True)
)

car_b_map = (
    car_b_map[["date", "speed", "throttle", "brake"]]
    .dropna(subset=["date"])
    .sort_values("date")
    .reset_index(drop=True)
)

if loc_a_map.empty or loc_b_map.empty or car_a_map.empty or car_b_map.empty:
    st.info("No hay suficientes datos de posición o telemetría para representar el mapa del circuito.")
else:
    track_a = pd.merge_asof(
        loc_a_map,
        car_a_map,
        on="date",
        direction="nearest",
        tolerance=pd.Timedelta("150ms"),
    )

    track_b = pd.merge_asof(
        loc_b_map,
        car_b_map,
        on="date",
        direction="nearest",
        tolerance=pd.Timedelta("150ms"),
    )

    track_a = track_a.dropna(subset=["speed", "throttle", "brake"]).reset_index(drop=True)
    track_b = track_b.dropna(subset=["speed", "throttle", "brake"]).reset_index(drop=True)

    base_track = loc_a_map if len(loc_a_map) >= len(loc_b_map) else loc_b_map
    base_track = base_track.reset_index(drop=True)

    min_len = min(len(track_a), len(track_b))

    if min_len == 0:
        st.info("No se pudo alinear la posición con la telemetría en esta vuelta.")
    else:
        track_a = track_a.iloc[:min_len].reset_index(drop=True)
        track_b = track_b.iloc[:min_len].reset_index(drop=True)

        track_compare = pd.DataFrame(
            {
                "x": track_a["x"],
                "y": track_a["y"],
                "speed_a": track_a["speed"],
                "speed_b": track_b["speed"],
                "throttle_a": track_a["throttle"],
                "throttle_b": track_b["throttle"],
                "brake_a": track_a["brake"],
                "brake_b": track_b["brake"],
            }
        )

        track_compare["speed_delta"] = track_compare["speed_a"] - track_compare["speed_b"]
        track_compare["throttle_delta"] = track_compare["throttle_a"] - track_compare["throttle_b"]
        track_compare["brake_delta"] = track_compare["brake_a"] - track_compare["brake_b"]

        metric_map = st.radio(
            "Métrica en pista",
            ["speed_delta", "throttle_delta", "brake_delta"],
            horizontal=True,
            format_func={
                "speed_delta": "Velocidad",
                "throttle_delta": "Aceleración",
                "brake_delta": "Frenada",
            }.get,
        )

        if metric_map == "speed_delta":
            color_col = "speed_delta"
            caption_text = (
                f"Turquesa: {acr_a} pasa por ese punto con más velocidad. "
                f"Rojo: {acr_b} pasa por ese punto con más velocidad."
            )
            colorbar_title = "Delta velocidad"
            hover_title = "Velocidad en este punto"

        elif metric_map == "throttle_delta":
            color_col = "throttle_delta"
            caption_text = (
                f"Turquesa: {acr_a} está acelerando más en esa zona. "
                f"Rojo: {acr_b} está acelerando más."
            )
            colorbar_title = "Delta acelerador"
            hover_title = "Aceleración en este punto"

        else:
            color_col = "brake_delta"
            caption_text = (
                f"Turquesa: {acr_a} está aplicando más freno en esa zona. "
                f"Rojo: {acr_b} está aplicando más freno."
            )
            colorbar_title = "Delta frenada"
            hover_title = "Frenada en este punto"

        vmax = np.nanmax(np.abs(track_compare[color_col].values))
        vmax = vmax if np.isfinite(vmax) and vmax > 0 else 1

        fig_track = go.Figure()

        # Borde exterior del circuito
        fig_track.add_scatter(
            x=base_track["x"],
            y=base_track["y"],
            mode="lines",
            line=dict(color="rgba(180,180,180,0.9)", width=16),
            hoverinfo="skip",
            showlegend=False,
        )

        # Asfalto interior oscuro
        fig_track.add_scatter(
            x=base_track["x"],
            y=base_track["y"],
            mode="lines",
            line=dict(color="rgba(10,10,10,1)", width=10),
            hoverinfo="skip",
            showlegend=False,
        )

        # Puntos del delta encima
        fig_track.add_scatter(
            x=track_compare["x"],
            y=track_compare["y"],
            mode="markers",
            marker=dict(
                size=6,
                color=track_compare[color_col],
                cmin=-vmax,
                cmax=vmax,
                colorscale=["#B3110C", "#F5F5F5", "#05AE9D"],
                colorbar=dict(title=colorbar_title),
                line=dict(width=0),
                opacity=1,
            ),
            customdata=np.stack(
                [
                    track_compare["speed_a"],
                    track_compare["speed_b"],
                    track_compare["throttle_a"],
                    track_compare["throttle_b"],
                    track_compare["brake_a"],
                    track_compare["brake_b"],
                ],
                axis=-1,
            ),
            hovertemplate=(
                f"<b>{hover_title}</b><br>"
                f"Velocidad {acr_a}: %{{customdata[0]:.1f}} km/h<br>"
                f"Velocidad {acr_b}: %{{customdata[1]:.1f}} km/h<br>"
                f"Acelerador {acr_a}: %{{customdata[2]:.0f}}%<br>"
                f"Acelerador {acr_b}: %{{customdata[3]:.0f}}%<br>"
                f"Freno {acr_a}: %{{customdata[4]:.0f}}%<br>"
                f"Freno {acr_b}: %{{customdata[5]:.0f}}%<br>"
                "<extra></extra>"
            ),
            showlegend=False,
        )

        fig_track.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=650,
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
            showlegend=False,
        )

        st.plotly_chart(fig_track, use_container_width=True)
        st.caption(
            f"{caption_text} El contorno gris marca el circuito y los puntos coloreados muestran el delta entre ambos pilotos."
        )

st.divider()
#==============5ª Division=========================
st.subheader("Lectura rápida")

st.markdown(
    f"""
    <div class="insight-box">
        <strong>Interpretación</strong><br><br>
        En la sesión seleccionada, <strong>{faster_driver}</strong> registra la mejor vuelta entre ambos pilotos,
        con una diferencia de <strong>{time_gap:.3f}s</strong>.<br><br>
        La mayor diferencia aparece en el <strong>{worst_sector['Sector']}</strong>, donde el delta es de
        <strong>{worst_sector['Delta']:+.3f}s</strong>. Ese sector debería ser el foco principal del análisis.<br><br>
        La telemetría y el mapa del circuito permiten localizar si la ventaja llega por velocidad punta,
        mejor frenada o una aceleración más limpia a la salida de curva.
    </div>
    """,
    unsafe_allow_html=True,
)