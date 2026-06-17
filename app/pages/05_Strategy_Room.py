import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from src.dashboard.data_loader import load_all_data, filter_valid_laps
from src.dashboard.utils import global_style

#Configuración de página
st.set_page_config(page_title="Strategy Room", layout="wide")
global_style()

#CTEs
COMPOUND_COLORS = {
    "SOFT":         "#E8002D",
    "MEDIUM":       "#FFF200",
    "HARD":         "#FFFFFF",
    "INTERMEDIATE": "#39B54A",
    "WET":          "#0067FF",
    "UNKNOWN":      "#777777",
}

PLOTLY_BASE = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    margin=dict(l=20, r=20, t=20, b=20),
)

#Helpers
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

##Datos + Merge
data = load_all_data()

driver_cols = [
    "session_key", "driver_number", "full_name", "last_name",
    "name_acronym", "team_name", "team_colour",
]

laps   = data["laps"].merge(data["drivers"][driver_cols], on=["session_key", "driver_number"], how="left")
stints = data["stints"].merge(data["drivers"][driver_cols], on=["session_key", "driver_number"], how="left")

##=============Sidebar Filtros===========================
st.sidebar.header("Filtros")

# Solo sesiones de carrera
race_sessions = (
    stints[["season", "country_name", "session_name", "session_type", "session_key"]]
    .drop_duplicates()
    .pipe(lambda df: df[df["session_type"] == "Race"])
)

if race_sessions.empty:
    st.warning("No hay carreras disponibles para analizar.")
    st.stop()

season = st.sidebar.selectbox("Season", sorted(race_sessions["season"].dropna().unique()))
sessions_season = race_sessions[race_sessions["season"] == season]

country = st.sidebar.selectbox("Grand Prix", sorted(sessions_season["country_name"].dropna().unique()))
sessions_country = sessions_season[sessions_season["country_name"] == country]

session_key = sessions_country["session_key"].iloc[0]

session_laps   = laps[laps["session_key"] == session_key].copy()
session_stints = stints[stints["session_key"] == session_key].copy()
valid_laps     = filter_valid_laps(session_laps)

driver_options = sorted(session_stints["name_acronym"].dropna().unique())
selected_drivers = st.sidebar.multiselect("Pilotos", driver_options, default=driver_options)

#=============Guards=======================
st.title("Strategy Room")
st.caption(f"{country} · {season} · Race Strategy Analysis")

if session_stints.empty or not selected_drivers:
    st.warning("No hay datos de estrategia para la selección actual.")
    st.stop()

session_stints   = session_stints[session_stints["name_acronym"].isin(selected_drivers)].copy()
valid_laps       = valid_laps[valid_laps["name_acronym"].isin(selected_drivers)].copy()

session_stints = session_stints[
    session_stints["lap_start"].notna() &
    session_stints["lap_end"].notna() &
    session_stints["stint_number"].notna()
].copy()

session_stints["lap_start"] = session_stints["lap_start"].astype(int)
session_stints["lap_end"] = session_stints["lap_end"].astype(int)
session_stints["stint_number"] = session_stints["stint_number"].astype(int)

if session_stints.empty:
    st.warning("No hay stints válidos para esta selección.")
    st.stop()

session_stints["stint_length"] = session_stints["lap_end"] - session_stints["lap_start"] + 1

st.divider()

##=========1ª DIVISION====
st.subheader("¿Qué estrategia siguió cada piloto?")

total_stints      = len(session_stints)
avg_stint         = session_stints["stint_length"].mean()
most_used_compound = session_stints["compound"].mode().iloc[0]
max_stint         = session_stints["stint_length"].max()
longest_stint_row = session_stints.sort_values("stint_length", ascending=False).iloc[0]
most_stops_driver = (
    session_stints.groupby("name_acronym")["stint_number"].max().idxmax()
)
most_stops_count  = session_stints.groupby("name_acronym")["stint_number"].max().max() - 1

col1, col2, col3, col4 = st.columns(4)

with col1:
    metric_flip_card(
        "Stints totales",
        f"{total_stints}",
        "Media por piloto",
        f"{total_stints / max(len(selected_drivers), 1):.1f}",
    )
