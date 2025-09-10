import streamlit as st
import pandas as pd
import numpy as np

# Título de la aplicación y descripción
st.title("⛽ Control de Gasto de Combustible (Kia Seltos 2021)")
st.write("Registra tus recorridos y repostajes de forma intuitiva.")

# -----------------
# LÓGICA DE LA SESIÓN
# -----------------
# Inicializar la variable en la sesión si no existe
if "km_inicial_sesion" not in st.session_state:
    st.session_state.km_inicial_sesion = None
    st.session_state.iniciando_recorrido = False

# Función para iniciar el recorrido
def iniciar_recorrido():
    st.session_state.km_inicial_sesion = st.session_state.km_inicial_input
    st.session_state.iniciando_recorrido = True
    st.success(f"Recorrido iniciado. Kilometraje registrado: {st.session_state.km_inicial_sesion} km.")

# Función para finalizar el recorrido
def finalizar_recorrido():
    # Validar que se haya iniciado un recorrido
    if st.session_state.km_inicial_sesion is None:
        st.warning("⚠️ Debes iniciar un recorrido primero.")
        return

    km_inicial = st.session_state.km_inicial_sesion
    km_final = st.session_state.km_final_input

    # Validar que los datos sean coherentes
    if km_final > km_inicial:
        try:
            df_registros = pd.read_csv("registros_combustible.csv")
        except FileNotFoundError:
            df_registros = pd.DataFrame(columns=["fecha", "km_inicial", "km_final", "galones", "precio", "es_repostaje", "aire_acondicionado", "km_recorridos", "consumo_km_gal", "costo_por_km", "km_restante"])

        # Capturar los datos del formulario de finalización
        fecha = st.session_state.fecha_input
        aire_acondicionado = st.session_state.aire_acondicionado_input
        es_repostaje = st.session_state.es_repostaje_input

        # Calcular los kilómetros recorridos
        km_recorridos = km_final - km_inicial
        
        # Calcular consumo y costo solo si es un repostaje
        consumo_km_gal = np.nan
        costo_por_km = np.nan
        km_restante = 0
        galones = 0
        precio = 0

        if es_repostaje:
            galones = st.session_state.galones_input
            precio = st.session_state.precio_input
            km_restante = st.session_state.km_restante_input

            if galones > 0 and precio > 0:
                consumo_km_gal = km_recorridos / galones
                costo_por_km = precio / km_recorridos
        
        # Crear un nuevo registro
        nuevo_registro = pd.DataFrame([{
            "fecha": fecha,
            "km_inicial": km_inicial,
            "km_final": km_final,
            "galones": galones,
            "precio": precio,
            "es_repostaje": es_repostaje,
            "aire_acondicionado": aire_acondicionado,
            "km_recorridos": km_recorridos,
            "consumo_km_gal": consumo_km_gal,
            "costo_por_km": costo_por_km,
            "km_restante": km_restante
        }])
        
        df_registros = pd.concat([df_registros, nuevo_registro], ignore_index=True)
        df_registros.to_csv("registros_combustible.csv", index=False)
        st.success("✅ Recorrido finalizado y registro añadido con éxito.")
        
        # Resetear el estado de la sesión para el próximo recorrido
        st.session_state.iniciando_recorrido = False
        st.session_state.km_inicial_sesion = None
    else:
        st.warning("⚠️ El kilometraje final debe ser mayor que el inicial.")

# -----------------
# INTERFAZ DE USUARIO
# -----------------
# Mostrar el formulario para iniciar o finalizar recorrido
if not st.session_state.iniciando_recorrido:
    st.header("1️⃣ Iniciar Recorrido")
    st.number_input("🚗 Kilometraje inicial (km):", key="km_inicial_input", min_value=0, step=1)
    st.button("🟢 Iniciar Recorrido", on_click=iniciar_recorrido)
else:
    st.header(f"2️⃣ Finalizar Recorrido (Iniciaste en {st.session_state.km_inicial_sesion} km)")
    with st.form("form_finalizar_recorrido"):
        st.date_input("📅 Fecha del registro:", key="fecha_input")
        st.number_input("🏁 Kilometraje final (km):", key="km_final_input", min_value=st.session_state.km_inicial_sesion + 1, step=1)
        st.checkbox("❄️ ¿Se usó el aire acondicionado?", key="aire_acondicionado_input")

        es_repostaje = st.checkbox("⛽ ¿Este registro incluye un repostaje?", key="es_repostaje_input")

        # Seccion de inputs de combustible, solo se muestra si el checkbox de repostaje esta activo
        if es_repostaje:
            st.number_input("💧 Cantidad de combustible (galones):", key="galones_input", min_value=0.01)
            st.number_input("💰 Precio total del repostaje ($ COP):", key="precio_input", min_value=0.01)
            st.number_input("🎯 Kilometraje restante en el tablero (km):", key="km_restante_input", min_value=0, step=1)

        st.form_submit_button("✅ Finalizar Recorrido", on_click=finalizar_recorrido)

# ---
st.divider()

# Sección de visualización de datos
st.header("📊 Resumen y Análisis")

try:
    df_registros = pd.read_csv("registros_combustible.csv")
    st.subheader("📋 Historial de Registros")
    st.dataframe(df_registros)

    # Filtrar solo los registros de repostaje para el análisis de consumo
    df_repostajes = df_registros[df_registros["es_repostaje"] == True].dropna(subset=["consumo_km_gal", "costo_por_km"])

    if not df_repostajes.empty:
        st.subheader("📈 Consumo por Repostaje (km/galón)")
        st.line_chart(df_repostajes["consumo_km_gal"])
        st.subheader("📉 Costo por Kilómetro ($ COP)")
        st.line_chart(df_repostajes["costo_por_km"])

        st.subheader("💡 Métricas Clave Promedio")
        promedio_consumo = df_repostajes["consumo_km_gal"].mean()
        promedio_costo = df_repostajes["costo_por_km"].mean()
        
        st.metric(label="Consumo Promedio (km/galón)", value=f"{promedio_consumo:.2f}")
        st.metric(label="Costo Promedio por Kilómetro", value=f"${promedio_costo:,.2f} COP")

        # Análisis con y sin aire acondicionado (solo en registros de repostaje)
        st.subheader("Análisis comparativo (con/sin aire acondicionado)")
        df_con_ac = df_repostajes[df_repostajes["aire_acondicionado"] == True]
        df_sin_ac = df_repostajes[df_repostajes["aire_acondicionado"] == False]

        if not df_con_ac.empty:
            consumo_con_ac = df_con_ac["consumo_km_gal"].mean()
            st.metric("Consumo Promedio (con A/C)", value=f"{consumo_con_ac:.2f} km/galón")
        else:
            st.info("No hay suficientes datos con aire acondicionado para analizar.")

        if not df_sin_ac.empty:
            consumo_sin_ac = df_sin_ac["consumo_km_gal"].mean()
            st.metric("Consumo Promedio (sin A/C)", value=f"{consumo_sin_ac:.2f} km/galón")
        else:
            st.info("No hay suficientes datos sin aire acondicionado para analizar.")
    else:
        st.info("No hay suficientes registros de repostaje para mostrar el análisis.")
except FileNotFoundError:
    st.info("No hay registros guardados. ¡Empieza a añadir tu primer recorrido!")
