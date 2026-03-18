import streamlit as st
from database_manager import cargar_db, obtener_ofertas_por_filtros
from database_google import limpiar_texto_abc

DISTRITOS_OFICIALES = [
    "9 de Julio", "25 de Mayo", "A. Alsina", "Adolfo Gonzales Chaves", "Alberti", "Almirante Brown", "Arrecifes",
    "Avellaneda", "Ayacucho", "Azul", "B. Blanca", "Balcarce", "Baradero", "Berazategui", "Berisso", "Bolívar",
    "Bragado", "Campana", "Cañuelas", "C. Sarmiento", "C. Casares", "C. Tejedor", "C. de Areco", "Castelli",
    "Chacabuco", "Chascomús", "Chivilcoy", "Colón", "Coronel Brandsen", "C. Dorrego", "C. Pringles", "C. Rosales",
    "C. Suárez", "Daireaux", "Dolores", "Ensenada", "Escobar", "Esteban Echeverría", "Exaltación de la Cruz", "Ezeiza",
    "F. Ameghino", "F. Varela", "G. Alvarado", "G. Alvear", "G. Arenales", "G. Belgrano", "G. Chaves", "G. Guido",
    "G. LaMadrid", "G. Las Heras", "G. Lavalle", "G. Madariaga", "G. Paz", "G. Pinto", "G. Pueyrredón", "G. Rodríguez",
    "G. San Martín", "G. Sarmiento", "G. Viamonte", "G. Villegas", "Guaminí", "H. Yrigoyen", "Hurlingham", "Ituzaingó",
    "José C. Paz", "Junín", "L. N. Alem", "La Costa", "La Matanza", "La Plata", "Lanús", "Laprida", "Las Flores",
    "Leandro N. Alem", "Lincoln", "Lobería", "Lobos", "Lomas de Zamora", "Luján", "Magdalena", "Maipú", "Malvinas Arg.",
    "M. Chiquita", "Marcos Paz", "Mercedes", "Merlo", "Monte", "M. Hermoso", "Moreno", "Morón", "Navarro", "Necochea",
    "Olavarría", "Pehuajó", "Pellegrini", "Pergamino", "Pila", "Pilar", "Pinamar", "Pte. Perón", "Puan", "Punta Indio",
    "Quilmes", "Ramallo", "Rauch", "Rivadavia", "Rojas", "R. Pérez", "Saavedra", "Saladillo", "Salliqueló", "Salto",
    "S. A. de Giles", "S. A. de Areco", "San Cayetano", "San Fernando", "San Isidro", "San Miguel", "San Nicolás",
    "San Pedro", "San Vicente", "Suipacha", "Tandil", "Tapalqué", "Tigre", "Tordillo", "Tornquist", "T. Lauquen",
    "Tres Arroyos", "Tres de Febrero", "Tres Lomas", "V. Gesell", "Villarino", "V. López", "Zárate"
]

MAPEO_DISTRITOS = {
    "Almirante Brown": "A. Brown",
    "Esteban Echeverría": "E. Echeverría",
    "Exaltación de la Cruz": "E. de la Cruz",
    "Lomas de Zamora": "L de Zamora",
    "Tres de Febrero": "T. de Febrero"
}


# === CONFIGURACIÓN DE PÁGINA ===
st.set_page_config(page_title="Buscador APD - Lector ABC", page_icon="🔎", layout="centered")

