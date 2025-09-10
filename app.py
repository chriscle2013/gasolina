import streamlit as st
import pandas as pd
import numpy as np
import os

# Título de la aplicación y descripción
st.title("⛽ Control de Gasto de Combustible (Kia Seltos 2021)")
st.write("Registra tus recorridos y repostajes para un cálculo de consumo preciso (método 'tanque a tanque').")

# -----------------
# LÓGICA DE LA SESIÓN
# -----------------
# Inicializar la variable en la sesión si no existe
if "km_inicial_sesion" not in st.session_state:
    st.session_state.km_inicial_sesion = None
    st.session_state.iniciando_recorrido = False

# Crear la carpeta de datos si no existe
def ensure_data_directory_exists():
    if not os.path.exists('data'):
        os.makedirs('data')

# Función para iniciar el recorrido
def iniciar_recorrido():
    if "km_inicial_input" in st.session_state:
        st.session_state.km_inicial_sesion = st.session_state.km_inicial_input
        st.session_state.iniciando_recorrido = True
        st.success(f"Recorrido iniciado. Kilometraje registrado: {st.session_state.km_inicial_sesion} km.")

# Función para finalizar el recorrido
def finalizar_recorrido():
    if st.session_state.km_inicial_sesion is None:
        st.warning("⚠️ Debes iniciar un recorrido primero.")
        return

    km_inicial = st.session_state.km_inicial_sesion
    km_final = st.session_state.km_final_input

    if km_final > km_inicial:
        ensure_data_directory_exists()
        try:
            df_recorridos = pd.read_csv("data/recorridos.csv")
        except FileNotFoundError:
            df_recorridos = pd.DataFrame(columns=["fecha", "km_inicial", "km_final", "km_recorridos", "aire_acondicionado"])

        km_recorridos = km_final - km_inicial
        
        nuevo_recorrido = pd.DataFrame([{
            "fecha": st.session_state.fecha_recorrido_input,
            "km_inicial": km_inicial,
            "km_final": km_final,
            "km_recorridos": km_recorridos,
            "aire_acondicionado": st.session_state.aire_acondicionado_input
        }])
        
        df_recorridos = pd.concat([df_recorridos, nuevo_recorrido], ignore_index=True)
        df_recorridos.to_csv("data/recorridos.csv", index=False)
        st.success("✅ Recorrido finalizado y registro añadido con éxito.")
        
        st.session_state.iniciando_recorrido = False
        st.session_state.km_inicial_sesion = None
        st.rerun()
    else:
        st.warning("⚠️ El kilometraje final debe ser mayor que el inicial.")

# Función para registrar un repostaje
def registrar_repostaje():
    km_actual_repostaje = st.session_state.km_repostaje_input
    galones_repostaje = st.session_state.galones_repostaje_input
    precio_repostaje = st.session_state.precio_repostaje_input

    if galones_repostaje <= 0 or precio_repostaje <= 0:
        st.warning("⚠️ La cantidad de galones y el precio total deben ser mayores a cero.")
        return

    ensure_data_directory_exists()
    try:
        df_repostajes = pd.read_csv("data/repostajes.csv")
    except FileNotFoundError:
        df_repostajes = pd.DataFrame(columns=["fecha", "km_actual", "galones", "precio", "km_recorridos_acum", "consumo_km_gal", "cost
