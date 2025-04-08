import streamlit as st
import pandas as pd
import re
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# Autenticación
authenticator = stauth.Authenticate('config.yaml')

try:
    authenticator.login(location="main")
except Exception as e:
    st.error(f"Error de autenticación: {e}")

if st.session_state['authentication_status']:
    authenticator.logout()
    st.write(f'Welcome *{st.session_state["name"]}*')
    
    # Título
    st.title("🔍 Buscador de Palabras Clave ICC1 CNX")

    # URL del archivo
    archivo = 'https://raw.githubusercontent.com/giraggio/icc1cnx/refs/heads/main/textos_con_mammoth.csv'

    # Inicializar variable de estado
    if 'buscar' not in st.session_state:
        st.session_state['buscar'] = False
    if 'resultados_df' not in st.session_state:
        st.session_state['resultados_df'] = pd.DataFrame()
    if 'palabras_clave_input' not in st.session_state:
        st.session_state['palabras_clave_input'] = ""

    # Input de palabras clave
    palabras_input = st.text_area("Escribe las palabras o frases clave separadas por coma", "sitio prioritario, zona protegida")
    palabras_clave = [p.strip().lower() for p in palabras_input.split(",") if p.strip()]

    if st.button("Buscar"):
        st.session_state['buscar'] = True
        st.session_state['palabras_clave_input'] = palabras_input

        # Cargar CSV
        df = pd.read_csv(archivo)

        # Filtrar por palabras clave
        palabras_regex = "|".join([re.escape(p) for p in palabras_clave])
        df["texto"] = df["texto"].astype(str).str.lower()
        coincidencias = df[df["texto"].str.contains(palabras_regex, na=False, regex=True)]

        if not coincidencias.empty:
            resultados_df = coincidencias[["texto", "nombre_archivo"]].copy()
            resultados_df["Palabra Clave"] = resultados_df["texto"].apply(
                lambda texto: ", ".join([p for p in palabras_clave if p in texto])
            )
            resultados_df["Archivo"] = resultados_df["nombre_archivo"]

            st.session_state['resultados_df'] = resultados_df
        else:
            st.session_state['resultados_df'] = pd.DataFrame()
            st.warning("No se encontraron coincidencias.")

    # Mostrar resultados si ya se hizo la búsqueda
    if st.session_state['buscar'] and not st.session_state['resultados_df'].empty:
        st.success(f"Se encontraron coincidencias en {len(st.session_state['resultados_df'])} archivos.")

        resultados_df = st.session_state['resultados_df']
        palabras_unicas = sorted(resultados_df["Palabra Clave"].unique())
        palabra_seleccionada = st.selectbox("Filtrar por Palabra Clave", ["Todas"] + palabras_unicas)

        if palabra_seleccionada != "Todas":
            df_filtrado = resultados_df[resultados_df["Palabra Clave"] == palabra_seleccionada]
        else:
            df_filtrado = resultados_df

        st.dataframe(df_filtrado[["Palabra Clave", "Archivo"]])

        # if st.button("🔁 Nueva búsqueda"):
        #     st.session_state['buscar'] = False
        #     st.session_state['resultados_df'] = pd.DataFrame()
        #     st.experimental_rerun()

elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')
elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')
