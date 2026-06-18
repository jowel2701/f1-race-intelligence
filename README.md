# 🏎️ F1 Race Intelligence Dashboard

F1 Race Intelligence Dashboard es una plataforma interactiva desarrollada con Python y Streamlit para el análisis avanzado de datos de Fórmula 1.

El proyecto utiliza datos reales obtenidos desde la API OpenF1 para construir un entorno completo de análisis que incluye procesos ETL, análisis exploratorio de datos (EDA) y dashboards interactivos orientados al estudio del rendimiento de pilotos, estrategias de carrera, telemetría, condiciones de pista y simulación técnica en tiempo real.

Su objetivo es transformar grandes volúmenes de datos técnicos en visualizaciones claras e intuitivas que permitan entender cómo influyen distintos factores en el rendimiento de un monoplaza durante un fin de semana de competición.

---

## 🚀 Características principales

- Extracción de datos reales de Fórmula 1 desde OpenF1.
- Pipeline ETL para limpieza, transformación y estructuración de datasets.
- Análisis exploratorio de datos sobre vueltas, telemetría, clima y estrategia.
- Dashboard interactivo en Streamlit con múltiples módulos especializados.
- Comparación de pilotos, análisis de stint, trazado y condiciones de carrera.
- Módulo avanzado **Engineer Mode** con diagnóstico visual del monoplaza.
- Modelo predictivo de tiempo de vuelta basado en condiciones meteorológicas y desgaste de neumáticos.
- Análisis del punto óptimo de frenada a partir de telemetría y posición en pista.

---

## 🎯 Objetivos

- Obtener datos reales de Fórmula 1 mediante OpenF1.
- Construir un pipeline ETL robusto para extracción, limpieza y transformación.
- Realizar análisis exploratorio para validar calidad y consistencia de los datos.
- Desarrollar dashboards interactivos orientados a la toma de decisiones.
- Analizar estrategias de carrera, degradación de neumáticos y rendimiento de pilotos.
- Implementar un entorno tipo ingeniería de pista mediante **Engineer Mode**.

---

## 🛠️ Tecnologías utilizadas

### Lenguaje
- Python 3.10

### Librerías principales
- Pandas
- NumPy
- Plotly
- Streamlit
- Scikit-learn
- OpenF1 API
- Requests

### Entorno de desarrollo
- Visual Studio Code
- Git
- GitHub

---

## 🏗️ Arquitectura del proyecto

El proyecto sigue una arquitectura modular basada en varias etapas:

- Extracción de datos
- Limpieza y transformación
- Almacenamiento
- Análisis exploratorio
- Visualización interactiva

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

## 📊 Datasets utilizados

### Drivers
Información de pilotos:
- Nombre
- Acrónimo
- Equipo
- Número de piloto
- Nacionalidad

### Sessions
Información de sesiones:
- Carrera
- Clasificación
- Entrenamientos
- Temporada
- Circuito

### Laps
Información por vuelta:
- Tiempo de vuelta
- Posición
- Sectores
- Número de vuelta
- Flags de outlier y pit out lap

### Stints
Información estratégica:
- Compuesto
- Inicio del stint
- Final del stint
- Edad del neumático
- Número de stint

### Car Data
Telemetría:
- Velocidad
- RPM
- Marcha
- Throttle
- Brake
- DRS

### Location
Posición GPS:
- Coordenada X
- Coordenada Y

### Weather
Información meteorológica:
- Temperatura ambiente
- Temperatura de pista
- Humedad
- Lluvia

### Race Control
Eventos FIA:
- Safety Car
- Virtual Safety Car
- Yellow Flag
- Track Limits
- Incidentes

---

## ⚙️ Proceso ETL

Los datos se obtienen mediante scripts independientes para cada endpoint de OpenF1.

Posteriormente se realiza una fase de limpieza y transformación donde:

- Se eliminan columnas irrelevantes.
- Se normalizan nombres de columnas.
- Se corrigen tipos de datos.
- Se gestionan valores nulos.
- Se validan rangos físicos de telemetría.
- Se generan datasets optimizados para análisis y visualización.

Finalmente, los datos procesados se almacenan en formato CSV para facilitar su uso posterior en notebooks, modelos y dashboards interactivos.

---

## 📈 Análisis Exploratorio de Datos

Se desarrolló un EDA completo para estudiar:

- Distribución de velocidades.
- Distribución de RPM.
- Uso de marchas.
- Uso de DRS.
- Relación velocidad-RPM.
- Frenadas.
- Trazado de circuitos.
- Comportamiento del acelerador.
- Consistencia de vueltas.
- Calidad y cobertura de la telemetría por sesión.

El objetivo del EDA fue comprender la estructura real de los datos, detectar anomalías y extraer patrones relevantes antes de construir la capa de visualización.

Además, este estudio estadístico es la base que alimenta el modelo predictivo: a partir de los datos extraídos, limpiados y analizados, se construyen variables explicativas que representan el comportamiento real de la sesión. En otras palabras, el valor del modelo no está solo en el algoritmo, sino en el dato procesado que lo alimenta y que hace posible capturar patrones repetibles y útiles [web:83][web:85][web:87].

---

## 🖥️ Dashboard Streamlit

El dashboard está organizado en diferentes módulos especializados:

