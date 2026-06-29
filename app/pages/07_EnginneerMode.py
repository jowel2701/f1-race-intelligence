import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from streamlit_image_coordinates import streamlit_image_coordinates

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from src.dashboard.data_loader import load_all_data
from src.dashboard.utils import global_style

st.set_page_config(page_title="Engineer Mode", layout="wide")
global_style()

def metric_flip_card(title, front_value, back_title, back_value):
    st.markdown(f"""
        <div class="flip-card"><div class="flip-card-inner">
            <div class="flip-card-front"><p class="card-title">{title}</p><h2>{front_value}</h2></div>
            <div class="flip-card-back"><p class="card-title">{back_title}</p><h2>{back_value}</h2></div>
        </div></div>""", unsafe_allow_html=True)

PLOTLY_BASE = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                   font=dict(color="white"), margin=dict(l=20, r=20, t=20, b=20))

data = load_all_data()
laps     = data["laps"]
stints   = data["stints"]
car_data = data["car_data"]
location = data["location"]
drivers  = data["drivers"]
weather  = data["weather"]

driver_cols = ["session_key", "driver_number", "name_acronym", "team_name"]
laps = laps.merge(drivers[driver_cols], on=["session_key", "driver_number"], how="left")

st.sidebar.header("Filtros")
available_sessions = laps[["season", "country_name", "session_name", "session_key"]].drop_duplicates()
season = st.sidebar.selectbox("Season", sorted(available_sessions["season"].unique()))
sessions_season = available_sessions[available_sessions["season"] == season]
country = st.sidebar.selectbox("Grand Prix", sorted(sessions_season["country_name"].unique()))
sessions_country = sessions_season[sessions_season["country_name"] == country]
session = st.sidebar.selectbox("Session", sorted(sessions_country["session_name"].unique()))
session_key = sessions_country[sessions_country["session_name"] == session]["session_key"].iloc[0]

session_drivers = drivers[drivers["session_key"] == session_key]
driver_options  = session_drivers[["driver_number", "name_acronym"]].drop_duplicates()
if driver_options.empty:
    st.warning("No hay pilotos disponibles."); st.stop()

selected_driver = st.sidebar.selectbox("Driver", sorted(driver_options["name_acronym"]))
driver_number   = driver_options[driver_options["name_acronym"] == selected_driver]["driver_number"].iloc[0]

driver_car      = car_data[(car_data["session_key"] == session_key) & (car_data["driver_number"] == driver_number)].copy()
driver_stints   = stints[(stints["session_key"] == session_key) & (stints["driver_number"] == driver_number)].copy()
driver_location = location[(location["session_key"] == session_key) & (location["driver_number"] == driver_number)].copy()
has_telemetry   = not driver_car.empty and not driver_location.empty

st.title("Engineer Mode")
st.caption(f"{country} · {season} · {session} · {selected_driver}")

tab_diagnostico, tab_lap_pred, tab_braking = st.tabs([
    "Diagnostico del coche", "Prediccion de vuelta", "Punto optimo de frenada"])


