import streamlit as st
import sqlite3
import pandas as pd
from pymongo import MongoClient, GEOSPHERE
import folium
from streamlit_folium import st_folium
import plotly.express as px
import random
from datetime import datetime, timezone

conn_sqlite = sqlite3.connect('logitech.db', check_same_thread=False)
cursor = conn_sqlite.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS motoristas (
    id INTEGER PRIMARY KEY,
    nome TEXT,
    cnh TEXT,
    status TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS veiculos (
    id INTEGER PRIMARY KEY,
    placa TEXT,
    modelo TEXT,
    motorista_id INTEGER,
    FOREIGN KEY(motorista_id) REFERENCES motoristas(id)
)
''')

cursor.execute("SELECT COUNT(*) FROM motoristas")
if cursor.fetchone()[0] == 0:
    motoristas_seed = [
        (1, "Carlos Andrade", "123456789", "Ativo"),
        (2, "Mariana Silva", "987654321", "Ativo"),
        (3, "Roberto Souza", "456789123", "Em Descanso")
    ]
    veiculos_seed = [
        (101, "ABC-1A23", "Volvo FH 540", 1),
        (102, "XYZ-9876", "Scania R450", 2),
        (103, "KGB-4567", "Mercedes Actros", 3)
    ]
    cursor.executemany("INSERT INTO motoristas VALUES (?, ?, ?, ?)", motoristas_seed)
    cursor.executemany("INSERT INTO veiculos VALUES (?, ?, ?, ?)", veiculos_seed)
    conn_sqlite.commit()

client = MongoClient("mongodb://localhost:27017/")
db = client["geolog_db"]
colecao_telemetria = db["telemetria"]

colecao_telemetria.create_index([("location", GEOSPHERE)])

if colecao_telemetria.count_documents({}) == 0:
    telemetria_seed = [
        {
            "veiculo_id": 101,
            "location": {"type": "Point", "coordinates": [-34.873, -7.115]}, 
            "temperatura": 4.2,
            "velocidade": 65,
            "timestamp": "2026-09-11T10:00:00Z"
        },
        {
            "veiculo_id": 102,
            "location": {"type": "Point", "coordinates": [-34.832, -7.121]}, 
            "temperatura": -18.5, 
            "velocidade": 85, 
            "timestamp": "2026-09-11T10:05:00Z"
        },
        {
            "veiculo_id": 103,
            "location": {"type": "Point", "coordinates": [-34.950, -7.150]}, 
            "temperatura": 22.0,
            "velocidade": 0,
            "timestamp": "2026-09-11T09:45:00Z"
        }
    ]
    colecao_telemetria.insert_many(telemetria_seed)

st.set_page_config(page_title="GeoLog - LogiTech Express", layout="wide")
st.title("🎯 Plataforma GeoLog — Telemetria Logística")
st.markdown("Sistema de Monitoramento Geospacial e Persistência Poliglota integrado (SQLite + MongoDB).")

if st.sidebar.button("Simular Movimentação"):
    veiculos = [101, 102, 103]
    novos_dados = []
    for v_id in veiculos:
        ultimo_registro = colecao_telemetria.find_one({"veiculo_id": v_id}, sort=[("timestamp", -1)])
        if ultimo_registro:
            lon, lat = ultimo_registro["location"]["coordinates"]
            nova_lon = lon + random.uniform(-0.005, 0.005)
            nova_lat = lat + random.uniform(-0.005, 0.005)
            nova_temp = ultimo_registro["temperatura"] + random.uniform(-2, 2)
            nova_vel = random.randint(0, 90)
            
            novos_dados.append({
                "veiculo_id": v_id,
                "location": {"type": "Point", "coordinates": [nova_lon, nova_lat]},
                "temperatura": round(nova_temp, 1),
                "velocidade": nova_vel,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            })
    if novos_dados:
        colecao_telemetria.insert_many(novos_dados)
        st.sidebar.success("Movimentação simulada com sucesso!")

st.sidebar.header("Filtro Geoespacial")
lat_ref = st.sidebar.number_input("Latitude Referência", value=-7.115, format="%.5f")
lon_ref = st.sidebar.number_input("Longitude Referência", value=-34.873, format="%.5f")
raio_km = st.sidebar.slider("Raio de Busca (km)", min_value=1, max_value=50, value=10)

raio_metros = raio_km * 1000

query_geo = {
    "location": {
        "$near": {
            "$geometry": {
                "type": "Point",
                "coordinates": [lon_ref, lat_ref]
            },
            "$maxDistance": raio_metros
        }
    }
}

resultados_geo = list(colecao_telemetria.find(query_geo))

veiculos_no_raio = {}
for reg in resultados_geo:
    v_id = reg["veiculo_id"]
    if v_id not in veiculos_no_raio or reg["timestamp"] > veiculos_no_raio[v_id]["timestamp"]:
        veiculos_no_raio[v_id] = reg

df_sqlite = pd.read_sql_query("""
    SELECT v.id as veiculo_id, v.placa, m.nome as motorista, m.status 
    FROM veiculos v 
    JOIN motoristas m ON v.motorista_id = m.id
""", conn_sqlite)

pipeline_ultimos = [
    {"$sort": {"timestamp": -1}},
    {"$group": {
        "_id": "$veiculo_id",
        "temperatura": {"$first": "$temperatura"},
        "velocidade": {"$first": "$velocidade"},
        "lon": {"$first": {"$arrayElemAt": ["$location.coordinates", 0]}},
        "lat": {"$first": {"$arrayElemAt": ["$location.coordinates", 1]}},
        "timestamp": {"$first": "$timestamp"}
    }}
]
dados_mongo = list(colecao_telemetria.aggregate(pipeline_ultimos))
df_mongo = pd.DataFrame(dados_mongo).rename(columns={"_id": "veiculo_id"})

if not df_mongo.empty:
    df_join = pd.merge(df_sqlite, df_mongo, on="veiculo_id", how="inner")
else:
    df_join = pd.DataFrame()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📍 Mapa de Veículos no raio de {raio_km} km")
    mapa = folium.Map(location=[lat_ref, lon_ref], zoom_start=12)
    folium.Circle(
        location=[lat_ref, lon_ref],
        radius=raio_metros,
        color='blue',
        fill=True,
        fill_opacity=0.1
    ).add_to(mapa)
    
    folium.Marker([lat_ref, lon_ref], popup="Ponto de Referência", icon=folium.Icon(color='red')).add_to(mapa)
    
    for v_id, dados in veiculos_no_raio.items():
        lon, lat = dados["location"]["coordinates"]
        info_veiculo = df_sqlite[df_sqlite["veiculo_id"] == v_id]
        placa = info_veiculo["placa"].values[0] if not info_veiculo.empty else "Desconhecida"
        
        folium.Marker(
            [lat, lon], 
            popup=f"Veículo: {placa}<br>Velocidade: {dados['velocidade']} km/h", 
            icon=folium.Icon(color='green', icon='truck', prefix='fa')
        ).add_to(mapa)
        
    st_folium(mapa, width=700, height=500)

with col2:
    st.subheader("⚠️ Alertas e KPIs")
    if not df_join.empty:
        frotas_ativas = len(df_join[df_join['status'] == 'Ativo'])
        media_temp = df_join['temperatura'].mean()
        alertas_vel = len(df_join[df_join['velocidade'] > 80])
        
        st.metric("Total Frotas Ativas", frotas_ativas)
        st.metric("Média de Temperatura (°C)", f"{media_temp:.1f}")
        st.metric("Alertas de Velocidade (> 80 km/h)", alertas_vel, delta_color="inverse")
    else:
        st.warning("Sem dados de telemetria.")

st.markdown("---")
st.subheader("📋 Visão Unificada (Transacional + Telemetria Atualizada)")
if not df_join.empty:
    st.dataframe(df_join[["motorista", "placa", "temperatura", "velocidade", "lat", "lon", "timestamp"]], use_container_width=True)

st.markdown("---")
st.subheader("📊 Análises")

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    if not df_join.empty:
        fig_status = px.pie(df_join, names='status', title="Distribuição de Status dos Motoristas", hole=0.4)
        st.plotly_chart(fig_status, use_container_width=True)

with col_graf2:
    historico_mongo = list(colecao_telemetria.find({}, {"veiculo_id": 1, "temperatura": 1, "timestamp": 1, "_id": 0}))
    df_hist = pd.DataFrame(historico_mongo)
    if not df_hist.empty:
        df_hist = pd.merge(df_hist, df_sqlite[["veiculo_id", "placa"]], on="veiculo_id")
        df_hist = df_hist.sort_values(by="timestamp")
        fig_temp = px.line(df_hist, x="timestamp", y="temperatura", color="placa", title="Histórico de Variação de Temperatura por Veículo", markers=True)
        st.plotly_chart(fig_temp, use_container_width=True)