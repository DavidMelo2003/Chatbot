import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import time
import os

# --- PRIMERA LLAMADA A STREAMLIT: set_page_config ---
st.set_page_config(page_title="EmprendoBot IoT", layout="wide", initial_sidebar_state="expanded")

# --- Configuración API DeepSeek ---
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
1.  **Generar y refinar ideas de negocio innovadoras basadas en IoT.**
2.  **Formular propuestas de valor claras y convincentes.**
3.  **Esbozar los componentes principales de un plan de negocio.**
4.  **Discutir tecnologías IoT relevantes.**
5.  **Identificar posibles desafíos y riesgos en emprendimientos IoT.**

Mantén un tono profesional, alentador y práctico. Proporciona ejemplos concretos cuando sea posible.
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
        st.error("La solicitud a EmprendoBot tardó demasiado (timeout).")
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
        display_text = full_response + ("▌" if i < len(words) - 1 else "")
        placeholder.markdown(display_text)
        time.sleep(0.03 if len(word) < 5 else 0.05)
    placeholder.markdown(full_response.strip())
    return full_response.strip()

def text_to_speech_component(text, auto_play=False):
    """
    Crea un componente HTML con JavaScript para TTS, con ajustes para autoplay más confiable.
    """
    clean_text = text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", " ").replace("\r", "")
    if len(clean_text) > 1000:
        clean_text = clean_text[:997] + "..."
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

            async function ensureSpeechSynthesisReady() {{
                return new Promise(resolve => {{
                    if (window.speechSynthesis.getVoices().length > 0) {{
                        resolve();
                    }} else {{
                        window.speechSynthesis.onvoiceschanged = () => resolve();
                    }}
                }});
            }}

            async function speakText_{component_id}() {{
                if (!('speechSynthesis' in window)) {{
                    updateStatus_{component_id}('❌ TTS no disponible en este navegador');
                    return;
                }}
                try {{
                    await ensureSpeechSynthesisReady();
                }} catch (err) {{
                    console.error('Error al preparar TTS:', err);
                }}

                window.speechSynthesis.cancel();
                utterance_{component_id} = new SpeechSynthesisUtterance(text_{component_id});
                utterance_{component_id}.lang = 'es-ES';
                utterance_{component_id}.rate = 0.9;
                utterance_{component_id}.pitch = 1.0;
                utterance_{component_id}.volume = 1.0;

                utterance_{component_id}.onstart = function() {{
                    document.getElementById('playBtn_{component_id}').disabled = true;
                    document.getElementById('stopBtn_{component_id}').disabled = false;
                    updateStatus_{component_id}('🎤 Reproduciendo...');
                }};
                utterance_{component_id}.onend = function() {{
                    document.getElementById('playBtn_{component_id}').disabled = false;
                    document.getElementById('stopBtn_{component_id}').disabled = true;
                    updateStatus_{component_id}('✅ Reproducción completada');
                }};
                utterance_{component_id}.onerror = function(event) {{
                    document.getElementById('playBtn_{component_id}').disabled = false;
                    document.getElementById('stopBtn_{component_id}').disabled = true;
                    updateStatus_{component_id}('❌ Error en la reproducción');
                    console.error('Error TTS:', event.error);
                }};

                window.speechSynthesis.speak(utterance_{component_id});
            }}

            function stopSpeech_{component_id}() {{
                if (window.speechSynthesis) {{
                    window.speechSynthesis.cancel();
                    document.getElementById('playBtn_{component_id}').disabled = false;
                    document.getElementById('stopBtn_{component_id}').disabled = true;
                    updateStatus_{component_id}('⏸️ Reproducción detenida');
                }}
            }}

            window.addEventListener('load', function() {{
                if ({str(auto_play).lower()}) {{
                    setTimeout(function() {{
                        speakText_{component_id}();
                    }}, 500);
                }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=150)

def voice_to_text_component():
    """
    Componente HTML/JS para reconocimiento de voz en español,
    que inyecta el texto en el st.chat_input y envía automáticamente.
    """
    html_voice = f"""
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body>
        <div style="text-align:center; padding:10px;">
            <button id="startRec" style="
                background: #43a047; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 8px; 
                font-size: 16px; 
                cursor: pointer;
            ">
                🎤 Iniciar dictado
            </button>
            <span id="statusRec" style="margin-left:20px; font-style: italic; color: #555;">Listo para dictar</span>
        </div>
        <script>
            window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!window.SpeechRecognition) {{
                document.getElementById('statusRec').textContent = '❌ Tu navegador no soporta reconocimiento de voz';
            }} else {{
                const recognition = new window.SpeechRecognition();
                recognition.lang = 'es-ES';
                recognition.interimResults = false;
                recognition.maxAlternatives = 1;

                const btn = document.getElementById('startRec');
                const statusEl = document.getElementById('statusRec');

                recognition.onstart = function() {{
                    statusEl.textContent = '🎤 Escuchando...';
                    btn.disabled = true;
                }};
                recognition.onerror = function(event) {{
                    statusEl.textContent = '❌ Error en reconocimiento';
                    btn.disabled = false;
                }};
                recognition.onend = function() {{
                    btn.disabled = false;
                    if (!recognition.resultIndex) {{
                        statusEl.textContent = 'Listo para dictar';
                    }}
                }};
                recognition.onresult = function(event) {{
                    const transcript = event.results[0][0].transcript;
                    statusEl.textContent = '✅ Capturado: ' + transcript;
                    setTimeout(function() {{
                        const textarea = document.querySelector('textarea[data-baseweb="input"]');
                        if (textarea) {{
                            textarea.value = transcript;
                            const inputEvent = new Event('input', {{ bubbles: true }});
                            textarea.dispatchEvent(inputEvent);
                            const sendButton = textarea.closest('form').querySelector('button[type="submit"]');
                            if (sendButton) {{
                                sendButton.click();
                            }}
                        }} else {{
                            console.warn('No se encontró el textarea de chat_input');
                            statusEl.textContent = '❌ No se encontró el input del chat';
                        }}
                    }}, 300);
                }};

                btn.addEventListener('click', function() {{
                    recognition.start();
                }});
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_voice, height=120)


# --- Interfaz de Streamlit ---
st.title("🚀 EmprendoBot IoT Assistant")
st.caption("Tu copiloto para ideas de negocio IoT y planes de emprendimiento.")

# --- Sidebar para Opciones ---
with st.sidebar:
    st.header("⚙️ Opciones")
    auto_tts = st.checkbox("🔊 Reproducir respuestas automáticamente", value=False,
                            help="Las respuestas se reproducirán automáticamente al generarse")
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
    st.markdown("### 🎯 Ejemplos de preguntas")
    example_questions = [
        "Ideas de IoT para agricultura",
        "Plan de negocio para hogar inteligente",
        "Tecnologías IoT para salud",
        "Costos de startup IoT",
        "Riesgos en proyectos IoT"
    ]
    for q in example_questions:
        if st.button(f"💬 {q}", use_container_width=True, key=f"example_{q}"):
            st.session_state.example_question = q
    st.markdown("---")
    st.markdown("**Desarrollado con IA y ☕**")

# --- Inicializar historial ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT}
    ]

# --- Mostrar mensajes previos ---
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            # Se pasa auto_tts sólo cuando se genera la respuesta, no durante la reproducción manual
            text_to_speech_component(message["content"], auto_play=False)

# --- Llamada al componente de dictado de voz ---
voice_to_text_component()

# --- Input del chat ---
if prompt := st.chat_input("Pregunta a EmprendoBot sobre tu idea IoT...", key="chat_input_main"):
    process_user_input(prompt)
    st.rerun()

# --- Información adicional si aún no hay conversación iniciada ---
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
