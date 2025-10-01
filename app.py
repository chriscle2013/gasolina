import streamlit as st
import pandas as pd
import numpy as np
import uuid
from pathlib import Path
import os
import time

# --- CONFIGURACIÓN DE ARCHIVOS ---
# Rutas relativas a la carpeta 'data/' en tu repositorio
BASE_DIR = Path(__file__).resolve().parent
RECORRIDOS_PATH = BASE_DIR / "data" / "recorridos.csv"
REPOSTAJES_PATH = BASE_DIR / "data" / "repostajes.csv"

# --- FUNCIONES DE LECTURA Y ESCRITURA ---

@st.cache_data(ttl=1) # Cachea por 1 segundo para ver los cambios rápidamente
def load_data(file_path, sheet_name):
    """Carga datos desde un archivo CSV local o lo crea si no existe."""
    cols_recorridos = ["id", "fecha", "km_inicial", "km_final", "km_recorridos", "aire_acondicionado", "km_restante"]
    cols_repostajes = ["id", "fecha", "km_actual", "galones", "precio", "km_recorridos_acum", "consumo_km_gal", "costo_por_km"]
    
    # Define las columnas basadas en el nombre del archivo
    cols = cols_recorridos if sheet_name == "Recorridos" else cols_repostajes

    if not file_path.exists():
        # Crea un DataFrame vacío si el archivo no existe
        df = pd.DataFrame(columns=cols)
        # Inicializa el archivo CSV vacío con solo los encabezados
        df.to_csv(file_path, index=False)
        return df
    
    try:
        df = pd.read_csv(file_path)
        df = df.dropna(how='all') # Elimina filas completamente vacías
        
        # Forzar tipos para cálculos
        if sheet_name == "Recorridos":
            for col in ['km_inicial', 'km_final', 'km_recorridos', 'km_restante']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            df['aire_acondicionado'] = df['aire_acondicionado'].astype(bool)
        elif sheet_name == "Repostajes":
            df['km_actual'] = pd.to_numeric(df['km_actual'], errors='coerce').fillna(0).astype(int)
            df['galones'] = pd.to_numeric(df['galones'], errors='coerce').fillna(0.0)
            df['precio'] = pd.to_numeric(df['precio'], errors='coerce').fillna(0.0)

        return df
    except Exception as e:
        st.error(f"Error al leer el archivo {file_path.name}: {e}. Asegúrate de que los encabezados son correctos.")
        return pd.DataFrame(columns=cols)

def update_repostajes_analysis(df_repostajes):
    """Recalcula las métricas de repostaje después de un cambio."""
    df_repostajes = df_repostajes.sort_values(by="fecha").reset_index(drop=True)
    
    # Inicializar columnas que se recalcularán
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

