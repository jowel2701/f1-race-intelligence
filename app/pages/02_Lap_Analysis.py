import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from src.dashboard.data_loader import load_all_data, filter_valid_laps
from src.dashboard.utils import global_style

#Configuración de página
st.set_page_config(page_title="Lap Analysis", layout="wide")
global_style()

##Datos
data = load_all_data()

# Merge laps + drivers
laps = data["laps"]
drivers = data["drivers"]

laps = laps.merge(
    drivers[
        [
            "session_key",
            "driver_number",
            "full_name",
            "last_name",
            "name_acronym",
            "team_name",
            "team_colour",
        ]
    ],
    on=["session_key", "driver_number"],
    how="left"
)

# Merge stints para compound y número de stint
stints = data["stints"][
    ["session_key", "driver_number", "stint_number", "compound",
     "lap_start", "lap_end"]
]

def assign_compound(all_laps, all_stints):
    laps_with_compound = []

    for _, current_stint in all_stints.iterrows():
        #misma sesión, mismo piloto, en el rango de vueltas del stint
        is_same_session = all_laps["session_key"] == current_stint["session_key"]
        is_same_driver  = all_laps["driver_number"] == current_stint["driver_number"]
        is_within_stint = (
            (all_laps["lap_number"] >= current_stint["lap_start"])
            & (all_laps["lap_number"] <= current_stint["lap_end"])
        )

        laps_in_stint = all_laps[is_same_session & is_same_driver & is_within_stint].copy()
        laps_in_stint["compound"]     = current_stint["compound"]
        laps_in_stint["stint_number"] = current_stint["stint_number"]

        laps_with_compound.append(laps_in_stint)

    if laps_with_compound:
        import pandas as pd
        return pd.concat(laps_with_compound).drop_duplicates(
            subset=["session_key", "driver_number", "lap_number"]
        )

    return all_laps

laps = assign_compound(laps, stints)

#=============Sidebar Filtros===========================
st.sidebar.header("Filtros")

season = st.sidebar.selectbox(
    "Season",
    sorted(laps["season"].dropna().unique()),
)
laps_season = laps[laps["season"] == season]

country = st.sidebar.selectbox(
    "Grand Prix",
    sorted(laps_season["country_name"].dropna().unique()),
)
laps_country = laps_season[laps_season["country_name"] == country]

session = st.sidebar.selectbox(
    "Session",
    sorted(laps_country["session_name"].dropna().unique()),
)
laps_filtered = laps_country[laps_country["session_name"] == session]
valid_laps = filter_valid_laps(laps_filtered)

available_drivers = sorted(valid_laps["name_acronym"].dropna().unique())
selected_drivers = st.sidebar.multiselect(
    "Pilotos",
    available_drivers,
    default=available_drivers,
)

#=================Guards============
st.title("Lap Analysis")
st.caption(f"{country} · {season} · {session}")

if valid_laps.empty or not selected_drivers:
    st.warning("Selecciona al menos un piloto con vueltas válidas.")
    st.stop()

valid_laps = valid_laps[valid_laps["name_acronym"].isin(selected_drivers)]

##===========Colores compuestos y Pilotos============
##ESTOS COLORES SON REGLAMENTARIOS Y NO CAMBIAN A NO SE QUE FABRICANTE
##Y FIA LO HAGAN
COMPOUND_COLORS = {
    "SOFT":  "#E8002D",
    "MEDIUM": "#FFF200",
    "HARD":  "#FFFFFF",
    "INTERMEDIATE": "#39B54A",
    "WET":   "#0067FF",
}

driver_colors = {
    d: c for d, c in zip(
        available_drivers,
        px.colors.qualitative.Safe + px.colors.qualitative.Vivid
    )
}

st.divider()

##=========1ª DIVISION====
st.subheader("¿Cuál fue la vuelta más rápida?")

fastest = valid_laps.sort_values("lap_duration").iloc[0]
driver_bests = (
    valid_laps.groupby(["name_acronym", "last_name", "team_name"], as_index=False)
    .agg(best_lap=("lap_duration", "min"), avg_lap=("lap_duration", "mean"))
    .sort_values("best_lap")
)

#FLIP CARDS
def metric_flip_card(title: str, front_value, back_title: str, back_value) -> None:
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
##márgen
gap = driver_bests.iloc[-1]["best_lap"] - driver_bests.iloc[0]["best_lap"]

col1, col2, col3 = st.columns(3)
with col1:
    metric_flip_card(
        "Vuelta más rápida",
        f"{fastest['lap_duration']:.3f}s",
        "Piloto · Vuelta",
        f"{fastest['last_name']} · V{int(fastest['lap_number'])}",
    )
with col2:
    metric_flip_card(
        "Mejor ritmo medio",
        f"{driver_bests.iloc[0]['avg_lap']:.3f}s",
        "Piloto",
        driver_bests.iloc[0]['last_name'],
    )