# === ESTILOS CSS ===
st.markdown("""
<style>
    /* Ocultar menú default de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilo de Tarjetas Violeta idéntico al email (Anti-Modo Oscuro) */
    .oferta-card {
        font-family: Arial, sans-serif;
        border-left: 5px solid #800080;
        padding: 16px;
        margin-bottom: 16px;
        background-color: #f9f9f9 !important;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        color: #000000 !important;
    }
    .oferta-encabezado {
        color: #800080 !important;
        margin: 0 0 10px 0;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .oferta-detalle {
        margin: 4px 0;
        color: #000000 !important;
        font-size: 0.95rem;
    }
    .oferta-detalle b {
        color: #000000 !important;
        font-weight: 600;
    }
    hr {
        margin: 10px 0;
        border: none;
        border-top: 1px solid #c0c0c0;
    }
    /* Estilo del Banner CTA */
    .cta-banner {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        border: 1px solid #d1d1d1;
        border-radius: 8px;
        padding: 24px;
        text-align: center;
        margin-top: 40px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .cta-text {
        font-size: 1.1rem;
        color: #333 !important;
        margin-bottom: 16px;
    }
    .cta-highlight {
        color: #800080 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# === CARGA DE DATOS E ÍNDICES ===
@st.cache_data(ttl=60) # Refresca caché cada 60s
def load_data():
    return cargar_db()

db = load_data()
indicadores = db.get("metadata", {})
indices_materia = db.get("indices", {}).get("materia", {})

lista_materias = sorted(list(indices_materia.keys()))

# === UI PRINCIPAL ===
st.title("🔎 Buscador Rápido - Lector ABC")
st.markdown("Encontrá las ofertas de Actos Públicos Digitales al instante.")

if "ultima_actualizacion_barrido" in indicadores:
    ultima_act = indicadores["ultima_actualizacion_barrido"]
    try:
        from datetime import datetime, timedelta
        
        dt_last = datetime.fromisoformat(ultima_act)
        # La próxima actualización se espera en 60 minutos
        dt_next = dt_last + timedelta(minutes=60)
        
        # Calcular los minutos restantes
        ahora = datetime.now()
        tiempo_restante = dt_next - ahora
        minutos_restantes = int(tiempo_restante.total_seconds() / 60)
        
        if minutos_restantes > 0:
            mensaje_eta = f"Próxima actualización en aprox. {minutos_restantes} minutos."
        else:
            mensaje_eta = "Actualización en curso o próxima a iniciar."
            
        st.caption(
            f"🕒 Última actualización de la base de datos: {dt_last.strftime('%H:%M')}hs. "
            f"<span style='color: #800080; font-weight: bold;'>{mensaje_eta}</span>",
            unsafe_allow_html=True
        )
    except Exception as e:
        st.caption(f"🕒 Última actualización de la base de datos: {ultima_act}")
else:
    st.caption("🕒 Base de datos sin inicializar. Ejecutá la primera cosecha masiva.")

st.divider()

# Formularios de Búsqueda
col1, col2 = st.columns(2)

with col1:
    distrito_seleccionado = st.selectbox(
        "📍 Seleccionar Distrito",
        options=["Todos"] + DISTRITOS_OFICIALES,
        index=0
    )

with col2:
    # Permitir tanto usar el selectbox como escribir libremente
    materia_input = st.text_input("📚 Código de Materia (Ej: CCD, /PR)")
    st.caption("⚠️ Ingresá solo un código por vez (Ej: CCD). Evitá poner varios códigos o la búsqueda no funcionará.")

# Botón de Búsqueda
if st.button("Buscar Ofertas", use_container_width=True, type="primary"):
    
    materia_limpia = limpiar_texto_abc(materia_input)
    
    if not materia_limpia:
        st.warning("No ingresaste ningún código de materia. Por favor, escribí uno para iniciar la búsqueda.")
    else:
        # Preparar parámetros
        distritos_a_buscar = []
        if distrito_seleccionado != "Todos":
            oficial = MAPEO_DISTRITOS.get(distrito_seleccionado, distrito_seleccionado)
            distritos_a_buscar.append(oficial)
        else:
            # Si selecciona Todos, cargamos todas las llaves formales mapeadas
            distritos_a_buscar = [MAPEO_DISTRITOS.get(d, d) for d in DISTRITOS_OFICIALES]
            
        materias_a_buscar = [materia_limpia]
        
        with st.spinner("Buscando en la base de datos..."):
            resultados = obtener_ofertas_por_filtros(distritos_a_buscar, materias_a_buscar)
            
        if not resultados:
            st.info("No se encontraron ofertas activas para este filtro en este momento. ¡Suscribite para que te avisemos apenas aparezca una!")
        else:
            st.success(f"Se encontraron {len(resultados)} ofertas vigentes.")
            
            # Renderizado de Tarjetas
            for o in resultados:
                # Convertir los saltos de línea de 'Horarios' de texto crudo a <br>
                horarios_html = o.get('horarios', 'Ver en Portal').strip()
                horarios_html = horarios_html.replace("\n", "<br>").replace(" | ", "<br>")
                
                card_html = f"""
                <div class="oferta-card">
                    <h3 class="oferta-encabezado">{o.get('encabezado', 'N/A').strip()}</h3>
                    <div class="oferta-detalle">
                        <b>Nivel:</b> {o.get('nivel', 'Desconocido').strip()} &nbsp;|&nbsp;
                        <b>Escuela:</b> {o.get('escuela', 'Desconocido').strip()}
                    </div>
                    <hr>
                    <div class="oferta-detalle"><b>Horarios:</b><br>{horarios_html}</div>
                    <hr>
                    <div class="oferta-detalle"><b>Observaciones:</b> {o.get('observaciones', '-').strip()}</div>
                    <div class="oferta-detalle" style="margin-top: 8px; font-size: 0.85rem; color: #666 !important;">
                        <b>Nro. IGE:</b> {o.get('ige', 'Desconocido').strip()}
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
# === CALL TO ACTION (CTA) ===
st.markdown("""
<div class="cta-banner">
    <div class="cta-text">
        💡 ¿No querés entrar todos los días? <br>
        <span class="cta-highlight">Suscribite a nuestras alertas Premium</span> y te avisamos por Mail/WhatsApp al instante.
    </div>
    <a href="https://docs.google.com/forms/d/e/1FAIpQLSdn6pJoHFKmBdUKqyyLGYsbf7MBx5lqP-Q6EMXWMZSUiEhH8w/viewform" target="_blank" style="background-color: #800080; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
        Ver Planes de Suscripción
    </a>
</div>
""", unsafe_allow_html=True)