# TAB 1
with tab_diagnostico:
    if not has_telemetry:
        st.info("No hay telemetria disponible para esta combinacion de sesion y piloto.")
    else:
        IMAGE_PATH = ROOT_DIR / "app" / "assets" / "Car_AMR26.png"
        if not IMAGE_PATH.exists():
            st.error(f"Imagen no encontrada en: {IMAGE_PATH}")
        else:
            if "module" not in st.session_state:
                st.session_state.module = "Engine"
            coords = streamlit_image_coordinates(str(IMAGE_PATH), key="car_click", width=900)
            if coords:
                x, y = coords["x"], coords["y"]
                if   250 <= x <= 450 and 220 <= y <= 450: st.session_state.module = "Front Tyres"
                elif 660 <= x <= 740 and 235 <= y <= 320: st.session_state.module = "Rear Tyres"
                elif 550 <= x <= 600 and 215 <= y <= 320: st.session_state.module = "Engine"
                elif  50 <= x <= 250 and 300 <= y <= 500: st.session_state.module = "Aero"
                elif 650 <= x <= 850 and 196 <= y <= 213: st.session_state.module = "DRS"
                elif 380 <= x <= 520 and 180 <= y <= 280: st.session_state.module = "Driver"

            selected_module = st.session_state.module
            st.subheader(f"Sistema seleccionado: {selected_module}")
            col1, col2, col3, col4 = st.columns(4)

            if selected_module == "Engine":
                with col1: metric_flip_card("Velocidad punta", f"{driver_car['speed'].max():.0f} km/h", "Media", f"{driver_car['speed'].mean():.0f} km/h")
                with col2: metric_flip_card("RPM maxima", f"{driver_car['rpm'].max():.0f}", "RPM media", f"{driver_car['rpm'].mean():.0f}")
                with col3: metric_flip_card("Marcha maxima", f"{int(driver_car['n_gear'].max())}", "Marcha media", f"{driver_car['n_gear'].mean():.1f}")
                with col4: metric_flip_card("% a plena potencia", f"{(driver_car['throttle']>=90).mean()*100:.1f}%", "Throttle medio", f"{driver_car['throttle'].mean():.0f}%")
                st.markdown("""<div class="insight-box">El motor se evalua por velocidad punta, RPM y uso de marchas. La marcha media refleja el tipo de circuito.</div>""", unsafe_allow_html=True)

            elif selected_module == "DRS":
                drs_pct = (driver_car["drs"] >= 10).mean() * 100
                drs_top = driver_car.loc[driver_car["drs"] >= 10, "speed"].max()
                drs_gain = driver_car.loc[driver_car["drs"] >= 10, "speed"].mean() - driver_car.loc[driver_car["drs"] < 10, "speed"].mean()
                with col1: metric_flip_card("Uso de DRS", f"{drs_pct:.1f}%", "Muestras", f"{(driver_car['drs']>=10).sum():,}")
                with col2: metric_flip_card("Vel. punta DRS", f"{drs_top:.0f} km/h" if pd.notna(drs_top) else "N/A", "Estado max", str(int(driver_car["drs"].max())))
                with col3: metric_flip_card("Sin DRS", f"{driver_car.loc[driver_car['drs']<10,'speed'].mean():.0f} km/h", "Con DRS", f"{driver_car.loc[driver_car['drs']>=10,'speed'].mean():.0f} km/h")
                with col4: metric_flip_card("Ganancia DRS", f"+{drs_gain:.1f} km/h" if not np.isnan(drs_gain) else "N/A", "Zonas DRS", f"{int((driver_car['drs'].diff().fillna(0)>0).sum())}")
                st.markdown("""<div class="insight-box">El DRS abre el aleron trasero para reducir la resistencia aerodinamica.</div>""", unsafe_allow_html=True)

            elif selected_module in ("Front Tyres", "Rear Tyres"):
                if driver_stints.empty:
                    st.warning("No hay datos de stints.")
                else:
                    ls = driver_stints.sort_values("stint_number").iloc[-1]
                    ts = int(driver_stints["stint_number"].max())
                    with col1: metric_flip_card("Compuesto", ls["compound"], "Stint", str(int(ls["stint_number"])))
                    with col2: metric_flip_card("Vueltas stint", str(int(ls["lap_end"]-ls["lap_start"]+1)), "Inicio", str(int(ls["lap_start"])))
                    with col3: metric_flip_card("Edad neumatico", f"{int(ls['tyre_age_at_start'])} vueltas", "Al inicio", "Vueltas acumuladas")
                    with col4: metric_flip_card("Stints totales", str(ts), "Paradas", str(ts-1))
                    st.markdown(f"""<div class="insight-box">Neumaticos <strong>{ls['compound']}</strong> con <strong>{int(ls['tyre_age_at_start'])} vueltas</strong> al inicio. <strong>{ts-1} parada{'s' if ts>2 else ''}</strong> en boxes.</div>""", unsafe_allow_html=True)

            elif selected_module == "Aero":
                with col1: metric_flip_card("Vel. media", f"{driver_car['speed'].mean():.0f} km/h", "Punta", f"{driver_car['speed'].max():.0f} km/h")
                with col2: metric_flip_card("Throttle medio", f"{driver_car['throttle'].mean():.0f}%", "Plena potencia", f"{(driver_car['throttle']>=90).mean()*100:.1f}%")
                with col3: metric_flip_card("DRS", f"{(driver_car['drs']>=10).mean()*100:.1f}%", "Circuito", "Alta carga" if driver_car['speed'].mean()<200 else "Baja carga")
                with col4: metric_flip_card("Frenada media", f"{driver_car['brake'].mean():.1f}%", "% frenando", f"{(driver_car['brake']>0).mean()*100:.1f}%")
                st.markdown("""<div class="insight-box">Throttle alto y poco DRS = alta carga. DRS frecuente y vel. punta alta = baja carga.</div>""", unsafe_allow_html=True)

            elif selected_module == "Driver":
                dl = laps[(laps["session_key"]==session_key) & (laps["driver_number"]==driver_number)]
                if dl.empty:
                    st.warning("No hay vueltas registradas.")
                else:
                    fl = dl["lap_duration"].min(); al = dl["lap_duration"].mean()
                    s1 = dl["duration_sector_1"].min() if "duration_sector_1" in dl.columns else None
                    with col1: metric_flip_card("Vuelta rapida", f"{fl:.3f}s", "Media", f"{al:.3f}s")
                    with col2: metric_flip_card("Vueltas", str(int(dl["lap_number"].max())), "Consistencia", f"{dl['lap_duration'].std():.3f}s std")
                    with col3: metric_flip_card("Mejor S1", f"{s1:.3f}s" if s1 else "N/A", "Gap rapida vs media", f"+{al-fl:.3f}s")
                    with col4:
                        team = drivers[drivers["driver_number"]==driver_number]["team_name"]
                        metric_flip_card("Piloto", selected_driver, "Equipo", team.iloc[0] if not team.empty else "-")
                    st.markdown(f"""<div class="insight-box">Gap rapida vs media: <strong>{al-fl:.3f}s</strong> — {'alta consistencia' if al-fl<1 else 'variabilidad en el rendimiento'}.</div>""", unsafe_allow_html=True)

            st.caption("Haz clic sobre el motor, los neumaticos, el aleron, el DRS o el cockpit para inspeccionar cada sistema.")