with col3:
    metric_flip_card(
        "Gap mejor → peor",
        f"+{gap:.3f}s",
        "Comparativa",
        f"{driver_bests.iloc[0]['name_acronym']} vs {driver_bests.iloc[-1]['name_acronym']}",
    )

st.divider()

#==========2ª DIVISION===========
st.subheader("¿Quién fue más consistente?")

##Dibujo así el violin porque ncesito tener precision con 
##cada trazada en pocas vueltas y dif pilotos
fig_violin = go.Figure()

for driver in selected_drivers:
    d = valid_laps[valid_laps["name_acronym"] == driver]
    color = driver_colors.get(driver, "#00D2BE")
    fig_violin.add_trace(go.Violin(
        y=d["lap_duration"],
        name=driver,
        box_visible=True,
        meanline_visible=True,
        spanmode="hard",
        bandwidth=0.8,
        fillcolor=color,
        line_color=color,
        opacity=0.6,
    ))

fig_violin.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    height=450,
    showlegend=False,
    yaxis=dict(
        title="Tiempo por vuelta (s)",
        gridcolor="rgba(0, 210, 190, 0.12)",
    ),
    margin=dict(l=20, r=20, t=20, b=20),
    violingap=0.25,
    violinmode="group",
)


st.plotly_chart(fig_violin, use_container_width=True)

is_race = laps_filtered["session_type"].iloc[0] == "Race" if not laps_filtered.empty else False

if is_race:
    # En carrera pongo una desviación típica absoluta con mínimo 5 vueltas
    consistency = (
        valid_laps.groupby("name_acronym")
        .filter(lambda x: len(x) >= 5)
        .groupby("name_acronym")["lap_duration"]
        .std()
        .sort_values()
        .reset_index()
        .rename(columns={"lap_duration": "metric"})
    )
    metric_label = "desviación típica"
    metric_unit = "s"
    caption_note = "Un violin estrecho indica mayor regularidad entre vueltas."
else:
    # En qualifying pongo un coeficiente de variación (std/mean) — normaliza por ritmo
    consistency = (
        valid_laps.groupby("name_acronym")["lap_duration"]
        .agg(lambda x: x.std() / x.mean())
        .sort_values()
        .reset_index()
        .rename(columns={"lap_duration": "metric"})
    )
    metric_label = "coeficiente de variación"
    metric_unit = ""
    caption_note = (
        "En qualifying se usa el coeficiente de variación (std/media) "
        "para comparar consistencia de forma justa entre pilotos con distinto número de intentos."
    )

if not consistency.empty:
    most_consistent = consistency.iloc[0]
    value = f"{most_consistent['metric']:.4f}{metric_unit}" if not is_race else f"{most_consistent['metric']:.3f}{metric_unit}"
    st.caption(
        f"Piloto más consistente: **{most_consistent['name_acronym']}** "
        f"({metric_label}: {value}). {caption_note}"
    )

st.divider()

##===============3ª DIVISION===================
st.subheader("¿Qué sectores fueron más determinantes?")

sector_cols = ["duration_sector_1", "duration_sector_2", "duration_sector_3"]
sector_labels = {"duration_sector_1": "S1", "duration_sector_2": "S2", "duration_sector_3": "S3"}

sector_laps = valid_laps.dropna(subset=sector_cols)

if sector_laps.empty:
    st.info("No hay datos de sectores disponibles para esta sesión.")
else:
    sector_best = (
        sector_laps.groupby("name_acronym")[sector_cols]
        .min()
        .reset_index()
        .rename(columns=sector_labels)
    )

    col1, col2, col3 = st.columns(3)
    for col, s, label in zip(
        [col1, col2, col3],
        ["S1", "S2", "S3"],
        ["Sector 1", "Sector 2", "Sector 3"],
    ):
        best_s = sector_best.sort_values(s).iloc[0]
        with col:
            fig_s = px.bar(
                sector_best.sort_values(s),
                x="name_acronym",
                y=s,
                labels={"name_acronym": "Piloto", s: "Mejor tiempo (s)"},
                color="name_acronym",
                color_discrete_map=driver_colors,
            )
            fig_s.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                height=300,
                showlegend=False,
                title=label,
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig_s, use_container_width=True)
            st.caption(f"Mejor: **{best_s['name_acronym']}** · {best_s[s]:.3f}s")

    # Varianza por sector
    sector_var = sector_laps[sector_cols].min() - sector_laps[sector_cols].min()
    ranges = {
        "S1": sector_laps["duration_sector_1"].max() - sector_laps["duration_sector_1"].min(),
        "S2": sector_laps["duration_sector_2"].max() - sector_laps["duration_sector_2"].min(),
        "S3": sector_laps["duration_sector_3"].max() - sector_laps["duration_sector_3"].min(),
    }
    most_decisive = max(ranges, key=ranges.get)
    st.caption(
        f"El sector más determinante es **{most_decisive}** "
        f"(rango de {ranges[most_decisive]:.3f}s entre pilotos)."
    )

