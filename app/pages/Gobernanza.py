import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from src.dashboard.data_loader import load_all_data
from src.dashboard.utils import global_style

st.set_page_config(page_title="Gobernanza y Calidad del Dato", layout="wide")
global_style()

st.title("Gobernanza y Calidad del Dato")
st.caption(
    "Antes de tomar cualquier decisión basada en este cuadro de mando, "
    "es importante conocer las limitaciones y sesgos detectados en el origen de los datos."
)

data = load_all_data()
laps = data["laps"]
drivers = data["drivers"]
car_data = data["car_data"]

st.divider()

st.subheader("Resumen para dirección")
st.markdown(
    """
    Los datos de este proyecto proceden de una fuente pública (OpenF1) y, como toda
    fuente externa no controlada por la organización, presentan **limitaciones que
    deben tenerse en cuenta antes de extraer conclusiones de negocio**. A continuación
    se detallan los cuatro hallazgos más relevantes, su causa y el impacto que tendría
    ignorarlos.
    """
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Carreras con nombre inconsistente", "2 de 24")
col2.metric("Temporadas sin dato de país del piloto", "2 de 3")
col3.metric(
    "Vueltas excluidas del ritmo de carrera",
    f"{int((laps['is_outlier_lap'] | laps['is_pit_out_lap']).sum()):,}",
)
col4.metric("Sesiones de telemetría recuperadas tras error de origen", "107 de 107")

st.divider()

##Nombre de circuitos
st.markdown("### 1. Un mismo circuito aparecía con varios nombres distintos")
col_a, col_b = st.columns([2, 1])

with col_a:
    st.markdown(
        """
        **Qué se encontró:** los circuitos de Miami y Mónaco aparecían registrados con
        nombres diferentes según el año (por ejemplo, "Miami" en 2024 pero "Miami
        Gardens" en 2025 y 2026; "Mónaco" en 2024-2025 pero "Monte Carlo" en 2026).

        **Por qué importa:** si no se corrige, cualquier comparación histórica por
        circuito (por ejemplo, "¿cómo ha evolucionado el ritmo en Mónaco en los últimos
        tres años?") **excluiría silenciosamente datos reales**, dando la falsa
        impresión de que faltan carreras cuando en realidad solo están mal etiquetadas.

        **Acción tomada:** se unificaron los nombres de circuito en todo el conjunto
        de datos antes de construir este dashboard.
        """
    )

with col_b:
    st.markdown(
        """
        <div class="insight-box">
        <strong>Impacto si se ignora</strong><br><br>
        Un análisis de tendencia por circuito mostraría huecos inexistentes,
        llevando a conclusiones erróneas sobre la evolución del rendimiento
        en esos Grandes Premios.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()


## Siglas de país del piloto
st.markdown("### 2. El país de origen del piloto no está disponible para todas las temporadas")
col_a, col_b = st.columns([2, 1])

pct_2024 = (
    drivers[drivers["season"] == 2024]["country_code"].notna().mean() * 100
    if 2024 in drivers["season"].unique()
    else 0
)

with col_a:
    st.markdown(
        f"""
        **Qué se encontró:** el país de origen del piloto está disponible para la
        temporada 2024 (**{pct_2024:.0f}% de cobertura**), pero la fuente de datos
        no lo proporciona para las temporadas 2025 y 2026.

        **Por qué importa:** cualquier análisis o filtro que dependa de la
        nacionalidad del piloto (por ejemplo, agrupar resultados por país) solo
        sería fiable para 2024. Aplicarlo a temporadas más recientes daría una
        cobertura parcial sin advertencia visible.

        **Acción tomada:** el dato se mantiene visible donde existe y se documenta
        como ausente donde no, sin inventar ni estimar valores.
        """
    )

with col_b:
    st.markdown(
        """
        <div class="insight-box">
        <strong>Impacto si se ignora</strong><br><br>
        Un informe que agrupe por nacionalidad usando solo temporadas recientes
        quedaría prácticamente vacío, pudiendo interpretarse erróneamente como
        ausencia real de diversidad de pilotos en lugar de una limitación del dato.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

##Ritmo de carrera
st.markdown("### 3. No todas las vueltas reflejan el ritmo real de carrera")
col_a, col_b = st.columns([2, 1])

n_pit = int(laps["is_pit_out_lap"].sum())
n_outlier = int(laps["is_outlier_lap"].sum())

with col_a:
    st.markdown(
        f"""
        **Qué se encontró:** un porcentaje de las vueltas registradas corresponden a
        vueltas de salida de boxes (**{n_pit:,} vueltas**) o a interrupciones de
        sesión como banderas rojas (**{n_outlier:,} vueltas**). Estas vueltas tienen
        tiempos mucho más altos de lo normal por razones ajenas al rendimiento del
        piloto.

        **Por qué importa:** si se incluyen en el cálculo de tiempos medios o mejores
        tiempos por sesión, distorsionan gravemente las comparativas. Se detectó que
        incluirlas podía inflar el tiempo medio de clasificación en más de 60 segundos
        sobre el valor real.

        **Acción tomada:** estas vueltas se identifican y excluyen automáticamente de
        cualquier cálculo de ritmo o comparativa de pilotos en este dashboard.
        """
    )

with col_b:
    st.markdown(
        """
        <div class="insight-box">
        <strong>Impacto si se ignora</strong><br><br>
        Decisiones de estrategia o comparativas de rendimiento basadas en
        tiempos medios sin filtrar llevarían a conclusiones completamente
        erróneas sobre qué piloto o equipo es realmente más rápido.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

#Re-extract
st.markdown("### 4. Se detectó un error en la fuente de datos de telemetría")
col_a, col_b = st.columns([2, 1])

n_sessions_telemetry = car_data["session_key"].nunique()

with col_a:
    st.markdown(
        f"""
        **Qué se encontró:** durante el proceso de verificación, se detectó que la
        fuente de datos devolvía en ciertos casos información de telemetría
        (velocidad, marchas, revoluciones del motor) mezclada o desplazada entre
        columnas, lo que podía generar valores físicamente imposibles
        (por ejemplo, velocidades superiores a 11.000 km/h).

        **Por qué importa:** de no haberse detectado, cualquier análisis de
        velocidad punta, frenada o rendimiento del motor habría dado resultados
        sin sentido, sin que fuera evidente a primera vista que el origen del
        problema era la fuente externa y no el análisis.

        **Acción tomada:** se diseñó un proceso de validación que identifica y
        corrige automáticamente este error en origen. Tras la corrección, las
        **{n_sessions_telemetry} sesiones** de telemetría disponibles superan los
        controles de calidad.
        """
    )

with col_b:
    st.markdown(
        """
        <div class="insight-box">
        <strong>Impacto si se ignora</strong><br><br>
        Cualquier recomendación sobre puntos de frenada, velocidad punta o
        rendimiento del motor basada en datos sin validar habría sido
        completamente inútil o contraproducente para un equipo de carreras.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

##Conclusión
st.subheader("Recomendación operativa")
st.markdown(
    """
    <div class="insight-box">
    Antes de integrar fuentes de datos externas en procesos de decisión
    automatizados, se recomienda establecer un proceso de validación de
    calidad como el aplicado en este proyecto: verificación de rangos físicos
    o lógicos esperados, detección de inconsistencias de nomenclatura entre
    periodos, y documentación explícita de la cobertura real de cada variable.
    Ignorar estos pasos puede traducirse en decisiones de negocio basadas en
    datos incorrectos, con el consiguiente impacto reputacional y financiero.
    </div>
    """,
    unsafe_allow_html=True,
)
