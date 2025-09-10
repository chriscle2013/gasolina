import streamlit as st
import pandas as pd

# Título de la aplicación y descripción
st.title("⛽ Control de Gasto de Combustible")
st.write("Registra tus repostajes para calcular el consumo y el costo de combustible por kilómetro.")

# Sección de entrada de datos
st.header("📝 Ingreso de Datos")

# Widgets para la entrada de datos
fecha = st.date_input("📅 Fecha del repostaje:")
kilometraje = st.number_input("🚗 Kilometraje actual (km):", min_value=0, step=1)
litros = st.number_input("💧 Cantidad de combustible (litros):", min_value=0.01)
precio = st.number_input("💰 Precio total del repostaje:", min_value=0.01)

# Botón para añadir los datos
if st.button("➕ Añadir Registro"):
    # Cargar datos existentes o crear un DataFrame vacío si no existe
    try:
        df_registros = pd.read_csv("registros_combustible.csv")
    except FileNotFoundError:
        df_registros = pd.DataFrame(columns=["fecha", "kilometraje", "litros", "precio"])

    # Validar que se ingresen los datos correctamente
    if kilometraje > 0 and litros > 0 and precio > 0:
        # Calcular el costo por litro
        costo_por_litro = precio / litros
        
        # Calcular el consumo (km/l) solo si hay registros previos
        if not df_registros.empty:
            km_recorridos = kilometraje - df_registros["kilometraje"].iloc[-1]
            litros_consumidos = litros
            consumo_km_l = km_recorridos / litros_consumidos if litros_consumidos > 0 else 0
            costo_por_km = precio / km_recorridos if km_recorridos > 0 else 0
        else:
            consumo_km_l = 0
            costo_por_km = 0

        # Crear un nuevo registro
        nuevo_registro = pd.DataFrame([{
            "fecha": fecha,
            "kilometraje": kilometraje,
            "litros": litros,
            "precio": precio,
            "costo_por_litro": costo_por_litro,
            "consumo_km_l": consumo_km_l,
            "costo_por_km": costo_por_km
        }])
        
        # Unir el nuevo registro al DataFrame existente
        df_registros = pd.concat([df_registros, nuevo_registro], ignore_index=True)
        
        # Guardar los datos en un archivo CSV para persistencia
        df_registros.to_csv("registros_combustible.csv", index=False)
        st.success("✅ Registro añadido con éxito.")
    else:
        st.warning("⚠️ Por favor, completa todos los campos para añadir un registro.")

# ---
st.divider()

# Sección de visualización de datos
st.header("📊 Resumen y Análisis")

try:
    # Cargar y mostrar la tabla de datos
    df_registros = pd.read_csv("registros_combustible.csv")
    st.subheader("📋 Historial de Registros")
    st.dataframe(df_registros)

    # Gráficos si hay suficientes datos (más de un registro)
    if len(df_registros) > 1:
        # Gráfico de consumo
        st.subheader("📈 Evolución del Consumo (km/L)")
        st.line_chart(df_registros["consumo_km_l"])

        # Gráfico de costo por kilómetro
        st.subheader("📉 Evolución del Costo por Kilómetro")
        st.line_chart(df_registros["costo_por_km"])

        # Resumen de métricas
        st.subheader("💡 Métricas Clave")
        promedio_consumo = df_registros["consumo_km_l"].mean()
        promedio_costo = df_registros["costo_por_km"].mean()
        
        st.metric(label="Consumo Promedio (km/L)", value=f"{promedio_consumo:.2f}")
        st.metric(label="Costo Promedio por Kilómetro", value=f"${promedio_costo:.2f}")

except FileNotFoundError:
    st.info("No hay registros guardados. ¡Empieza a añadir uno!")