st.divider()

##========4ª DIVISION=========================
st.subheader("¿Qué neumático fue más rápido?")

tyre_laps = valid_laps.dropna(subset=["compound"])

if tyre_laps.empty:
    st.info("No hay datos de compuestos disponibles para esta sesión.")
else:
    tyre_summary = (
        tyre_laps.groupby("compound", as_index=False)
        .agg(
            avg_lap=("lap_duration", "mean"),
            best_lap=("lap_duration", "min"),
            laps=("lap_duration", "count"),
        )
        .sort_values("avg_lap")
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        fig_tyre = px.bar(
            tyre_summary,
            x="compound",
            y="avg_lap",
            color="compound",
            color_discrete_map=COMPOUND_COLORS,
            hover_data={"best_lap": ":.3f", "laps": True, "avg_lap": ":.3f"},
            labels={
                "compound": "Compuesto",
                "avg_lap": "Ritmo medio (s)",
                "best_lap": "Mejor vuelta",
                "laps": "Vueltas",
            },
        )
        fig_tyre.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=350,
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_tyre, use_container_width=True)

    with col2:
        fig_tyre_box = px.box(
            tyre_laps,
            x="compound",
            y="lap_duration",
            color="compound",
            color_discrete_map=COMPOUND_COLORS,
            labels={
                "compound": "Compuesto",
                "lap_duration": "Tiempo por vuelta (s)",
            },
        )
        fig_tyre_box.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=350,
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_tyre_box, use_container_width=True)

    best_compound = tyre_summary.iloc[0]
    st.caption(
        f"Compuesto más rápido: **{best_compound['compound']}** "
        f"con un ritmo medio de {best_compound['avg_lap']:.3f}s "
        f"sobre {int(best_compound['laps'])} vueltas válidas."
    )

st.divider()

##==========5ª DIVISION===================
#stint en F1 es el periodo de tiempo o número de vueltas que un monoplaza 
#rueda en la pista con el mismo juego de neumáticos
st.subheader("¿Qué stint fue más eficiente?")

##ritmo de vueltas
pace_laps = valid_laps.dropna(subset=["stint_number"])

# Filtrar in-laps
if not pace_laps.empty and "stint_number" in pace_laps.columns:
    last_laps_idx = (
        pace_laps.groupby(["driver_number", "stint_number"])["lap_number"]
        .idxmax()
    )
    pace_laps = pace_laps.drop(index=last_laps_idx)

if pace_laps.empty:
    st.info("No hay datos de stints disponibles para esta sesión.")
else:
    fig_pace = px.line(
        pace_laps.sort_values(["name_acronym", "lap_number"]),
        x="lap_number",
        y="lap_duration",
        color="name_acronym",
        line_dash="compound" if "compound" in pace_laps.columns else None,
        color_discrete_map=driver_colors,
        hover_data={
            "full_name": True,
            "compound": True,
            "stint_number": True,
            "lap_duration": ":.3f",
        },
        labels={
            "lap_number": "Vuelta",
            "lap_duration": "Tiempo (s)",
            "name_acronym": "Piloto",
            "compound": "Compuesto",
            "stint_number": "Stint",
        },
    )
    fig_pace.update_traces(line_width=2, opacity=0.85)
    fig_pace.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=480,
        yaxis=dict(gridcolor="rgba(0, 210, 190, 0.12)"),
        margin=dict(l=20, r=160, t=20, b=20),
        legend=dict(
            orientation="v",
            x=1.01,
            y=1,
            xanchor="left",
            yanchor="top",
            font=dict(color="white", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    st.plotly_chart(fig_pace, use_container_width=True)

    stint_summary = (
        pace_laps.groupby(["name_acronym", "stint_number", "compound"], as_index=False)
        .agg(avg=("lap_duration", "mean"), laps=("lap_duration", "count"))
        .sort_values("avg")
    )
    best_stint = stint_summary.iloc[0]
    worst_stint = stint_summary.iloc[-1]
    gap_stints = worst_stint["avg"] - best_stint["avg"]

    st.caption(
        f"Stint más eficiente: **{best_stint['name_acronym']}** · "
        f"Stint {int(best_stint['stint_number'])} · "
        f"Compuesto {best_stint['compound']} · "
        f"Ritmo medio **{best_stint['avg']:.3f}s** sobre {int(best_stint['laps'])} vueltas. "
        f"El stint menos eficiente fue **{worst_stint['name_acronym']}** "
        f"(Stint {int(worst_stint['stint_number'])}, {worst_stint['compound']}) "
        f"con {worst_stint['avg']:.3f}s — una diferencia de **{gap_stints:.3f}s** por vuelta."
    )

st.divider()

