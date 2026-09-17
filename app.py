import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Apuestas Deportivas", page_icon="⚽", layout="wide")
st.title("⚽ Análisis de Apuestas Deportivas")

# Configuración en barra lateral
st.sidebar.header("⚙️ Configuración")
api_key = st.sidebar.text_input("Ingresa tu API Key de API-Football:", type="password")

if not api_key:
    st.info("👈 Por favor, ingresa tu API Key en la barra lateral para continuar.")
    st.stop()

headers = {'x-apisports-key': api_key}

# Pestañas principales (Partidos va de primero)
tab1, tab2, tab3 = st.tabs(["📅 Partidos del Día", "🧮 Calculadora EV", "📊 Equipos"])

with tab1:
    st.header("Partidos Programados")
    fecha = st.date_input("Selecciona Fecha:", pd.to_datetime("today"))
    
    if st.button("Consultar Partidos"):
        with st.spinner("Cargando cartelera..."):
            url = f"https://v3.football.api-sports.io/fixtures?date={fecha.strftime('%Y-%m-%d')}"
            res = requests.get(url, headers=headers)
            if res.status_code == 200 and res.json().get('response'):
                partidos = []
                for item in res.json()['response']:
                    partidos.append({
                        "Liga": item['league']['name'],
                        "Local": item['teams']['home']['name'],
                        "Visitante": item['teams']['away']['name'],
                        "Estado": item['fixture']['status']['short']
                    })
                st.dataframe(pd.DataFrame(partidos), use_container_width=True)
            else:
                st.warning("No se encontraron partidos o la clave no es válida.")

with tab2:
    st.header("Calculadora de Valor Esperado (EV)")
    col1, col2, col3 = st.columns(3)
    with col1:
        cuota = st.number_input("Cuota:", min_value=1.01, value=2.00)
    with col2:
        prob = st.number_input("Probabilidad Estimada (%):", min_value=1.0, max_value=100.0, value=55.0) / 100
    with col3:
        bank = st.number_input("Capital ($):", min_value=10.0, value=1000.0)
    
    ev = (prob * (cuota - 1)) - (1 - prob)
    st.metric("Valor Esperado (EV)", f"{ev * 100:.2f}%", delta="Rentable" if ev > 0 else "Sin Valor")

with tab3:
    st.header("Consulta de Equipos")
    league = st.text_input("ID Liga:", value="39")
    season = st.text_input("Temporada:", value="2023")
    if st.button("Buscar Equipos"):
        res = requests.get(f"https://v3.football.api-sports.io/teams?league={league}&season={season}", headers=headers)
        if res.status_code == 200 and res.json().get('response'):
            teams = [x['team']['name'] for x in res.json()['response']]
            st.dataframe(pd.DataFrame(teams, columns=["Equipo"]))
