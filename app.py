import streamlit as st
import pandas as pd
import numpy as np
import uuid

# Título de la aplicación y descripción
st.title("⛽ Control de Gasto de Combustible (Kia Seltos 2021)")
st.write("Registra tus recorridos y repostajes para un control preciso de tu consumo.")

# --- CONFIGURACIÓN DE CONEXIÓN A GOOGLE SHEETS ---
# REEMPLAZA ESTA URL con la URL de tu hoja de cálculo.
# EJEMPLO: https://docs.google.com/spreadsheets/d/1234567890abcdefghijklmnopqrstuvwxyz/edit
GSHEETS_URL = "https://docs.google.com/spreadsheets/d/1k_91FFgqh1kCUx-f480vQ55cnXv_k5hp3Z9XSelfkLg/edit?usp=sharing"

# Crea la conexión a Google Sheets. Streamlit lee automáticamente las credenciales de secrets.toml
try:
    conn = st.connection("gsheets", type="streamlit_gsheets")
except Exception as e:
    st.error("Error de conexión con Google Sheets. Asegúrate de que las credenciales en .streamlit/secrets.toml son correctas y de haber compartido la hoja con la cuenta de servicio.")
    st.stop()


# --- FUNCIONES DE LECTURA Y ESCRITURA ---

@st.cache_data(ttl=600)
def load_data(sheet_name):
    """Carga datos de una pestaña específica de Google Sheets."""
    # Columnas esperadas si la hoja está vacía
    if sheet_name == "Recorridos":
        cols = ["id", "fecha", "km_inicial", "km_final", "km_recorridos", "aire_acondicionado", "km_restante"]
    else:
        cols = ["id", "fecha", "km_actual", "galones", "precio", "km_recorridos_acum", "consumo_km_gal", "costo_por_km"]

    try:
        df = conn.read(spreadsheet=GSHEETS_URL, worksheet=sheet_name, usecols=cols, ttl=5)
        df = df.dropna(how='all') # Elimina filas completamente vacías
        
        # Streamlit-gsheets lee todas las columnas como objetos, forzamos tipos
        if sheet_name == "Recorridos":
            df['km_inicial'] = pd.to_numeric(df['km_inicial'], errors='coerce').fillna(0).astype(int)
            df['km_final'] = pd.to_numeric(df['km_final'], errors='coerce').fillna(0).astype(int)
            df['km_restante'] = pd.to_numeric(df['km_restante'], errors='coerce').fillna(0).astype(int)
        
        return df
    except Exception as e:
        # Si no puede leer (ej: hoja vacía), devuelve un DataFrame vacío con las columnas correctas
        return pd.DataFrame(columns=cols)

def update_repostajes_analysis(df_repostajes):
    """Recalcula las métricas de repostaje después de un cambio."""
    df_repostajes = df_repostajes.sort_values(by="fecha").reset_index(drop=True)
    df_repostajes['km_recorridos_acum'] = np.nan
    df_repostajes['consumo_km_gal'] = np.nan
    df_repostajes['costo_por_km'] = np.nan

    if len(df_repostajes) > 1:
        for i in range(1, len(df_repostajes)):
            km_recorridos_acum = df_repostajes['km_actual'].iloc[i] - df_repostajes['km_actual'].iloc[i-1]
            galones = df_repostajes['galones'].iloc[i]
            precio = df_repostajes['precio'].iloc[i]
            if galones > 0 and km_recorridos_acum > 0:
                df_repostajes.loc[i, "consumo_km_gal"] = km_recorridos_acum / galones
                df_repostajes.loc[i, "costo_por_km"] = precio / km_recorridos_acum
                df_repostajes.loc[i, "km_recorridos_acum"] = km_recorridos_acum
    return df_repostajes


# Recarga los datos globales (deshabilita el cache para asegurar la frescura)
df_recorridos_global = load_data("Recorridos")
df_repostajes_global = load_data("Repostajes")


