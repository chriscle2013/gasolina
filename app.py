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
    if "km_inicial_input" in st.session_state:
        st.session_state.km_inicial_sesion = st.session_state.km_inicial_input
        st.session_state.iniciando_recorrido = True
        st.success(f"Recorrido iniciado. Kilometraje registrado: {st.session_state.km_inicial_sesion} km.")

# Función para finalizar el recorrido y guardar el registro
def finalizar_recorrido():
    if st.session_state.km_inicial_sesion is None:
        st.warning("⚠️ Debes iniciar un recorrido primero.")
        return

    km_inicial = st.session_state.km_inicial_sesion
    km_final = st.session_state.km_final_input

    if km_final > km_inicial:
        try:
            df_registros = pd.read_csv("registros_combustible.csv")
        except FileNotFoundError:
            df_registros = pd.DataFrame(columns=["fecha", "km_inicial", "km_final", "galones", "precio", "es_repostaje", "aire_acondicionado", "km_recorridos", "consumo_km_gal", "costo_por_km", "km_restante"])

        fecha = st.session_state.fecha_input
        aire_acondicionado = st.session_state.aire_acondicionado_input
        es_repostaje = st.session_state.es_repostaje_input

        km_recorridos = km_final - km_inicial
        
        consumo_km_gal = np.nan
        costo_por_km = np.nan
        km_restante = 0
        galones = 0
        precio = 0

        if es_repostaje:
            if 'galones_input' in st.session_state:
                galones = st.session_state.galones_input
            if 'precio_input' in st.session_state:
                precio = st.session_state.precio_input
            if 'km_restante_input' in st.session_state:
                km_restante = st.session_state.km_restante_input

            if galones > 0 and precio > 0:
                consumo_km_gal = km_recorridos / galones
                costo_por_km = precio / km_recorridos
        
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
        
        st.session_state.iniciando_recorrido = False
        st.session_state.km_inicial_sesion = None
    else:
        st.warning("⚠️ El kilometraje final debe ser mayor que el inicial.")

# -----------------
# INTERFAZ DE USUARIO - FORMULARIO DE REGISTRO
# -----------------
if not st.session_state.iniciando_recorrido:
    st.header("1️⃣ Iniciar Recorrido")
    st.number_input("🚗 Kilometraje inicial (km):", key="km_inicial_input", min_value=0, step=1)
    st.button("🟢 Iniciar Recorrido", on_click=iniciar_recorrido)
else:
    st.header(f"2️⃣ Finalizar Recorrido (Iniciaste en {st.session_state.km_inicial_sesion} km)")
    st.date_input("📅 Fecha del registro:", key="fecha_input")
    st.number_input("🏁 Kilometraje final (km):", key="km_final_input", min_value=st.session_state.km_inicial_sesion + 1, step=1)
    st.checkbox("❄️ ¿Se usó el aire acondicionado?", key="aire_acondicionado_input")

    es_repostaje = st.checkbox("⛽ ¿Este registro incluye un repostaje?", key="es_repostaje_input")

    if es_repostaje:
        st.number_input("💧 Cantidad de combustible (galones):", key="galones_input", min_value=0.01)
        st.number_input("💰 Precio total del repostaje ($ COP):", key="precio_input", min_value=0.01)
        st.number_input("🎯 Kilometraje restante en el tablero (km):", key="km_restante_input", min_value=0, step=1)

    st.button("✅ Finalizar Recorrido", on_click=finalizar_recorrido)

# Sección de visualización de datos
st.header("📊 Resumen y Análisis")

try:
    df_registros = pd.read_csv("registros_combustible.csv")
    st.subheader("📋 Historial de Registros")
    st.dataframe(df_registros)

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

# Sección de edición de registros
st.header("✏️ Editar Registros")

try:
    df_registros = pd.read_csv("registros_combustible.csv")
    
    opciones_edicion = [f"Registro {i+1} ({row['fecha']})" for i, row in df_registros.iterrows()]
    registro_a_editar_indice = st.selectbox("Selecciona el registro a editar:", range(len(opciones_edicion)), format_func=lambda i: opciones_edicion[i])

    if st.button("📝 Cargar para editar"):
        st.session_state.registro_seleccionado = df_registros.iloc[registro_a_editar_indice]
        st.session_state.editing = True
    
    if "editing" in st.session_state and st.session_state.editing:
        st.subheader("Formulario de Edición")
        registro_actual = st.session_state.registro_seleccionado
        
        with st.form("formulario_edicion"):
            fecha_e = st.date_input("📅 Fecha", value=pd.to_datetime(registro_actual["fecha"]), key="fecha_e")
            km_inicial_e = st.number_input("🚗 Kilometraje inicial (km)", value=int(registro_actual["km_inicial"]), min_value=0, step=1, key="km_inicial_e")
            km_final_e = st.number_input("🏁 Kilometraje final (km)", value=int(registro_actual["km_final"]), min_value=0, step=1, key="km_final_e")
            aire_acondicionado_e = st.checkbox("❄️ ¿Se usó el aire acondicionado?", value=bool(registro_actual["aire_acondicionado"]), key="aire_acondicionado_e")
            es_repostaje_e = st.checkbox("⛽ ¿Incluye un repostaje?", value=bool(registro_actual["es_repostaje"]), key="es_repostaje_e")

            galones_e = 0.0
            precio_e = 0.0
            km_restante_e = 0

            if es_repostaje_e:
                galones_e = st.number_input("💧 Cantidad de combustible (galones)", value=float(registro_actual["galones"]), min_value=0.01, key="galones_e")
                precio_e = st.number_input("💰 Precio total del repostaje ($ COP)", value=float(registro_actual["precio"]), min_value=0.01, key="precio_e")
                if "km_restante" in registro_actual:
                    km_restante_e = st.number_input("🎯 Kilometraje restante en el tablero (km)", value=int(registro_actual["km_restante"]), min_value=0, step=1, key="km_restante_e")

            if st.form_submit_button("💾 Guardar Cambios"):
                if km_final_e > km_inicial_e:
                    km_recorridos_e = km_final_e - km_inicial_e
                    consumo_km_gal_e = np.nan
                    costo_por_km_e = np.nan

                    if es_repostaje_e and galones_e > 0 and precio_e > 0:
                        consumo_km_gal_e = km_recorridos_e / galones_e
                        costo_por_km_e = precio_e / km_recorridos_e

                    df_registros.loc[registro_a_editar_indice, [
                        "fecha", "km_inicial", "km_final", "galones", "precio", "es_repostaje", 
                        "aire_acondicionado", "km_recorridos", "consumo_km_gal", "costo_por_km", "km_restante"
                    ]] = [
                        fecha_e, km_inicial_e, km_final_e, galones_e, precio_e, es_repostaje_e, 
                        aire_acondicionado_e, km_recorridos_e, consumo_km_gal_e, costo_por_km_e, km_restante_e
                    ]
                    
                    df_registros.to_csv("registros_combustible.csv", index=False)
                    st.success("✅ ¡Registro actualizado con éxito!")
                    st.session_state.editing = False
                    st.rerun()
                else:
                    st.warning("⚠️ El kilometraje final debe ser mayor que el inicial para guardar.")

except FileNotFoundError:
    st.info("No hay registros para editar. ¡Añade uno primero!")
