import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import fiona
from shapely.ops import nearest_points
from shapely.geometry import Point

# Configuração e Suporte KML
fiona.drvsupport.supported_drivers['KML'] = 'rw'
st.set_page_config(page_title="Monitoramento BR-153/PR", layout="wide")

st.title("Sistema de Consulta - BR-153/PR")

# --- FUNÇÃO DE CARREGAMENTO ---
@st.cache_data
def load_data(file):
    try:
        return gpd.read_file(file, driver='KML')
    except Exception as e:
        st.error(f"Erro ao carregar {file}: {e}")
        return None

# Carregamento das bases
df_pontes = load_data("pontes.kml")
df_rodovia = load_data("rodovia.kml")
df_pol = load_data("poligonos_mun_conex.kml")

# --- BARRA LATERAL (CONSULTA) ---
st.sidebar.header("📍 Consulta de Coordenadas")
lat_input = st.sidebar.number_input("Latitude (ex: -23.5)", format="%.6f", value=-23.000000)
lon_input = st.sidebar.number_input("Longitude (ex: -50.2)", format="%.6f", value=-50.000000)

ponto_usuario = Point(lon_input, lat_input)

if st.sidebar.button("Calcular OAE mais próxima"):
    if df_pontes is not None:
        # Encontrar ponto mais próximo
        pts_geoms = df_pontes.geometry.unary_union
        nearest_geoms = nearest_points(ponto_usuario, pts_geoms)
        distancia = nearest_geoms[0].distance(nearest_geoms[1]) * 111.139 # Conversão aproximada para km
        
        # Identificar qual ponte é
        ponte_proxima = df_pontes.iloc[df_pontes.geometry.distance(ponto_usuario).idxmin()]
        
        st.sidebar.success(f"**OAE Próxima:** {ponte_proxima['name']}")
        st.sidebar.info(f"**Distância:** {distancia:.2f} km")
    else:
        st.sidebar.error("Base de pontes não carregada.")

# --- MAPA ---
m = folium.Map(location=[lat_input, lon_input], zoom_start=8)

# Adicionar ponto da consulta no mapa
folium.Marker([lat_input, lon_input], tooltip="Sua Consulta", icon=folium.Icon(color='red', icon='screenshot')).add_to(m)

if df_rodovia is not None:
    folium.GeoJson(df_rodovia, name="Rodovia", style_function=lambda x: {'color': 'orange'}).add_to(m)

if df_pontes is not None:
    for _, row in df_pontes.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=5,
            popup=f"OAE: {row['name']}",
            color="blue",
            fill=True
        ).add_to(m)

# Renderizar Mapa
st_folium(m, width=1000, height=500)

# --- TABELA DE DADOS (CORREÇÃO DO ERRO) ---
st.subheader("Dados das OAEs (Pontes)")
if df_pontes is not None:
    # Removemos a coluna geometry apenas para exibição na tabela
    display_df = df_pontes.copy()
    if 'geometry' in display_df.columns:
        display_df = display_df.drop(columns=['geometry'])
    st.dataframe(display_df)
else:
    st.warning("Dados das pontes indisponíveis para exibição.")