# -----------------
# FORMULARIO DE RECORRIDOS (CREACIÓN)
# -----------------
st.header("1️⃣ Registrar Recorrido Diario")
with st.form("recorrido_form", clear_on_submit=True):
    fecha_recorrido = st.date_input("📅 Fecha del recorrido:")
    km_inicial_recorrido = st.number_input("🚗 Kilometraje inicial (km):", min_value=0, step=1)
    km_final_recorrido = st.number_input("🏁 Kilometraje final (km):", min_value=0, step=1)
    aire_acondicionado = st.checkbox("❄️ ¿Se usó el aire acondicionado?")
    km_restante = st.number_input("🎯 Kilometraje restante en el tablero (km):", min_value=0, step=1)

    submitted_recorrido = st.form_submit_button("➕ Añadir Recorrido")

    if submitted_recorrido:
        if km_final_recorrido > km_inicial_recorrido:
            
            km_recorridos = km_final_recorrido - km_inicial_recorrido
            
            nuevo_recorrido = pd.DataFrame([{
                "id": str(uuid.uuid4()),
                "fecha": str(fecha_recorrido), # Convertir a string para la hoja de cálculo
                "km_inicial": km_inicial_recorrido,
                "km_final": km_final_recorrido,
                "km_recorridos": km_recorridos,
                "aire_acondicionado": aire_acondicionado,
                "km_restante": km_restante
            }])
            
            # --- USO DE GOOGLE SHEETS PARA AGREGAR ---
            conn.append(spreadsheet=GSHEETS_URL, worksheet="Recorridos", data=nuevo_recorrido)
            # ----------------------------------------
            
            st.success("✅ Recorrido registrado con éxito.")
            st.cache_data.clear() # Limpia la caché para recargar los datos
            st.rerun()
        else:
            st.warning("⚠️ El kilometraje final debe ser mayor que el inicial.")

st.divider()

# -----------------
# FORMULARIO DE REPOSTAJE (CREACIÓN)
# -----------------
st.header("⛽ Registrar Repostaje")
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
            km_recorridos_acum = np.nan
            consumo_km_gal = np.nan
            costo_por_km = np.nan
            
            # Calculamos métricas si hay datos anteriores
            df_temp = load_data("Repostajes")
            if not df_temp.empty:
                # Obtenemos el KM anterior al último que acaba de ser registrado
                # Si el usuario añade un registro con fecha anterior, esto podría fallar
                ultimo_km_repostaje = df_temp["km_actual"].astype(int).iloc[-1]
                km_recorridos_acum = km_actual_repostaje - ultimo_km_repostaje
                
                if km_recorridos_acum > 0:
                    consumo_km_gal = km_recorridos_acum / galones_repostaje
                    costo_por_km = precio_repostaje / km_recorridos_acum
            
            nuevo_repostaje = pd.DataFrame([{
                "id": str(uuid.uuid4()),
                "fecha": str(fecha_repostaje),
                "km_actual": km_actual_repostaje,
                "galones": galones_repostaje,
                "precio": precio_repostaje,
                "km_recorridos_acum": km_recorridos_acum,
                "consumo_km_gal": consumo_km_gal,
                "costo_por_km": costo_por_km
            }])
            
            # --- USO DE GOOGLE SHEETS PARA AGREGAR ---
            conn.append(spreadsheet=GSHEETS_URL, worksheet="Repostajes", data=nuevo_repostaje)
            # ----------------------------------------

            st.success("✅ Repostaje registrado con éxito. El análisis de consumo se actualizará con el próximo llenado.")
            st.cache_data.clear()
            st.rerun()

st.divider()

# -----------------
# SECCIÓN DE ANÁLISIS
# -----------------
st.header("📊 Resumen y Análisis")

df_recorridos = load_data("Recorridos")
st.subheader("📋 Historial de Recorridos")
if not df_recorridos.empty:
    st.dataframe(df_recorridos.drop(columns=["id"]).sort_values(by="fecha", ascending=False))
