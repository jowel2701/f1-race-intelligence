import base64
import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.dashboard.data_loader import load_all_data
from src.dashboard.utils import global_style


st.set_page_config(
    page_title="F1 Race Intelligence",
    page_icon="favicon.ico",
    layout="wide",
)

global_style()

data = load_all_data()
laps = data["laps"]

st.title("F1 Race Intelligence")
st.caption("Telemetría · Tiempos de Vuelta · Meteorología · Control de Carrera")

st.markdown("<br>", unsafe_allow_html=True)

##GIF
_gif_path = Path(__file__).parent / "assets" / "f1_intro.gif"
if _gif_path.exists():
    _gif_b64 = base64.b64encode(_gif_path.read_bytes()).decode()
    st.markdown(
        f"""
        <style>
            .gif-fullwidth {{
                position: relative;
                left: 50%;
                right: 50%;
                margin-left: -50vw;
                margin-right: -50vw;
                width: 100vw;
                max-height: 480px;
                overflow: hidden;
                margin-bottom: 2rem;
            }}
            .gif-fullwidth img {{
                width: 100%;
                height: 480px;
                object-fit: cover;
                object-position: center;
                display: block;
            }}
        </style>
        <div class="gif-fullwidth">
            <img src="data:image/gif;base64,{_gif_b64}" />
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.warning("GIF de introducción no encontrado — se esperaba en app/assets/f1_intro.gif")

## KPIs 
num_seasons     = laps["season"].nunique()
num_drivers     = laps["driver_number"].nunique()
num_grands_prix = laps["country_name"].nunique()
num_laps        = len(laps)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Temporadas", num_seasons)

with col2:
    st.metric("Grandes Premios", num_grands_prix)

with col3:
    st.metric("Pilotos", num_drivers)

with col4:
    st.metric("Vueltas Analizadas", f"{num_laps:,}")

st.divider()

#Paginas
st.subheader("Módulos de la Plataforma")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="insight-box">
            <h4>Lap Analysis</h4>
            Analiza tiempos de vuelta, sectores y rendimiento de neumáticos por piloto y sesión.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="insight-box">
            <h4>Driver Comparison</h4>
            Compara pilotos cara a cara e identifica dónde se gana o se pierde tiempo.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="insight-box">
            <h4>Circuit Intelligence</h4>
            Explora velocidad, frenada, acelerador y comportamiento del DRS sobre el trazado.
        </div>
        """,
        unsafe_allow_html=True,
    )

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown(
        """
        <div class="insight-box">
            <h4>Strategy Room</h4>
            Analiza stints, compuestos y tiempos de pit stop a lo largo de la carrera.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col5:
    st.markdown(
        """
        <div class="insight-box">
            <h4>Race Conditions</h4>
            Revisa la evolución meteorológica y los eventos de la dirección de carrera.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col6:
    st.markdown(
        """
        <div class="insight-box">
            <h4>Engineer Mode</h4>
            Diagnóstico interactivo del coche y reproducción de telemetría sobre el trazado.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

#Resumen
st.markdown(
    """
    <div class="insight-box">
        <h3>Sobre el Proyecto</h3>
        F1 Race Intelligence transforma telemetría bruta de Fórmula 1, tiempos de vuelta,
        datos meteorológicos y eventos de la dirección de carrera en una plataforma
        interactiva de apoyo a la decisión.<br><br>
        El objetivo es ayudar a ingenieros, analistas y aficionados al motorsport a explorar
        el rendimiento en carrera, entender las decisiones estratégicas e identificar patrones
        ocultos en miles de vueltas de datos.
    </div>
    """,
    unsafe_allow_html=True,
)