import streamlit as st
import pandas as pd
import os

CSV_FILE = "participantes.csv"

st.set_page_config(page_title="REGISTRO AL EVENTO", page_icon="📈", layout="centered")

# Función para verificar si el email ya está registrado
def email_existe(email):
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        return email in df["Email"].values
    return False

# Inicializar variables en la sesión de Streamlit
if "registro_exitoso" not in st.session_state:
    st.session_state.registro_exitoso = False
    st.session_state.nombre = ""
    st.session_state.email = ""
    st.session_state.intereses = []

# Si el usuario ya se registró, mostrar solo el resumen
if st.session_state.registro_exitoso:
    st.title("✅ Registro confirmado")
    st.subheader("🎉 ¡Gracias por registrarte en el evento!")
    st.write("Aquí tienes un resumen de tu registro:")
    
    # Mostrar datos registrados
    st.write(f"**📛 Nombre:** {st.session_state.nombre}")
    st.write(f"**📧 Email:** {st.session_state.email}")
    st.write(f"**🌟 Intereses:** {', '.join(st.session_state.intereses)}")

    st.success("¡Nos vemos en el evento! 🚀")
    
    # Botón para permitir otro registro
    if st.button("🔙 Registrar otro participante"):
        st.session_state.registro_exitoso = False
        st.session_state.nombre = ""
        st.session_state.email = ""
        st.session_state.intereses = []
        st.rerun() 

# Si aún no se ha registrado, mostrar el formulario
else:
    st.title("📈 Registro al evento")
    st.write("Por favor, completa el formulario para participar en el evento.")

    # Entrada de datos
    nombre = st.text_input("✍️ Nombre", placeholder="Ingresa tu nombre aquí")
    email = st.text_input("📧 Correo electrónico", placeholder="ejemplo@correo.com")

    # Lista de intereses
    intereses_lista = [
        "Startups",
        "Mercados y bolsa",
        "Capital de riesgo",
        "Blockchain y cripto",
        "IA en Finanzas",
        "Inversión en bienes raíces",
        "Fintech",
        "Criptomonedas",
        "Growth Hacking",
        "Fondos de Inversión",
        "Networking de inversores",
        "Inversiones sostenibles"
    ]

    # Selección múltiple de intereses con límite
    intereses_seleccionados = st.multiselect("🌟 Selecciona entre 3 y 5 intereses", intereses_lista)

    # Mostrar alerta si selecciona menos de 3 o más de 5
    if len(intereses_seleccionados) < 3:
        st.warning("⚠️ Debes seleccionar al menos **3 intereses**.")
    elif len(intereses_seleccionados) > 5:
        st.warning("⚠️ Solo puedes seleccionar **hasta 5 intereses**. Elige los más relevantes.")

    # Envío
    if st.button("📩 Enviar registro"):
        if nombre and email and 3 <= len(intereses_seleccionados) <= 5:
            if email_existe(email):
                st.error("❌ Este correo electrónico ya está registrado. Usa otro email.")
            else:
                # Convertir intereses a formato binario (0 o 1)
                intereses_dict = {interes: 1 if interes in intereses_seleccionados else 0 for interes in intereses_lista}
                nuevo_registro = pd.DataFrame([{**{"Nombre": nombre, "Email": email}, **intereses_dict}])

                # Guardar en CSV
                if not os.path.exists(CSV_FILE):
                    nuevo_registro.to_csv(CSV_FILE, index=False)
                else:
                    nuevo_registro.to_csv(CSV_FILE, mode="a", header=False, index=False)

                # Guardar datos en la sesión para mostrar el resumen
                st.session_state.registro_exitoso = True
                st.session_state.nombre = nombre
                st.session_state.email = email
                st.session_state.intereses = intereses_seleccionados

                # Recargar la página para ocultar el formulario y mostrar el resumen
                st.rerun()
        else:
            st.error("❌ Por favor, completa todos los campos y selecciona entre **3 y 5 intereses** antes de enviar.")