else:
    st.info("No hay registros de recorridos guardados. ¡Empieza a añadir tu primer recorrido!")

st.divider()

df_repostajes = load_data("Repostajes")
df_repostajes_analisis = update_repostajes_analysis(df_repostajes.copy())

st.subheader("📋 Historial de Repostajes")
if not df_repostajes.empty:
    st.dataframe(df_repostajes_analisis.drop(columns=["id"]).sort_values(by="fecha", ascending=False))

    if len(df_repostajes_analisis.dropna(subset=['consumo_km_gal'])) > 0:
        st.subheader("📈 Consumo y Gasto por Tanqueada")
        st.line_chart(df_repostajes_analisis, x="fecha", y=["consumo_km_gal", "costo_por_km"])
        
        st.subheader("💡 Métricas Clave Promedio")
        promedio_consumo = df_repostajes_analisis["consumo_km_gal"].mean()
        promedio_costo = df_repostajes_analisis["costo_por_km"].mean()
        
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
else:
    st.info("No hay registros de repostaje guardados. ¡Añade uno para empezar a ver el análisis!")

st.divider()

# -----------------
# SECCIÓN DE EDICIÓN Y ELIMINACIÓN (USANDO GOOGLE SHEETS)
# -----------------
st.header("✏️ Editar o Eliminar Registros")
st.info("Para editar, selecciona el registro, haz clic en 'Cargar para editar' y luego en 'Guardar Cambios'. Para eliminar, haz clic en el botón 'Eliminar Registro'.")

df_recorridos = load_data("Recorridos")
df_repostajes = load_data("Repostajes")

