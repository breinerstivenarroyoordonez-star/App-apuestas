import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Análisis de Apuestas Deportivas", page_icon="⚽", layout="wide")

st.title("⚽ Análisis de Apuestas Deportivas")

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Configuración")
api_key = st.sidebar.text_input("Ingresa tu API Key de The Odds API:", type="password")

st.sidebar.markdown("---")
st.sidebar.info("Obtén tu API Key gratuita en [the-odds-api.com](https://the-odds-api.com)")

# --- PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["📅 Partidos y Cuotas", "🧮 Calculadora EV", "📊 Análisis / Equipos"])

# ---------------------------------------------------------
# PESTAÑA 1: PARTIDOS Y CUOTAS (THE ODDS API)
# ---------------------------------------------------------
with tab1:
    st.header("Partidos Programados y Cuotas")
    
    deporte = st.selectbox(
        "Selecciona la Liga / Deporte:",
        [
            ("soccer_mexico_ligamx", "Liga MX (México)"),
            ("soccer_spain_la_liga", "La Liga (España)"),
            ("soccer_epl", "Premier League (Inglaterra)"),
            ("soccer_uefa_champs_league", "Champions League"),
            ("soccer_usa_mls", "MLS (EE.UU.)"),
            ("soccer_conmebol_libertadores", "Copa Libertadores")
        ],
        format_func=lambda x: x[1]
    )

    if st.button("Consultar Partidos"):
        if not api_key:
            st.warning("⚠️ Por favor, ingresa tu API Key en la barra lateral para continuar.")
        else:
            sport_key = deporte[0]
            url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={api_key}&regions=us,eu&markets=h2h"
            
            with st.spinner("Cargando cuotas desde The Odds API..."):
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if not data:
                        st.info("No hay partidos con cuotas disponibles actualmente para esta liga.")
                    else:
                        filas = []
                        for match in data:
                            home_team = match.get("home_team", "Local")
                            away_team = match.get("away_team", "Visitante")
                            commence_time = match.get("commence_time", "").replace("T", " ").replace("Z", "")
                            
                            # Extraer cuotas de la primera casa de apuestas disponible
                            bookmakers = match.get("bookmakers", [])
                            if bookmakers:
                                bookmaker_name = bookmakers[0].get("title", "Casa")
                                outcomes = bookmakers[0].get("markets", [{}])[0].get("outcomes", [])
                                
                                cuota_home = None
                                cuota_away = None
                                cuota_draw = None
                                
                                for outcome in outcomes:
                                    if outcome.get("name") == home_team:
                                        cuota_home = outcome.get("price")
                                    elif outcome.get("name") == away_team:
                                        cuota_away = outcome.get("price")
                                    elif outcome.get("name") == "Draw":
                                        cuota_draw = outcome.get("price")
                                
                                prob_home = f"{round((1/cuota_home)*100, 1)}%" if cuota_home else "N/A"
                                prob_draw = f"{round((1/cuota_draw)*100, 1)}%" if cuota_draw else "N/A"
                                prob_away = f"{round((1/cuota_away)*100, 1)}%" if cuota_away else "N/A"
                                
                                filas.append({
                                    "Fecha/Hora": commence_time,
                                    "Local": home_team,
                                    "Visitante": away_team,
                                    "Cuota 1": cuota_home,
                                    "Cuota X": cuota_draw,
                                    "Cuota 2": cuota_away,
                                    "Prob. Local": prob_home,
                                    "Prob. Empate": prob_draw,
                                    "Prob. Visitante": prob_away,
                                    "Casa de Apuestas": bookmaker_name
                                })
                        
                        if filas:
                            df = pd.DataFrame(filas)
                            st.success(f"Se encontraron {len(df)} partidos activos.")
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("No se encontraron cuotas para los partidos de esta liga.")
                            
                elif response.status_code == 401:
                    st.error("❌ API Key no válida o expirada. Verifica tu clave de The Odds API.")
                elif response.status_code == 429:
                    st.error("⚠️ Alcanzaste el límite de consultas de tu plan gratuito en The Odds API.")
                else:
                    st.error(f"Error al consultar la API: {response.status_code}")

# ---------------------------------------------------------
# PESTAÑA 2: CALCULADORA DE VALOR ESPERADO (EV)
# ---------------------------------------------------------
with tab2:
    st.header("Calculadora de Valor Esperado (EV)")
    st.write("Calcula si una apuesta tiene valor matemático positivo a largo plazo.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cuota = st.number_input("Cuota de la Casa de Apuestas:", min_value=1.01, value=2.00, step=0.05)
    with col2:
        probabilidad_estimada = st.number_input("Tu Probabilidad Estimada (%):", min_value=1.0, max_value=100.0, value=55.0, step=1.0)
    with col3:
        monto = st.number_input("Monto a Apostar ($):", min_value=1.0, value=10.0, step=5.0)
        
    prob_decimal = probabilidad_estimada / 100.0
    ganancia_potencial = (cuota - 1) * monto
    ev = (prob_decimal * ganancia_potencial) - ((1 - prob_decimal) * monto)
    
    st.markdown("---")
    st.subheader("Resultado del Análisis:")
    
    col_res1, col_res2 = st.columns(2)
    col_res1.metric("Ganancia Potencial", f"${ganancia_potencial:.2f}")
    
    if ev > 0:
        col_res2.metric("Valor Esperado (EV)", f"+${ev:.2f}", delta="¡Apuesta de Valor (EV+)! 🎉", delta_color="normal")
        st.success(f"✅ **¡Recomendado!** Esta apuesta tiene un EV positivo del {round((ev/monto)*100, 2)}%. A largo plazo representa una ventaja sobre la casa de apuestas.")
    else:
        col_res2.metric("Valor Esperado (EV)", f"${ev:.2f}", delta="EV Negativo ⚠️", delta_color="inverse")
        st.error(f"❌ **No recomendada.** La casa de apuestas tiene la ventaja matemática en esta cuota.")

# ---------------------------------------------------------
# PESTAÑA 3: ANÁLISIS DE EQUIPOS
# ---------------------------------------------------------
with tab3:
    st.header("Análisis de Equipos y Rendimiento")
    st.write("Usa este espacio para anotar y comparar métricas antes de calcular el EV.")
    
    equipo = st.text_input("Nombre del equipo a analizar:", "América")
    if equipo:
        st.subheader(f"Resumen para: {equipo}")
        st.info("💡 Consejo: Revisa los últimos 5 partidos del equipo, su porcentaje de victorias como local/visitante y bajas de jugadores para ajustar tu porcentaje de probabilidad en la Calculadora EV.")
