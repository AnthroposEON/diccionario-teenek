# ==========================================
# INTERFAZ WEB CON STREAMLIT
# ==========================================
import streamlit as st

st.set_page_config(page_title="Diccionario Teenek", page_icon="📖", layout="centered")

st.title("🖥️ Buscador Morfológico Teenek v1.0")
st.markdown("Herramienta de investigación lingüística y análisis de campo para raíces CVC y formas derivadas.")

# Caja de texto interactiva de Streamlit
busqueda = st.text_input("Ingresa una palabra, raíz CVC o traducción en español:", placeholder="ej. ka-tsemdha'")

if busqueda:
    with st.spinner("Analizando morfología..."):
        resultado = buscar_en_diccionario(busqueda)
        
        # Si el resultado empieza con una equis o advertencia, lo pintamos diferente
        if "❌" in resultado or "⚠️" in resultado:
            st.warning(resultado)
        else:
            st.info(resultado)
