import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from src.dashboard.data_loader import load_all_data, filter_valid_laps
from src.dashboard.utils import global_style

#Configuración de página
st.set_page_config(page_title="Race Overview", layout="wide")
global_style()


##Datos
data = load_all_data()

laps = data["laps"]
drivers = data["drivers"]

laps = laps.merge(
    drivers[
        [
            "session_key",
            "driver_number",
            "full_name",
            "name_acronym",
            "team_name",
            "team_colour",
        ]
    ],
    on=["session_key", "driver_number"],
    how="left"
)

##=============Sidebar Filtros===========================
st.sidebar.header("Filtros")

season = st.sidebar.selectbox(
    "Season",
    sorted(laps["season"].dropna().unique())
)

laps_season = laps[laps["season"] == season]

country = st.sidebar.selectbox(
    "Grand Prix",
    sorted(laps_season["country_name"].dropna().unique())
)

laps_country = laps_season[laps_season["country_name"] == country]

session = st.sidebar.selectbox(
    "Session",
    sorted(laps_country["session_name"].dropna().unique())
)

laps_filtered = laps_country[laps_country["session_name"] == session]
valid_laps = filter_valid_laps(laps_filtered)

#=================Guard============
st.title("Race Intelligence")
st.caption("Vista ejecutiva del ritmo de carrera, consistencia y rendimiento por equipo.")
st.caption(f"{country} · {season} · {session}")

if valid_laps.empty:
    st.warning(
        "No hay vueltas válidas para la sesión seleccionada. "
        "Prueba con otra combinación de temporada, GP o sesión."
    )
    st.stop()

#=============Resumenes============

driver_summary = (
    valid_laps.groupby(
        ["driver_number", "full_name", "name_acronym", "team_name"],
        as_index=False
    )
    .agg(
        avg_lap_time=("lap_duration", "mean"),
        best_lap=("lap_duration", "min"),
        lap_std=("lap_duration", "std"),
        laps_completed=("lap_number", "count"),
    )
    .sort_values("avg_lap_time")
)

team_summary = (
    driver_summary.groupby("team_name", as_index=False)
    .agg(
        avg_lap_time=("avg_lap_time", "mean"),
        best_lap=("best_lap", "min"),
        avg_deviation=("lap_std", "mean"),
        drivers=("driver_number", "nunique"),
    )
    .sort_values("avg_lap_time")
)

fastest_lap_driver = valid_laps.sort_values("lap_duration").iloc[0]
best_average_driver = driver_summary.iloc[0]

##==========Flip Cards====================
   
def metric_flip_card(title, front_value, back_title, back_value):
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
        unsafe_allow_html=True
    )
    
col1, col2, col3, col4 = st.columns(4)

with col1:
    metric_flip_card(
        "Piloto más rápido",
        fastest_lap_driver["name_acronym"],
        "Mejor vuelta",
        f"{fastest_lap_driver['lap_duration']:.2f}s",
    )
with col2:
    metric_flip_card(
        "Mejor ritmo medio",
        best_average_driver["name_acronym"],
        "Media por vuelta",
        f"{best_average_driver['avg_lap_time']:.2f}s",
    )
with col3:
    metric_flip_card(
        "Ritmo de sesión",
        f"{valid_laps['lap_duration'].mean():.2f}s",
        "Vueltas válidas",
        len(valid_laps),
    )
with col4:
    metric_flip_card(
        "Pilotos analizados",
        valid_laps["driver_number"].nunique(),
        "Vueltas registradas",
        len(laps_filtered),
    )

st.divider()

##==========Gráfico de Barra de Ritmo=======

left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("Ritmo medio por piloto")

    fig_pace = px.bar(
        driver_summary,
        x="name_acronym",
        y="avg_lap_time",
        hover_data={
            "full_name": True,
            "team_name": True,
            "best_lap": ":.2f",
            "lap_std": ":.2f",
            "laps_completed": True,
            "avg_lap_time": ":.2f",
        },
        labels={
            "name_acronym": "Piloto",
            "avg_lap_time": "Tiempo medio por vuelta (s)",
            "full_name": "Nombre",
            "team_name": "Equipo",
            "best_lap": "Mejor vuelta",
            "lap_std": "Desviación",
            "laps_completed": "Vueltas válidas",
        },
    )
    fig_pace.update_traces(marker_color="#00D2BE")
    fig_pace.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=430,
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig_pace, use_container_width=True)

with right_col:
    st.subheader("Conclusión principal")

    if fastest_lap_driver is not None and best_average_driver is not None:
        st.markdown(
            f"""
            **{fastest_lap_driver['full_name']}** registró la vuelta más rápida de la sesión,
            con un tiempo de **{fastest_lap_driver['lap_duration']:.2f}s**.

            **{best_average_driver['full_name']}** presenta el mejor ritmo medio:
            **{best_average_driver['avg_lap_time']:.2f}s** por vuelta.

            El análisis excluye vueltas de salida de boxes y valores atípicos para representar el rendimiento real en pista.
            """
        )
    else:
        st.warning(
            "No existen suficientes vueltas válidas para generar conclusiones con la selección actual."
        )

st.divider()

#===========Distribución tiempo/vuelta y Ritmo Equipo============

col1, col2 = st.columns(2)

with col1:
    st.subheader("Distribución de tiempos por vuelta")

    fig_dist = px.histogram(
        valid_laps,
        x="lap_duration",
        nbins=40,
        labels={
            "lap_duration": "Tiempo por vuelta (s)",
            "count": "Número de vueltas",
        },
    )
    fig_dist.update_traces(
        marker_color="#00D2BE",
        marker_line_color="#004d45",
        marker_line_width=1.2,
    )
    fig_dist.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
    )

    st.plotly_chart(fig_dist, use_container_width=True)
    

with col2:
    st.subheader("Rendimiento por equipo")

    fig_team = px.bar(
        team_summary,
        x="avg_lap_time",
        y="team_name",
        orientation="h",
        hover_data={
            "best_lap": ":.2f",
            "avg_deviation": ":.2f",
            "drivers": True,
        },
        labels={
            "team_name": "Equipo",
            "avg_lap_time": "Tiempo medio (s)",
            "best_lap": "Mejor vuelta",
            "avg_deviation": "Desviación media",
            "drivers": "Pilotos",
        },
    )
    fig_team.update_traces(marker_color="#006F62")
    fig_team.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=400,
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig_team, use_container_width=True)
    
    
###==============Conclusion===========

best_team = team_summary.iloc[0]
worst_team = team_summary.iloc[-1]
pace_gap = worst_team["avg_lap_time"] - best_team["avg_lap_time"]

st.info(
    f"""
    CONCLUSIONES DE LA SESIÓN

• {best_team['team_name']} registra el mejor ritmo medio de la sesión con un tiempo de {best_team['avg_lap_time']:.2f}s por vuelta.

• {worst_team['team_name']} presenta el ritmo medio más lento con {worst_team['avg_lap_time']:.2f}s.

• La diferencia entre ambos equipos es de {pace_gap:.2f}s por vuelta.

• La distribución de tiempos muestra que la mayoría de vueltas competitivas se concentran entre los valores más bajos del histograma, mientras que las vueltas más lentas pueden estar asociadas a tráfico, errores, preparación de vuelta o degradación de neumáticos.

• Los resultados mostrados excluyen vueltas de salida de boxes y registros detectados como atípicos durante el proceso de limpieza.
"""
)

st.divider()
