import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. Configuración de la interfaz
st.set_page_config(page_title="Suplementos R&A Showroom", page_icon="🌿", layout="wide")

# --- INICIALIZACIÓN DEL CARRITO ---
if "carrito" not in st.session_state:
    st.session_state.carrito = {}

# 2. Cargar los datos desde tu archivo Excel
def cargar_datos():
    # Usar la ruta absoluta garantiza que lo encuentre sin importar desde dónde ejecutes la app
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_excel = os.path.join(ruta_actual, "BD.xlsx")
    
    return pd.read_excel(ruta_excel, sheet_name="SHOWROOM")

try:
    df = cargar_datos()
except Exception as e:
    st.error("❌ No se pudo cargar el archivo 'BD.xlsx'.")
    st.error(f"🔍 Detalle técnico del error: {e}") # <- Esto te dirá exactamente qué pasa
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
            mensaje_codificado = urllib.parse.quote(mensaje_wa)
            enlace_final = f"https://wa.me/{MI_WHATSAPP}?text={mensaje_codificado}"
            st.link_button("Confirmar Pedido por WhatsApp 📲", url=enlace_final, use_container_width=True)
            
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
            
            # Extracción segura de datos leyendo las columnas reales de la BD
            prod_nombre = row.get("Producto", df.iloc[index, 0])
            prod_marca = row.get("Marca", "Sin marca")
            
            # CORRECCIÓN: Buscamos la columna 'Presentación' y 'Duración'
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
                
                # MODIFICACIÓN: Añadimos Presentación y Duración exactamente como vienen de la BD
                linea_detalles = f"🏷️ **Marca:** {prod_marca} | 💊 **Presentación:** {prod_presentacion} | ⏳ **Duración:** {prod_duracion}"
                
                if pd.notna(prod_tratamiento) and str(prod_tratamiento).strip() != "":
                    modo_uso_limpio = str(prod_tratamiento).replace(".- ", "").replace("\n", " ").strip()
                    linea_detalles += f" | 📝 **Modo de uso:** {modo_uso_limpio}"
                
                st.caption(linea_detalles)
                
                # Sección de beneficios abajo
                st.markdown("**Propiedades:**")
                propiedades_limpias = str(prod_propiedades).replace(".- ", "* ")
                st.markdown(propiedades_limpias)
                
            # --- Columna 3: Precio y Agregar al Carrito ---
            with col_accion:
                st.write("### ") 
                st.metric(label="Precio", value=f"${prod_precio}.00")
                st.caption("*Tasa BCV*")
                
                id_unico_producto = f"{prod_nombre}_{prod_marca}"
                
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