# TAB 2
with tab_lap_pred:
    st.subheader("Prediccion de tiempo de vuelta")
    st.caption("Modelo entrenado solo con vueltas de Race. Cambia el Driver o el Grand Prix en el sidebar para comparar.")

    valid_laps = laps[laps["lap_duration"].notna() & (laps["is_pit_out_lap"]==False) & (laps["is_outlier_lap"]==False)].copy()

    stints_expand = stints.copy()
    stints_expand["lap_start"] = stints_expand["lap_start"].astype(float)
    stints_expand["lap_end"]   = stints_expand["lap_end"].astype(float)

    def attach_stint_info(laps_df, stints_df):
        rows = []
        for (sk, dn), group in laps_df.groupby(["session_key", "driver_number"]):
            s = stints_df[(stints_df["session_key"]==sk) & (stints_df["driver_number"]==dn)]
            g = group.copy(); g["compound"] = "UNKNOWN"; g["tyre_age_at_start"] = np.nan
            if not s.empty:
                for _, sr in s.iterrows():
                    mask = (g["lap_number"]>=sr["lap_start"]) & (g["lap_number"]<=sr["lap_end"])
                    g.loc[mask, "compound"] = sr["compound"]
                    g.loc[mask, "tyre_age_at_start"] = sr["tyre_age_at_start"]
            rows.append(g)
        return pd.concat(rows, ignore_index=True)

    with st.spinner("Preparando dataset..."):
        laps_with_stint = attach_stint_info(valid_laps, stints_expand)

    weather_small = weather[["session_key","date","air_temperature","track_temperature","humidity","rainfall"]].copy()
    laps_with_stint["date_start"] = pd.to_datetime(laps_with_stint["date_start"], utc=True, format="mixed")
    weather_small["date"]         = pd.to_datetime(weather_small["date"], utc=True, format="mixed")
    laps_with_stint = laps_with_stint.dropna(subset=["date_start"]).sort_values("date_start")
    weather_small   = weather_small.dropna(subset=["date"]).sort_values("date")

    model_df = pd.merge_asof(laps_with_stint, weather_small,
        left_on="date_start", right_on="date", by="session_key", direction="nearest",
    ).dropna(subset=["lap_duration","air_temperature","track_temperature","humidity","tyre_age_at_start","compound","name_acronym"])

    # Solo Race — qualifying distorsiona porque casi todo es SOFT
    if "session_type" in model_df.columns:
        model_df = model_df[model_df["session_type"] == "Race"].copy()

    model_df["driver_avg_pace"] = model_df.groupby("name_acronym")["lap_duration"].transform("mean")

    tyre_life_map     = {"SOFT":25,"MEDIUM":35,"HARD":45,"INTERMEDIATE":25,"WET":20,"UNKNOWN":30}
    tyre_temp_window  = {"SOFT":85,"MEDIUM":95,"HARD":110,"INTERMEDIATE":70,"WET":60,"UNKNOWN":90}
    degradation_rate  = {"SOFT":0.10,"MEDIUM":0.05,"HARD":0.02,"INTERMEDIATE":0.08,"WET":0.06,"UNKNOWN":0.05}
    initial_advantage = {"SOFT":1.0,"MEDIUM":0.5,"HARD":0.0,"INTERMEDIATE":0.0,"WET":0.0,"UNKNOWN":0.3}

    def tyre_curve(compound, tyre_age, track_temp, is_rain=False):
        """
        Curva de rendimiento del neumatico con degradacion cuadratica y
        penalizacion por temperatura fuera de la ventana optima.
        Devuelve offset en segundos: positivo = mas rapido que la base.
        """
        init_adv  = initial_advantage.get(compound, 0.0)
        deg_rate  = degradation_rate.get(compound, 0.05)
        life_max  = tyre_life_map.get(compound, 30)
        temp_opt  = tyre_temp_window.get(compound, 90)

        # Ratio de vida: 0=nuevo, 1=al limite — la degradacion se acelera al final
        age_ratio   = min(tyre_age / life_max, 1.5)
        deg_penalty = deg_rate * tyre_age * (1 + age_ratio)

        # Fuera de la ventana termica optima el neumatico pierde rendimiento
        temp_penalty = abs(track_temp - temp_opt) * 0.015

        # Penalizacion por condicion meteorologica incompatible
        if not is_rain and compound in ["INTERMEDIATE", "WET"]:
            rain_penalty = 10.0   # en seco se sobrecalientan
        elif is_rain and compound in ["SOFT", "MEDIUM", "HARD"]:
            rain_penalty = 12.0   # en mojado con seco son peligrosos
        else:
            rain_penalty = 0.0

        return init_adv - deg_penalty - temp_penalty - rain_penalty

    model_df["tyre_life_max"]    = model_df["compound"].map(tyre_life_map)
    model_df["tyre_degradation"] = model_df["tyre_age_at_start"] / model_df["tyre_life_max"]
    model_df["temp_vs_optimal"]  = model_df["track_temperature"] - model_df["compound"].map(tyre_temp_window)
    model_df["rain_wrong_tyre"]  = ((model_df["rainfall"]==1) & model_df["compound"].isin(["SOFT","MEDIUM","HARD"])).astype(int)
    model_df["tyre_performance"] = model_df.apply(lambda r: tyre_curve(r["compound"], r["tyre_age_at_start"], r["track_temperature"], is_rain=bool(r["rainfall"])), axis=1)
    model_df["crossover_lap"]    = model_df.apply(lambda r: initial_advantage.get(r["compound"],0) / (degradation_rate.get(r["compound"],0.05)-0.02) if degradation_rate.get(r["compound"],0.05)>0.02 else 999, axis=1)
    model_df["past_crossover"]   = (model_df["tyre_age_at_start"] > model_df["crossover_lap"]).astype(int)

    st.caption(f"Dataset: **{len(model_df)} vueltas de carrera validas**.")

    if "lap_model_bundle" not in st.session_state:
        st.session_state.lap_model_bundle = None

    if len(model_df) < 30:
        st.warning("No hay suficientes datos para entrenar el modelo.")
    else:
        c1, c2 = st.columns(2)
        with c1: train_clicked = st.button("Entrenar modelo de prediccion")
        with c2:
            if st.button("Resetear modelo"):
                st.session_state.lap_model_bundle = None; st.rerun()

        if train_clicked:
            try:
                with st.spinner("Entrenando..."):
                    features_num = ["air_temperature","track_temperature","humidity","rainfall"]
                    # compound fuera del modelo — su efecto es offset deterministico via tyre_curve
                    # name_acronym y country_name como categoricas para capturar piloto y circuito
                    features_cat = ["name_acronym","country_name"]

                    mdt = model_df.dropna(subset=features_num+features_cat+["lap_duration","driver_avg_pace","tyre_performance"]).copy()
                    X   = mdt[features_num+features_cat]
                    # Target: residual ajustado por ritmo del piloto y compuesto
                    y   = mdt["lap_duration"] - mdt["driver_avg_pace"] + mdt["tyre_performance"]

                    Xtr,Xte,ytr,yte = train_test_split(X, y, test_size=0.2, random_state=42)
                    pre = ColumnTransformer(transformers=[("cat",OneHotEncoder(handle_unknown="ignore"),features_cat)], remainder="passthrough")
                    pipe = Pipeline([("prep",pre),("reg",RandomForestRegressor(n_estimators=200,random_state=42,max_depth=12,min_samples_leaf=4,n_jobs=-1))])
                    pipe.fit(Xtr, ytr)
                    yp  = pipe.predict(Xte)
                    r2  = r2_score(yte, yp)
                    mae = mean_absolute_error(yte, yp)

                    st.session_state.lap_model_bundle = {
                        "pipeline": pipe, "r2": r2, "mae": mae,
                        "y_floor": float(ytr.quantile(0.05)),
                        "y_ceiling": float(ytr.quantile(0.95)),
                        "train_rows": len(mdt),
                        "driver_pace_map": mdt.groupby("name_acronym")["driver_avg_pace"].first().to_dict(),
                        "overall_avg_pace": float(mdt["lap_duration"].mean()),
                    }
            except Exception as e:
                st.error(f"Error: {type(e).__name__}: {e}")

        if st.session_state.lap_model_bundle is not None:
            b   = st.session_state.lap_model_bundle
            pipe= b["pipeline"]; r2=b["r2"]; mae=b["mae"]
            y_floor=b["y_floor"]; y_ceiling=b["y_ceiling"]
            dpm =b["driver_pace_map"]; oap=b["overall_avg_pace"]

            c1,c2,c3 = st.columns(3)
            with c1: st.metric("R2 del modelo",f"{r2:.3f}"); st.caption("Cuanto mas cerca de 1.0, mejor predice.")
            with c2: st.metric("Error medio",f"+/-{mae:.3f}s"); st.caption("Margen de error medio por vuelta.")
            with c3: st.metric("Vueltas analizadas",f"{b['train_rows']:,}"); st.caption("Vueltas de carrera usadas.")

            st.divider()
            st.markdown("##### Simula condiciones para predecir el tiempo de vuelta")

            ca,cb,cc = st.columns(3)
            with ca:
                sim_air   = st.slider("Temperatura aire (C)", 15.0, 45.0, float(model_df["air_temperature"].mean()))
                sim_track = st.slider("Temperatura pista (C)", 15.0, 60.0, float(model_df["track_temperature"].mean()))
            with cb:
                sim_hum  = st.slider("Humedad (%)", 0.0, 100.0, float(model_df["humidity"].mean()))
                sim_rain = st.checkbox("Lluvia", value=False)
            with cc:
                sim_compound = st.selectbox("Compuesto", sorted(model_df["compound"].dropna().unique()))
                sim_tyre_age = st.slider("Edad del neumatico (vueltas)", 0, 40, 5)

            _deg_rate  = degradation_rate.get(sim_compound, 0.05)
            _init_adv  = initial_advantage.get(sim_compound, 0.0)
            _crossover = _init_adv / (_deg_rate - 0.02) if _deg_rate > 0.02 else 999

            # Curva cuadratica: ventaja inicial - degradacion acelerada - penalizacion termica
            _tyre_perf   = tyre_curve(sim_compound, sim_tyre_age, sim_track, is_rain=sim_rain)
            sim_drv_pace = dpm.get(selected_driver, oap)

            sim_input = pd.DataFrame([{
                "air_temperature": sim_air, "track_temperature": sim_track,
                "humidity": sim_hum, "rainfall": int(sim_rain),
                "name_acronym": selected_driver, "country_name": country,
            }])

            # Avisos de combinaciones fisicamente incorrectas
            if sim_rain and sim_compound in ["SOFT","MEDIUM","HARD"]:
                st.warning(f"Con lluvia y {sim_compound} de seco la prediccion no es realista. Usa Intermedio o WET.")
            if not sim_rain and sim_compound in ["INTERMEDIATE","WET"]:
                st.info(
                    f"En pista seca el {sim_compound} se sobrecalienta y pierde todo el agarre. "
                    f"El tiempo estimado incluye una penalizacion de +10s sobre el ritmo base."
                )
            
            if sim_tyre_age > _crossover and sim_compound != "HARD":
                st.warning(f"Con {sim_tyre_age} vueltas en {sim_compound}, el HARD ya seria mas rapido (crossover vuelta {_crossover:.0f}).")
            if sim_track >= 45 and sim_compound == "SOFT" and sim_tyre_age >= 15:
                st.warning(f"SOFT con {sim_tyre_age} vueltas y {sim_track:.0f}C — degradacion extrema.")

            try:
                raw     = float(pipe.predict(sim_input)[0])
                clipped = float(np.clip(raw, y_floor, y_ceiling))

                # Penalizacion determinista por combinacion incorrecta de neumatico y condicion
                wrong_condition_penalty = 0.0
                if sim_rain and sim_compound in ["SOFT","MEDIUM","HARD"]:
                    # Seco con lluvia: perdida total de agarre, +8s por vuelta minimo
                    wrong_condition_penalty = 8.0
                if not sim_rain and sim_compound in ["INTERMEDIATE","WET"]:
                    # Lluvia en seco: neumatico se destruye rapidamente, +6s por vuelta
                    wrong_condition_penalty = 6.0

                sim_pred = clipped + sim_drv_pace - _tyre_perf + wrong_condition_penalty
                # Clip fisico: ninguna prediccion puede ser absurda
                sim_pred = float(np.clip(sim_pred, sim_drv_pace * 0.95, sim_drv_pace * 1.60))

                p1,p2,p3 = st.columns(3)
                with p1: st.metric("Tiempo estimado", f"{sim_pred:.3f}s")
                with p2: st.metric("Mejor caso", f"{sim_pred-mae:.3f}s")
                with p3: st.metric("Peor caso", f"{sim_pred+mae:.3f}s")

                cross_msg = f" · Crossover con HARD en vuelta {_crossover:.0f}." if sim_compound != "HARD" and _crossover < 999 else ""
                st.caption(
                    f"Prediccion: **{sim_pred:.3f}s** (+/-{mae:.3f}s). "
                    f"Offset compuesto: {_tyre_perf:+.3f}s "
                    f"(ventaja inicial {_init_adv:.1f}s, degradacion acumulada {_deg_rate*sim_tyre_age*(1+min(sim_tyre_age/tyre_life_map.get(sim_compound,30),1.5)):.2f}s)."
                    f"{cross_msg}"
                )
            except Exception as e:
                st.error(f"Error: {type(e).__name__}: {e}")
        else:
            st.info("Pulsa 'Entrenar modelo de prediccion' para activar la simulacion.")


