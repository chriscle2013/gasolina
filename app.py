import streamlit as st
import pandas as pd

# Título y descripción
st.title("⛽ Control de Gasto de Combustible")
st.write("Registra tus tanqueadas para calcular el consumo y el costo de combustible por recorrido.")

# Sección de entrada de datos
st.header("📝 Ingreso de Datos")

# Widgets para la entrada de datos
fecha = st.date_input("📅 Fecha de tanqueada:")
# Nuevo campo para el kilometraje inicial
km_inicial = st.number_input("🚗 Kilometraje inicial del recorrido (km):", min_value=0, step=1)
km_final = st.number_input("🏁 Kilometraje final del recorrido (km):", min_value=0, step=1)
litros = st.number_input("💧 Cantidad de combustible (litros):", min_value=0.01)
precio = st.number_input("💰 Precio total de la tanqueada:", min_value=0.01)

# Botón para añadir los datos
if st.button("➕ Añadir Registro"):
    try:
        df_registros = pd.read_csv("registros_combustible.csv")
    except FileNotFoundError:
        # Añadimos la columna 'km_recorridos' al DataFrame vacío
        df_registros = pd.DataFrame(columns=["fecha", "km_inicial", "km_final", "litros", "precio", "km_recorridos", "consumo_km_l", "costo_por_km"])

    # Validar que los datos sean correctos y coherentes
    if km_final > km_inicial and litros > 0 and precio > 0:
        # Calcular los kilómetros recorridos
        km_recorridos = km_final - km_inicial
        
        # Calcular el consumo y el costo
        consumo_km_l = km_recorridos / litros
        costo_por_km = precio / km_recorridos

        # Crear un nuevo registro
        nuevo_registro = pd.DataFrame([{
            "fecha": fecha,
            "km_inicial": km_inicial,
            "km_final": km_final,
            "litros": litros,
            "precio": precio,
            "km_recorridos": km_recorridos,
            "consumo_km_l": consumo_km_l,
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
    # Mostrar el DataFrame sin la columna de precio
    st.dataframe(df_registros)

    # Gráficos si hay suficientes datos
    if len(df_registros) > 0:
        # Gráfico de consumo por recorrido
        st.subheader("📈 Consumo por Recorrido (km/L)")
        st.line_chart(df_registros["consumo_km_l"])

        # Gráfico de costo por kilómetro
        st.subheader("📉 Costo por Kilómetro por Recorrido")
        st.line_chart(df_registros["costo_por_km"])

        # Métricas clave
        st.subheader("💡 Métricas Clave Promedio")
        promedio_consumo = df_registros["consumo_km_l"].mean()
        promedio_costo = df_registros["costo_por_km"].mean()
        
        st.metric(label="Consumo Promedio (km/L)", value=f"{promedio_consumo:.2f}")
        st.metric(label="Costo Promedio por Kilómetro", value=f"${promedio_costo:.2f}")

except FileNotFoundError:
    st.info("No hay registros guardados. ¡Empieza a añadir tu primer recorrido!")
