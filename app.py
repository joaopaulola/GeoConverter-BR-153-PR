import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import fiona
from shapely.ops import nearest_points
from shapely.geometry import Point
from geopy.distance import geodesic

# Habilitar KML
fiona.drvsupport.supported_drivers['KML'] = 'rw'

st.set_page_config(page_title="Monitoramento BR-153/PR", layout="wide")

st.title("Sistema de Consulta Geográfica - BR-153/PR")

# --- FUNÇÃO DE CARREGAMENTO ---
@st.cache_data
def load_data(file):
    try:
        df = gpd.read_file(file, driver='KML')
        return df
    except Exception as e:
        return None

# Carregamento das bases
df_pontes = load_data("pontes.kml")
df_rodovia = load_data("rodovia.kml")
df_pol = load_data("poligonos_mun_conex.kml")

# --- LÓGICA DE CONSULTA ---
st.sidebar.header("📍 Localizar OAE mais próxima")
lat_input = st.sidebar.number_input("Digite a Latitude", format="%.6f", value=-23.5000)
lon_input = st.sidebar.number_input("Digite a Longitude", format="%.6f", value=-50.5000)

if st.sidebar.button("Calcular Distância"):
    if df_pontes is not None:
        ponto_usuario = Point(lon_input, lat_input)
        
        # Encontrar a geometria mais próxima
        pts_geoms = df_pontes.geometry.unary_union
        ponto_proximo_geom = nearest_points(ponto_usuario, pts_geoms)[1]
        
        # Calcular distância real (Haversine) em km
        coord_usuario = (lat_input, lon_input)
        coord_ponte = (ponto_proximo_geom.y, ponto_proximo_geom.x)
        distancia_km = geodesic(coord_usuario, coord_ponte).kilometers
        
        # Localizar a linha correspondente no dataframe
        idx_proximo = df_pontes.geometry.distance(ponto_usuario).idxmin()
        ponte_dados = df_pontes.iloc[idx_proximo]
        
        # Tentar identificar o nome da ponte (várias possibilidades de colunas)
        nome_oae = "Não identificado"
        for col in ['name', 'Name', 'ID_N_S_OAE', 'ID']:
            if col in ponte_dados and ponte_dados[col]:
                nome_oae = ponte_dados[col]
                break
        
        st.sidebar.success(f"**OAE Próxima:** {nome_oae}")
        st.sidebar.info(f"**Distância:** {distancia_km:.3f} km")
        
        # Atualizar centro do mapa para o resultado
        map_center = [lat_input, lon_input]
    else:
        st.sidebar.error("Base de dados de pontes não carregada.")
        map_center = [-24.0, -50.5]
else:
    map_center = [-24.0, -50.5]

# --- MAPA INTERATIVO ---
m = folium.Map(location=map_center, zoom_start=9)

# Adicionar Marcador do Usuário
folium.Marker([lat_input, lon_input], tooltip="Sua Posição", icon=folium.Icon(color='red')).add_to(m)

# Camadas KML
if df_rodovia is not None:
    folium.GeoJson(df_rodovia, name="Rodovia BR-153", style_function=lambda x: {'color': 'black', 'weight': 2}).add_to(m)

if df_pol is not None:
    folium.GeoJson(df_pol, name="Municípios", style_function=lambda x: {'fillColor': 'green', 'fillOpacity': 0.1, 'weight': 1}).add_to(m)

if df_pontes is not None:
    for _, row in df_pontes.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=4,
            color="blue",
            popup=f"OAE: {row.get('Name', row.get('name', 'Ponte'))}"
        ).add_to(m)

st_folium(m, width=1100, height=550)

# --- TABELA DE DADOS ---
with st.expander("Ver base de dados completa (OAEs)"):
    if df_pontes is not None:
        st.dataframe(df_pontes.drop(columns='geometry', errors='ignore'))
