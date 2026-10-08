import pandas as pd
import re
from IPython.display import display, clear_output

# ID de tu Google Sheet detectado en tu Google Drive
file_id = '1fm8nsliBRwTKnCQyiHxmFTMVUV2rX01RjgGCA1r-KPI'
enlace_sheets_csv = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv"

df = None

try:
    df = pd.read_csv(enlace_sheets_csv)
    print("🟢 ¡CONEXIÓN EXITOSA! Tu diccionario se cargó en tiempo real desde Google Sheets.")
except Exception as e:
    print(f"🔴 Error de conexión directa: {e}")
    print("Intentando cargar la base de datos de manera local desde tu Google Drive montado...")
    try:
        df = pd.read_excel('/content/drive/MyDrive/diccionario_teenek.xlsx')
        print("🟢 ¡ÉXITO! Cargado desde el archivo de respaldo en Google Drive.")
    except Exception as e_drive:
        print(f"🔴 No se pudo cargar el respaldo: {e_drive}")

# --- FUNCIÓN DE LIMPIEZA LINGÜÍSTICA ---
def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().lower()
    # Eliminar acentos en español para búsquedas más flexibles
    texto = re.sub(r"[áàäâ]", "a", texto)
    texto = re.sub(r"[éèëê]", "e", texto)
    texto = re.sub(r"[íìïî]", "i", texto)
    texto = re.sub(r"[óòöô]", "o", texto)
    texto = re.sub(r"[úùüû]", "u", texto)
    # Cambia saltillos curvos o acentos graves por apóstrofe recto estándar
    texto = re.sub(r"[’‘`´]", "'", texto)
    return texto

def buscar_en_diccionario(palabra_usuario):
    if df is None:
        return "❌ Error: No se ha podido cargar la base de datos del diccionario."

    # Determinar dinámicamente el nombre de la columna en español
    col_esp = 'Español' if 'Español' in df.columns else ('Espanol' if 'Espanol' in df.columns else None)
    if 'Palabra_Teenek' not in df.columns or not col_esp:
        return "❌ Error: Asegúrate de que existan las columnas 'Palabra_Teenek' y 'Español' en tu documento."

    # 1. Normalizar la entrada del usuario
    palabra_limpia = normalizar_texto(palabra_usuario)

    # Preparar columnas normalizadas en segundo plano (No alteran tu Excel original)
    df['Palabra_Teenek_Lower'] = df['Palabra_Teenek'].apply(normalizar_texto)
    df['Español_Lower'] = df[col_esp].apply(normalizar_texto)
    df['Raiz_Lower'] = df['Raiz'].apply(normalizar_texto) if 'Raiz' in df.columns else ""

    # 2. Catálogo de prefijos Teenek configurables
    prefijos_teenek = ["ka-", "ka", "u-", "in-"] 
    palabras_a_buscar = [palabra_limpia]
    
    for prefijo in prefijos_teenek:
        if palabra_limpia.startswith(prefijo):
            sin_prefijo = palabra_limpia[len(prefijo):].strip()
            if sin_prefijo and sin_prefijo not in palabras_a_buscar:
                palabras_a_buscar.append(sin_prefijo)
            break

    # ==========================================
    # RUTA A: BÚSQUEDA EN TEENEK (Exacta)
    # ==========================================
    resultado_exacto = pd.DataFrame()
    for p in palabras_a_buscar:
        resultado_exacto = df[df['Palabra_Teenek_Lower'] == p]
        if not resultado_exacto.empty:
            break

    if not resultado_exacto.empty:
        fila = resultado_exacto.iloc[0]
        clase = fila.get('Clase_Gramatical', 'Desconocida')
        significado = fila.get(col_esp, 'Sin traducción')
        raiz = fila.get('Raiz', '')
        es_derivado = str(fila.get('Es_Derivado', 'No')).strip().lower()

        if es_derivado in ["sí", "si", "yes", "true", "1"] and pd.notna(raiz):
            raiz_normalizada = normalizar_texto(raiz)
            info_raiz = df[df['Palabra_Teenek_Lower'] == raiz_normalizada]
            sig_raiz = info_raiz.iloc[0].get(col_esp, 'Desconocido') if not info_raiz.empty else "No registrada como palabra exenta"
            
            return (f"📖 Coincidencia exacta Teenek: '{fila['Palabra_Teenek']}'\n"
                    f"👉 Es una forma derivada ({clase}).\n"
                    f"🔗 Raíz morfológica (CVC): '{raiz}' (Significado raíz: {sig_raiz}).\n"
                    f"📝 Significado de esta forma: {significado}.")
        else:
            return f"📖 Coincidencia exacta Teenek: '{fila['Palabra_Teenek']}' es una raíz pura o forma base ({clase}): {significado}."

    # ==========================================
    # RUTA B: MODO INVESTIGADOR TEENEK (Aproximación)
    # ==========================================
    termino_busqueda = palabras_a_buscar[-1]
    coincidencias_teenek = df[
        df['Palabra_Teenek_Lower'].str.contains(termino_busqueda, na=False, regex=False) | 
        df['Raiz_Lower'].str.contains(termino_busqueda, na=False, regex=False)
    ]

    # Si encontramos resultados por fragmento morfológico Teenek, los priorizamos
    if not coincidencias_teenek.empty and len(termino_busqueda) > 2:
        reporte = [f"🔍 Hallé {len(coincidencias_teenek)} formas Teenek asociadas a la raíz/patrón '{termino_busqueda}':"]
        for idx, fila in coincidencias_teenek.iterrows():
            raiz_info = f" [Raíz: {fila['Raiz']}]" if pd.notna(fila['Raiz']) else ""
            traduccion = fila[col_esp] if pd.notna(fila[col_esp]) else "Sin traducción"
            reporte.append(f"  • {fila['Palabra_Teenek']} ({fila.get('Clase_Gramatical', 'Desconocida')}){raiz_info} ➔ {traduccion}")
        return "\n".join(reporte)

    # ==========================================
    # RUTA C: BÚSQUEDA INVERSA (En Español)
    # ==========================================
    # Buscamos filas donde la columna de Español contenga la palabra ingresada
    coincidencias_espanol = df[df['Español_Lower'].str.contains(palabra_limpia, na=False, regex=False)]

    if not coincidencias_espanol.empty:
        reporte = [f"🇪🇸 Equivalencias encontradas para la búsqueda en español '{palabra_usuario}':"]
        for idx, fila in coincidencias_espanol.iterrows():
            raiz_info = f" (Raíz CVC: {fila['Raiz']})" if pd.notna(fila['Raiz']) else " (Raíz pura)"
            reporte.append(f"  • {fila['Palabra_Teenek']} [{fila.get('Clase_Gramatical', 'Desconocida')}] {raiz_info} ➔ {fila[col_esp]}")
        return "\n".join(reporte)

    return f"❌ El término, raíz o traducción '{palabra_usuario}' no generó ninguna coincidencia en el corpus."
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
