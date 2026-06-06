import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_database
from datetime import datetime

st.set_page_config(page_title="Dashboard Administrativo", page_icon="📊", layout="wide")

# Guardián de seguridad en ruta protegida
if not st.session_state.get("logged_in") or st.session_state.get("role") != "Administrador":
    st.error("Acceso denegado. Por favor, inicie sesión desde la página principal.")
    st.stop()

db = get_database()

# Función de carga con cache controlable por TTL y limpieza explícita
@st.cache_data(ttl=60)
def load_analytics_data():
    if db is None:
        return pd.DataFrame(), datetime.now()
        
    collection = db["acopio"]
    # Se extraen todos los registros (datos semiestructurados de los JSON recibidos)
    raw_data = list(collection.find())
    
    current_time = datetime.now()
    if raw_data:
        # pd.json_normalize aplana estructuras complejas/anidadas para Pandas
        df = pd.json_normalize(raw_data)
        return df, current_time
    return pd.DataFrame(), current_time

# Interfaz del Panel
st.title("📊 Panel de Análisis Operativo - CAC Valle Verde")

# Fila de control: Botón de actualización y etiqueta de marca de tiempo (Timestamp)
col_btn, col_time = st.columns([1, 3])

with col_btn:
    # Al presionar el botón, se limpia la caché específica y se recarga la vista
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Carga de datos procesados
df_acopio, last_update = load_analytics_data()

with col_time:
    st.info(f"**Última actualización del sistema:** {last_update.strftime('%d/%m/%Y %H:%M:%S')}")

st.markdown("---")

# Visualización de KPIs y Tablas
if not df_acopio.empty:
    # Métricas principales
    total_registros = len(df_acopio)
    
    # Manejo dinámico por si Databricks inyecta esquemas nuevos o campos nulos
    total_peso = df_acopio['peso_neto'].sum() if 'peso_neto' in df_acopio.columns else 0.0
    promedio_humedad = df_acopio['humedad'].mean() if 'humedad' in df_acopio.columns else 0.0

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Lotes Recibidos", f"{total_registros} u")
    kpi2.metric("Volumen Total Acopiado", f"{total_peso:,.2f} Kg")
    kpi3.metric("Promedio Humedad de Grano", f"{promedio_humedad:.2f} %")

    # Área de Tablas Estructuradas
    st.subheader("📋 Registro Consolidado de Datos")
    # Remover columna interna de MongoDB para visualización limpia si existe
    display_df = df_acopio.drop(columns=['_id'], errors='ignore')
    st.dataframe(display_df, use_container_width=True)

    # Área de Gráficas de Análisis
    st.subheader("📈 Comportamiento de Variables en Tiempo Real")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        if 'fecha' in df_acopio.columns and 'peso_neto' in df_acopio.columns:
            fig_line = px.line(df_acopio, x='fecha', y='peso_neto', title="Tendencia de Pesaje Neto Ingresado")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("Datos insuficientes para generar gráfico de líneas.")

    with col_g2:
        if 'humedad' in df_acopio.columns:
            fig_hist = px.histogram(df_acopio, x='humedad', nbins=10, title="Distribución del Porcentaje de Humedad", color_discrete_sequence=['#2E7D32'])
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.warning("Datos insuficientes para generar histograma de calidad.")
else:
    st.warning("La base de datos se encuentra vacía o en estado de 'Cold Start'. Esperando la primera ejecución de datos desde Databricks.")