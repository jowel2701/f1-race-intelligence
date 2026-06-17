import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy.ndimage import uniform_filter1d

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from src.dashboard.data_loader import load_all_data, filter_valid_laps
from src.dashboard.utils import global_style

#Configuración de página
st.set_page_config(page_title="Circuit & Engineer", layout="wide")
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


def circuit_map(
    base_track: pd.DataFrame,
    color_data: pd.Series,
    colorscale: list,
    colorbar_title: str,
    cmin: float = None,
    cmax: float = None,
    point_size: int = 6,
    height: int = 520,
) -> go.Figure:
    """Mapa del circuito coloreado por métrica."""
    vmin = cmin if cmin is not None else color_data.min()
    vmax = cmax if cmax is not None else color_data.max()

    fig = go.Figure()
    fig.add_scatter(
        x=base_track["x"], y=base_track["y"],
        mode="lines",
        line=dict(color="rgba(180,180,180,0.9)", width=16),
        hoverinfo="skip", showlegend=False,
    )
    fig.add_scatter(
        x=base_track["x"], y=base_track["y"],
        mode="lines",
        line=dict(color="rgba(10,10,10,1)", width=10),
        hoverinfo="skip", showlegend=False,
    )
    fig.add_scatter(
        x=base_track["x"], y=base_track["y"],
        mode="markers",
        marker=dict(
            size=point_size,
            color=color_data,
            colorscale=colorscale,
            cmin=vmin, cmax=vmax,
            colorbar=dict(
                title=dict(text=colorbar_title, font=dict(color="white")),
                tickfont=dict(color="white"),
                thickness=14,
            ),
            line=dict(width=0),
            opacity=1,
        ),
        hovertemplate="%{marker.color:.1f}<extra></extra>",
        showlegend=False,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=height,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


PLOTLY_BASE = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    margin=dict(l=20, r=20, t=20, b=20),
)

COLORSCALE_MAP = {
    "speed":    [[0, "#1a0a4a"], [0.5, "#00D2BE"], [1, "#ffffff"]],
    "throttle": [[0, "#1a0a0a"], [0.5, "#E8A000"], [1, "#00D2BE"]],
    "brake":    [[0, "#0a0a0a"], [0.5, "#FF6B00"], [1, "#E10600"]],
    "rpm":      [[0, "#0a1a0a"], [0.5, "#006F62"], [1, "#00D2BE"]],
    "n_gear":   [[0, "#1a1a1a"], [0.5, "#8B00FF"], [1, "#00D2BE"]],
}

UNIT_MAP = {
    "speed": "km/h", "throttle": "%",
    "brake": "%", "rpm": "rpm", "n_gear": "marcha",
}

##Datos
data = load_all_data()

driver_cols = [
    "session_key", "driver_number", "full_name", "last_name",
    "name_acronym", "team_name", "team_colour",
]

car_data = data["car_data"].merge(data["drivers"][driver_cols], on=["session_key", "driver_number"], how="left")
location  = data["location"].merge(data["drivers"][driver_cols], on=["session_key", "driver_number"], how="left")
laps      = data["laps"].merge(data["drivers"][driver_cols], on=["session_key", "driver_number"], how="left")
stints    = data["stints"].merge(data["drivers"][driver_cols], on=["session_key", "driver_number"], how="left")

#=============Sidebar Filtros===========================
st.sidebar.header("Filtros")

available_sessions = car_data[
    ["season", "country_name", "session_name", "session_key"]
].drop_duplicates()

season = st.sidebar.selectbox("Season", sorted(available_sessions["season"].dropna().unique()))
sessions_season = available_sessions[available_sessions["season"] == season]

country = st.sidebar.selectbox("Grand Prix", sorted(sessions_season["country_name"].dropna().unique()))
sessions_country = sessions_season[sessions_season["country_name"] == country]

session = st.sidebar.selectbox("Session", sorted(sessions_country["session_name"].dropna().unique()))
session_key = sessions_country[sessions_country["session_name"] == session]["session_key"].iloc[0]

