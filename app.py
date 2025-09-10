import streamlit as st
import pandas as pd

# Título de la aplicación y descripción
st.title("⛽ Control de Gasto de Combustible")
st.write("Registra tus repostajes para calcular el consumo (km/galón) y el costo ($/km) por recorrido.")

# Sección de entrada de datos
st.header("📝 Ingreso de Datos")

# Widgets para la entrada de datos
fecha = st.date_input("📅 Fecha del repostaje:")
km_inicial = st.number_input("🚗 Kilometraje inicial (km):", min_value=0, step=1)
km_final = st.number_input("🏁 Kilometraje final (km):", min_value=0, step=1)
galones = st.number_input("💧 Cantidad de combustible (galones):", min_value=0.01)
precio = st.number_input("💰 Precio total del repostaje ($ COP):", min_value=0.01)
# Nuevo campo de checkbox para el aire acondicionado
aire_acondicionado = st.checkbox("❄️ ¿Se usó el aire acondicionado?")

# Botón para añadir los datos
if st.button("➕ Añadir Registro"):
    try:
        df_registros = pd.read_csv("registros_combustible.csv")
    except FileNotFoundError:
        # Añadimos la columna 'aire_acondicionado' al DataFrame vacío
        df_registros = pd.DataFrame(columns=["fecha", "km_inicial", "km_final", "galones", "precio", "aire_acondicionado", "km_recorridos", "consumo_km_gal", "costo_por_km"])

    # Validar que los datos sean correctos y coherentes
    if km_final > km_inicial and galones > 0 and precio > 0:
        # Calcular los kilómetros recorridos
        km_recorridos = km_final - km_inicial
        
        # Calcular el consumo (km/galón) y el costo por kilómetro
        consumo_km_gal = km_recorridos / galones
        costo_por_km = precio / km_recorridos

        # Crear un nuevo registro
        nuevo_registro = pd.DataFrame([{
            "fecha": fecha,
            "km_inicial": km_inicial,
            "km_final": km_final,
            "galones": galones,
            "precio": precio,
            "aire_acondicionado": aire_acondicionado,
            "km_recorridos": km_recorridos,
            "consumo_km_gal": consumo_km_gal,
            "costo_por_km": costo_por_km
        }])
        
        # Unir el nuevo registro al DataFrame existente
        df_registros = pd.concat([df_registros, nuevo_registro], ignore_index=True)
        
        # Guardar los datos en un archivo CSV para persistencia
        df_registros.to_csv("registros_combustible.csv", index=False)
        st.success("✅ Registro de recorrido añadido con éxito.")
    else:
        st.warning("⚠️ Por favor, asegúrate de que el kilometraje final sea mayor que el inicial y de completar todos los campos.")

# ---
st.divider()

# Sección de visualización de datos
st.header("📊 Resumen y Análisis por Recorrido")

try:
    # Cargar y mostrar la tabla de datos
    df_registros = pd.read_csv("registros_combustible.csv")
    st.subheader("📋 Historial de Registros de Recorridos")
    st.dataframe(df_registros)

    # Gráficos si hay suficientes datos
    if len(df_registros) > 0:
        # Gráfico de consumo por recorrido
        st.subheader("📈 Consumo por Recorrido (km/galón)")
        st.line_chart(df_registros["consumo_km_gal"])

        # Gráfico de costo por kilómetro
        st.subheader("📉 Costo por Kilómetro ($ COP)")
        st.line_chart(df_registros["costo_por_km"])

        # Métricas clave
        st.subheader("💡 Métricas Clave Promedio")
        promedio_consumo = df_registros["consumo_km_gal"].mean()
        promedio_costo = df_registros["costo_por_km"].mean()
        
        st.metric(label="Consumo Promedio (km/galón)", value=f"{promedio_consumo:.2f}")
        st.metric(label="Costo Promedio por Kilómetro", value=f"${promedio_costo:,.2f} COP")

        # Análisis con y sin aire acondicionado
        st.subheader("Análisis comparativo (con/sin aire acondicionado)")
        
        # Filtrar datos con aire acondicionado
        df_con_ac = df_registros[df_registros["aire_acondicionado"] == True]
        if not df_con_ac.empty:
            consumo_con_ac = df_con_ac["consumo_km_gal"].mean()
            st.metric("Consumo Promedio (con A/C)", value=f"{consumo_con_ac:.2f} km/galón")
        else:
            st.info("No hay registros con aire acondicionado para analizar.")

        # Filtrar datos sin aire acondicionado
        df_sin_ac = df_registros[df_registros["aire_acondicionado"] == False]
        if not df_sin_ac.empty:
            consumo_sin_ac = df_sin_ac["consumo_km_gal"].mean()
            st.metric("Consumo Promedio (sin A/C)", value=f"{consumo_sin_ac:.2f} km/galón")
        else:
            st.info("No hay registros sin aire acondicionado para analizar.")

except FileNotFoundError:
    st.info("No hay registros guardados. ¡Empieza a añadir tu primer recorrido!")
