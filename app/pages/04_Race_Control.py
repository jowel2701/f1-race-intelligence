import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from src.dashboard.data_loader import load_all_data
from src.dashboard.utils import global_style

#Configuración de página
st.set_page_config(page_title="Race Conditions", layout="wide")
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

FLAG_COLORS = {
    "GREEN":     "#39B54A",
    "YELLOW":    "#FFF200",
    "DOUBLE YELLOW": "#FFA500",
    "RED":       "#E10600",
    "BLUE":      "#0067FF",
    "BLACK":     "#FFFFFF",
    "CHEQUERED": "#FFFFFF",
    "CLEAR":     "#00D2BE",
}

##Datos
data = load_all_data()
weather      = data["weather"]
race_control = data["race_control"]

#=============Sidebar Filtros===========================
st.sidebar.header("Filtros")

available_sessions = weather[
    ["season", "country_name", "session_name", "session_type", "session_key"]
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
session_key = sessions_country[
    sessions_country["session_name"] == session
]["session_key"].iloc[0]

session_weather = weather[weather["session_key"] == session_key].copy()
session_control = race_control[race_control["session_key"] == session_key].copy()

#=================Guards============
st.title("Race Conditions")
st.caption(f"{country} · {season} · {session}")

if session_weather.empty:
    st.warning("No hay datos meteorológicos para esta sesión.")
    st.stop()

session_weather["date"] = pd.to_datetime(
    session_weather["date"], format="mixed", utc=True, errors="coerce"
)
session_weather = session_weather.sort_values("date").reset_index(drop=True)

if not session_control.empty:
    session_control["date"] = pd.to_datetime(
        session_control["date"], format="mixed", utc=True, errors="coerce"
    )
    session_control = session_control.sort_values("date").reset_index(drop=True)

st.divider()

##=========1ª DIVISION====
st.subheader("¿Cuáles fueron las condiciones de pista?")

avg_air    = session_weather["air_temperature"].mean()
avg_track  = session_weather["track_temperature"].mean()
max_track  = session_weather["track_temperature"].max()
avg_hum    = session_weather["humidity"].mean()
avg_wind   = session_weather["wind_speed"].mean()
max_wind   = session_weather["wind_speed"].max()
rain_pct   = session_weather["rainfall"].mean() * 100
had_rain   = session_weather["rainfall"].any()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    metric_flip_card(
        "Temp. ambiente",
        f"{avg_air:.1f} °C",
        "Variación",
        f"{session_weather['air_temperature'].min():.1f} → {session_weather['air_temperature'].max():.1f} °C",
    )
with col2:
    metric_flip_card(
        "Temp. pista",
        f"{avg_track:.1f} °C",
        "Máxima",
        f"{max_track:.1f} °C",
    )
with col3:
    metric_flip_card(
        "Humedad",
        f"{avg_hum:.1f}%",
        "Impacto",
        "Alta → neumáticos más fríos",
    )
with col4:
    metric_flip_card(
        "Viento medio",
        f"{avg_wind:.1f} km/h",
        "Ráfaga máxima",
        f"{max_wind:.1f} km/h",
    )
with col5:
    metric_flip_card(
        "Lluvia",
        "Sí" if had_rain else "No",
        "% sesión con lluvia",
        f"{rain_pct:.1f}%",
    )

st.divider()

#==============2ª Division=========================
st.subheader("¿Cómo evolucionó el clima durante la sesión?")

tab_temp, tab_wind, tab_hum = st.tabs(["🌡 Temperatura", "💨 Viento", "💧 Humedad y lluvia"])

with tab_temp:
    weather_temp = session_weather.melt(
        id_vars="date",
        value_vars=["air_temperature", "track_temperature"],
        var_name="metric", value_name="value",
    )
    weather_temp["metric"] = weather_temp["metric"].map({
        "air_temperature":   "Temp. ambiente",
        "track_temperature": "Temp. pista",
    })

    fig_temp = px.line(
        weather_temp, x="date", y="value", color="metric",
        labels={"date": "Tiempo", "value": "Temperatura (°C)", "metric": ""},
        color_discrete_map={
            "Temp. ambiente": "#00D2BE",
            "Temp. pista":    "#E10600",
        },
    )
    fig_temp.update_traces(line=dict(width=2.5))
    fig_temp.update_layout(
        **PLOTLY_BASE, height=380,
        yaxis=dict(gridcolor="rgba(0,210,190,0.12)"),
        legend=dict(orientation="h", y=1.05, x=0, bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_temp, use_container_width=True)
    st.caption(
        "La temperatura de pista suele ser 10-20°C mayor que la ambiente y condiciona "
        "directamente la degradación y el comportamiento del neumático."
    )

with tab_wind:
    fig_wind = go.Figure()
    fig_wind.add_trace(go.Scatter(
        x=session_weather["date"],
        y=session_weather["wind_speed"],
        mode="lines",
        name="Velocidad viento",
        line=dict(color="#00D2BE", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(0,210,190,0.08)",
    ))
    fig_wind.update_layout(
        **PLOTLY_BASE, height=380,
        yaxis=dict(title="Velocidad (km/h)", gridcolor="rgba(0,210,190,0.12)"),
        xaxis=dict(title="Tiempo"),
    )
    st.plotly_chart(fig_wind, use_container_width=True)

    avg_dir = session_weather["wind_direction"].mean()
    st.caption(
        f"Viento medio de **{avg_wind:.1f} km/h** con dirección media de **{avg_dir:.0f}°**. "
        f"Ráfagas de hasta **{max_wind:.1f} km/h**. "
        f"El viento lateral fuerte puede afectar la estabilidad en rectas y la carga aerodinámica."
    )

with tab_hum:
    fig_hum = go.Figure()
    fig_hum.add_trace(go.Scatter(
        x=session_weather["date"],
        y=session_weather["humidity"],
        mode="lines",
        name="Humedad",
        line=dict(color="#4ECDC4", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(78,205,196,0.08)",
    ))

    if had_rain:
        rain_times = session_weather[session_weather["rainfall"] == True]["date"]
        for t in rain_times:
            fig_hum.add_vline(
                x=t.timestamp() * 1000,
                line=dict(color="#0067FF", width=1, dash="dot"),
            )

    fig_hum.update_layout(
        **PLOTLY_BASE, height=380,
        yaxis=dict(title="Humedad (%)", gridcolor="rgba(0,210,190,0.12)", range=[0, 100]),
        xaxis=dict(title="Tiempo"),
    )
    st.plotly_chart(fig_hum, use_container_width=True)
    st.caption(
        f"Humedad media del **{avg_hum:.1f}%**. "
        + ("Las líneas azules marcan los momentos en que se registró lluvia." if had_rain
           else "No se registró lluvia durante la sesión.")
    )

st.divider()

#==============3ª Division=========================
st.subheader("¿Qué ocurrió durante la sesión?")

if session_control.empty:
    st.info("No hay eventos de Race Control disponibles para esta sesión.")
else:
    event_counts = (
        session_control["category"]
        .fillna("UNKNOWN")
        .value_counts()
        .reset_index()
        .rename(columns={"category": "category", "count": "count"})
    )

    col_chart, col_table = st.columns([1, 1])

    with col_chart:
        fig_events = px.bar(
            event_counts.sort_values("count", ascending=True),
            x="count", y="category",
            orientation="h",
            color="count",
            color_continuous_scale=["#006F62", "#00D2BE"],
            labels={"count": "Eventos", "category": "Categoría"},
        )
        fig_events.update_layout(
            **PLOTLY_BASE, height=380,
            coloraxis_showscale=False,
            xaxis=dict(gridcolor="rgba(0,210,190,0.12)"),
            yaxis=dict(title=""),
        )
        st.plotly_chart(fig_events, use_container_width=True)
        st.caption("Distribución de eventos registrados por Dirección de Carrera.")

    # Banderas
    if "flag" in session_control.columns:
        flag_counts = (
            session_control["flag"]
            .dropna()
            .value_counts()
            .reset_index()
            .rename(columns={"flag": "Bandera", "count": "Veces"})
        )
        if not flag_counts.empty:
            st.caption(
                "Banderas mostradas: "
                + " · ".join(f"**{row['Bandera']}** ({row['Veces']})" for _, row in flag_counts.iterrows())
            )

st.divider()

#==============4ª Division=========================
st.subheader("Conclusión de condiciones")

total_events = len(session_control) if not session_control.empty else 0
sc_events = (
    len(session_control[session_control["category"].str.upper().str.contains("SAFETY", na=False)])
    if not session_control.empty else 0
)

st.markdown(
    f"""
    <div class="insight-box">
        <strong>Resumen de condiciones · {country} {season}</strong><br><br>
        La sesión se disputó con una temperatura ambiente media de <strong>{avg_air:.1f} °C</strong>
        y una temperatura de pista de <strong>{avg_track:.1f} °C</strong>
        (máxima: <strong>{max_track:.1f} °C</strong>).<br><br>
        {'Se registró lluvia durante la sesión, lo que pudo condicionar la estrategia de neumáticos y los tiempos por vuelta.' if had_rain
         else 'No hubo lluvia, con condiciones de pista seca durante toda la sesión.'}<br><br>
        La humedad media fue del <strong>{avg_hum:.1f}%</strong> con un viento medio de
        <strong>{avg_wind:.1f} km/h</strong>.<br><br>
        {'Se registraron <strong>' + str(total_events) + '</strong> eventos de Race Control'
         + (f', incluyendo <strong>{sc_events}</strong> intervenciones del Safety Car' if sc_events > 0 else '')
         + '.' if total_events > 0 else 'No se registraron eventos de Race Control.'}
    </div>
    """,
    unsafe_allow_html=True,
)