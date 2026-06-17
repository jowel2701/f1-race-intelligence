# 🏎️ F1 Race Intelligence Dashboard

## 📖 Descripción

F1 Race Intelligence Dashboard es una plataforma interactiva desarrollada en Python y Streamlit para el análisis avanzado de datos de Fórmula 1.

El proyecto integra información procedente de la API OpenF1 para construir un entorno completo de análisis compuesto por procesos ETL, exploración de datos (EDA) y dashboards interactivos orientados al estudio del rendimiento de pilotos, estrategias de carrera, telemetría y condiciones de pista.

El objetivo principal es transformar grandes volúmenes de datos técnicos en visualizaciones intuitivas que permitan comprender cómo influyen distintos factores en el rendimiento de un monoplaza de Fórmula 1.

---

# 🎯 Objetivos

* Obtener datos reales de Fórmula 1 mediante OpenF1.
* Construir un pipeline ETL para la extracción, limpieza y transformación de datos.
* Realizar análisis exploratorio de datos (EDA).
* Desarrollar dashboards interactivos con Streamlit.
* Analizar estrategias de carrera, telemetría y rendimiento de pilotos.
* Implementar un módulo interactivo tipo ingeniería de pista mediante Engineer Mode.

---

# 🛠️ Tecnologías utilizadas

## Lenguaje

* Python 3.10

## Librerías principales

* Pandas
* NumPy
* Plotly
* Streamlit
* OpenF1 API
* Requests

## Entorno

* Visual Studio Code
* Git
* GitHub

---

# 🏗️ Arquitectura del proyecto

El proyecto sigue una arquitectura modular basada en:

* Extracción de datos
* Limpieza y transformación
* Almacenamiento
* Análisis exploratorio
* Visualización interactiva

```text
OpenF1 API
    │
    ▼
Extraction
    │
    ▼
Raw Data
    │
    ▼
Cleaning
    │
    ▼
Processed Data
    │
    ▼
EDA
    │
    ▼
Streamlit Dashboard
```

---

# 📊 Datasets utilizados

## Drivers

Información de pilotos:

* Nombre
* Acrónimo
* Equipo
* Número de piloto
* Nacionalidad

---

## Sessions

Información de sesiones:

* Carrera
* Clasificación
* Entrenamientos
* Temporada
* Circuito

---

## Laps

Información por vuelta:

* Tiempo de vuelta
* Posición
* Sectores
* Compuesto
* Stint

---

## Stints

Información estratégica:

* Compuesto
* Inicio de stint
* Final de stint
* Edad del neumático

---

## Car Data

Telemetría:

* Velocidad
* RPM
* Marcha
* Throttle
* Brake
* DRS

---

## Location

Posición GPS:

* Coordenada X
* Coordenada Y

---

## Weather

Información meteorológica:

* Temperatura ambiente
* Temperatura de pista
* Humedad
* Viento
* Lluvia

---

## Race Control

Eventos FIA:

* Safety Car
* Virtual Safety Car
* Yellow Flag
* Track Limits
* Incidentes

---

# ⚙️ Proceso ETL

Los datos son obtenidos mediante scripts independientes para cada endpoint de OpenF1.

Posteriormente se realiza una fase de limpieza donde:

* Se eliminan columnas irrelevantes.
* Se normalizan nombres de columnas.
* Se corrigen tipos de datos.
* Se gestionan valores nulos.
* Se validan rangos físicos de telemetría.
* Se generan datasets optimizados para análisis.

Los datos procesados se almacenan en formato CSV para facilitar su uso en análisis y visualización.

---

# 📈 Análisis Exploratorio de Datos

Se desarrolló un EDA completo para:

* Distribución de velocidades.
* Distribución de RPM.
* Uso de marchas.
* Uso de DRS.
* Relación velocidad-RPM.
* Frenadas.
* Trazado de circuitos.
* Comportamiento del acelerador.

El objetivo fue comprender la calidad de los datos y detectar patrones relevantes antes de construir los dashboards.

---

# 🖥️ Dashboard Streamlit

El dashboard está compuesto por diferentes módulos especializados.

## Overview

Resumen general de la sesión seleccionada.

---

## Lap Analysis

Análisis detallado de vueltas rápidas y rendimiento.

---

## Driver Comparison

Comparación directa entre dos pilotos.

---

## Circuit Intelligence

Estudio técnico del circuito mediante telemetría.

---

## Strategy Room

Análisis de estrategias de carrera y gestión de neumáticos.

---

## Race Conditions

Análisis de condiciones meteorológicas y eventos FIA.

---

## Engineer Mode

Módulo interactivo diseñado para simular una estación de ingeniería de pista.

Permite:

* Inspeccionar sistemas del monoplaza mediante una imagen interactiva.
* Analizar motor, neumáticos, aerodinámica y DRS.
* Visualizar métricas en tiempo real.
* Reproducir telemetría mediante un sistema de replay sobre el trazado del circuito.

---

# 🚀 Instalación

```bash
git clone https://github.com/usuario/f1-race-intelligence.git

cd f1-race-intelligence

pip install -r requirements.txt
```

---

# ▶️ Ejecución

```bash
streamlit run app/streamlit_app.p
```

---

# 📁 Estructura del proyecto

```text
f1-race-intelligence/
│
├── app/
│   ├── streamlit_app.py
│   ├── pages/
│
├── data/
│   ├── raw/
│   ├── processed/
│
├── notebooks/
│
├── src/
│   ├── extraction/
│   ├── cleaning/
│   ├── dashboard/
│
├── assets/
│
├── requirements.txt
│
└── README.md
```

---

# ⚠️ Limitaciones

* OpenF1 no proporciona telemetría completa para todas las sesiones.
* Algunas sesiones únicamente contienen información de vueltas y resultados.
* La telemetría detallada está limitada a determinadas combinaciones de piloto y sesión.

---

# 🔮 Futuras mejoras

* Integración con FastF1.
* Predicción de estrategias mediante Machine Learning.
* Simulación de paradas en boxes.
* Comparación multi temporada.
* Análisis de degradación de neumáticos.
* Dashboard específico para clasificación.
* Soporte para MotoGP.

---

# 👨‍💻 Autor

Joel Ibarra

Proyecto desarrollado como trabajo final de análisis de datos y visualización aplicada a Fórmula 1.
