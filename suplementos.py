import streamlit as st
import pandas as pd
import urllib.parse
import os
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de la interfaz
st.set_page_config(page_title="Suplementos R&A Showroom", page_icon="🌿", layout="wide")

# --- INICIALIZACIÓN DEL CARRITO ---
if "carrito" not in st.session_state:
    st.session_state.carrito = {}

# 2. Conectar y Cargar los datos desde Google Sheets
# Esto busca automáticamente tus contraseñas en la carpeta .streamlit o en la nube
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    # ttl=0 obliga a la app a leer el archivo en vivo, sin usar memoria caché
    return conn.read(worksheet="SHOWROOM", ttl=0)

try:
    df = cargar_datos()
except Exception as e:
    st.error("❌ No se pudo conectar a Google Sheets. Revisa tus contraseñas (secrets.toml).")
    st.error(f"🔍 Detalle técnico del error: {e}")
    st.stop()

# Número de WhatsApp configurado para Suplementos R&A
MI_WHATSAPP = "584145973895" 

# 3. Encabezado principal
st.title("🌿 Suplementos R&A Showroom")
st.write("Arma tu pedido agregando suplementos al carrito y confírmalo en un solo mensaje por WhatsApp.")
st.divider()

# --- SECCIÓN DEL CARRITO DE COMPRAS ---
if st.session_state.carrito:
    cantidad_total_productos = sum(item["cantidad"] for item in st.session_state.carrito.values())
    
    with st.expander(f"🛒 **Mi Carrito de Compras ({cantidad_total_productos} prod.)**", expanded=True):
        total_general = 0
        mensaje_wa = "¡Hola Suplementos R&A! 👋 Quiero realizar el siguiente pedido de mi showroom:\n\n"
        
        for key, item in list(st.session_state.carrito.items()):
            subtotal = item["precio"] * item["cantidad"]
            total_general += subtotal
            
            col_txt, col_btn_eliminar = st.columns([4, 1])
            with col_txt:
                st.write(f"🔹 **{item['cantidad']}x** {item['producto']} *({item['marca']})* — ${subtotal}.00")
            with col_btn_eliminar:
                if st.button("❌", key=f"remove_{key}", help="Quitar del carrito"):
                    del st.session_state.carrito[key]
                    st.rerun()
            
            mensaje_wa += f"• {item['cantidad']}x {item['producto']} ({item['marca']}) -> ${subtotal}.00\n"
        
        st.divider()
        st.write(f"#### 💰 Total a Pagar: **${total_general}.00**")
        st.caption("*Tasa BCV*")
        
        mensaje_wa += f"\n💵 *Total General: ${total_general}.00*\n\n¿Me indican los métodos de pago y disponibilidad por favor?"
        
        col_vaciar, col_enviar = st.columns(2)
        with col_vaciar:
            if st.button("Vaciar Carrito 🗑️", use_container_width=True):
                st.session_state.carrito = {}
                st.rerun()
                
        with col_enviar:
            if st.button("Confirmar Pedido y Procesar 📲", use_container_width=True):
                # 1. Volver a leer la base de datos en este instante
                df_actual = conn.read(worksheet="SHOWROOM", ttl=0)
                
                # 2. Restar lo que el cliente tiene en el carrito
                for key, item in st.session_state.carrito.items():
                    filtro = (df_actual['Producto'] == item['producto']) & (df_actual['Marca'] == item['marca'])
                    df_actual.loc[filtro, 'Stock'] -= item['cantidad']
                
                # 3. Sobrescribir el Google Sheets con el nuevo inventario
                conn.update(worksheet="SHOWROOM", data=df_actual)
                
                # 4. Generar link de WhatsApp
                mensaje_codificado = urllib.parse.quote(mensaje_wa)
                enlace_final = f"https://wa.me/{MI_WHATSAPP}?text={mensaje_codificado}"
                
                # 5. Vaciar carrito para que no lo vuelvan a cobrar
                st.session_state.carrito = {}
                
                # 6. Mostrar mensaje de éxito y enlace final
                st.success("✅ ¡Inventario reservado exitosamente!")
                st.markdown(f"### [👉 Haz clic AQUÍ para enviar tu pedido a nuestro WhatsApp]({enlace_final})")
            
    st.divider()


# 4. Filtros interactivos en la barra lateral
st.sidebar.header("🔍 Panel de Búsqueda")
buscar_producto = st.sidebar.text_input("Buscar por nombre del producto:", "")

columna_marca = "Marca" if "Marca" in df.columns else df.columns[1] if len(df.columns) > 1 else None