if not df_recorridos.empty or not df_repostajes.empty:
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
            
            # --- Obtener el índice de la fila en la hoja de cálculo (necesario para la edición) ---
            # El conector de Streamlit-gsheets maneja los índices de fila por ti,
            # pero necesitamos el ID único para localizar la fila a editar/eliminar.
            registro_id = registro_actual['id']
            tipo = registro_actual['tipo']
            hoja = "Recorridos" if tipo == 'Recorrido' else "Repostajes"
            
            # Cargar el DataFrame completo de la hoja para obtener el índice real de GSheets
            df_hoja_completa = load_data(hoja)
            row_index = df_hoja_completa[df_hoja_completa['id'] == registro_id].index[0]

            fecha_e = st.date_input("📅 Fecha", value=pd.to_datetime(registro_actual["fecha"]), key="fecha_e")
            
            if tipo == 'Recorrido':
                # Convertir a tipos nativos para los widgets de Streamlit
                km_inicial_val = int(registro_actual.get("km_inicial", 0)) if not pd.isna(registro_actual.get("km_inicial", np.nan)) else 0
                km_final_val = int(registro_actual.get("km_final", 0)) if not pd.isna(registro_actual.get("km_final", np.nan)) else 0
                km_restante_val = int(registro_actual.get("km_restante", 0)) if not pd.isna(registro_actual.get("km_restante", np.nan)) else 0
                aire_acondicionado_val = bool(registro_actual.get("aire_acondicionado", False)) if not pd.isna(registro_actual.get("aire_acondicionado", np.nan)) else False

                km_inicial_e = st.number_input("🚗 Kilometraje inicial (km)", value=km_inicial_val, min_value=0, step=1, key="km_inicial_e")
                km_final_e = st.number_input("🏁 Kilometraje final (km)", value=km_final_val, min_value=0, step=1, key="km_final_e")
                aire_acondicionado_e = st.checkbox("❄️ ¿Se usó el aire acondicionado?", value=aire_acondicionado_val, key="aire_acondicionado_e")
                km_restante_e = st.number_input("🎯 Kilometraje restante en el tablero (km)", value=km_restante_val, min_value=0, step=1, key="km_restante_e")

                guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
                eliminar_registro = st.form_submit_button("🗑️ Eliminar Registro")

                if guardar_cambios:
                    if km_final_e > km_inicial_e:
                        km_recorridos_e = km_final_e - km_inicial_e
                        
                        df_update = pd.DataFrame([{
                            "id": registro_id,
                            "fecha": str(fecha_e),
                            "km_inicial": km_inicial_e,
                            "km_final": km_final_e,
                            "km_recorridos": km_recorridos_e,
                            "aire_acondicionado": aire_acondicionado_e,
                            "km_restante": km_restante_e
                        }])
                        
                        # --- USO DE GOOGLE SHEETS PARA MODIFICAR ---
                        # Se usa el índice de la fila para hacer el update
                        conn.update(spreadsheet=GSHEETS_URL, worksheet=hoja, data=df_update, row=row_index)
                        # ------------------------------------------

                        st.success("✅ ¡Registro de recorrido actualizado con éxito!")
                        st.session_state.editing = False
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.warning("⚠️ El kilometraje final debe ser mayor que el inicial para guardar.")
                
                if eliminar_registro:
                    # --- USO DE GOOGLE SHEETS PARA ELIMINAR ---
                    conn.delete(spreadsheet=GSHEETS_URL, worksheet=hoja, row=row_index)
                    # -----------------------------------------
                    
                    st.success("✅ ¡Registro de recorrido eliminado con éxito!")
                    st.session_state.editing = False
                    st.cache_data.clear()
                    st.rerun()

            elif tipo == 'Repostaje':
                km_actual_val = int(registro_actual.get("km_actual", 0)) if not pd.isna(registro_actual.get("km_actual", np.nan)) else 0
                galones_val = float(registro_actual.get("galones", 0.01)) if not pd.isna(registro_actual.get("galones", np.nan)) else 0.01
                precio_val = float(registro_actual.get("precio", 0.01)) if not pd.isna(registro_actual.get("precio", np.nan)) else 0.01

                km_actual_e = st.number_input("🚗 Kilometraje actual:", value=km_actual_val, min_value=0, step=1, key="km_actual_e")
                galones_e = st.number_input("💧 Cantidad de combustible (galones)", value=galones_val, min_value=0.01, key="galones_e")
                precio_e = st.number_input("💰 Precio total del repostaje ($ COP)", value=precio_val, min_value=0.01, key="precio_e")
                
                guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
                eliminar_registro = st.form_submit_button("🗑️ Eliminar Registro")
            
                if guardar_cambios:
                    if galones_e <= 0 or precio_e <= 0:
                        st.warning("⚠️ La cantidad de galones y el precio total deben ser mayores a cero.")
                    else:
                        # Preparamos los datos para la actualización. Las columnas de cálculo se recalcularán
                        # en la función update_repostajes_analysis
                        df_update = pd.DataFrame([{
                            "id": registro_id,
                            "fecha": str(fecha_e),
                            "km_actual": km_actual_e,
                            "galones": galones_e,
                            "precio": precio_e,
                            "km_recorridos_acum": np.nan, # Se recalcula en la app
                            "consumo_km_gal": np.nan,
                            "costo_por_km": np.nan
                        }])
                        
                        # --- USO DE GOOGLE SHEETS PARA MODIFICAR ---
                        conn.update(spreadsheet=GSHEETS_URL, worksheet=hoja, data=df_update, row=row_index)
                        # ------------------------------------------

                        st.success("✅ ¡Registro de repostaje actualizado con éxito! Recargando datos para recalcular métricas.")
                        st.session_state.editing = False
                        st.cache_data.clear()
                        st.rerun()

                if eliminar_registro:
                    # --- USO DE GOOGLE SHEETS PARA ELIMINAR ---
                    conn.delete(spreadsheet=GSHEETS_URL, worksheet=hoja, row=row_index)
                    # -----------------------------------------

                    st.success("✅ ¡Registro de repostaje eliminado con éxito! Recargando datos para recalcular métricas.")
                    st.session_state.editing = False
                    st.cache_data.clear()
                    st.rerun()
else:
    st.info("No hay registros para editar o eliminar. ¡Añade uno primero!")
