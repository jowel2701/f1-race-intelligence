import streamlit as st


def global_style() -> None:
    """
    Inyecta el CSS global del dashboard.
    Llamar una vez al inicio de cada página, justo después de set_page_config().
    """
    st.markdown(
        """
        <style>
        /* Header transparente (NO oculto): mantiene visible y funcional
           el botón de colapso del sidebar, que vive dentro del header */
        header {
            background: transparent !important;
            box-shadow: none !important;
        }

        /* Ocultar footer */
        footer {
            visibility: hidden;
        }

        [data-testid="collapsedControl"] svg,
        button[kind="header"] svg {
            color: #00D2BE !important;
            fill: #00D2BE !important;
        }

        /* Reducir margen superior */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
        .stApp {
            background: linear-gradient(135deg, #050505 0%, #071f1b 45%, #00352f 100%);
            color: #F5F5F5;
        }

        h1, h2, h3 {
            color: #F5F5F5;
            font-weight: 700;
        }

        p, label, span, div {
            color: #F5F5F5;
        }

        /* Métricas nativas de Streamlit */
        [data-testid="stMetric"] {
            background-color: rgba(0, 111, 98, 0.22);
            border: 1px solid rgba(0, 210, 190, 0.35);
            padding: 18px;
            border-radius: 14px;
            box-shadow: 0 0 18px rgba(0, 210, 190, 0.08);
        }
        [data-testid="stMetricLabel"] { color: #B8FFF4; }
        [data-testid="stMetricValue"] { color: #FFFFFF; }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #050505;
            border-right: 1px solid rgba(0, 210, 190, 0.25);
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background-color: #071f1b !important;
            border: 1px solid rgba(0, 210, 190, 0.45) !important;
            border-radius: 10px !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] span {
            color: #FFFFFF !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
            color: #00D2BE !important;
            fill: #00D2BE !important;
        }
        section[data-testid="stSidebar"] label {
            color: #F5F5F5 !important;
            font-weight: 600 !important;
        }

        /* Dropdowns */
        ul { background-color: #071f1b !important; }
        li[role="option"] {
            background-color: #071f1b !important;
            color: #FFFFFF !important;
        }
        li[role="option"] div { color: #FFFFFF !important; }
        li[role="option"]:hover { background-color: #0c3a34 !important; }
        li[aria-selected="true"] {
            background-color: rgba(0, 210, 190, 0.25) !important;
            color: white !important;
        }

        /* DataFrames y expanders */
        .stDataFrame {
            background-color: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
        }
        div[data-testid="stExpander"] {
            border: 1px solid rgba(0, 210, 190, 0.25);
            border-radius: 12px;
        }

        /* Flip cards */
        .flip-card {
            background-color: transparent;
            height: 150px;
            perspective: 1000px;
        }
        .flip-card-inner {
            position: relative;
            width: 100%;
            height: 100%;
            transition: transform 0.7s;
            transform-style: preserve-3d;
        }
        .flip-card:hover .flip-card-inner {
            transform: rotateY(180deg);
        }
        .flip-card-front,
        .flip-card-back {
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 16px;
            backface-visibility: hidden;
            border: 1px solid rgba(0, 210, 190, 0.35);
            background: rgba(0, 111, 98, 0.24);
            box-shadow: 0 0 22px rgba(0, 210, 190, 0.10);
            padding: 22px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .flip-card-front h2,
        .flip-card-back h2 {
            margin: 0;
            color: #FFFFFF;
            font-size: 2rem;
        }
        .flip-card-back {
            transform: rotateY(180deg);
            background: rgba(0, 35, 31, 0.92);
        }
        .card-title {
            color: #B8FFF4 !important;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 10px;
        }

        /* Insight box (por si se usa en otras páginas) */
        .insight-box {
            margin-top: 25px;
            padding: 20px 24px;
            border-left: 4px solid #00D2BE;
            background: rgba(0, 210, 190, 0.08);
            border-radius: 10px;
            line-height: 1.7;
            color: #F5F5F5;
        }
        /* Contenedor general del dataframe */
        div[data-testid="stDataFrame"] {
            background: transparent !important;
            border: 1px solid rgba(0, 210, 190, 0.22) !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }

        /* Capa interna real de Glide */
        div[data-testid="stDataFrame"] div[role="grid"] {
            background: rgba(7, 31, 27, 0.92) !important;
            color: #F5F5F5 !important;
        }

        div[data-testid="stDataFrame"] .dvn-scroller {
            background: rgba(7, 31, 27, 0.92) !important;
        }

        div[data-testid="stDataFrame"] .stDataFrameGlideDataEditor {
            background: rgba(7, 31, 27, 0.92) !important;
            color: #F5F5F5 !important;
        }

        /* Celdas y textos internos */
        div[data-testid="stDataFrame"] div,
        div[data-testid="stDataFrame"] span,
        div[data-testid="stDataFrame"] td {
            color: #F5F5F5 !important;
        }

        /* Cabecera visual */
        div[data-testid="stDataFrame"] canvas {
            background: rgba(7, 31, 27, 0.92) !important;
        }
        [data-testid="stTable"] {
            background-color: rgba(0,0,0,0);
        }

        [data-testid="stTable"] table {
            background-color: #071f1b;
            color: white;
            border: 1px solid rgba(0,210,190,0.3);
        }

        [data-testid="stTable"] th {
            background-color: #00352f;
            color: #00D2BE;
        }
        div[data-testid="stDataFrame"] {
            text-align: center !important;
        }
        [data-testid="stTable"] td,
        [data-testid="stTable"] th {
            text-align: center !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )