import streamlit as st
import pandas as pd
from datetime import datetime
from database import col_acopios

st.set_page_config(page_title="Dashboard Administrativo", page_icon="📊", layout="wide")

# =========================
# GUARDIÁN DE SEGURIDAD
# =========================
if not st.session_state.get("autenticado") or st.session_state.get("rol") != "Administrador":
    st.warning("⚠️ Acceso denegado. Por favor, inicia sesión como Administrador en la página principal.")
    st.stop()

# =========================
# FUNCIÓN DE CARGA (REQUERIMIENTO CLOUD)
# =========================
@st.cache_data(ttl=60)
def load_analytics_data():
    cursor = col_acopios.find({}, {"_id": 0})
    datos_lista = list(cursor)
    current_time = datetime.now()
    
    if not datos_lista:
        return pd.DataFrame(), current_time

    # Convertir JSON anidado a DataFrame plano
    df = pd.json_normalize(datos_lista)

    # Convertir fecha si existe
    if 'fecha_registro' in df.columns:
        df['fecha_registro'] = pd.to_datetime(df['fecha_registro'])

    # Renombrar columnas según tu estructura original
    # Usamos errors='ignore' por si Databricks envía un lote incompleto temporalmente
    df = df.rename(columns={
        'agricultor.nombre_completo': 'Agricultor',
        'agricultor.sector_comunidad': 'Sector',
        'agricultor.tipo_cacao': 'Tipo de Cacao',
        'datos_pesaje.peso_neto_total_kg': 'Peso Neto (Kg)',
        'control_calidad.estado_lote': 'Estado',
        'valores_comerciales.monto_total_pagar': 'Monto Total (S/.)'
    }, errors='ignore')
    
    return df, current_time

# =========================
# TÍTULO Y CONTROLES DE ACTUALIZACIÓN
# =========================
st.title("📊 Dashboard Administrativo")
st.markdown("Panel gerencial para monitoreo de inventario, calidad y pagos.")

# Requerimiento: Botón y Timestamp
col_btn, col_time = st.columns([1, 3])

with col_btn:
    if st.button("🔄 Actualizar Datos Ahora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Extraer datos procesados
df, last_update = load_analytics_data()

with col_time:
    st.info(f"**Última actualización:** {last_update.strftime('%d/%m/%Y %H:%M:%S')} (Sincronizado con Databricks)")

st.divider()

if df.empty:
    st.warning("No hay datos de acopio registrados aún. Esperando ingesta del Job...")
    st.stop()

# =========================
# KPIs
# =========================
# Usamos .get() con un fallback a 0 por seguridad si la columna falta
total_kg = df.get('Peso Neto (Kg)', pd.Series([0])).sum()
total_pago = df.get('Monto Total (S/.)', pd.Series([0])).sum()
total_registros = len(df)
lotes_observados = (df.get('Estado', pd.Series([''])) != "Aprobado").sum()

col1, col2, col3, col4 = st.columns(4)

col1.metric("🌱 Kg Acopiados", f"{total_kg:,.2f} kg")
col2.metric("💰 Pagos Totales", f"S/ {total_pago:,.2f}")
col3.metric("📦 Registros", total_registros)
col4.metric("⚠️ Lotes Observados", lotes_observados)

st.divider()

# =========================
# GRÁFICOS
# =========================
col_g1, col_g2, col_g3 = st.columns(3)

with col_g1:
    st.subheader("📌 Acopio por Sector")
    if 'Sector' in df.columns and 'Peso Neto (Kg)' in df.columns:
        sector_chart = df.groupby('Sector')['Peso Neto (Kg)'].sum()
        st.bar_chart(sector_chart)

with col_g2:
    st.subheader("📌 Estado de Calidad")
    if 'Estado' in df.columns:
        estado_chart = df['Estado'].value_counts()
        st.bar_chart(estado_chart)

with col_g3:
    st.subheader("📌 Tipo de Cacao")
    if 'Tipo de Cacao' in df.columns:
        tipo_chart = df['Tipo de Cacao'].value_counts()
        st.bar_chart(tipo_chart)

st.divider()

# =========================
# TABLA
# =========================
st.subheader("📋 Registros de Acopio")

# Filtramos solo las columnas que realmente existen en el DataFrame
columnas_deseadas = [
    'fecha_registro', 'Agricultor', 'Sector', 'Tipo de Cacao', 
    'Peso Neto (Kg)', 'Estado', 'Monto Total (S/.)'
]
columnas_finales = [col for col in columnas_deseadas if col in df.columns]

st.dataframe(df[columnas_finales], use_container_width=True)