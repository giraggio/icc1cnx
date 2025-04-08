import streamlit as st
import pandas as pd

st.title("🔍 Buscador de Palabras Clave ICC1 CNX")


# 📂 URLs de los archivos
archivo = 'https://raw.githubusercontent.com/giraggio/icc1cnx/refs/heads/main/textos_con_mammoth.csv'

palabras_input = st.text_area(f"Escribe las palabras o frases clave separadas por coma", "sitio prioritario, zona protegida")
palabras_clave = [p.strip().lower() for p in palabras_input.split(",") if p.strip()]

if st.button("Buscar"):
    # Cargar CSV según la opción seleccionada
    df = pd.read_csv(archivo)

    # Combinar palabras clave en una expresión regular
    palabras_regex = "|".join([f"\\b{p}\\b" for p in palabras_clave])

    # Filtrar filas que contienen alguna palabra clave
    df["texto"] = df["texto"].astype(str).str.lower()
    coincidencias = df[df["texto"].str.contains(palabras_regex, na=False, regex=True)]

    if not coincidencias.empty:
        st.success(f"Se encontraron coincidencias en {len(coincidencias)} archivos.")
        resultados_df = coincidencias[["texto", "nombre_archivo"]].copy()
        resultados_df["Palabra Clave"] = resultados_df["texto"].apply(
            lambda texto: ", ".join([p for p in palabras_clave if p in texto])
        )

        # Hacer clickeables las URLs
        resultados_df["Archivo"] = resultados_df["nombre_archivo"]
        # Mostrar la tabla con HTML
        st.dataframe(resultados_df[["Palabra Clave", "Archivo"]])
    else:
        st.warning("No se encontraron coincidencias.")