with col2:
    metric_flip_card(
        "Duración media",
        f"{avg_stint:.1f} vueltas",
        "Stint más largo",
        f"{int(max_stint)} · {longest_stint_row['name_acronym']}",
    )
with col3:
    metric_flip_card(
        "Neumático dominante",
        most_used_compound,
        "Color",
        "↑ el más usado en carrera",
    )
with col4:
    metric_flip_card(
        "Más paradas",
        most_stops_driver,
        "Número de paradas",
        f"{int(most_stops_count)}",
    )

st.divider()

#==========2ª DIVISION===========
st.subheader("¿Cuándo paró cada uno?")

fig_timeline = go.Figure()

for driver in selected_drivers:
    driver_stints = session_stints[
        session_stints["name_acronym"] == driver
    ].sort_values("stint_number")

    for _, row in driver_stints.iterrows():
        compound = row["compound"]
        color    = COMPOUND_COLORS.get(compound, "#999999")

        fig_timeline.add_trace(go.Bar(
            x=[row["stint_length"]],
            y=[driver],
            base=row["lap_start"],
            orientation="h",
            marker=dict(color=color, line=dict(color="rgba(255,255,255,0.35)", width=1)),
            hovertemplate=(
                f"<b>{driver}</b><br>"
                f"Compuesto: {compound}<br>"
                f"Stint: {int(row['stint_number'])}<br>"
                f"Vueltas: {int(row['lap_start'])} → {int(row['lap_end'])}<br>"
                f"Duración: {int(row['stint_length'])} vueltas"
                "<extra></extra>"
            ),
            showlegend=False,
        ))

# Leyenda de compuestos usados
for compound in session_stints["compound"].dropna().unique():
    fig_timeline.add_trace(go.Bar(
        x=[None], y=[None],
        marker=dict(color=COMPOUND_COLORS.get(compound, "#999")),
        name=compound,
        showlegend=True,
    ))

fig_timeline.update_layout(
    **PLOTLY_BASE,
    barmode="stack",
    height=max(380, len(selected_drivers) * 38),
    xaxis=dict(title="Vuelta", gridcolor="rgba(0,210,190,0.12)"),
    yaxis=dict(title=""),
    legend=dict(
        orientation="h", y=1.05, x=0,
        font=dict(color="white"), bgcolor="rgba(0,0,0,0)",
    ),
)

st.plotly_chart(fig_timeline, use_container_width=True)
st.caption(
    "Cada barra es un stint. El color indica el compuesto y la longitud muestra cuántas vueltas duró. "
    "Las transiciones entre barras representan las paradas en boxes."
)

st.divider()

#===========3ª DIVISION=================
st.subheader("¿Qué neumático dominó la carrera?")

compound_summary = (
    session_stints.groupby("compound", as_index=False)
    .agg(
        stints=("stint_number", "count"),
        total_laps=("stint_length", "sum"),
        avg_length=("stint_length", "mean"),
    )
    .sort_values("total_laps", ascending=False)
)

col1, col2 = st.columns(2)

with col1:
    fig_total = px.bar(
        compound_summary,
        x="compound", y="total_laps",
        color="compound",
        color_discrete_map=COMPOUND_COLORS,
        labels={"compound": "Compuesto", "total_laps": "Vueltas totales"},
    )
    fig_total.update_layout(**PLOTLY_BASE, height=340, showlegend=False,
                             yaxis=dict(gridcolor="rgba(0,210,190,0.12)"))
    st.plotly_chart(fig_total, use_container_width=True)
    st.caption("Vueltas totales acumuladas por compuesto en toda la carrera.")

with col2:
    fig_avg = px.bar(
        compound_summary,
        x="compound", y="avg_length",
        color="compound",
        color_discrete_map=COMPOUND_COLORS,
        labels={"compound": "Compuesto", "avg_length": "Duración media (vueltas)"},
    )
    fig_avg.update_layout(**PLOTLY_BASE, height=340, showlegend=False,
                           yaxis=dict(gridcolor="rgba(0,210,190,0.12)"))
    st.plotly_chart(fig_avg, use_container_width=True)
    st.caption("Duración media por stint según compuesto — indica cuánto aguanta cada neumático.")

