import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import time
import os

# --- PRIMERA LLAMADA A STREAMLIT DEBE SER set_page_config ---
st.set_page_config(page_title="EmprendoBot IoT", layout="wide", initial_sidebar_state="expanded")

# --- Configuración API DeepSeek ---
# IMPORTANTE: Usar secrets de Streamlit en producción
try:
    API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except KeyError:
    API_KEY = ""
    st.error("⚠️ API Key no configurada. Ve a Settings > Secrets en Streamlit Cloud.")
API_URL = 'https://api.deepseek.com/v1/chat/completions'
MODEL_NAME = "deepseek-chat"

# --- Mensaje de Sistema Especializado ---
SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT = """
Eres EmprendoBot, un asistente experto en emprendimiento con un fuerte enfoque en el Internet de las Cosas (IoT).
Tu objetivo es ayudar a los usuarios a:
1.  **Generar y refinar ideas de negocio innovadoras basadas en IoT.** Piensa en soluciones para problemas reales en diversos sectores (hogar inteligente, ciudades inteligentes, industria 4.0, agricultura de precisión, salud, etc.).
2.  **Formular propuestas de valor claras y convincentes** para estas ideas. Ayuda a definir el problema que se resuelve, la solución IoT propuesta, el público objetivo y los diferenciadores clave.
3.  **Esbozar los componentes principales de un plan de negocio.** Esto incluye análisis de mercado (tamaño, tendencias, competencia), modelo de negocio (cómo se generarán ingresos), estrategias de marketing y ventas, equipo necesario, y proyecciones financieras básicas (costos iniciales, fuentes de ingresos, punto de equilibrio conceptual).
4.  **Discutir tecnologías IoT relevantes** (sensores, actuadores, plataformas de conectividad, análisis de datos, seguridad).
5.  **Identificar posibles desafíos y riesgos** en emprendimientos IoT y cómo mitigarlos.

Mantén un tono profesional, alentador y práctico. Proporciona ejemplos concretos cuando sea posible.
Cuando te pregunten algo general de emprendimiento, intenta relacionarlo con oportunidades en IoT si es pertinente.
No des consejos financieros específicos ni garantices el éxito. Tu rol es de guía y facilitador de ideas.
Responde siempre en español.
"""

def get_deepseek_response(prompt_messages):
    """Obtiene respuesta de la API de DeepSeek."""
    if not API_KEY:
        return "❌ Error: API Key de DeepSeek no configurada. Por favor contacta al administrador."

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    data = {
        "model": MODEL_NAME,
        "messages": prompt_messages,
        "max_tokens": st.session_state.get("max_tokens", 1500),
        "temperature": st.session_state.get("temperature", 0.7),
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=90)
        response.raise_for_status()
        response_json = response.json()

        if "choices" in response_json and len(response_json["choices"]) > 0:
            assistant_message = response_json["choices"][0]["message"]["content"]
            return assistant_message.strip()
        else:
            st.error(f"Respuesta inesperada de la API: {response_json}")
            return "Lo siento, no pude obtener una respuesta válida de EmprendoBot."

    except requests.exceptions.Timeout:
        st.error("La solicitud a EmprendoBot tardó demasiado (timeout). Intenta ser más específico o reduce la complejidad.")
        return "Lo siento, la respuesta tardó demasiado. ¿Podrías reformular tu pregunta?"
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la solicitud a la API: {e}")
        return "Lo siento, hubo un problema de conexión con EmprendoBot."
    except json.JSONDecodeError:
        st.error(f"Error al decodificar la respuesta JSON.")
        return "Lo siento, recibí una respuesta malformada de EmprendoBot."
    except Exception as e:
        st.error(f"Un error inesperado ocurrió al contactar la API: {e}")
        return "Lo siento, ocurrió un error inesperado."

def display_typing_effect(text, placeholder):
    """Simula efecto de escritura."""
    full_response = ""
    words = text.split(" ")

    for i, word in enumerate(words):
        full_response += word + " "
        # Mostrar cursor de escritura mientras no sea la última palabra
        display_text = full_response + ("▌" if i < len(words) - 1 else "")
        placeholder.markdown(display_text)
        time.sleep(0.03 if len(word) < 5 else 0.05)

    # Mostrar texto final sin cursor
    placeholder.markdown(full_response.strip())
    return full_response.strip()

