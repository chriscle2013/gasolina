import streamlit as st
import pandas as pd
import numpy as np
import os
import uuid

# Título de la aplicación y descripción
st.title("⛽ Control de Gasto de Combustible (Kia Seltos 2021)")
st.write("Registra tus recorridos y repostajes para un control preciso de tu consumo.")

# -----------------
# LÓGICA DE LA APLICACIÓN
# -----------------
def ensure_data_directory_exists():
    """Crea la carpeta de datos si no existe."""
    if not os.path.exists('data'):
        os.makedirs('data')

# -----------------
# FORMULARIO DE RECORRIDOS
# -----------------
st.header("1️⃣ Registrar Recorrido Diario")
st.write("Registra un viaje corto. No es necesario ingresar el combustible.")

with st.form("recorrido_form", clear_on_submit=True):
    fecha_recorrido = st.date_input("📅 Fecha del recorrido:")
    km_inicial_recorrido = st.number_input("🚗 Kilometraje inicial (km):", min_value=0, step=1)
    km_final_recorrido = st.number_input("🏁 Kilometraje final (km):", min_value=0, step=1)
    aire_acondicionado = st.checkbox("❄️ ¿Se usó el aire acondicionado?")
    km_restante = st.number_input("🎯 Kilometraje restante en el tablero (km):", min_value=0, step=1)

    submitted_recorrido = st.form_submit_button("➕ Añadir Recorrido")

    if submitted_recorrido:
        if km_final_recorrido > km_inicial_recorrido:
            ensure_data_directory_exists()
            try:
                df_recorridos = pd.read_csv("data/recorridos.csv")
            except FileNotFoundError:
                df_recorridos = pd.DataFrame(columns=["id", "fecha", "km_inicial", "km_final", "km_recorridos", "aire_acondicionado", "km_restante"])
            
            km_recorridos = km_final_recorrido - km_inicial_recorrido
            nuevo_recorrido = pd.DataFrame([{
                "id": str(uuid.uuid4()),
                "fecha": fecha_recorrido,
                "km_inicial": km_inicial_recorrido,
                "km_final": km_final_recorrido,
                "km_recorridos": km_recorridos,
                "aire_acondicionado": aire_acondicionado,
                "km_restante": km_restante
            }])
            df_recorridos = pd.concat([df_recorridos, nuevo_recorrido], ignore_index=True)
            df_recorridos.to_csv("data/recorridos.csv", index=False)
            st.success("✅ Recorrido registrado con éxito.")
            st.rerun()
        else:
            st.warning("⚠️ El kilometraje final debe ser mayor que el inicial.")

st.divider()

# -----------------
# FORMULARIO DE REPOSTAJE
# -----------------
st.header("⛽ Registrar Repostaje")
st.write("Usa esta sección solo cuando llenes el tanque. Aquí se calcula el consumo.")

with st.form("repostaje_form", clear_on_submit=True):
    fecha_repostaje = st.date_input("📅 Fecha del repostaje:")
    km_actual_repostaje = st.number_input("🚗 Kilometraje actual:", min_value=0, step=1)
    galones_repostaje = st.number_input("💧 Cantidad de combustible (galones):", min_value=0.01)
    precio_repostaje = st.number_input("💰 Precio total del repostaje ($ COP):", min_value=0.01)

    submitted_repostaje = st.form_submit_button("➕ Añadir Repostaje")
    
    if submitted_repostaje:
        if galones_repostaje <= 0 or precio_repostaje <= 0:
            st.warning("⚠️ La cantidad de galones y el precio total deben ser mayores a cero.")
        else:
            ensure_data_directory_exists()
            try:
                df_repostajes = pd.read_csv("data/repostajes.csv")
            except FileNotFoundError:
                df_repostajes = pd.DataFrame(columns=["id", "fecha", "km_actual", "galones", "precio", "km_recorridos_acum", "consumo_km_gal", "costo_por_km"])
            
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
                "id": str(uuid.uuid4()),
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

st.divider()

# -----------------
# SECCIÓN DE ANÁLISIS
# -----------------
st.header("📊 Resumen y Análisis")

try:
    df_recorridos = pd.read_csv("data/recorridos.csv")
    st.subheader("📋 Historial de Recorridos")
    st.dataframe(df_recorridos.sort_values(by="fecha", ascending=False))
except FileNotFoundError:
    st.info("No hay registros de recorridos guardados. ¡Empieza a añadir tu primer recorrido!")

