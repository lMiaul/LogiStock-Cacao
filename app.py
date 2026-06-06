import streamlit as st
from database import get_database

st.set_page_config(page_title="LogiStock - Acceso", page_icon="🔒")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

st.title("🔑 LogiStock Cacao - Control de Acceso")
st.write("Ingrese sus credenciales de administrador para acceder al panel de analítica.")

username = st.text_input("Usuario institucional")
password = st.text_input("Contraseña", type="password")

if st.button("Iniciar Sesión", use_container_width=True):
    db = get_database()
    if db is not None:
        # Validación directa contra la colección de usuarios
        user_doc = db["usuarios"].find_one({
            "username": username, 
            "password": password, 
            "role": "Administrador"
        })
        
        if user_doc:
            st.session_state.logged_in = True
            st.session_state.role = "Administrador"
            st.success("Autenticación exitosa. Redirigiendo...")
            st.switch_page("pages/1_Dashboard.py")
        else:
            st.error("Credenciales incorrectas o el usuario no posee el rol de Administrador.")