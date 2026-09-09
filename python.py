import warnings
import difflib
import streamlit as st
from google import genai
from google.genai import types

warnings.filterwarnings("ignore")

# Configuración de página
st.set_page_config(
    page_title="Parafraseador Pro", 
    page_icon="📝", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS para ocultar elementos de la interfaz, marcas de agua y ajustar márgenes
st.markdown("""
    <style>
    /* Ocultar elementos principales de la interfaz */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ocultar marcas de agua, badges, avatares y botones flotantes */
    .stAppDeployButton {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stViewerBadge"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    
    /* Selectores por patrones de clase de Streamlit */
    div[class*="viewerBadge"] {display: none !important;}
    div[class*="stActionButton"] {display: none !important;}
    div[class*="styles_viewerBadge"] {display: none !important;}
    
    /* Ajustar el espacio superior tras ocultar el header */
    .block-container {
        padding-top: 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📝 Parafraseador Multi-Modo con IA")
st.write("Selecciona el modo de redacción deseado y transforma tu texto al instante.")

PROMPTS_MODOS = {
    "Estándar": "Reescribe el texto recibido manteniendo la estructura general pero variando el léxico y conectores.",
    "Humanizar": (
        "Reescribe el texto eliminando cualquier rastro de redacción robótica. "
        "Alterna la longitud de oraciones, usa vocabulario natural y cambia voces gramaticales."
    ),
    "Formal": "Reescribe el texto utilizando un tono sumamente elegante, profesional y protocolar.",
    "Académico": "Reescribe el texto adaptándolo a un estándar de publicación científica o universitaria.",
    "Creativo": "Reescribe el texto aportando dinamismo, metáforas expresivas y variedad de estilo.",
    "Simple": "Reescribe el texto con un lenguaje extremadamente sencillo, directo y fácil de entender.",
    "Acortar": "Resume y condensa el texto quitando redundancias y dejando la esencia central.",
    "Ampliar": "Desarrolla con mayor profundidad el contenido del texto agregando explicaciones complementarias."
}

# Inicializar sesión para persisitir resultados
if "texto_generado" not in st.session_state:
    st.session_state.texto_generado = ""
if "html_resultado" not in st.session_state:
    st.session_state.html_resultado = ""

def parafrasear_texto(texto_original: str, modo: str) -> str:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    system_instruction = PROMPTS_MODOS.get(modo, PROMPTS_MODOS["Estándar"])
    temp = 0.85 if modo in ["Humanizar", "Creativo"] else 0.5

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temp,
        top_p=0.92,
    )

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=f"Texto a reescribir:\n\n{texto_original}",
        config=config,
    )

    return response.text

def generar_diferencias_html(original: str, parafraseado: str) -> str:
    palabras_orig = original.split()
    palabras_para = parafraseado.split()
    
    matcher = difflib.SequenceMatcher(None, palabras_orig, palabras_para)
    resultado_html = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        subtexto = " ".join(palabras_para[j1:j2])
        if not subtexto.strip():
            continue

        if tag == 'equal':
            resultado_html.append(f'<span style="border-bottom: 2px solid #f1c40f; padding-bottom: 2px;">{subtexto}</span>')
        elif tag == 'replace':
            resultado_html.append(f'<span style="color: #e74c3c; font-weight: 500;">{subtexto}</span>')
        elif tag == 'insert':
            resultado_html.append(f'<span style="color: #3498db; font-weight: 500;">{subtexto}</span>')

    return " ".join(resultado_html)

# Selector de modos
modo_seleccionado = st.radio(
    "Selecciona el modo de parafraseo:",
    options=list(PROMPTS_MODOS.keys()),
    horizontal=True
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Texto original")
    texto_entrada = st.text_area(
        "Ingresa tu texto aquí:",
        height=300,
        placeholder="Pega el texto que deseas transformar...",
        label_visibility="collapsed"
    )
    btn_procesar = st.button("Reformular", type="primary", use_container_width=True)

with col2:
    st.subheader(f"Resultado ({modo_seleccionado})")
    
    st.markdown(
        """
        <div style="font-size: 0.85rem; margin-bottom: 10px; background-color: #1e1e1e; padding: 8px; border-radius: 5px;">
            <b>Leyenda de cambios:</b> 
            <span style="border-bottom: 2px solid #f1c40f; margin-right: 10px;">Texto sin cambios</span>
            <span style="color: #e74c3c; font-weight: bold; margin-right: 10px;">Sinónimos / Cambios</span>
            <span style="color: #3498db; font-weight: bold;">Estructura nueva</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if btn_procesar:
        if texto_entrada.strip():
            with st.spinner("Transformando texto..."):
                st.session_state.texto_generado = parafrasear_texto(texto_entrada, modo_seleccionado)
                st.session_state.html_resultado = generar_diferencias_html(texto_entrada, st.session_state.texto_generado)
        else:
            st.warning("Escribe o pega un texto en la columna izquierda antes de presionar el botón.")

    # Mostrar resultado y opción de copia si existe texto generado
    if st.session_state.texto_generado:
        st.markdown(
            f"""
            <div style="background-color: #262730; padding: 15px; border-radius: 8px; min-height: 200px; font-size: 1.05rem; line-height: 1.6; margin-bottom: 15px;">
                {st.session_state.html_resultado}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("📋 **Texto plano listo para copiar en móvil:**")
        # El componente st.code incluye de forma nativa un botón de copiado flotante fácil de usar en celulares
        st.code(st.session_state.texto_generado, language=None)