session_car    = car_data[car_data["session_key"] == session_key]
session_loc    = location[location["session_key"] == session_key]
session_laps   = laps[laps["session_key"] == session_key]
session_stints = stints[stints["session_key"] == session_key]

available_drivers = (
    session_car[["driver_number", "name_acronym", "full_name", "team_name"]]
    .dropna(subset=["name_acronym"])
    .drop_duplicates()
    .sort_values("name_acronym")
)
driver_labels = {
    f"{row['name_acronym']} — {row['full_name']}": row["driver_number"]
    for _, row in available_drivers.iterrows()
}

selected_label = st.sidebar.selectbox("Piloto", list(driver_labels.keys()))
driver_number  = driver_labels[selected_label]
driver_name    = available_drivers[available_drivers["driver_number"] == driver_number]["name_acronym"].iloc[0]
driver_fullname = available_drivers[available_drivers["driver_number"] == driver_number]["full_name"].iloc[0]

#=================Guards============
st.title("Circuit Intelligence")
st.caption(f"{country} · {season} · {session} · {driver_name}")

driver_laps = filter_valid_laps(
    session_laps[session_laps["driver_number"] == driver_number]
)

has_valid_laps = not driver_laps.empty

if has_valid_laps:
    fastest_lap_number = int(driver_laps.sort_values("lap_duration").iloc[0]["lap_number"])

    telem = session_car[
        (session_car["driver_number"] == driver_number)
        & (session_car["lap_number"] == fastest_lap_number)
    ].sort_values("date").reset_index(drop=True)

    loc = session_loc[
        (session_loc["driver_number"] == driver_number)
        & (session_loc["lap_number"] == fastest_lap_number)
    ].sort_values("date").reset_index(drop=True)

    has_telemetry = not telem.empty and not loc.empty

    if has_telemetry:
        telem["date"] = pd.to_datetime(telem["date"], format="mixed", utc=True, errors="coerce")
        loc["date"]   = pd.to_datetime(loc["date"], format="mixed", utc=True, errors="coerce")

        track = pd.merge_asof(
            loc.sort_values("date"),
            telem[["date", "speed", "throttle", "brake", "rpm", "drs", "n_gear"]].sort_values("date"),
            on="date", direction="nearest",
            tolerance=pd.Timedelta("150ms"),
        ).dropna(subset=["speed"]).reset_index(drop=True)

        track["drs_active"] = track["drs"] >= 10
else:
    has_telemetry = False

driver_stints = session_stints[session_stints["driver_number"] == driver_number].copy()

if not has_telemetry:
    st.warning(
        "No hay telemetría disponible para este piloto y sesión. "
        "Solo algunas sesiones tienen telemetría completa de la vuelta más rápida."
    )

st.divider()

##=========1ª DIVISION====

tab_circuit, tab_engineer = st.tabs(["Circuit Intelligence", "Engineer Mode"])

