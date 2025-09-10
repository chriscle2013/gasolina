import streamlit as st
import pandas as pd
import numpy as np
import os

# Título de la aplicación y descripción
st.title("⛽ Control de Gasto de Combustible (Kia Seltos 2021)")
st.write("Registra tus repostajes para un cálculo de consumo preciso (método 'tanque a tanque').")

# -----------------
# LÓGICA DE LA APLICACIÓN
# -----------------
# Crear la carpeta de datos si no existe
def ensure_data_directory_exists():
    if not os.path.exists('data'):
        os.makedirs('data')

# -----------------
# INTERFAZ DE USUARIO
# -----------------
st.header("⛽ Registrar Repostaje")
st.write("Solo usa esta sección cada vez que llenes el tanque.")

with st.form("repostaje_form", clear_on_submit=True):
    fecha_repostaje = st.date_input("📅 Fecha del repostaje:")
    km_actual_repostaje = st.number_input("🚗 Kilometraje actual (km):", min_value=0, step=1)
    galones_repostaje = st.number_input("💧 Cantidad de combustible (galones):", min_value=0.01)
    precio_repostaje = st.number_input("💰 Precio total del repostaje ($ COP):", min_value=0.01)

    submitted = st.form_submit_button("➕ Añadir Repostaje")
    
    if submitted:
        if galones_repostaje <= 0 or precio_repostaje <= 0:
            st.warning("⚠️ La cantidad de galones y el precio total deben ser mayores a cero.")
        else:
            ensure_data_directory_exists()
            try:
                df_repostajes = pd.read_csv("data/repostajes.csv")
            except FileNotFoundError:
                df_repostajes = pd.DataFrame(columns=["fecha", "km_actual", "galones", "precio", "km_recorridos_acum", "consumo_km_gal", "costo_por_km"])
            
            km_recorridos_acum = np.nan
            consumo_km_gal = np.nan
            costo_por_km = np.nan
            
            if not df_repostajes.empty:
                ultimo_km_repostaje = df_repostajes["km_actual"].iloc[-1]
                km_recorridos_acum = km_actual_repostaje - ultimo_km_repostaje
                
                if km_recorridos_acum > 0:
                    consumo_km_gal = km_recorridos_acum / galones_repostaje
                    costo_por_km = precio_repostaje / km_recorridos_acum
            
            nuevo_repostaje = pd.DataFrame([{
                "fecha": fecha_repostaje,
                "km_actual": km_actual_repostaje,
                "galones": galones_repostaje,
                "precio": precio_repostaje,
                "km_recorridos_acum": km_recorridos_acum,
                "consumo_km_gal": consumo_km_gal,
                "costo_por_km": costo_por_km
            }])
            
            df_repostajes = pd.concat([df_repostajes, nuevo_repostaje], ignore_index=True)
            df_repostajes.to_csv("data/repostajes.csv", index=False)
            st.success("✅ Repostaje registrado con éxito. El análisis de consumo se actualizará con el próximo llenado.")
            st.dataframe(df_repostajes) # Mostrar la tabla actualizada inmediatamente

st.divider()

# Sección de visualización de datos
st.header("📊 Resumen y Análisis")

try:
    df_repostajes = pd.read_csv("data/repostajes.csv")
    
    st.subheader("📋 Historial de Repostajes")
    st.dataframe(df_repostajes)

    if len(df_repostajes) > 1:
        st.subheader("📈 Consumo por Repostaje (km/galón)")
        st.line_chart(df_repostajes["consumo_km_gal"])
        st.subheader("📉 Costo por Kilómetro ($ COP)")
        st.line_chart(df_repostajes["costo_por_km"])

        st.subheader("💡 Métricas Clave Promedio")
        promedio_consumo = df_repostajes["consumo_km_gal"].mean()
        promedio_costo = df_repostajes["costo_por_km"].mean()
        
        st.metric(label="Consumo Promedio (km/galón)", value=f"{promedio_consumo:.2f}")
        st.metric(label="Costo Promedio por Kilómetro", value=f"${promedio_costo:,.2f} COP")
    else:
        st.info("Aún no hay suficientes registros de repostaje para mostrar el análisis. ¡Agrega al menos dos registros para ver las gráficas!")
        
except FileNotFoundError:
    st.info("No hay registros guardados. ¡Empieza a añadir tu primer repostaje!")
