import os
import streamlit as st
from pymongo import MongoClient

@st.cache_resource
def get_database():
    # Railway inyecta de forma nativa las variables del sistema
    mongo_url = os.environ.get("MONGO_URL") or st.secrets.get("MONGO_URL")
    
    if not mongo_url:
        st.error("Error de configuración: La variable MONGO_URL no está definida.")
        return None
        
    try:
        client = MongoClient(mongo_url)
        # Retorna la base de datos compartida para el acopio
        return client["cac_valleverde"]
    except Exception as e:
        st.error(f"Error al conectar con MongoDB: {e}")
        return None