def save_data(df, file_path):
    """Guarda el DataFrame en el archivo CSV."""
    try:
        df.to_csv(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar los datos en {file_path.name}: {e}")
        return False

# --- LÓGICA PRINCIPAL ---

st.title("⛽ Control de Gasto de Combustible (Almacenamiento Local)")
st.write("Los datos se guardan directamente en archivos CSV en tu repositorio de GitHub.")

# Recarga los datos globales
df_recorridos_global = load_data(RECORRIDOS_PATH, "Recorridos")
df_repostajes_global = load_data(REPOSTAJES_PATH, "Repostajes")


# -----------------
# FORMULARIO DE RECORRIDOS (CREACIÓN)
# -----------------
st.header("1️⃣ Registrar Recorrido Diario")
with st.form("recorrido_form", clear_on_submit=True):
    fecha_recorrido = st.date_input("📅 Fecha del recorrido:", value="today")
    km_inicial_recorrido = st.number_input("🚗 Kilometraje inicial (km):", min_value=0, step=1, key="ki_r")
    km_final_recorrido = st.number_input("🏁 Kilometraje final (km):", min_value=0, step=1, key="kf_r")
    aire_acondicionado = st.checkbox("❄️ ¿Se usó el aire acondicionado?", key="ac_r")
    km_restante = st.number_input("🎯 Kilometraje restante en el tablero (km):", min_value=0, step=1, key="kr_r")

    submitted_recorrido = st.form_submit_button("➕ Añadir Recorrido")

    if submitted_recorrido:
        if km_final_recorrido > km_inicial_recorrido:
            
            km_recorridos = km_final_recorrido - km_inicial_recorrido
            
            nuevo_recorrido = pd.DataFrame([{
                "id": str(uuid.uuid4()),
                "fecha": str(fecha_recorrido),
                "km_inicial": km_inicial_recorrido,
                "km_final": km_final_recorrido,
                "km_recorridos": km_recorridos,
                "aire_acondicionado": aire_acondicionado,
                "km_restante": km_restante
            }])
            
            # 1. Combina el nuevo registro con el DataFrame global
            df_recorridos_updated = pd.concat([df_recorridos_global, nuevo_recorrido], ignore_index=True)
            
            # 2. Guarda el DataFrame actualizado en el archivo CSV
            if save_data(df_recorridos_updated, RECORRIDOS_PATH):
                st.success("✅ Recorrido registrado con éxito.")
                st.cache_data.clear()
                time.sleep(0.1) # Pausa mínima para que el sistema de archivos se actualice
                st.rerun()
        else:
            st.warning("⚠️ El kilometraje final debe ser mayor que el inicial.")

st.divider()

# -----------------
# FORMULARIO DE REPOSTAJE (CREACIÓN)
# -----------------
st.header("⛽ Registrar Repostaje")
with st.form("repostaje_form", clear_on_submit=True):
    fecha_repostaje = st.date_input("📅 Fecha del repostaje:", value="today", key="f_rep")
    km_actual_repostaje = st.number_input("🚗 Kilometraje actual:", min_value=0, step=1, key="ka_rep")
    galones_repostaje = st.number_input("💧 Cantidad de combustible (galones):", min_value=0.01, key="g_rep")
    precio_repostaje = st.number_input("💰 Precio total del repostaje ($ COP):", min_value=0.01, key="p_rep")

    submitted_repostaje = st.form_submit_button("➕ Añadir Repostaje")
    
    if submitted_repostaje:
        if galones_repostaje <= 0 or precio_repostaje <= 0:
            st.warning("⚠️ La cantidad de galones y el precio total deben ser mayores a cero.")
        else:
            
            nuevo_repostaje = pd.DataFrame([{
                "id": str(uuid.uuid4()),
                "fecha": str(fecha_repostaje),
                "km_actual": km_actual_repostaje,
                "galones": galones_repostaje,
                "precio": precio_repostaje,
                "km_recorridos_acum": np.nan, 
                "consumo_km_gal": np.nan,
                "costo_por_km": np.nan
            }])
            
            # 1. Combina el nuevo registro con el DataFrame global
            df_repostajes_updated = pd.concat([df_repostajes_global, nuevo_repostaje], ignore_index=True)

            # 2. Guarda el DataFrame actualizado en el archivo CSV
            if save_data(df_repostajes_updated, REPOSTAJES_PATH):
                st.success("✅ Repostaje registrado con éxito. El análisis de consumo se actualizará al recargar.")
                st.cache_data.clear()
                time.sleep(0.1)
                st.rerun()

st.divider()

# -----------------
# SECCIÓN DE ANÁLISIS
# -----------------
st.header("📊 Resumen y Análisis")

df_recorridos = load_data(RECORRIDOS_PATH, "Recorridos")
st.subheader("📋 Historial de Recorridos")
if not df_recorridos.empty:
    st.dataframe(df_recorridos.drop(columns=["id"]).sort_values(by="fecha", ascending=False))
else:
    st.info("No hay registros de recorridos guardados.")

st.divider()

df_repostajes = load_data(REPOSTAJES_PATH, "Repostajes")
df_repostajes_analisis = update_repostajes_analysis(df_repostajes.copy())

st.subheader("📋 Historial de Repostajes")
if not df_repostajes.empty:
    st.dataframe(df_repostajes_analisis.drop(columns=["id"]).sort_values(by="fecha", ascending=False))
    # ... (El resto del análisis de gráficas y métricas es el mismo)
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
        # Asegúrate de que df_recorridos no esté vacío antes de acceder a iloc[-1]
        if not df_recorridos.empty and "km_restante" in df_recorridos.columns:
            st.metric(label="Kilometraje restante estimado", value=f"{df_recorridos['km_restante'].iloc[-1]} km")
    else:
        st.info("No hay suficientes registros de repostaje con datos de recorrido (Km/galón) para mostrar el análisis.")
else:
    st.info("No hay registros de repostaje guardados.")

st.divider()

# -----------------
# SECCIÓN DE EDICIÓN Y ELIMINACIÓN
# -----------------
st.header("✏️ Editar o Eliminar Registros")
st.info("Selecciona, edita y luego guarda. Esto reescribirá el archivo CSV.")

# Recarga de datos para edición
df_recorridos = load_data(RECORRIDOS_PATH, "Recorridos")
df_repostajes = load_data(REPOSTAJES_PATH, "Repostajes")

if not df_recorridos.empty or not df_repostajes.empty:
    # Lógica para combinar y seleccionar (similar a la versión de Google Sheets)
    df_registros_combinados = pd.concat([
        df_recorridos.assign(tipo='Recorrido'),
        df_repostajes.assign(tipo='Repostaje')
    ], ignore_index=True)
    
    df_registros_combinados = df_registros_combinados.sort_values(by="fecha", ascending=False).reset_index(drop=True)

    opciones_edicion = [f"Tipo: {row['tipo']} | Fecha: {row['fecha']}" for i, row in df_registros_combinados.iterrows()]
    
    registro_a_editar_indice = st.selectbox("Selecciona el registro a editar:", range(len(opciones_edicion)), format_func=lambda i: opciones_edicion[i], key="sel_edit")
    
    if st.button("📝 Cargar para editar", key="btn_load"):
        st.session_state.registro_seleccionado = df_registros_combinados.iloc[registro_a_editar_indice]
        st.session_state.editing = True
        st.rerun()

    if "editing" in st.session_state and st.session_state.editing:
        st.subheader("Formulario de Edición")
        registro_actual = st.session_state.registro_seleccionado
        
        with st.form("formulario_edicion"):
            st.markdown(f"**Editando registro de tipo:** **{registro_actual['tipo']}**")
            
            registro_id = registro_actual['id']
            tipo = registro_actual['tipo']
            file_path = RECORRIDOS_PATH if tipo == 'Recorrido' else REPOSTAJES_PATH
            df_hoja_completa = df_recorridos if tipo == 'Recorrido' else df_repostajes
            
            # Encuentra el índice basado en el ID para actualizar el DataFrame
            idx_to_update = df_hoja_completa[df_hoja_completa['id'] == registro_id].index[0]

            fecha_e = st.date_input("📅 Fecha", value=pd.to_datetime(registro_actual["fecha"]), key="fecha_e_csv")
            
            if tipo == 'Recorrido':
                # Obtención de valores y widgets de edición
                km_inicial_e = st.number_input("🚗 Kilometraje inicial (km)", value=int(registro_actual.get("km_inicial", 0)), min_value=0, step=1, key="ki_e_csv")
                km_final_e = st.number_input("🏁 Kilometraje final (km)", value=int(registro_actual.get("km_final", 0)), min_value=0, step=1, key="kf_e_csv")
                aire_acondicionado_e = st.checkbox("❄️ ¿Se usó el aire acondicionado?", value=bool(registro_actual.get("aire_acondicionado", False)), key="ac_e_csv")
                km_restante_e = st.number_input("🎯 Kilometraje restante en el tablero (km)", value=int(registro_actual.get("km_restante", 0)), min_value=0, step=1, key="kr_e_csv")

                col_g, col_e = st.columns(2)
                with col_g:
                    guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
                with col_e:
                    eliminar_registro = st.form_submit_button("🗑️ Eliminar Registro")

                if guardar_cambios:
                    if km_final_e > km_inicial_e:
                        km_recorridos_e = km_final_e - km_inicial_e
                        
                        # Actualiza la fila en el DataFrame en memoria
                        df_hoja_completa.loc[idx_to_update, "fecha"] = str(fecha_e)
                        df_hoja_completa.loc[idx_to_update, "km_inicial"] = km_inicial_e
                        df_hoja_completa.loc[idx_to_update, "km_final"] = km_final_e
                        df_hoja_completa.loc[idx_to_update, "km_recorridos"] = km_recorridos_e
                        df_hoja_completa.loc[idx_to_update, "aire_acondicionado"] = aire_acondicionado_e
                        df_hoja_completa.loc[idx_to_update, "km_restante"] = km_restante_e
                        
                        if save_data(df_hoja_completa, file_path):
                            st.success("✅ ¡Registro de recorrido actualizado con éxito!")
                            st.session_state.editing = False
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        st.warning("⚠️ El kilometraje final debe ser mayor que el inicial para guardar.")
                
                if eliminar_registro:
                    # Elimina la fila del DataFrame
                    df_hoja_completa = df_hoja_completa.drop(index=idx_to_update).reset_index(drop=True)

                    if save_data(df_hoja_completa, file_path):
                        st.success("✅ ¡Registro de recorrido eliminado con éxito!")
                        st.session_state.editing = False
                        st.cache_data.clear()
                        st.rerun()

            elif tipo == 'Repostaje':
                # Obtención de valores y widgets de edición
                km_actual_e = st.number_input("🚗 Kilometraje actual:", value=int(registro_actual.get("km_actual", 0)), min_value=0, step=1, key="ka_e_csv")
                galones_e = st.number_input("💧 Cantidad de combustible (galones)", value=float(registro_actual.get("galones", 0.01)), min_value=0.01, key="g_e_csv")
                precio_e = st.number_input("💰 Precio total del repostaje ($ COP)", value=float(registro_actual.get("precio", 0.01)), min_value=0.01, key="p_e_csv")
                
                col_g, col_e = st.columns(2)
                with col_g:
                    guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
                with col_e:
                    eliminar_registro = st.form_submit_button("🗑️ Eliminar Registro")
            
                if guardar_cambios:
                    if galones_e <= 0 or precio_e <= 0:
                        st.warning("⚠️ La cantidad de galones y el precio total deben ser mayores a cero.")
                    else:
                        # Actualiza la fila en el DataFrame en memoria
                        df_hoja_completa.loc[idx_to_update, "fecha"] = str(fecha_e)
                        df_hoja_completa.loc[idx_to_update, "km_actual"] = km_actual_e
                        df_hoja_completa.loc[idx_to_update, "galones"] = galones_e
                        df_hoja_completa.loc[idx_to_update, "precio"] = precio_e

                        if save_data(df_hoja_completa, file_path):
                            st.success("✅ ¡Registro de repostaje actualizado con éxito!")
                            st.session_state.editing = False
                            st.cache_data.clear()
                            st.rerun()

                if eliminar_registro:
                    # Elimina la fila del DataFrame
                    df_hoja_completa = df_hoja_completa.drop(index=idx_to_update).reset_index(drop=True)

                    if save_data(df_hoja_completa, file_path):
                        st.success("✅ ¡Registro de repostaje eliminado con éxito!")
                        st.session_state.editing = False
                        st.cache_data.clear()
                        st.rerun()
else:
    st.info("No hay registros para editar o eliminar. ¡Añade uno primero!")
