import streamlit as st
import pandas as pd
import re
import unicodedata

# ----------------- Funciones auxiliares ------------------

def normalizar(s: str) -> str:
    """Convierte texto a minúsculas y elimina acentos/tildes."""
    return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()

def construir_patron(frase: str) -> re.Pattern:
    """
    Crea una expresión regular que:
    - tolere saltos de línea entre palabras
    - busque palabras completas (evita coincidencias parciales)
    """
    expr = re.escape(frase.strip())
    expr = expr.replace(r'\ ', r'\s+')
    return re.compile(rf'\b{expr}\b', re.IGNORECASE | re.MULTILINE)

def tiene_coincidencia(texto: str, patrones: dict) -> list[str]:
    """Devuelve la lista de frases que aparecen en el texto normalizado."""
    return [frase for frase, patron in patrones.items() if patron.search(texto)]

@st.cache_data(show_spinner=False)
def cargar_csv(url: str) -> pd.DataFrame:
    return pd.read_csv(url, dtype={"Número Observación": str})

# ----------------- Streamlit App -------------------------

st.set_page_config(page_title="Buscador ICC1 CNX", layout="wide")
st.title("🔍 Buscador de Palabras Clave ICC1 CNX")

# ---- Selector de base de datos ----
st.subheader("Fuente de datos")
opcion_base = st.selectbox("Elegir base a consultar", ["AC", "ICE"], index=0)

URL_AC = "https://raw.githubusercontent.com/giraggio/icc1cnx/refs/heads/main/textos_con_mammoth.csv"
url_ice = "https://github.com/giraggio/icc1cnx/raw/refs/heads/main/icc1_platform.csv"

if opcion_base == "AC":
    archivo = URL_AC
    
else:
    url_ice = st.text_input("Pega aquí el URL CSV de la base **ICE**", value="", placeholder="https://...")
    archivo = url_ice.strip()
    

st.divider()

# Inputs y estados
if 'buscar' not in st.session_state:
    st.session_state['buscar'] = False
if 'resultados_df' not in st.session_state:
    st.session_state['resultados_df'] = pd.DataFrame()

# Entrada de palabras clave
palabras_input = st.text_area(
    "Escribe las palabras o frases clave separadas por coma",
    "sitio prioritario, zona protegida"
)
palabras_clave = [p.strip() for p in palabras_input.split(",") if p.strip()]
palabras_norm = [normalizar(p) for p in palabras_clave]
patrones = {p: construir_patron(normalizar(p)) for p in palabras_clave}

# Acción de búsqueda
if st.button("Buscar"):
    if opcion_base == "ICE" and not archivo:
        st.error("Para buscar en **ICE**, pega primero el URL del CSV.")
        st.session_state['buscar'] = False
    else:
        try:
            df = cargar_csv(archivo)
        except Exception as e:
            st.error(f"No se pudo cargar el CSV desde: {archivo}\nDetalle: {e}")
            st.session_state['buscar'] = False
        else:
            st.session_state['buscar'] = True

            # Normalización y coincidencias
            if "texto" not in df.columns:
                st.error("La columna 'texto' no existe en el CSV seleccionado.")
                st.session_state['buscar'] = False
            else:
                df["texto_norm"] = df["texto"].astype(str).apply(normalizar)
                df["coincidencias"] = df["texto_norm"].apply(lambda txt: tiene_coincidencia(txt, patrones))
                df_filtrado = df[df["coincidencias"].str.len() > 0].copy()

                # Campo combinaciones únicas
                df_filtrado["Palabras Clave (combinadas)"] = df_filtrado["coincidencias"].apply(
                    lambda l: ", ".join(sorted(set(l)))
                )

                # Asegurar columna Número Observación
                if "Número Observación" not in df_filtrado.columns and "nombre_archivo" in df_filtrado.columns:
                    df_filtrado.rename(columns={"nombre_archivo": "Número Observación"}, inplace=True)

                st.session_state['resultados_df'] = df_filtrado

# Mostrar resultados
if st.session_state['buscar']:
    df_filtrado = st.session_state['resultados_df']

    if df_filtrado.empty:
        st.warning("No se encontraron coincidencias.")
    else:
        combinaciones_unicas = sorted(df_filtrado["Palabras Clave (combinadas)"].unique())
        seleccion = st.selectbox("Filtrar por combinación de palabras clave", ["Todas"] + combinaciones_unicas)

        if seleccion != "Todas":
            df_filtrado = df_filtrado[df_filtrado["Palabras Clave (combinadas)"] == seleccion]

        # Explota por coincidencia individual para mostrar
        cols_presentes = df_filtrado.columns
        col_obs = "Número Observación" if "Número Observación" in cols_presentes else (
            "nombre_archivo" if "nombre_archivo" in cols_presentes else None
        )

        df_resultados = (
            df_filtrado
            .explode("coincidencias")
            .rename(columns={"coincidencias": "Palabra Clave"})
        )

        cols_mostrar = ["Palabras Clave (combinadas)"]
        if col_obs:
            cols_mostrar.append(col_obs)

        df_resultados = (
            df_resultados[cols_mostrar]
            .drop_duplicates()
            .reset_index(drop=True)
        )

        n_obs = df_resultados[col_obs].nunique() if col_obs else "N/A"
        st.success(f"Se encontraron {len(df_resultados)} coincidencias en {n_obs} observaciones.")
        st.dataframe(df_resultados, use_container_width=True)