def text_to_speech_component(text, auto_play=False):
    """Crea un componente HTML con JavaScript para TTS que funciona mejor en Streamlit."""
    # Limpiar el texto para JavaScript
    clean_text = text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", " ").replace("\r", "")
    
    # Truncar si es muy largo (límite de caracteres para TTS)
    if len(clean_text) > 1000:
        clean_text = clean_text[:997] + "..."
    
    # ID único para evitar conflictos
    component_id = f"tts_{hash(text) % 10000}"
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0;
                padding: 10px;
                font-family: Arial, sans-serif;
            }}
            .tts-container {{
                text-align: center;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                padding: 15px;
                color: white;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .tts-button {{
                background: rgba(255,255,255,0.2);
                border: 2px solid rgba(255,255,255,0.3);
                color: white;
                padding: 10px 20px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                margin: 5px;
                transition: all 0.3s ease;
            }}
            .tts-button:hover {{
                background: rgba(255,255,255,0.3);
                transform: translateY(-2px);
            }}
            .tts-button:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
            .status {{
                margin-top: 10px;
                font-size: 14px;
                min-height: 20px;
            }}
            .speaker-icon {{
                font-size: 20px;
                margin-right: 8px;
            }}
        </style>
    </head>
    <body>
        <div class="tts-container">
            <div>
                <button id="playBtn_{component_id}" class="tts-button" onclick="speakText_{component_id}()">
                    <span class="speaker-icon">🔊</span>Escuchar Respuesta
                </button>
                <button id="stopBtn_{component_id}" class="tts-button" onclick="stopSpeech_{component_id}()" disabled>
                    <span class="speaker-icon">⏹️</span>Detener
                </button>
            </div>
            <div id="status_{component_id}" class="status">Listo para reproducir</div>
        </div>

        <script>
            const text_{component_id} = `{clean_text}`;
            let utterance_{component_id} = null;
            
            function updateStatus_{component_id}(message) {{
                const statusEl = document.getElementById('status_{component_id}');
                if (statusEl) statusEl.textContent = message;
            }}
            
            function speakText_{component_id}() {{
                if ('speechSynthesis' in window) {{
                    // Detener cualquier síntesis anterior
                    window.speechSynthesis.cancel();
                    
                    utterance_{component_id} = new SpeechSynthesisUtterance(text_{component_id});
                    utterance_{component_id}.lang = 'es-ES';
                    utterance_{component_id}.rate = 0.9;
                    utterance_{component_id}.pitch = 1.0;
                    utterance_{component_id}.volume = 1.0;
                    
                    utterance_{component_id}.onstart = function() {{
                        const playBtn = document.getElementById('playBtn_{component_id}');
                        const stopBtn = document.getElementById('stopBtn_{component_id}');
                        if (playBtn) playBtn.disabled = true;
                        if (stopBtn) stopBtn.disabled = false;
                        updateStatus_{component_id}('🎤 Reproduciendo...');
                    }};
                    
                    utterance_{component_id}.onend = function() {{
                        const playBtn = document.getElementById('playBtn_{component_id}');
                        const stopBtn = document.getElementById('stopBtn_{component_id}');
                        if (playBtn) playBtn.disabled = false;
                        if (stopBtn) stopBtn.disabled = true;
                        updateStatus_{component_id}('✅ Reproducción completada');
                    }};
                    
                    utterance_{component_id}.onerror = function(event) {{
                        const playBtn = document.getElementById('playBtn_{component_id}');
                        const stopBtn = document.getElementById('stopBtn_{component_id}');
                        if (playBtn) playBtn.disabled = false;
                        if (stopBtn) stopBtn.disabled = true;
                        updateStatus_{component_id}('❌ Error en la reproducción');
                        console.error('Error TTS:', event.error);
                    }};
                    
                    try {{
                        window.speechSynthesis.speak(utterance_{component_id});
                    }} catch (error) {{
                        updateStatus_{component_id}('❌ Error al iniciar TTS');
                        console.error('Error al hablar:', error);
                    }}
                }} else {{
                    updateStatus_{component_id}('❌ TTS no disponible en este navegador');
                }}
            }}
            
            function stopSpeech_{component_id}() {{
                if (window.speechSynthesis) {{
                    window.speechSynthesis.cancel();
                    const playBtn = document.getElementById('playBtn_{component_id}');
                    const stopBtn = document.getElementById('stopBtn_{component_id}');
                    if (playBtn) playBtn.disabled = false;
                    if (stopBtn) stopBtn.disabled = true;
                    updateStatus_{component_id}('⏸️ Reproducción detenida');
                }}
            }}
            
            // Auto-reproducir si está habilitado
            window.addEventListener('load', function() {{
                setTimeout(function() {{
                    if ({str(auto_play).lower()}) {{
                        speakText_{component_id}();
                    }}
                }}, 1000);
            }});
        </script>
    </body>
    </html>
    """
    
    # Usar componente HTML sin key
    components.html(html_code, height=120)

# --- Interfaz de Streamlit ---
st.title("🚀 EmprendoBot IoT Assistant")
st.caption("Tu copiloto para ideas de negocio IoT y planes de emprendimiento.")

# --- Sidebar para Opciones ---
with st.sidebar:
    st.header("⚙️ Opciones")
    st.info("💡 **Versión Cloud Optimizada**\n\nEsta versión está optimizada para funcionar perfectamente en Streamlit Cloud sin dependencias de sistema.")
    
    # Opción para TTS automático
    auto_tts = st.checkbox("🔊 Reproducir respuestas automáticamente", value=False, help="Las respuestas se reproducirán automáticamente al generarse")
    
    st.subheader("Parámetros del Modelo")
    if "max_tokens" not in st.session_state:
        st.session_state.max_tokens = 1500
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7

    st.session_state.max_tokens = st.slider(
        "Max Tokens (longitud respuesta)", 
        200, 4000, 
        st.session_state.max_tokens, 
        100
    )
    st.session_state.temperature = st.slider(
        "Creatividad (Temperature)", 
        0.1, 1.0, 
        st.session_state.temperature, 
        0.1
    )

    if st.button("🧹 Limpiar Chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT}
        ]
        st.success("Historial de chat limpiado.")
        st.rerun()

    st.markdown("---")
    st.markdown("### ¿Cómo usar EmprendoBot?")
    st.markdown("""
    - **💡 Ideas**: Pídele ideas de negocio IoT  
    - **📋 Propuestas**: Pregunta cómo formular propuestas  
    - **📊 Planes**: Discute elementos de planes de negocio  
    - **🔧 Tecnología**: Consulta sobre tecnologías IoT  
    - **⚠️ Riesgos**: Identifica desafíos y soluciones  
    """)
    st.markdown("---")
    st.markdown("### 🎯 Ejemplos de preguntas")
    example_questions = [
        "Ideas de IoT para agricultura",
        "Plan de negocio para hogar inteligente",
        "Tecnologías IoT para salud",
        "Costos de startup IoT",
        "Riesgos en proyectos IoT"
    ]
    for question in example_questions:
        if st.button(f"💬 {question}", use_container_width=True, key=f"example_{question}"):
            st.session_state.example_question = question

    st.markdown("---")
    st.markdown("**Desarrollado con IA y ☕**")

# --- Inicializar historial de chat en session_state ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT}
    ]

# --- Mostrar mensajes del chat ---
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Agregar componente TTS para mensajes del asistente
        if message["role"] == "assistant":
            text_to_speech_component(message["content"], auto_play=False)

# --- Lógica de interacción ---
def process_user_input(user_text):
    """Procesa la entrada del usuario y genera respuesta con TTS."""
    if user_text:
        # Agregar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        # Generar respuesta del asistente
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()

            with st.spinner("EmprendoBot está generando ideas... 💡"):
                # Preparar mensajes para la API (limitar historial)
                max_history_items_api = 15
                api_messages = []
                if st.session_state.messages and st.session_state.messages[0]["role"] == "system":
                    api_messages.append(st.session_state.messages[0])
                    user_assistant_messages = [
                        m for m in st.session_state.messages[1:] 
                        if m["role"] in ["user", "assistant"]
                    ]
                    api_messages.extend(user_assistant_messages[-(max_history_items_api-1):])
                else:
                    api_messages.append({"role": "system", "content": SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT})
                    user_assistant_messages = [
                        m for m in st.session_state.messages 
                        if m["role"] in ["user", "assistant"]
                    ]
                    api_messages.extend(user_assistant_messages[-max_history_items_api:])

                assistant_response = get_deepseek_response(api_messages)

            # Mostrar respuesta con efecto de escritura
            final_response = display_typing_effect(assistant_response, message_placeholder)
            
            # Componente TTS para la nueva respuesta
            if auto_tts:
                # Si está en modo automático, auto-reproducir
                text_to_speech_component(final_response, auto_play=True)
            else:
                text_to_speech_component(final_response, auto_play=False)

        # Agregar respuesta al historial
        st.session_state.messages.append({"role": "assistant", "content": final_response})

        # Limitar historial para evitar problemas de memoria
        max_history_streamlit = 40
        if len(st.session_state.messages) > max_history_streamlit:
            if st.session_state.messages[0]["role"] == "system":
                st.session_state.messages = (
                    [st.session_state.messages[0]] + 
                    st.session_state.messages[-(max_history_streamlit-1):]
                )
            else:
                st.session_state.messages = st.session_state.messages[-max_history_streamlit:]

# --- Procesar pregunta de ejemplo si se seleccionó ---
if hasattr(st.session_state, 'example_question'):
    process_user_input(st.session_state.example_question)
    del st.session_state.example_question
    st.rerun()

# --- Input del chat ---
if prompt := st.chat_input("Pregunta a EmprendoBot sobre tu idea IoT...", key="chat_input_main"):
    process_user_input(prompt)
    st.rerun()

# --- Información adicional (solo si no hay conversación iniciada) ---
if len(st.session_state.messages) == 1:
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🏠 Hogar Inteligente")
        st.markdown("Automatización, seguridad, eficiencia energética")
    with col2:
        st.markdown("### 🏭 Industria 4.0")
        st.markdown("Sensores industriales, mantenimiento predictivo")
    with col3:
        st.markdown("### 🌱 AgTech")
        st.markdown("Agricultura de precisión, monitoreo ambiental")

# --- Verificar configuración (API Key) ---
if not API_KEY:
    st.error("⚠️ **Configuración requerida**: Necesitas configurar tu API Key de DeepSeek en los secrets de Streamlit.")
    with st.expander("📋 Instrucciones de configuración"):
        st.markdown("""
        1. Ve a tu app en Streamlit Cloud  
        2. Abre **Settings** > **Secrets**  
        3. Agrega tu API key en formato TOML:
        ```toml
        DEEPSEEK_API_KEY = "tu-api-key-aqui"
        ```  
        4. Guarda y reinicia la app  
        """)
