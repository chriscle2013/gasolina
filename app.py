import streamlit as st
import pandas as pd
import numpy as np
import os

# Título de la aplicación y descripción
st.title("⛽ Control de Gasto de Combustible (Kia Seltos 2021)")
st.write("Registra tus recorridos y repostajes para un cálculo de consumo preciso (método 'tanque a tanque').")

# -----------------
# LÓGICA DE LA APLICACIÓN
# -----------------
# Crear la carpeta de datos si no existe
def ensure_data_directory_exists():
    if not os.path.exists('data'):
        os.makedirs('data')

# Inicializar la variable en la sesión si no existe
if "km_inicial_sesion" not in st.session_state:
    st.session_state.km_inicial_sesion = None
    st.session_state.iniciando_recorrido = False

# Función para iniciar el recorrido
def iniciar_recorrido():
    if "km_inicial_input" in st.session_state:
        st.session_state.km_inicial_sesion = st.session_state.km_inicial_input
        st.session_state.iniciando_recorrido = True
        st.success(f"Recorrido iniciado. Kilometraje registrado: {st.session_state.km_inicial_sesion} km.")
        st.rerun()

# -----------------
# INTERFAZ DE USUARIO
# -----------------
# Formulario de Registro de Recorridos
st.header("1️⃣ Recorridos")

if not st.session_state.iniciando_recorrido:
    st.number_input("🚗 Kilometraje inicial (km):", key="km_inicial_input", min_value=0, step=1)
    if st.button("🟢 Iniciar Recorrido"):
        iniciar_recorrido()
else:
    st.subheader(f"2️⃣ Finalizar Recorrido (Iniciaste en {st.session_state.km_inicial_sesion} km)")
    st.date_input("📅 Fecha del registro:", key="fecha_recorrido_input")
    st.number_input("🏁 Kilometraje final (km):", key="km_final_input", min_value=st.session_state.km_inicial_sesion + 1, step=1)
    st.checkbox("❄️ ¿Se usó el aire acondicionado?", key="aire_acondicionado_input")

    if st.button("✅ Finalizar Recorrido"):
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

---

# Formulario para Repostajes
st.header("⛽ Registrar Repostaje")
st.write("Solo usa esta sección cuando llenes el tanque. Esto calculará el consumo de forma precisa.")

with st.form("repostaje_form", clear_on_submit=True):
    fecha_repostaje = st.date_input("📅 Fecha del repostaje:")
    km_actual_repostaje = st.number_input("🚗 Kilometraje actual:", min_value=0, step=1)
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
            st.rerun()

---

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
        
    st.subheader("📋 Historial de Recorridos")
    df_recorridos = pd.read_csv("data/recorridos.csv")
    st.dataframe(df_recorridos)

except FileNotFoundError:
    st.info("No hay registros guardados. ¡Empieza a añadir tu primer recorrido!")