st.divider()

try:
    df_repostajes = pd.read_csv("data/repostajes.csv")
    st.subheader("📋 Historial de Repostajes")
    st.dataframe(df_repostajes.sort_values(by="fecha", ascending=False))

    if len(df_repostajes) > 1:
        st.subheader("📈 Consumo y Gasto por Tanqueada")
        st.line_chart(df_repostajes, x="fecha", y=["consumo_km_gal", "costo_por_km"])
        
        st.subheader("💡 Métricas Clave Promedio")
        promedio_consumo = df_repostajes["consumo_km_gal"].mean()
        promedio_costo = df_repostajes["costo_por_km"].mean()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Consumo Promedio (km/galón)", value=f"{promedio_consumo:.2f}")
        with col2:
            st.metric(label="Costo Promedio por Kilómetro", value=f"${promedio_costo:,.2f} COP")

        st.subheader("🎯 Último Kilometraje Restante en Tablero")
        if not df_recorridos.empty and "km_restante" in df_recorridos.columns:
            st.metric(label="Kilometraje restante estimado", value=f"{df_recorridos['km_restante'].iloc[-1]} km")
    else:
        st.info("No hay suficientes registros de repostaje para mostrar el análisis. ¡Agrega al menos dos registros para ver las gráficas!")
except FileNotFoundError:
    st.info("No hay registros de repostaje guardados. ¡Añade uno para empezar a ver el análisis!")

st.divider()

# -----------------
# SECCIÓN DE EDICIÓN Y ELIMINACIÓN
# -----------------
st.header("✏️ Editar o Eliminar Registros")
st.info("Para editar, selecciona el registro, haz clic en 'Cargar para editar' y luego en 'Guardar Cambios'. Para eliminar, haz clic en el botón 'Eliminar Registro'.")