### Overview
Resumen general de la sesión seleccionada.

### Lap Analysis
Análisis detallado de vueltas rápidas, sectores y rendimiento.

### Driver Comparison
Comparación directa entre dos pilotos.

### Circuit Intelligence
Estudio técnico del circuito mediante telemetría y posición.

### Strategy Room
Análisis de estrategias de carrera, stints y gestión de neumáticos.

### Race Conditions
Análisis de meteorología, evolución de pista y eventos FIA.

### Engineer Mode
Módulo interactivo diseñado para simular una estación de ingeniería de pista.

Permite:

- Inspeccionar sistemas del monoplaza mediante una imagen interactiva.
- Analizar motor, neumáticos, aerodinámica, DRS y piloto.
- Visualizar métricas técnicas por módulo.
- Simular tiempos de vuelta bajo diferentes condiciones.
- Analizar zonas de frenada y estimar distancias óptimas de frenado.

---

## 🤖 Modelo predictivo de tiempo de vuelta

Uno de los módulos más avanzados del proyecto es el sistema de predicción de vuelta integrado en **Engineer Mode** [file:1].

Este módulo utiliza un pipeline de Machine Learning basado en Scikit-learn para estimar el tiempo de vuelta a partir de variables físicas y contextuales como temperatura ambiente, temperatura de pista, humedad, lluvia, compuesto de neumático y desgaste acumulado [file:1].

### Variables utilizadas
- Temperatura ambiente
- Temperatura de pista
- Humedad
- Lluvia
- Compuesto
- Edad del neumático
- Piloto
- Degradación estimada
- Diferencia respecto a la temperatura óptima del compuesto
- Indicadores de crossover entre compuestos
- Penalizaciones por uso incorrecto del neumático en lluvia

### Enfoque del modelo
- Filtrado de vueltas válidas
- Asociación de stint y compuesto a cada vuelta
- Unión temporal con datos meteorológicos
- Ingeniería de variables físicas relacionadas con neumáticos
- Entrenamiento de un modelo predictivo con Scikit-learn
- Evaluación mediante métricas como `R²` y `MAE`
- Simulación interactiva de condiciones para predecir tiempos de vuelta [file:1]

### Relación entre datos y modelo
El modelo se alimenta de los datos estadísticos y transformados del proyecto. Primero se extraen y limpian los datos reales de OpenF1, después se analizan sus distribuciones, rangos y relaciones, y finalmente esas variables derivadas se usan como entrada del modelo. Esto es importante porque el modelo no “inventa” conocimiento: aprende patrones a partir de los datos observados, y cuanto mejor representado esté el fenómeno en el CSV procesado, mejor capacidad tendrá para modelar la realidad.

### Objetivo del módulo
Este sistema no pretende sustituir un modelo profesional de simulación de equipo, sino ofrecer una aproximación interpretativa y visual al impacto de las condiciones de carrera sobre el rendimiento de vuelta [file:1].

---

## 🛑 Punto óptimo de frenada

El dashboard también incorpora un módulo para estudiar el punto óptimo de frenada a partir de telemetría y posición del coche [file:1].

Este análisis relaciona la velocidad de entrada en curva con la distancia recorrida hasta el inicio de la frenada real, detectando eventos de frenado sobre el trazado y ajustando un modelo lineal para estimar la distancia de frenada esperada en función de la velocidad de entrada [file:1].

Esto permite:
- Identificar frenadas críticas del circuito.
- Visualizar zonas de frenado sobre el mapa del trazado.
- Estimar la distancia óptima de frenada para una velocidad dada.
- Analizar la exigencia técnica del circuito [file:1].

---

## 🚀 Instalación

```bash
git clone https://github.com/usuario/f1-race-intelligence.git
cd f1-race-intelligence
pip install -r requirements.txt
```

---

## ▶️ Ejecución

```bash
streamlit run app/streamlit_app.py
```

> Nota: en tu versión actual del README aparece `streamlit_app.p`, pero la extensión correcta debe ser `.py` [file:1].

---

## 📁 Estructura del proyecto

```text
f1-race-intelligence/
│
├── app/
│   ├── streamlit_app.py
│   ├── pages/
│   ├── assets/
│
├── data/
│   ├── raw/
│   ├── processed/
│
├── notebooks/
│
├── src/
│   ├── cleaning/
│   ├── dashboard/
│
├── requirements.txt
└── README.md
```

---

## ⚠️ Limitaciones

- OpenF1 no proporciona telemetría completa para todas las sesiones.
- Algunas sesiones solo contienen información parcial de vueltas o resultados.
- La telemetría detallada depende de la combinación piloto-sesión disponible en la API.
- Los modelos predictivos son aproximaciones analíticas y no sustituyen herramientas profesionales de simulación de equipos de competición [file:1].

---

## 🔮 Futuras mejoras

- Integración con FastF1.
- Predicción de estrategias mediante Machine Learning.
- Simulación de paradas en boxes.
- Comparación multi-temporada.
- Análisis avanzado de degradación de neumáticos.
- Dashboard específico para clasificación.
- Mejora del modelo predictivo con validación cruzada e importancia de variables.
- Soporte futuro para otras categorías como MotoGP.

---

## 👨‍💻 Autor

**Joel Ibarra**
