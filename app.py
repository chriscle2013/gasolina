import streamlit as st
import pandas as pd
import numpy as np
import uuid
import sqlite3
import time
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Control de Combustible SQLite")

# ----------------------------------------
# 🚀 CONEXIÓN PERSISTENTE CON SQLITE
# ----------------------------------------

@st.cache_resource
def get_db_connection():
    """Establece y mantiene la conexión a la base de datos SQLite."""
    try:
        # La base de datos se guarda en la caché de recursos persistente de Streamlit.
        conn = sqlite3.connect('app_data.sqlite')
        return conn
    except Exception as e:
        # CORRECCIÓN CRÍTICA: Si falla la conexión, mostramos el error y detenemos el script
        st.error(f"Error CRÍTICO al conectar con SQLite: {e}")
        st.stop()
        # Nota: La función debe retornar algo, aunque st.stop() ya detiene la ejecución
        return None 

def create_tables(conn):
    """Crea las tablas Recorridos y Repostajes si aún no existen."""
    # La validación de 'conn' ahora ocurre antes de llamar esta función.
    cursor = conn.cursor()
    
    # 1. Tabla Recorridos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recorridos (
            id TEXT PRIMARY KEY,
            fecha TEXT,
            km_inicial INTEGER,
            km_final INTEGER,
            km_recorridos INTEGER,
            aire_acondicionado BOOLEAN,
            km_restante INTEGER
        )
    """)
    
    # 2. Tabla Repostajes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repostajes (
            id TEXT PRIMARY KEY,
            fecha TEXT,
            km_actual INTEGER,
            galones REAL,
            precio REAL,
            km_recorridos_acum REAL,
            consumo_km_gal REAL,
            costo_por_km REAL
        )
    """)
    conn.commit()

@st.cache_data(ttl=1)
def load_data(table_name):
    """Carga todos los datos de una tabla a un DataFrame de Pandas."""
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        # Conversión de tipos de datos para cálculos
        if table_name == "recorridos":
            for col in ['km_inicial', 'km_final', 'km_recorridos', 'km_restante']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            df['aire_acondicionado'] = df['aire_acondicionado'].astype(bool)
        elif table_name == "repostajes":
            df['km_actual'] = pd.to_numeric(df['km_actual'], errors='coerce').fillna(0).astype(int)
            df['galones'] = pd.to_numeric(df['galones'], errors='coerce').fillna(0.0)
            df['precio'] = pd.to_numeric(df['precio'], errors='coerce').fillna(0.0)
            
        return df
    except Exception as e:
        st.error(f"Error al leer la tabla {table_name}: {e}")
        return pd.DataFrame()

def execute_query(query, params=()):
    """Ejecuta una consulta SQL y fuerza la recarga de datos."""
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        st.cache_data.clear() # Limpia la caché para que load_data recargue con los nuevos datos
        st.rerun()
        return True
    except Exception as e:
        st.error(f"Error al ejecutar la consulta: {e}")
        return False

def update_repostajes_analysis(df_repostajes):
    """Recalcula las métricas de repostaje después de un cambio."""
    if df_repostajes.empty:
        return df_repostajes
    
    # Asegura que las fechas sean tratadas como fechas y ordena
    df_repostajes['fecha'] = pd.to_datetime(df_repostajes['fecha'])
    df_repostajes = df_repostajes.sort_values(by="fecha").reset_index(drop=True)
    
    # Inicializar columnas que se recalcularán
    df_repostajes['km_recorridos_acum'] = np.nan
    df_repostajes['consumo_km_gal'] = np.nan
    df_repostajes['costo_por_km'] = np.nan

    if len(df_repostajes) > 1:
        # Los cálculos se basan en la diferencia entre el KM actual y el KM del repostaje anterior
        df_repostajes['km_anterior'] = df_repostajes['km_actual'].shift(1)
        df_repostajes['km_recorridos_acum'] = df_repostajes['km_actual'] - df_repostajes['km_anterior']
        
        # Aplicar cálculos solo a las filas con datos de repostajes válidos
        for i in range(1, len(df_repostajes)):
            km_rec = df_repostajes.loc[i, 'km_recorridos_acum']
            galones = df_repostajes.loc[i, 'galones']
            precio = df_repostajes.loc[i, 'precio']
            
            if km_rec > 0 and galones > 0:
                df_repostajes.loc[i, "consumo_km_gal"] = km_rec / galones
                df_repostajes.loc[i, "costo_por_km"] = precio / km_rec
            else:
                # Si el dato es inválido, forzar NaN para que no contamine el promedio
                df_repostajes.loc[i, "km_recorridos_acum"] = np.nan 

    df_repostajes = df_repostajes.drop(columns=['km_anterior']).round(2)
    return df_repostajes

