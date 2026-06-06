import streamlit as st
from database import col_usuarios

# 1. Configuración principal de la página (Debe ser la primera línea)
st.set_page_config(page_title="LogiStock Cacao - Login Admin", page_icon="🍫", layout="centered")

# 2. Función para crear el usuario demo si la colección está vacía
def inicializar_usuarios_demo():
    if col_usuarios.count_documents({}) == 0:
        usuarios_demo = [
            {
                "email": "admin@valleverde.com",
                "password": "admin",
                "rol": "Administrador",
                "nombre": "Gerencia General",
                "operario_id": "admin_01"
            }
        ]
        col_usuarios.insert_many(usuarios_demo)

# Ejecutamos la validación inicial
inicializar_usuarios_demo()

# 3. Diseño de la interfaz de Login
st.title("🍫 Sistema LogiStock Cacao")
st.subheader("Acceso Exclusivo - Administración")

# Panel de ayuda para la exposición (Credenciales a la vista)
with st.expander("ℹ️ Credenciales de Acceso (Modo Demo)", expanded=True):
    st.markdown("""
    **Vista Administrador (Dashboard KPIs / Ingesta de Datos):**
    * **Email:** admin@valleverde.com
    * **Clave:** admin
    """)

# 4. Lógica del formulario de Login
# Usamos st.form para que la página no se recargue innecesariamente
with st.form("login_form"):
    email_input = st.text_input("Correo Electrónico")
    password_input = st.text_input("Contraseña", type="password")
    submit_button = st.form_submit_button("Ingresar")

    if submit_button:
        # Buscar el usuario en MongoDB exigiendo que el rol sea Administrador
        usuario = col_usuarios.find_one({
            "email": email_input, 
            "password": password_input,
            "rol": "Administrador"
        })
        
        if usuario:
            # 1. Guardamos sus datos en la sesión
            st.session_state["autenticado"] = True
            st.session_state["rol"] = usuario["rol"]
            st.session_state["nombre"] = usuario["nombre"]
            st.session_state["operario_id"] = usuario["operario_id"]
            
            # 2. Mostramos mensaje de éxito breve
            st.success(f"¡Bienvenido {usuario['nombre']}! Redirigiendo al Dashboard...")
            
            # 3. REDIRECCIÓN AUTOMÁTICA ÚNICA AL DASHBOARD
            st.switch_page("pages/2_Dashboard.py")
                
        else:
            st.error("Credenciales incorrectas o no posee permisos de Administrador.")

# 5. Mostrar información de sesión activa (Opcional, para feedback visual)
if st.session_state.get("autenticado"):
    st.info(f"🟢 Sesión iniciada como: **{st.session_state['rol']}**")
    if st.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()