try:
    df_recorridos = pd.read_csv("data/recorridos.csv")
    df_repostajes = pd.read_csv("data/repostajes.csv")

    df_registros_combinados = pd.concat([
        df_recorridos.assign(tipo='Recorrido'),
        df_repostajes.assign(tipo='Repostaje')
    ], ignore_index=True)
    
    df_registros_combinados = df_registros_combinados.sort_values(by="fecha", ascending=False).reset_index(drop=True)

    opciones_edicion = [f"Tipo: {row['tipo']} | Fecha: {row['fecha']}" for i, row in df_registros_combinados.iterrows()]
    registro_a_editar_indice = st.selectbox("Selecciona el registro a editar:", range(len(opciones_edicion)), format_func=lambda i: opciones_edicion[i])
    
    if st.button("📝 Cargar para editar"):
        st.session_state.registro_seleccionado = df_registros_combinados.iloc[registro_a_editar_indice]
        st.session_state.editing = True
        st.rerun()

    if "editing" in st.session_state and st.session_state.editing:
        st.subheader("Formulario de Edición")
        registro_actual = st.session_state.registro_seleccionado
        
        with st.form("formulario_edicion"):
            st.markdown(f"**Editando registro de tipo:** **{registro_actual['tipo']}**")
            
            fecha_e = st.date_input("📅 Fecha", value=pd.to_datetime(registro_actual["fecha"]), key="fecha_e")
            
            if registro_actual['tipo'] == 'Recorrido':
                km_inicial_e = st.number_input("🚗 Kilometraje inicial (km)", value=int(registro_actual.get("km_inicial", 0)) if not pd.isna(registro_actual.get("km_inicial", np.nan)) else 0, min_value=0, step=1, key="km_inicial_e")
                km_final_e = st.number_input("🏁 Kilometraje final (km)", value=int(registro_actual.get("km_final", 0)) if not pd.isna(registro_actual.get("km_final", np.nan)) else 0, min_value=0, step=1, key="km_final_e")
                aire_acondicionado_e = st.checkbox("❄️ ¿Se usó el aire acondicionado?", value=bool(registro_actual.get("aire_acondicionado", False)) if not pd.isna(registro_actual.get("aire_acondicionado", np.nan)) else False, key="aire_acondicionado_e")
                km_restante_e = st.number_input("🎯 Kilometraje restante en el tablero (km)", value=int(registro_actual.get("km_restante", 0)) if not pd.isna(registro_actual.get("km_restante", np.nan)) else 0, min_value=0, step=1, key="km_restante_e")

                guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
                eliminar_registro = st.form_submit_button("🗑️ Eliminar Registro")

                if guardar_cambios:
                    if km_final_e > km_inicial_e:
                        km_recorridos_e = km_final_e - km_inicial_e
                        df_recorridos_para_editar = pd.read_csv("data/recorridos.csv")
                        df_recorridos_para_editar.loc[df_recorridos_para_editar['id'] == registro_actual['id'], [
                            "fecha", "km_inicial", "km_final", "km_recorridos", "aire_acondicionado", "km_restante"
                        ]] = [
                            fecha_e, km_inicial_e, km_final_e, km_recorridos_e, aire_acondicionado_e, km_restante_e
                        ]
                        df_recorridos_para_editar.to_csv("data/recorridos.csv", index=False)
                        st.success("✅ ¡Registro de recorrido actualizado con éxito!")
                        st.session_state.editing = False
                        st.rerun()
                    else:
                        st.warning("⚠️ El kilometraje final debe ser mayor que el inicial para guardar.")
                
                if eliminar_registro:
                    df_recorridos_para_editar = pd.read_csv("data/recorridos.csv")
                    df_recorridos_para_editar = df_recorridos_para_editar[df_recorridos_para_editar['id'] != registro_actual['id']]
                    df_recorridos_para_editar.to_csv("data/recorridos.csv", index=False)
                    st.success("✅ ¡Registro de recorrido eliminado con éxito!")
                    st.session_state.editing = False
                    st.rerun()

            elif registro_actual['tipo'] == 'Repostaje':
                km_actual_e = st.number_input("🚗 Kilometraje actual:", value=int(registro_actual.get("km_actual", 0)) if not pd.isna(registro_actual.get("km_actual", np.nan)) else 0, min_value=0, step=1, key="km_actual_e")
                galones_e = st.number_input("💧 Cantidad de combustible (galones)", value=float(registro_actual.get("galones", 0.01)), min_value=0.01, key="galones_e")
                precio_e = st.number_input("💰 Precio total del repostaje ($ COP)", value=float(registro_actual.get("precio", 0.01)), min_value=0.01, key="precio_e")
                
                guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
                eliminar_registro = st.form_submit_button("🗑️ Eliminar Registro")
            
                if guardar_cambios:
                    if galones_e <= 0 or precio_e <= 0:
                        st.warning("⚠️ La cantidad de galones y el precio total deben ser mayores a cero.")
                    else:
                        df_repostajes_para_editar = pd.read_csv("data/repostajes.csv")
                        df_repostajes_para_editar.loc[df_repostajes_para_editar['id'] == registro_actual['id'], [
                            "fecha", "km_actual", "galones", "precio", "km_recorridos_acum", "consumo_km_gal", "costo_por_km"
                        ]] = [
                            fecha_e, km_actual_e, galones_e, precio_e, np.nan, np.nan, np.nan
                        ]
                        
                        df_repostajes_para_editar = df_repostajes_para_editar.sort_values(by="fecha").reset_index(drop=True)
                        for i in range(1, len(df_repostajes_para_editar)):
                            km_recorridos_acum = df_repostajes_para_editar['km_actual'].iloc[i] - df_repostajes_para_editar['km_actual'].iloc[i-1]
                            galones = df_repostajes_para_editar['galones'].iloc[i]
                            precio = df_repostajes_para_editar['precio'].iloc[i]
                            if galones > 0 and km_recorridos_acum > 0:
                                df_repostajes_para_editar.loc[i, "consumo_km_gal"] = km_recorridos_acum / galones
                                df_repostajes_para_editar.loc[i, "costo_por_km"] = precio / km_recorridos_acum
                                df_repostajes_para_editar.loc[i, "km_recorridos_acum"] = km_recorridos_acum
                        
                        df_repostajes_para_editar.to_csv("data/repostajes.csv", index=False)
                        st.success("✅ ¡Registro de repostaje actualizado con éxito!")
                        st.session_state.editing = False
                        st.rerun()

                if eliminar_registro:
                    df_repostajes_para_editar = pd.read_csv("data/repostajes.csv")
                    df_repostajes_para_editar = df_repostajes_para_editar[df_repostajes_para_editar['id'] != registro_actual['id']]
                    df_repostajes_para_editar.to_csv("data/repostajes.csv", index=False)
                    st.success("✅ ¡Registro de repostaje eliminado con éxito!")
                    st.session_state.editing = False
                    st.rerun()

except FileNotFoundError:
    st.info("No hay registros para editar. ¡Añade uno primero!")