#TAB1
with tab_circuit:
    if not has_telemetry:
        st.info("Selecciona una sesión con telemetría disponible para ver el análisis del circuito.")
    else:
        st.subheader(f"Vuelta rápida — {driver_name} · Lap {fastest_lap_number}")

        throttle_pct = (track["throttle"] >= 90).mean() * 100
        brake_pct    = (track["brake"] > 0).mean() * 100
        drs_pct      = track["drs_active"].mean() * 100
        drs_zones    = int((track["drs_active"].astype(int).diff().fillna(0) > 0).sum())

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            metric_flip_card("Velocidad máxima", f"{track['speed'].max():.0f} km/h", "Media", f"{track['speed'].mean():.0f} km/h")
        with col2:
            metric_flip_card("RPM máxima", f"{track['rpm'].max():.0f}", "RPM media", f"{track['rpm'].mean():.0f}")
        with col3:
            metric_flip_card("% a plena potencia", f"{throttle_pct:.1f}%", "Throttle medio", f"{track['throttle'].mean():.1f}%")
        with col4:
            metric_flip_card("% frenando", f"{brake_pct:.1f}%", "Zonas de frenada", f"{int((track['brake'].diff().fillna(0) > 0).sum())}")
        with col5:
            metric_flip_card("% con DRS", f"{drs_pct:.1f}%", "Zonas DRS", f"{drs_zones}")

        st.divider()
        
        ##=========1ª  SUB-DIVISION====

        st.subheader("¿Qué ocurre en cada zona del circuito?")

        metric_option = st.radio(
            "Colorear por",
            ["speed", "throttle", "brake", "rpm", "n_gear"],
            horizontal=True,
            format_func={
                "speed": "Velocidad", "throttle": "Acelerador",
                "brake": "Freno", "rpm": "RPM", "n_gear": "Marcha",
            }.get,
        )

        sm_values = uniform_filter1d(track[metric_option].fillna(0).values, size=15)

        fig_main = circuit_map(
            base_track=track,
            color_data=pd.Series(sm_values),
            colorscale=COLORSCALE_MAP[metric_option],
            colorbar_title=f"{metric_option.capitalize()} ({UNIT_MAP[metric_option]})",
            point_size=6,
        )
        st.plotly_chart(fig_main, use_container_width=True)

        max_idx = np.argmax(sm_values)
        min_idx = np.argmin(sm_values)
        st.caption(
            f"**{driver_name}** alcanza el máximo de {metric_option} "
            f"({sm_values[max_idx]:.1f} {UNIT_MAP[metric_option]}) "
            f"y el mínimo de {sm_values[min_idx]:.1f} {UNIT_MAP[metric_option]} "
            f"a lo largo de la vuelta {fastest_lap_number}."
        )

        st.divider()

        ##=========2ª SUB-DIVISION====

        col_brake_map, col_drs_map = st.columns(2)

        with col_brake_map:
            st.subheader("¿Dónde frena?")
            brake_smooth = uniform_filter1d(track["brake"].fillna(0).values, size=10)
            fig_brake = circuit_map(
                base_track=track,
                color_data=pd.Series(brake_smooth),
                colorscale=[[0, "#0a0a0a"], [0.4, "#0a0a0a"], [0.7, "#FF6B00"], [1, "#E10600"]],
                colorbar_title="Freno (%)",
                cmin=0, cmax=100, point_size=6, height=460,
            )
            st.plotly_chart(fig_brake, use_container_width=True)

            hard_braking = (track["brake"] >= 80).mean() * 100
            no_braking   = (track["brake"] == 0).mean() * 100
            st.markdown(
                f"""
                <div class="insight-box">
                    <strong>Frenada — {driver_fullname}</strong><br><br>
                    <strong>{brake_pct:.1f}%</strong> de la vuelta con freno aplicado.<br>
                    <strong>{hard_braking:.1f}%</strong> con frenada fuerte (≥80%).<br>
                    <strong>{no_braking:.1f}%</strong> sin freno — rectas o salidas de curva.<br><br>
                    Las zonas rojas intensas son los puntos de frenada más agresivos.
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_drs_map:
            st.subheader("¿Dónde activa el DRS?")
            drs_color = track["drs_active"].astype(float)
            fig_drs = circuit_map(
                base_track=track,
                color_data=drs_color,
                colorscale=[[0.0, "#0a0a0a"], [0.49, "#0a0a0a"], [0.5, "#00D2BE"], [1.0, "#00D2BE"]],
                colorbar_title="DRS",
                cmin=0, cmax=1, point_size=6, height=460,
            )
            fig_drs.data[-1].marker.showscale = False
            fig_drs.add_scatter(x=[None], y=[None], mode="markers",
                                marker=dict(size=10, color="#00D2BE"), name="DRS activo", showlegend=True)
            fig_drs.add_scatter(x=[None], y=[None], mode="markers",
                                marker=dict(size=10, color="#444444"), name="DRS inactivo", showlegend=True)
            fig_drs.update_layout(showlegend=True,
                                  legend=dict(font=dict(color="white"), bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig_drs, use_container_width=True)

            drs_gain = track.loc[track["drs_active"], "speed"].mean() - track.loc[~track["drs_active"], "speed"].mean()
            st.markdown(
                f"""
                <div class="insight-box">
                    <strong>DRS — {driver_fullname}</strong><br><br>
                    <strong>{drs_zones}</strong> zona{'s' if drs_zones != 1 else ''} DRS detectada{'s' if drs_zones != 1 else ''}.<br>
                    <strong>{drs_pct:.1f}%</strong> de la vuelta con DRS abierto.<br><br>
                    Con DRS: <strong>{track.loc[track['drs_active'], 'speed'].mean():.0f} km/h</strong><br>
                    Sin DRS: <strong>{track.loc[~track['drs_active'], 'speed'].mean():.0f} km/h</strong><br><br>
                    {'Ganancia media: <strong>' + f"{abs(drs_gain):.1f} km/h</strong>" if not np.isnan(drs_gain) else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )

##TAB2
with tab_engineer:
    if not has_telemetry:
        st.info("Selecciona una sesión con telemetría disponible para usar el trazado en vivo.")
    else:
        all_loc = session_loc[session_loc["driver_number"] == driver_number].copy()
        all_car = session_car[session_car["driver_number"] == driver_number].copy()

        all_loc["date"] = pd.to_datetime(all_loc["date"], utc=True, format="mixed")
        all_car["date"] = pd.to_datetime(all_car["date"], utc=True, format="mixed")

        merged = pd.merge_asof(
            all_loc.sort_values("date"),
            all_car[["date", "speed", "rpm", "n_gear", "throttle", "brake"]].sort_values("date"),
            on="date", direction="nearest",
        ).dropna(subset=["speed"]).reset_index(drop=True)

        st.caption(f"{len(merged)} puntos de telemetría · {driver_fullname} · {session}")

        frame = st.slider("Posición en la vuelta", 0, len(merged) - 1, 0)
        current = merged.iloc[frame]

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: metric_flip_card("Velocidad", f"{current['speed']:.0f} km/h", "Máxima sesión", f"{merged['speed'].max():.0f} km/h")
        with col2: metric_flip_card("RPM", f"{current['rpm']:.0f}", "Máxima", f"{merged['rpm'].max():.0f}")
        with col3: metric_flip_card("Marcha", str(int(current["n_gear"])), "Máxima", str(int(merged["n_gear"].max())))
        with col4: metric_flip_card("Throttle", f"{current['throttle']:.0f}%", "Media sesión", f"{merged['throttle'].mean():.0f}%")
        with col5: metric_flip_card("Freno", "ON" if current["brake"] > 0 else "OFF", "% frenando", f"{(merged['brake'] > 0).mean()*100:.1f}%")

        fig_trace = go.Figure()
        fig_trace.add_trace(go.Scatter(
            x=merged["x"], y=merged["y"],
            mode="markers+lines",
            line=dict(color="rgba(0,210,190,0.3)", width=1.5),
            marker=dict(
                size=4, color=merged["speed"],
                colorscale="Turbo", showscale=True,
                colorbar=dict(title="km/h", tickfont=dict(color="white")),
            ),
            customdata=merged[["speed", "rpm", "n_gear", "throttle", "brake"]],
            hovertemplate=(
                "Velocidad: %{customdata[0]:.0f} km/h<br>"
                "RPM: %{customdata[1]:.0f}<br>"
                "Marcha: %{customdata[2]:.0f}<br>"
                "Throttle: %{customdata[3]:.0f}%<br>"
                "Freno: %{customdata[4]:.0f}%<extra></extra>"
            ),
            showlegend=False,
        ))
        fig_trace.add_trace(go.Scatter(
            x=[current["x"]], y=[current["y"]],
            mode="markers",
            marker=dict(size=18, color="#00D2BE", symbol="circle", line=dict(color="white", width=2)),
            hoverinfo="skip", showlegend=False,
        ))
        fig_trace.update_layout(
            **PLOTLY_BASE, height=640,
            xaxis=dict(visible=False, scaleanchor="y"),
            yaxis=dict(visible=False),
            showlegend=False,
        )
        st.plotly_chart(fig_trace, use_container_width=True)
        st.caption(
            "Mueve el slider para desplazar el coche por el trazado. "
            "Pasa el cursor sobre cualquier punto para ver la telemetría exacta en esa posición."
        )