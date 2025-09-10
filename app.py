import streamlit as st
import pandas as pd
import numpy as np

# Constantes del vehículo
CAPACIDAD_TANQUE_GALONES = 13.2  # Capacidad del tanque del Kia Seltos 2021 en galones

# Título de la aplicación y descripción
st.title("⛽ Control de Gasto de Combustible (Kia Seltos 2021)")
st.write("Registra el kilometraje restante para calcular el consumo y el costo por kilómetro.")

# Sección de entrada de datos
st.header("📝 Ingreso de Datos")

# Widgets para la entrada de datos
fecha = st.date_input("📅 Fecha del registro:")
km_actual = st.number_input("🚗 Kilometraje actual (km):", min_value=0, step=1)
aire_acondicionado = st.checkbox("❄️ ¿Se usó el aire acondicionado?")

# Nuevo campo de checkbox para el repostaje
es_repostaje = st.checkbox("⛽ ¿Este registro incluye un repostaje?")

# Mostrar campos de combustible solo si se marca la casilla de "Repostaje"
if es_repostaje:
    km_restante = st.number_input("🎯 Kilometraje restante al llenar el tanque (km):", min_value=0, step=1)
    precio_total = st.number_input("💰 Precio total del repostaje ($ COP):", min_value=0.01)
else:
    km_restante = 0
    precio_total = 0.0

# Botón para añadir los datos
if st.button("➕ Añadir Registro"):
    try:
        df_registros = pd.read_csv("registros_combustible.csv")
    except FileNotFoundError:
        df_registros = pd.DataFrame(columns=["fecha", "km_actual", "km_recorridos_ultimo", "consumo_km_gal", "costo_por_km", "es_repostaje", "aire_acondicionado"])

    # Calcular los kilómetros recorridos desde el último registro
    km_recorridos_ultimo = 0
    if not df_registros.empty:
        ultimo_km = df_registros["km_actual"].iloc[-1]
        km_recorridos_ultimo = km_actual - ultimo_km
    
    # Validar que los datos sean coherentes
    if km_recorridos_ultimo >= 0:
        
        # Calcular consumo y costo solo si es un repostaje
        if es_repostaje and precio_total > 0 and km_restante > 0:
            # Consumo promedio histórico para estimar galones
            consumo_promedio = df_registros["consumo_km_gal"].mean() if "consumo_km_gal" in df_registros.columns else 0
            
            # Estimamos los galones consumidos desde el último llenado completo
            galones_consumidos = 0
            if not np.isnan(consumo_promedio) and consumo_promedio > 0:
                # El kilometraje restante es el resultado de la capacidad del tanque por el consumo
                galones_consumidos = (CAPACIDAD_TANQUE_GALONES * consumo_promedio - km_restante) / consumo_promedio
            
            # Si no hay historial, se puede estimar con un valor por defecto o esperar más registros
            if galones_consumidos <= 0:
                 st.warning("No hay suficiente historial para calcular los galones consumidos. Por favor, añade más registros de repostaje.")
                 st.stop() # Detiene la ejecución para no agregar un registro sin datos
            
            # Recalculamos el consumo y el costo con los galones estimados
            consumo_km_gal = km_recorridos_ultimo / galones_consumidos
            costo_por_km = precio_total / km_recorridos_ultimo
            
            st.success("✅ Registro de repostaje añadido con éxito.")
        else:
            consumo_km_gal = np.nan
            costo_por_km = np.nan
            st.success("✅ Registro de recorrido añadido con éxito. No se calculó el consumo.")

        # Crear un nuevo registro
        nuevo_registro = pd.DataFrame([{
            "fecha": fecha,
            "km_actual": km_actual,
            "km_recorridos_ultimo": km_recorridos_ultimo,
            "consumo_km_gal": consumo_km_gal,
            "costo_por_km": costo_por_km,
            "es_repostaje": es_repostaje,
            "aire_acondicionado": aire_acondicionado
        }])
        
        df_registros = pd.concat([df_registros, nuevo_registro], ignore_index=True)
        df_registros.to_csv("registros_combustible.csv", index=False)
        
    else:
        st.warning("⚠️ El kilometraje actual debe ser mayor o igual al último kilometraje registrado.")

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
