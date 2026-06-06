import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Importamos directamente la colección desde tu nuevo database.py
from database import col_acopios

st.set_page_config(page_title="Dashboard Administrativo", page_icon="📊", layout="wide")

# 1. Guardián de seguridad: Solo Administradores
if not st.session_state.get("autenticado") or st.session_state.get("rol") != "Administrador":
    st.error("Acceso denegado. Por favor, inicie sesión desde la página principal.")
    st.stop()

# 2. Función de carga de datos con caché y aplanamiento de JSON
@st.cache_data(ttl=60) # Caché de 60 segundos por si acaso
def load_analytics_data():
    # Extraemos todos los documentos de la colección acopios
    raw_data = list(col_acopios.find())
    current_time = datetime.now()
    
    if raw_data:
        # pd.json_normalize aplana cualquier JSON anidado o semiestructurado que envíe Databricks
        df = pd.json_normalize(raw_data)
        # Convertimos el ObjectId de Mongo a string para que no de error al graficar
        if '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)
        return df, current_time
        
    return pd.DataFrame(), current_time

# 3. Interfaz del Panel
st.title("📊 Panel de Análisis Operativo - CAC Valle Verde")
st.write(f"Bienvenido, **{st.session_state.get('nombre', 'Administrador')}**.")

# 4. Requerimiento: Botón de actualización y Etiqueta de Timestamp
col_btn, col_time = st.columns([1, 3])

with col_btn:
    # Al presionar, limpiamos la memoria y forzamos la recarga (útil para el Job de Databricks)
    if st.button("🔄 Actualizar Datos Ahora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Cargamos los datos
df_acopio, last_update = load_analytics_data()

with col_time:
    st.info(f"**Última actualización de datos:** {last_update.strftime('%d/%m/%Y %H:%M:%S')}")

st.markdown("---")

# 5. Renderizado de Gráficos y Tablas
if not df_acopio.empty:
    
    # KPIs Dinámicos (Usamos .get para no romper la app si Databricks aún no envía estos campos exactos)
    total_registros = len(df_acopio)
    total_peso = df_acopio.get('peso_neto', pd.Series([0])).sum()
    promedio_humedad = df_acopio.get('humedad', pd.Series([0])).mean()

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Lotes Recibidos", f"{total_registros} u")
    kpi2.metric("Volumen Total", f"{total_peso:,.2f} Kg")
    kpi3.metric("Promedio Humedad", f"{promedio_humedad:.2f} %")

    # Requerimiento: Área de Tablas Estructuradas
    st.subheader("📋 Registro Consolidado")
    st.dataframe(df_acopio, use_container_width=True)

    # Requerimiento: Área de Análisis Gráfico
    st.subheader("📈 Análisis Visual")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        # Gráfico de tendencias (si existe la columna fecha)
        if 'fecha' in df_acopio.columns and 'peso_neto' in df_acopio.columns:
            fig_line = px.line(df_acopio, x='fecha', y='peso_neto', title="Tendencia de Pesaje Neto", markers=True)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("Esperando datos de 'fecha' y 'peso_neto' para el gráfico de líneas.")

    with col_g2:
        # Histograma de calidad/humedad
        if 'humedad' in df_acopio.columns:
            fig_hist = px.histogram(df_acopio, x='humedad', nbins=10, title="Distribución de Humedad", color_discrete_sequence=['#2E7D32'])
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.warning("Esperando datos de 'humedad' para generar gráfico.")
else:
    st.info("ℹ️ La colección de acopios está vacía. Esperando la ingesta de datos desde Databricks...")