# TAB 3
with tab_braking:
    st.subheader("Punto optimo de frenada")
    st.caption("Relacion entre la velocidad de entrada a una curva y la distancia recorrida desde el fin de recta hasta el inicio de la frenada.")

    if not has_telemetry:
        st.warning("Selecciona una sesion y piloto con telemetria disponible.")
    else:
        loc = driver_location.sort_values("date").reset_index(drop=True)
        car = driver_car.sort_values("date").reset_index(drop=True)
        loc["date"] = pd.to_datetime(loc["date"], utc=True, format="mixed")
        car["date"] = pd.to_datetime(car["date"], utc=True, format="mixed")

        track = pd.merge_asof(loc, car[["date","speed","brake","throttle"]], on="date", direction="nearest").reset_index(drop=True)
        track["dist"] = np.sqrt(track["x"].diff()**2 + track["y"].diff()**2).fillna(0).cumsum()
        track["braking_start"] = (track["brake"].diff().fillna(0) > 0) & (track["brake"] > 0)
        brake_events = track[track["braking_start"]].copy()

        if len(brake_events) < 5:
            st.warning("No se detectaron suficientes zonas de frenada.")
        else:
            entry_speeds = []
            for idx in brake_events.index:
                w = track.iloc[max(0,idx-5):idx]
                entry_speeds.append(w["speed"].max() if not w.empty else track.loc[idx,"speed"])
            brake_events["entry_speed"] = entry_speeds

            braking_distances = []
            for idx in brake_events.index:
                w = track.iloc[max(0,idx-8):idx]
                if w.empty: braking_distances.append(np.nan); continue
                braking_distances.append(track.loc[idx,"dist"] - track.loc[w["speed"].idxmax(),"dist"])
            brake_events["braking_distance"] = braking_distances
            brake_events = brake_events.dropna(subset=["entry_speed","braking_distance"])
            brake_events = brake_events[brake_events["braking_distance"] <= 500]

            st.caption(f"{len(brake_events)} zonas de frenada detectadas.")

            Xb = brake_events[["entry_speed"]]; yb = brake_events["braking_distance"]
            rb = LinearRegression(); rb.fit(Xb, yb)
            r2b = rb.score(Xb, yb); maeb = mean_absolute_error(yb, rb.predict(Xb))

            c1,c2,c3 = st.columns(3)
            with c1: st.metric("Zonas de frenada", str(len(brake_events))); st.caption(f"Vel. media entrada: {brake_events['entry_speed'].mean():.0f} km/h")
            with c2: st.metric("R2 del ajuste", f"{r2b:.3f}"); st.caption("Relacion velocidad → distancia frenada.")
            with c3: st.metric("Error medio", f"+/-{maeb:.1f}m"); st.caption(f"Distancia media: {brake_events['braking_distance'].mean():.0f}m")

            st.divider()
            xr = np.linspace(brake_events["entry_speed"].min(), brake_events["entry_speed"].max(), 50)
            yl = rb.predict(xr.reshape(-1,1))

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=np.concatenate([xr,xr[::-1]]), y=np.concatenate([yl+maeb,(yl-maeb)[::-1]]),
                fill="toself", fillcolor="rgba(0,210,190,0.1)", line=dict(color="rgba(0,0,0,0)"), name=f"+/-{maeb:.1f}m"))
            fig.add_trace(go.Scatter(x=brake_events["entry_speed"], y=brake_events["braking_distance"],
                mode="markers", marker=dict(size=9,color="#00D2BE",opacity=0.85), name="Zona frenada"))
            fig.add_trace(go.Scatter(x=xr, y=yl, mode="lines", line=dict(color="white",dash="dash",width=2), name="Ajuste"))
            fig.update_layout(**PLOTLY_BASE, height=420,
                xaxis=dict(title="Velocidad entrada (km/h)", gridcolor="rgba(0,210,190,0.12)"),
                yaxis=dict(title="Distancia frenada (m)", gridcolor="rgba(0,210,190,0.12)"),
                legend=dict(font=dict(color="white"), bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.markdown("##### Simula una velocidad de entrada")
            ss = st.slider("Velocidad (km/h)", float(brake_events["entry_speed"].min()), float(brake_events["entry_speed"].max()), float(brake_events["entry_speed"].mean()))
            sd = rb.predict([[ss]])[0]
            s1,s2,s3 = st.columns(3)
            with s1: st.metric("Distancia estimada", f"{sd:.0f}m")
            with s2: st.metric("Mejor caso", f"{max(0,sd-maeb):.0f}m")
            with s3: st.metric("Peor caso", f"{sd+maeb:.0f}m")

            st.divider()
            st.markdown("##### Zonas de frenada sobre el trazado")
            fm = go.Figure()
            fm.add_trace(go.Scatter(x=track["x"],y=track["y"],mode="lines",line=dict(color="rgba(180,180,180,0.9)",width=16),hoverinfo="skip",showlegend=False))
            fm.add_trace(go.Scatter(x=track["x"],y=track["y"],mode="lines",line=dict(color="rgba(10,10,10,1)",width=10),hoverinfo="skip",showlegend=False))
            fm.add_trace(go.Scatter(x=brake_events["x"],y=brake_events["y"],mode="markers",
                marker=dict(size=11,color=brake_events["entry_speed"],
                    colorscale=[[0,"#FFF200"],[0.5,"#FF6B00"],[1,"#E10600"]],
                    colorbar=dict(title="Vel. entrada (km/h)",tickfont=dict(color="white")),
                    line=dict(color="white",width=1)),
                hovertemplate="Vel. entrada: %{marker.color:.0f} km/h<extra></extra>"))
            fm.update_layout(**PLOTLY_BASE,height=520,
                xaxis=dict(visible=False,scaleanchor="y",scaleratio=1),yaxis=dict(visible=False),showlegend=False)
            st.plotly_chart(fm, use_container_width=True)
            st.caption("Amarillo = baja velocidad, rojo = alta velocidad. Los puntos rojos son las frenadas mas exigentes.")