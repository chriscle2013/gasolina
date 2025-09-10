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
def ensure_data_directory_exists():
    """Crea la carpeta de datos si no existe."""
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

# Función para finalizar el recorrido y guardar el registro
def finalizar_recorrido():
    if st.session_state.km_inicial_sesion is None:
        st.warning("⚠️ Debes iniciar un recorrido primero.")
        return

    km_inicial = st.session_state.km_inicial_sesion
    km_final = st.session_state.km_final_input

    if km_final > km_inicial:
        ensure_data_directory_exists()
        
        # Lógica para guardar en la tabla de recorridos
        try:
            df_recorridos = pd.read_csv("data/recorridos.csv")
        except FileNotFoundError:
            df_recorridos = pd.DataFrame(columns=["fecha", "km_inicial", "km_final", "km_recorridos", "aire_acondicionado"])
        
        km_recorridos = km_final - km_inicial
        nuevo_recorrido = pd.DataFrame([{
            "fecha": st.session_state.fecha_input,
            "km_inicial": km_inicial,
            "km_final": km_final,
            "km_recorridos": km_recorridos,
            "aire_acondicionado": st.session_state.aire_acondicionado_input
        }])
        df_recorridos = pd.concat([df_recorridos, nuevo_recorrido], ignore_index=True)
        df_recorridos.to_csv("data/recorridos.csv", index=False)

        # Lógica para guardar en la tabla de repostajes (solo si se marca la opción)
        if st.session_state.es_repostaje_input:
            galones = st.session_state.galones_input
            precio = st.session_state.precio_input
            km_restante = st.session_state.km_restante_input
            
            try:
                df_repostajes = pd.read_csv("data/repostajes.csv")
            except FileNotFoundError:
                df_repostajes = pd.DataFrame(columns=["fecha", "km_actual", "galones", "precio", "km_recorridos_acum", "consumo_km_gal", "costo_por_km", "km_restante_tablero"])

            km_recorridos_acum = np.nan
            consumo_km_gal = np.nan
            costo_por_km = np.nan

            if not df_repostajes.empty:
                ultimo_km_repostaje = df_repostajes["km_actual"].iloc[-1]
                km_recorridos_acum = km_final - ultimo_km_repostaje
                
                if km_recorridos_acum > 0:
                    consumo_km_gal = km_recorridos_acum / galones
                    costo_por_km = precio / km_recorridos_acum
            else:
                st.info("Primer repostaje registrado. El consumo se calculará en el próximo llenado.")
            
            nuevo_repostaje = pd.DataFrame([{
                "fecha": st.session_state.fecha_input,
                "km_actual": km_final,
                "galones": galones,
                "precio": precio,
                "km_recorridos_acum": km_recorridos_acum,
                "consumo_km_gal": consumo_km_gal,
                "costo_por_km": costo_por_km,
                "km_restante_tablero": km_restante
            }])
            df_repostajes = pd.concat([df_repostajes, nuevo_repostaje], ignore_index=True)
            df_repostajes.to_csv("data/repostajes.csv", index=False)
        
        st.success("✅ Recorrido finalizado y registro añadido con éxito.")
        st.session_state.iniciando_recorrido = False
        st.session_state.km_inicial_sesion = None
        st.rerun()
    else:
        st.warning("⚠️ El kilometraje final debe ser mayor que el inicial.")

# -----------------
# INTERFAZ DE USUARIO - FORMULARIO DE REGISTRO
# -----------------
st.header("1️⃣ Recorridos")
if not st.session_state.iniciando_recorrido:
    st.number_input("🚗 Kilometraje inicial (km):", key="km_inicial_input", min_value=0, step=1)
    if st.button("🟢 Iniciar Recorrido"):
        iniciar_recorrido()
else:
    st.subheader(f"2️⃣ Finalizar Recorrido (Iniciaste en {st.session_state.km_inicial_sesion} km)")
    st.date_input("📅 Fecha del registro:", key="fecha_input")
    st.number_input("🏁 Kilometraje final (km):", key="km_final_input", min_value=st.session_state.km_inicial_sesion + 1, step=1)
    st.checkbox("❄️ ¿Se usó el aire acondicionado?", key="aire_acondicionado_input")

    es_repostaje = st.checkbox("⛽ ¿Este registro incluye un repostaje?", key="es_repostaje_input")

    if es_repostaje:
        st.number_input("💧 Cantidad de combustible (galones):", key="galones_input", min_value=0.01)
        st.number_input("💰 Precio total del repostaje ($ COP):", key="precio_input", min_value=0.01)
        st.number_input("🎯 Kilometraje restante en el tablero (km):", key="km_restante_input", min_value=0, step=1)

    if st.button("✅ Finalizar Recorrido"):
        finalizar_recorrido()
        
st.divider()

# Sección de visualización de datos
st.header("📊 Resumen y Análisis")