if columna_marca:
    marcas_disponibles = ["Todas"] + list(df[columna_marca].dropna().unique())
    marca_selected = st.sidebar.selectbox("Filtrar por marca:", marcas_disponibles)
else:
    marca_selected = "Todas"

# 5. Lógica de filtrado de datos
df_filtrado = df.copy()

columna_producto = "Producto" if "Producto" in df.columns else df.columns[0]

if buscar_producto:
    df_filtrado = df_filtrado[df_filtrado[columna_producto].str.contains(buscar_producto, case=False, na=False)]

if marca_selected != "Todas" and columna_marca:
    df_filtrado = df_filtrado[df_filtrado[columna_marca] == marca_selected]

# 6. Despliegue de los productos en la vitrina
if df_filtrado.empty:
    st.warning("No se encontraron productos que coincidan con tu búsqueda.")
else:
    for index, row in df_filtrado.iterrows():
        with st.container(border=True):
            col_img, col_info, col_accion = st.columns([1, 3, 1])
            
            # Extracción segura de datos
            prod_nombre = row.get("Producto", df.iloc[index, 0])
            prod_marca = row.get("Marca", "Sin marca")
            prod_presentacion = row.get("Presentación", row.get("Presentacion", "---"))
            prod_duracion = row.get("Duración", row.get("Duracion", "---"))
            prod_propiedades = row.get("Propiedades", "No hay propiedades registradas.")
            prod_precio = row.get("Precio", 0)
            prod_imagen = row.get("Imagen", None)
            prod_tratamiento = row.get("tratamiento", row.get("Tratamiento", None))
            
            # --- Columna 1: Imagen del Producto ---
            with col_img:
                if prod_imagen and pd.notna(prod_imagen):
                    ruta_imagen = str(prod_imagen).strip()
                    if os.path.exists(ruta_imagen):
                        st.image(ruta_imagen, use_container_width=True)
                    else:
                        st.info("📸\nFoto en camino")
                else:
                    st.info("📸\nSin imagen")
            
            # --- Columna 2: Información del Producto ---
            with col_info:
                st.subheader(prod_nombre)
                
                linea_detalles = f"🏷️ **Marca:** {prod_marca} | 💊 **Presentación:** {prod_presentacion} | ⏳ **Duración:** {prod_duracion}"
                
                if pd.notna(prod_tratamiento) and str(prod_tratamiento).strip() != "":
                    modo_uso_limpio = str(prod_tratamiento).replace(".- ", "").replace("\n", " ").strip()
                    linea_detalles += f" | 📝 **Modo de uso:** {modo_uso_limpio}"
                
                st.caption(linea_detalles)
                
                st.markdown("**Propiedades:**")
                propiedades_limpias = str(prod_propiedades).replace(".- ", "* ")
                st.markdown(propiedades_limpias)
                
            # --- Columna 3: Precio y Agregar al Carrito (CON LÓGICA DE STOCK) ---
            with col_accion:
                st.write("### ") 
                st.metric(label="Precio", value=f"${prod_precio}.00")
                st.caption("*Tasa BCV*")
                
                id_unico_producto = f"{prod_nombre}_{prod_marca}"
                
                # Extraemos el stock de Google Sheets (si la celda está vacía, asume 0)
                try:
                    prod_stock = int(row.get("Stock", 0))
                except:
                    prod_stock = 0
                
                # Calculamos cuántos de este producto ya están en el carrito de este cliente
                cantidad_en_carrito = 0
                if id_unico_producto in st.session_state.carrito:
                    cantidad_en_carrito = st.session_state.carrito[id_unico_producto]["cantidad"]
                
                # Restamos para saber cuántos quedan realmente disponibles
                disponible = prod_stock - cantidad_en_carrito
                
                # Mostramos visualmente el inventario
                if prod_stock > 0:
                    st.write(f"📦 **Disponibles: {disponible}**")
                else:
                    st.write("📦 **Agotado**")
                
                # Condicionamos el botón: Si hay disponibles, deja agregar. Si no, se bloquea.
                if disponible > 0:
                    if st.button("Agregar al Carrito 🛒", key=f"add_{index}", use_container_width=True):
                        if id_unico_producto in st.session_state.carrito:
                            st.session_state.carrito[id_unico_producto]["cantidad"] += 1
                        else:
                            st.session_state.carrito[id_unico_producto] = {
                                "producto": prod_nombre,
                                "marca": prod_marca,
                                "precio": prod_precio,
                                "cantidad": 1
                            }
                        st.toast(f"✅ ¡{prod_nombre} añadido al carrito!")
                        st.rerun()
                else:
                    st.button("Sin Stock 🚫", key=f"add_{index}", disabled=True, use_container_width=True)
