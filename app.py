import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import fiona

# Configuração da página
st.set_page_config(page_title="Monitoramento de Rodovias", layout="wide")

st.title("Visualizador de Infraestrutura Rodoviária")
st.markdown("Dados carregados diretamente do repositório GitHub.")

# Função para carregar KML usando Geopandas
def load_kml(file_path):
    fiona.drvsupport.supported_drivers['KML'] = 'rw'
    gdf = gpd.read_file(file_path, driver='KML')
    return gdf

# Sidebar para filtros
st.sidebar.header("Configurações de Visualização")
show_pontes = st.sidebar.checkbox("Mostrar Pontes", value=True)
show_rodovia = st.sidebar.checkbox("Mostrar Rodovia", value=True)
show_poligonos = st.sidebar.checkbox("Mostrar Polígonos de Conexão", value=True)

# Criar o mapa base (Centralizado na região dos dados)
m = folium.Map(location=[-26.0, -51.0], zoom_start=8, tiles="OpenStreetMap")

# Camada: Rodovia
if show_rodovia:
    try:
        df_rodovia = load_kml("rodovia.kml")
        folium.GeoJson(df_rodovia, name="Rodovia", style_function=lambda x: {'color': 'red', 'weight': 3}).add_to(m)
    except Exception as e:
        st.error(f"Erro ao carregar rodovia.kml: {e}")

# Camada: Polígonos
if show_poligonos:
    try:
        df_pol = load_kml("poligonos_mun_conex.kml")
        folium.GeoJson(df_pol, name="Municípios", style_function=lambda x: {'fillColor': 'blue', 'color': 'blue', 'weight': 1, 'fillOpacity': 0.2}).add_to(m)
    except Exception as e:
        st.error(f"Erro ao carregar poligonos.kml: {e}")

# Camada: Pontes (Marcadores)
if show_pontes:
    try:
        df_pontes = load_kml("pontes.kml")
        for _, row in df_pontes.iterrows():
            if row.geometry.type == 'Point':
                folium.Marker(
                    location=[row.geometry.y, row.geometry.x],
                    popup=f"Ponte ID: {row.get('name', 'N/A')}",
                    icon=folium.Icon(color="orange", icon="info-sign")
                ).add_to(m)
    except Exception as e:
        st.error(f"Erro ao carregar pontes.kml: {e}")

# Exibir o mapa no Streamlit
st_folium(m, width=1200, height=600)

# Tabela de dados (Opcional)
if st.sidebar.checkbox("Ver tabela de dados das pontes"):
    st.write(df_pontes.drop(columns='geometry'))