# ----------------------------------------
# 🎯 INICIALIZACIÓN DE LA APLICACIÓN
# ----------------------------------------

conn = get_db_connection() 
# Si get_db_connection() falla, la línea st.stop() dentro detiene el script
# antes de que intente usar 'conn' aquí.

create_tables(conn) 

# Carga inicial de datos (para usar en el resto de la app)
df_recorridos_global = load_data("recorridos")
df_repostajes_global = load_data("repostajes")

st.title("⛽ Control de Gasto de Combustible (SQLite)")
st.caption("Los datos se guardan de forma persistente gracias a la caché de recursos de Streamlit.")

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
            
            query = """
                INSERT INTO recorridos 
                (id, fecha, km_inicial, km_final, km_recorridos, aire_acondicionado, km_restante) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                str(uuid.uuid4()), 
                str(fecha_recorrido), 
                km_inicial_recorrido, 
                km_final_recorrido, 
                km_recorridos, 
                aire_acondicionado, 
                km_restante
            )
            
            if execute_query(query, params):
                st.success("✅ Recorrido registrado con éxito.")
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
            
            query = """
                INSERT INTO repostajes 
                (id, fecha, km_actual, galones, precio, km_recorridos_acum, consumo_km_gal, costo_por_km) 
                VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL)
            """
            params = (
                str(uuid.uuid4()), 
                str(fecha_repostaje), 
                km_actual_repostaje, 
                galones_repostaje, 
                precio_repostaje
            )
            
            if execute_query(query, params):
                st.success("✅ Repostaje registrado con éxito. El análisis de consumo se actualizará al recargar.")

st.divider()

# -----------------
# SECCIÓN DE ANÁLISIS
# -----------------
st.header("📊 Resumen y Análisis")

df_recorridos = load_data("recorridos")
st.subheader("📋 Historial de Recorridos")
if not df_recorridos.empty:
    st.dataframe(df_recorridos.drop(columns=["id"]).sort_values(by="fecha", ascending=False), use_container_width=True)
else:
    st.info("No hay registros de recorridos guardados.")

st.divider()

df_repostajes = load_data("repostajes")
df_repostajes_analisis = update_repostajes_analysis(df_repostajes.copy())

st.subheader("📋 Historial de Repostajes")
if not df_repostajes.empty:
    st.dataframe(df_repostajes_analisis.drop(columns=["id"]).sort_values(by="fecha", ascending=False), use_container_width=True)
    
    # Lógica para mostrar métricas y gráficas
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
        st.info("No hay suficientes registros de repostaje con datos de recorrido para el análisis.")
else:
    st.info("No hay registros de repostaje guardados.")

st.divider()

# -----------------
# SECCIÓN DE EDICIÓN Y ELIMINACIÓN
# -----------------
st.header("✏️ Editar o Eliminar Registros")

if not df_recorridos.empty or not df_repostajes.empty:
    
    # Preparación de datos combinados para el selectbox
    df_registros_combinados = pd.concat([
        df_recorridos.assign(tipo='Recorrido'),
        df_repostajes.assign(tipo='Repostaje')
    ], ignore_index=True, sort=False)
    
    df_registros_combinados = df_registros_combinados.sort_values(by="fecha", ascending=False).reset_index(drop=True)

    opciones_edicion = [f"Tipo: {row['tipo']} | Fecha: {row['fecha']}" for i, row in df_registros_combinados.iterrows()]
    
    # El índice seleccionado en el selectbox
    registro_a_editar_indice = st.selectbox("Selecciona el registro a editar:", range(len(opciones_edicion)), format_func=lambda i: opciones_edicion[i], key="sel_edit")
    
    # Cargar el registro seleccionado al estado de sesión para edición
    if st.button("📝 Cargar para editar", key="btn_load"):
        st.session_state.registro_seleccionado = df_registros_combinados.iloc[registro_a_editar_indice].to_dict()
        st.session_state.editing = True
        st.rerun()

    if "editing" in st.session_state and st.session_state.editing:
        st.subheader("Formulario de Edición")
        registro_actual = st.session_state.registro_seleccionado
        
        with st.form("formulario_edicion"):
            st.markdown(f"**Editando registro de tipo:** **{registro_actual['tipo']}**")
            
            registro_id = registro_actual['id']
            tipo = registro_actual['tipo']
            table_name = 'recorridos' if tipo == 'Recorrido' else 'repostajes'
            
            # Formato de fecha para el widget
            fecha_e_dt = pd.to_datetime(registro_actual.get("fecha")).date()
            fecha_e = st.date_input("📅 Fecha", value=fecha_e_dt, key="fecha_e_sql")

            if tipo == 'Recorrido':
                # Widgets de edición
                km_inicial_e = st.number_input("🚗 Kilometraje inicial (km)", value=int(registro_actual.get("km_inicial", 0)), min_value=0, step=1, key="ki_e_sql")
                km_final_e = st.number_input("🏁 Kilometraje final (km)", value=int(registro_actual.get("km_final", 0)), min_value=0, step=1, key="kf_e_sql")
                aire_acondicionado_e = st.checkbox("❄️ ¿Se usó el aire acondicionado?", value=bool(registro_actual.get("aire_acondicionado", False)), key="ac_e_sql")
                km_restante_e = st.number_input("🎯 Kilometraje restante en el tablero (km)", value=int(registro_actual.get("km_restante", 0)), min_value=0, step=1, key="kr_e_sql")

                col_g, col_e = st.columns(2)
                with col_g:
                    guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
                with col_e:
                    eliminar_registro = st.form_submit_button("🗑️ Eliminar Registro")

                if guardar_cambios:
                    if km_final_e > km_inicial_e:
                        km_recorridos_e = km_final_e - km_inicial_e
                        
                        query = """
                            UPDATE recorridos SET 
                            fecha = ?, km_inicial = ?, km_final = ?, km_recorridos = ?, 
                            aire_acondicionado = ?, km_restante = ? 
                            WHERE id = ?
                        """
                        params = (str(fecha_e), km_inicial_e, km_final_e, km_recorridos_e, 
                                  aire_acondicionado_e, km_restante_e, registro_id)
                        
                        if execute_query(query, params):
                            st.success("✅ ¡Registro de recorrido actualizado con éxito!")
                            st.session_state.editing = False
                    else:
                        st.warning("⚠️ El kilometraje final debe ser mayor que el inicial para guardar.")
                
                if eliminar_registro:
                    query = "DELETE FROM recorridos WHERE id = ?"
                    if execute_query(query, (registro_id,)):
                        st.success("✅ ¡Registro de recorrido eliminado con éxito!")
                        st.session_state.editing = False

            elif tipo == 'Repostaje':
                # Widgets de edición
                km_actual_e = st.number_input("🚗 Kilometraje actual:", value=int(registro_actual.get("km_actual", 0)), min_value=0, step=1, key="ka_e_sql")
                galones_e = st.number_input("💧 Cantidad de combustible (galones)", value=float(registro_actual.get("galones", 0.01)), min_value=0.01, key="g_e_sql")
                precio_e = st.number_input("💰 Precio total del repostaje ($ COP)", value=float(registro_actual.get("precio", 0.01)), min_value=0.01, key="p_e_sql")
                
                col_g, col_e = st.columns(2)
                with col_g:
                    guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
                with col_e:
                    eliminar_registro = st.form_submit_button("🗑️ Eliminar Registro")
            
                if guardar_cambios:
                    if galones_e <= 0 or precio_e <= 0:
                        st.warning("⚠️ La cantidad de galones y el precio total deben ser mayores a cero.")
                    else:
                        # La actualización de métricas (consumo, costo) se hace automáticamente en la carga
                        query = """
                            UPDATE repostajes SET 
                            fecha = ?, km_actual = ?, galones = ?, precio = ? 
                            WHERE id = ?
                        """
                        params = (str(fecha_e), km_actual_e, galones_e, precio_e, registro_id)

                        if execute_query(query, params):
                            st.success("✅ ¡Registro de repostaje actualizado con éxito!")
                            st.session_state.editing = False

                if eliminar_registro:
                    query = "DELETE FROM repostajes WHERE id = ?"
                    if execute_query(query, (registro_id,)):
                        st.success("✅ ¡Registro de repostaje eliminado con éxito!")
                        st.session_state.editing = False
else:
    st.info("No hay registros para editar o eliminar. ¡Añade uno primero!")