best_compound  = compound_summary.iloc[0]
worst_compound = compound_summary.iloc[-1]
st.caption(
    f"**{best_compound['compound']}** fue el compuesto más rodado con **{int(best_compound['total_laps'])} vueltas** "
    f"y una duración media de **{best_compound['avg_length']:.1f} vueltas** por stint. "
    f"**{worst_compound['compound']}** fue el menos utilizado con {int(worst_compound['total_laps'])} vueltas."
)

st.divider()

#===========4ª DIVISION===============
stint_info = session_stints[
    ["session_key", "driver_number", "stint_number", "compound", "lap_start", "lap_end"]
].copy()

laps_with_stint = []

for _, stint in stint_info.iterrows():
    in_lap = int(stint["lap_end"])  # última vuelta del stint = in-lap
    mask = (
        (valid_laps["session_key"] == stint["session_key"]) &
        (valid_laps["driver_number"] == stint["driver_number"]) &
        (valid_laps["lap_number"] >= stint["lap_start"]) &
        (valid_laps["lap_number"] < in_lap)   # excluir in-lap
    )
    tmp = valid_laps.loc[mask].copy()
    tmp["stint_number"] = stint["stint_number"]
    tmp["compound"] = stint["compound"]
    laps_with_stint.append(tmp)

if laps_with_stint:
    pace_laps = pd.concat(laps_with_stint, ignore_index=True)
else:
    pace_laps = pd.DataFrame()

st.subheader("¿Cuál fue el stint más eficiente?")

if not pace_laps.empty:
    stint_summary = (
        pace_laps
        .groupby(["name_acronym", "stint_number", "compound"], as_index=False)
        .agg(avg_lap=("lap_duration", "mean"), best_lap=("lap_duration", "min"), laps=("lap_duration", "count"))
        .pipe(lambda df: df[df["laps"] >= 3])
        .sort_values("avg_lap")
    )

    if not stint_summary.empty:
        best_stint  = stint_summary.iloc[0]
        worst_stint = stint_summary.iloc[-1]
        gap_stints  = worst_stint["avg_lap"] - best_stint["avg_lap"]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            metric_flip_card("Piloto", best_stint["name_acronym"], "Compuesto", best_stint["compound"])
        with col2:
            metric_flip_card("Stint", str(int(best_stint["stint_number"])), "Vueltas", str(int(best_stint["laps"])))
        with col3:
            metric_flip_card("Ritmo medio", f"{best_stint['avg_lap']:.3f}s", "Mejor vuelta", f"{best_stint['best_lap']:.3f}s")
        with col4:
            metric_flip_card("Gap vs peor stint", f"+{gap_stints:.3f}s", "Peor stint", worst_stint["name_acronym"])

        st.divider()

        st.subheader("Conclusión estratégica")
        st.markdown(
            f"""
            <div class="insight-box">
                <strong>Resumen de carrera</strong><br><br>
                El neumático más utilizado fue <strong>{most_used_compound}</strong>,
                lo que refleja la estrategia dominante en esta carrera.<br><br>
                El stint más largo alcanzó <strong>{int(max_stint)} vueltas</strong>
                ({longest_stint_row['name_acronym']}), indicando una apuesta por extender
                el compuesto y reducir el número de paradas.<br><br>
                El stint más eficiente fue el de <strong>{best_stint['name_acronym']}</strong>
                con <strong>{best_stint['compound']}</strong>,
                con un ritmo medio de <strong>{best_stint['avg_lap']:.3f}s</strong>
                sobre {int(best_stint['laps'])} vueltas válidas.<br><br>
                La diferencia entre el stint más rápido y el más lento fue de
                <strong>{gap_stints:.3f}s</strong> por vuelta —
                una brecha que a lo largo de una carrera puede traducirse en
                <strong>{gap_stints * 50:.1f}s</strong> de ventaja acumulada.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("No hay suficientes datos para identificar el stint más eficiente.")
else:
    st.info("No hay datos de ritmo disponibles para calcular el stint más eficiente.")