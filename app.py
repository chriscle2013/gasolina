import streamlit as st
import pandas as pd
import numpy as np

# Título de la aplicación y descripción
st.title("⛽ Control de Gasto de Combustible (Kia Seltos 2021)")
st.write("Registra tus recorridos y repostajes para calcular el consumo (km/galón) y el costo ($/km).")

# Sección de entrada de datos
st.header("📝 Ingreso de Datos")

# Widgets para la entrada de datos básicos
fecha = st.date_input("📅 Fecha del registro:")
km_inicial = st.number_input("🚗 Kilometraje inicial (km):", min_value=0, step=1)
km_final = st.number_input("🏁 Kilometraje final (km):", min_value=0, step=1)
aire_acondicionado = st.checkbox("❄️ ¿Se usó el aire acondicionado?")

# Nuevo campo de checkbox para el repostaje
es_repostaje = st.checkbox("⛽ ¿Este registro incluye un repostaje?")

# Mostrar campos de combustible solo si se marca la casilla de "Repostaje"
if es_repostaje:
    galones = st.number_input("💧 Cantidad de combustible (galones):", min_value=0.01)
    precio = st.number_input("💰 Precio total del repostaje ($ COP):", min_value=0.01)
    # Campo opcional para el kilometraje restante
    km_restante = st.number_input("🎯 Kilometraje restante en el tablero (km):", min_value=0, step=1)
else:
    galones = 0.0
    precio = 0.0
    km_restante = 0

# Botón para añadir los datos
if st.button("➕ Añadir Registro"):
    try:
        df_registros = pd.read_csv("registros_combustible.csv")
    except FileNotFoundError:
        df_registros = pd.DataFrame(columns=["fecha", "km_inicial", "km_final", "galones", "precio", "es_repostaje", "aire_acondicionado", "km_recorridos", "consumo_km_gal", "costo_por_km", "km_restante"])

    # Validar que los datos sean coherentes
    if km_final > km_inicial:
        km_recorridos = km_final - km_inicial
        
        # Calcular consumo y costo solo si es un repostaje
        if es_repostaje and galones > 0 and precio > 0:
            consumo_km_gal = km_recorridos / galones
            costo_por_km = precio / km_recorridos
        else:
            consumo_km_gal = np.nan  # Usamos NaN para indicar que no hay datos de combustible
            costo_por_km = np.nan
        
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
        st.success("✅ Registro añadido con éxito.")
    else:
        st.warning("⚠️ El kilometraje final debe ser mayor que el inicial.")

# ---

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