try:
    df_recorridos = pd.read_csv("data/recorridos.csv")
    st.subheader("📋 Historial de Recorridos")
    st.dataframe(df_recorridos)

    st.subheader("📋 Historial de Repostajes")
    df_repostajes = pd.read_csv("data/repostajes.csv")
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

        st.subheader("Análisis comparativo (con/sin aire acondicionado)")
        df_con_ac = df_recorridos[df_recorridos["aire_acondicionado"] == True]
        df_sin_ac = df_recorridos[df_recorridos["aire_acondicionado"] == False]

        if not df_con_ac.empty:
            consumo_con_ac = df_recorridos.loc[df_con_ac.index, "km_recorridos"].sum() / df_repostajes.loc[df_repostajes['aire_acondicionado'] == True, "galones"].sum()
            st.metric("Consumo Promedio (con A/C)", value=f"{consumo_con_ac:.2f} km/galón")
        else:
            st.info("No hay suficientes datos con aire acondicionado para analizar.")

        if not df_sin_ac.empty:
            consumo_sin_ac = df_recorridos.loc[df_sin_ac.index, "km_recorridos"].sum() / df_repostajes.loc[df_repostajes['aire_acondicionado'] == False, "galones"].sum()
            st.metric("Consumo Promedio (sin A/C)", value=f"{consumo_sin_ac:.2f} km/galón")
        else:
            st.info("No hay suficientes datos sin aire acondicionado para analizar.")
    else:
        st.info("No hay suficientes registros de repostaje para mostrar el análisis.")
except FileNotFoundError:
    st.info("No hay registros guardados. ¡Empieza a añadir tu primer recorrido!")

st.divider()

# Sección de edición de registros
st.header("✏️ Editar Registros")

try:
    df_recorridos = pd.read_csv("data/recorridos.csv")
    df_repostajes = pd.read_csv("data/repostajes.csv")
    df_registros = pd.concat([df_recorridos, df_repostajes], ignore_index=True)
    df_registros = df_registros.sort_values(by="fecha").reset_index(drop=True)
    
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
            km_inicial_e = st.number_input("🚗 Kilometraje inicial (km)", value=int(registro_actual["km_inicial"]) if not pd.isna(registro_actual["km_inicial"]) else 0, min_value=0, step=1, key="km_inicial_e")
            km_final_e = st.number_input("🏁 Kilometraje final (km)", value=int(registro_actual["km_final"]) if not pd.isna(registro_actual["km_final"]) else 0, min_value=0, step=1, key="km_final_e")
            aire_acondicionado_e = st.checkbox("❄️ ¿Se usó el aire acondicionado?", value=bool(registro_actual["aire_acondicionado"]) if not pd.isna(registro_actual["aire_acondicionado"]) else False, key="aire_acondicionado_e")
            
            es_repostaje_e = st.checkbox("⛽ ¿Es un repostaje?", value=bool("km_recorridos_acum" in registro_actual and not pd.isna(registro_actual["km_recorridos_acum"])), key="es_repostaje_e")
            
            galones_e = np.nan
            precio_e = np.nan
            km_restante_e = np.nan

            if es_repostaje_e:
                galones_e = st.number_input("💧 Cantidad de combustible (galones)", value=float(registro_actual["galones"]) if not pd.isna(registro_actual.get("galones", np.nan)) else 0.01, min_value=0.01, key="galones_e")
                precio_e = st.number_input("💰 Precio total del repostaje ($ COP)", value=float(registro_actual["precio"]) if not pd.isna(registro_actual.get("precio", np.nan)) else 0.01, min_value=0.01, key="precio_e")
                km_restante_e = st.number_input("🎯 Kilometraje restante en el tablero (km)", value=int(registro_actual["km_restante_tablero"]) if "km_restante_tablero" in registro_actual and not pd.isna(registro_actual["km_restante_tablero"]) else 0, min_value=0, step=1, key="km_restante_e")

            if st.form_submit_button("💾 Guardar Cambios"):
                if km_final_e > km_inicial_e:
                    km_recorridos_e = km_final_e - km_inicial_e

                    if not es_repostaje_e:
                        df_recorridos.loc[registro_a_editar_indice, [
                            "fecha", "km_inicial", "km_final", "km_recorridos", "aire_acondicionado"
                        ]] = [
                            fecha_e, km_inicial_e, km_final_e, km_recorridos_e, aire_acondicionado_e
                        ]
                        df_recorridos.to_csv("data/recorridos.csv", index=False)
                        
                        # Eliminar el registro de repostajes si existía
                        df_repostajes = df_repostajes[df_repostajes['fecha'] != registro_actual['fecha']]
                        df_repostajes.to_csv("data/repostajes.csv", index=False)

                    else: # es_repostaje_e
                        # Guardar en la tabla de recorridos
                        df_recorridos.loc[registro_a_editar_indice, [
                            "fecha", "km_inicial", "km_final", "km_recorridos", "aire_acondicionado"
                        ]] = [
                            fecha_e, km_inicial_e, km_final_e, km_recorridos_e, aire_acondicionado_e
                        ]
                        df_recorridos.to_csv("data/recorridos.csv", index=False)

                        # Guardar o actualizar en la tabla de repostajes
                        consumo_km_gal_e = np.nan
                        costo_por_km_e = np.nan
                        df_temp = pd.DataFrame([{"fecha": fecha_e, "km_actual": km_final_e, "galones": galones_e, "precio": precio_e, "km_recorridos_acum": np.nan, "consumo_km_gal": np.nan, "costo_por_km": np.nan, "km_restante_tablero": km_restante_e}])
                        df_repostajes = pd.concat([df_repostajes, df_temp], ignore_index=True)
                        df_repostajes = df_repostajes.sort_values(by="fecha").reset_index(drop=True)
                        df_repostajes.to_csv("data/repostajes.csv", index=False)

                    st.success("✅ ¡Registro actualizado con éxito!")
                    st.session_state.editing = False
                    st.rerun()
                else:
                    st.warning("⚠️ El kilometraje final debe ser mayor que el inicial para guardar.")

except FileNotFoundError:
    st.info("No hay registros para editar. ¡Añade uno primero!")
