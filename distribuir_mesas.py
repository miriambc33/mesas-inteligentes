import pandas as pd
from sklearn.cluster import KMeans
import streamlit as st
import os
import numpy as np

CSV_FILE = "participantes.csv"
OUTPUT_FILE = "asignacion_mesas.csv"

# Verificar si el archivo CSV existe
if not os.path.exists(CSV_FILE):
    st.error("❌ No se encontró el archivo 'participantes.csv'. Asegúrate de que hay registros.")
    st.stop()

# Cargar los datos de los participantes
df = pd.read_csv(CSV_FILE)

# Verificar que haya suficientes participantes
if df.shape[0] < 2:
    st.error("❌ No hay suficientes participantes registrados para hacer la distribución.")
    st.stop()

st.title("📊 Distribución de mesas")

st.markdown(
    """
    <style>
        .block-container {
            max-width: 75%;
        }
        table {
            width: 100% !important;
        }
        th, td {
            padding: 10px !important;
            text-align: left !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

if "fase" not in st.session_state:
    st.session_state.fase = "configuracion"

if st.session_state.fase == "configuracion":
    num_mesas = st.number_input("🪑 Número de mesas", min_value=2, max_value=len(df), value=max(2, len(df) // 4), step=1)
    capacidad_mesa = st.number_input("👥 Capacidad máxima por mesa", min_value=1, max_value=len(df), value=max(3, len(df) // num_mesas), step=1)

    st.write("Lista de participantes registrados:")
    st.dataframe(df)

    if st.button("📌 Asignar mesas"):
        try:
            feature_columns = df.columns[2:]
            features = df[feature_columns].astype(float)

            # Aplicamos K-Means con un peso mayor en los intereses
            kmeans = KMeans(n_clusters=num_mesas, random_state=42, n_init=10)
            df["Mesa"] = kmeans.fit_predict(features * 2) 

            # Función para detectar personas sin intereses comunes en su mesa
            def detectar_sin_intereses_comunes(df):
                sin_afinidad = []
                for _, row in df.iterrows():
                    mesa_actual = row["Mesa"]
                    intereses_persona = set(feature_columns[row[feature_columns] == 1].tolist())

                    # Obtener los intereses del resto de la mesa, excluyéndose a sí mismo
                    intereses_mesa = set()
                    for _, compañero in df[df["Mesa"] == mesa_actual].iterrows():
                        if compañero["Nombre"] != row["Nombre"]: 
                            intereses_mesa.update(set(feature_columns[compañero[feature_columns] == 1].tolist()))

                    # Si no hay intersección de intereses, agregarlo a la lista
                    if not intereses_persona.intersection(intereses_mesa) and intereses_persona:
                        sin_afinidad.append(row["Nombre"])

                return sin_afinidad

            # Función para balancear mesas sin perder afinidad
            def balancear_mesas_con_afinidad(df, num_mesas, capacidad_mesa):
                """
                Asegura que ninguna mesa tenga más participantes de lo permitido.
                Si una mesa está llena, mueve al participante con menor afinidad a otra mesa con menos personas.
                """
                while True:
                    # Contamos los participantes por mesa
                    mesas = df["Mesa"].value_counts().to_dict()

                    # Verificamos si alguna mesa supera la capacidad
                    mesa_excedente = next((mesa for mesa, count in mesas.items() if count > capacidad_mesa), None)
                    if mesa_excedente is None:
                        break

                    # Buscar el participante con menor afinidad dentro de la mesa excedente
                    participantes_mesa = df[df["Mesa"] == mesa_excedente]
                    distancias = (participantes_mesa[feature_columns] @ participantes_mesa[feature_columns].T).sum(axis=1)
                    participante_a_mover = distancias.idxmin()  

                    # Buscar una mesa con menos participantes y más afinidad
                    mesas_disponibles = {m: c for m, c in mesas.items() if c < capacidad_mesa}
                    if not mesas_disponibles:
                        break  # Si no hay espacio en ninguna mesa, detenemos el ajuste

                    # Evaluar afinidad con cada mesa
                    mejor_mesa = min(mesas_disponibles, key=lambda m: (features.iloc[participante_a_mover] @ features[df["Mesa"] == m].mean()).sum())

                    # Mover el participante
                    df.at[participante_a_mover, "Mesa"] = mejor_mesa
                    mesas[mejor_mesa] += 1
                    mesas[mesa_excedente] -= 1

                return df

            df = balancear_mesas_con_afinidad(df, num_mesas, capacidad_mesa)

            # Detectar personas sin intereses en común en su mesa
            personas_sin_afinidad = detectar_sin_intereses_comunes(df)

            # Transformar los intereses en nombres legibles
            def obtener_intereses(row):
                return ", ".join([feature for feature in feature_columns if row[feature] == 1]) or "Sin intereses comunes"

            df["Intereses"] = df.apply(obtener_intereses, axis=1)

            df.to_csv(OUTPUT_FILE, index=False)

            st.session_state.df_asignado = df
            st.session_state.fase = "resultado"
            st.session_state.personas_sin_afinidad = personas_sin_afinidad
            st.rerun()

        except ValueError as e:
            st.error(f"❌ Error al procesar los datos. Revisa el formato del archivo CSV.\n{e}")

elif st.session_state.fase == "resultado":
    df_asignado = st.session_state.df_asignado
    personas_sin_afinidad = st.session_state.get("personas_sin_afinidad", [])

    st.subheader("📌 Distribución de participantes en mesas")

    # Mostrar mesas en filas de 3 horizontalmente
    mesas = df_asignado["Mesa"].nunique()
    mesas_list = list(range(mesas))

    for i in range(0, mesas, 3):  
        columnas = st.columns(3)  

        for j in range(3):  
            if i + j < mesas: 
                with columnas[j]:  
                    mesa_numero = i + j
                    participantes = df_asignado[df_asignado["Mesa"] == mesa_numero]

                    st.markdown(f"### 🪑 Mesa {mesa_numero + 1}")
                    st.dataframe(participantes[["Nombre", "Intereses"]])

    # Mostrar aviso si hay personas sin intereses comunes
    if personas_sin_afinidad:
        st.warning(f"⚠️ Estas personas no tienen intereses en común con nadie en su mesa: {', '.join(personas_sin_afinidad)}")

    if st.button("🔙 Volver atrás"):
        st.session_state.fase = "configuracion"
        st.rerun()