import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import time
import os
import uuid

# --- 1. CONFIGURACIÓN INICIAL DE STREAMLIT ---
st.set_page_config(page_title="EmprendoBot IoT", layout="wide", initial_sidebar_state="expanded")

# --- 2. CONFIGURACIÓN DE LA API DE DEEPSEEK ---
try:
    API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except KeyError:
    API_KEY = ""
    st.error("⚠️ API Key no configurada. Ve a Settings > Secrets en Streamlit Cloud.")
API_URL = 'https://api.deepseek.com/v1/chat/completions'
MODEL_NAME = "deepseek-chat"

# --- 3. MENSAJE DE SISTEMA PARA EL BOT ---
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

# --- 4. FUNCIONES AUXILIARES ---

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
    """Simula efecto de escritura en el chat."""
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
    Componente HTML con JavaScript para TTS mejorado y más compatible.
    """
    # Limpieza y preparación del texto
    clean_text = text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')\
                     .replace("\n", " ").replace("\r", "").replace("`", "")
    if len(clean_text) > 800:
        clean_text = clean_text[:797] + "..."
    
    # ID único para evitar conflictos
    component_id = str(uuid.uuid4())[:8]

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                margin: 0; 
                padding: 10px; 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #f8f9fa;
            }}
            .tts-container {{
                text-align: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 20px;
                color: white;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                max-width: 400px;
                margin: 0 auto;
            }}
            .tts-button {{
                background: rgba(255,255,255,0.15);
                border: 2px solid rgba(255,255,255,0.3);
                color: white;
                padding: 12px 24px;
                border-radius: 30px;
                cursor: pointer;
                font-size: 15px;
                font-weight: 500;
                margin: 6px;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }}
            .tts-button:hover:not(:disabled) {{
                background: rgba(255,255,255,0.25);
                transform: translateY(-1px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }}
            .tts-button:active {{
                transform: translateY(0);
            }}
            .tts-button:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }}
            .status {{
                margin-top: 15px;
                font-size: 13px;
                min-height: 20px;
                font-weight: 400;
                opacity: 0.9;
            }}
            .icon {{
                font-size: 16px;
            }}
        </style>
    </head>
    <body>
        <div class="tts-container">
            <div>
                <button id="playBtn_{component_id}" class="tts-button" onclick="handlePlay_{component_id}()">
                    <span class="icon">🔊</span>Reproducir Audio
                </button>
                <button id="stopBtn_{component_id}" class="tts-button" onclick="handleStop_{component_id}()" disabled>
                    <span class="icon">⏹️</span>Detener
                </button>
            </div>
            <div id="status_{component_id}" class="status">Listo para reproducir</div>
        </div>

        <script>
            (function() {{
                const componentId = '{component_id}';
                const textToSpeak = `{clean_text}`;
                let currentUtterance = null;
                let isInitialized = false;

                function updateStatus(message) {{
                    const statusEl = document.getElementById(`status_${{componentId}}`);
                    if (statusEl) statusEl.textContent = message;
                }}

                function updateButtons(playing) {{
                    const playBtn = document.getElementById(`playBtn_${{componentId}}`);
                    const stopBtn = document.getElementById(`stopBtn_${{componentId}}`);
                    if (playBtn) playBtn.disabled = playing;
                    if (stopBtn) stopBtn.disabled = !playing;
                }}

                async function initializeSpeech() {{
                    if (isInitialized) return true;
                    
                    if (!('speechSynthesis' in window)) {{
                        updateStatus('❌ Text-to-Speech no disponible');
                        return false;
                    }}

                    // Esperar a que las voces estén disponibles
                    return new Promise((resolve) => {{
                        const checkVoices = () => {{
                            const voices = speechSynthesis.getVoices();
                            if (voices.length > 0) {{
                                isInitialized = true;
                                resolve(true);
                            }} else {{
                                setTimeout(checkVoices, 100);
                            }}
                        }};
                        
                        if (speechSynthesis.onvoiceschanged !== undefined) {{
                            speechSynthesis.onvoiceschanged = checkVoices;
                        }}
                        checkVoices();
                    }});
                }}

                window.handlePlay_{component_id} = async function() {{
                    try {{
                        const initialized = await initializeSpeech();
                        if (!initialized) return;

                        // Cancelar cualquier reproducción anterior
                        speechSynthesis.cancel();
                        
                        // Crear nueva utterance
                        currentUtterance = new SpeechSynthesisUtterance(textToSpeak);
                        
                        // Configurar voz en español
                        const voices = speechSynthesis.getVoices();
                        const spanishVoice = voices.find(voice => 
                            voice.lang.startsWith('es') || 
                            voice.name.toLowerCase().includes('spanish') ||
                            voice.name.toLowerCase().includes('español')
                        );
                        
                        if (spanishVoice) {{
                            currentUtterance.voice = spanishVoice;
                        }}
                        currentUtterance.lang = 'es-ES';
                        currentUtterance.rate = 0.9;
                        currentUtterance.pitch = 1.0;
                        currentUtterance.volume = 0.8;

                        // Event listeners
                        currentUtterance.onstart = function() {{
                            updateButtons(true);
                            updateStatus('🎤 Reproduciendo audio...');
                        }};

                        currentUtterance.onend = function() {{
                            updateButtons(false);
                            updateStatus('✅ Reproducción completada');
                            currentUtterance = null;
                        }};

                        currentUtterance.onerror = function(event) {{
                            updateButtons(false);
                            updateStatus('❌ Error en reproducción');
                            console.error('TTS Error:', event);
                            currentUtterance = null;
                        }};

                        // Iniciar reproducción
                        speechSynthesis.speak(currentUtterance);

                    }} catch (error) {{
                        console.error('Error en TTS:', error);
                        updateStatus('❌ Error inesperado');
                        updateButtons(false);
                    }}
                }};

                window.handleStop_{component_id} = function() {{
                    if (speechSynthesis) {{
                        speechSynthesis.cancel();
                        updateButtons(false);
                        updateStatus('⏸️ Reproducción detenida');
                        currentUtterance = null;
                    }}
                }};

                // Auto-play si está habilitado
                if ({str(auto_play).lower()}) {{
                    setTimeout(() => {{
                        window.handlePlay_{component_id}();
                    }}, 1000);
                }}

                // Limpiar al salir
                window.addEventListener('beforeunload', function() {{
                    if (speechSynthesis) {{
                        speechSynthesis.cancel();
                    }}
                }});
            }})();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=140)

def voice_to_text_component():
    """
    Componente de reconocimiento de voz mejorado para mayor compatibilidad.
    """
    component_id = str(uuid.uuid4())[:8]
    
    html_voice = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                margin: 0;
                padding: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #f8f9fa;
            }}
            .voice-container {{
                text-align: center;
                background: linear-gradient(135deg, #43a047 0%, #66bb6a 100%);
                border-radius: 12px;
                padding: 20px;
                color: white;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                max-width: 400px;
                margin: 0 auto;
            }}
            .voice-button {{
                background: rgba(255,255,255,0.15);
                border: 2px solid rgba(255,255,255,0.3);
                color: white;
                padding: 12px 24px;
                border-radius: 30px;
                cursor: pointer;
                font-size: 15px;
                font-weight: 500;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }}
            .voice-button:hover:not(:disabled) {{
                background: rgba(255,255,255,0.25);
                transform: translateY(-1px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }}
            .voice-button:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }}
            .voice-status {{
                margin-top: 15px;
                font-size: 13px;
                min-height: 20px;
                font-weight: 400;
                opacity: 0.9;
            }}
            .icon {{
                font-size: 16px;
            }}
            .recording {{
                animation: pulse 1.5s infinite;
            }}
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
                100% {{ opacity: 1; }}
            }}
        </style>
    </head>
    <body>
        <div class="voice-container">
            <button id="voiceBtn_{component_id}" class="voice-button" onclick="handleVoice_{component_id}()">
                <span class="icon">🎤</span>Iniciar Dictado
            </button>
            <div id="voiceStatus_{component_id}" class="voice-status">Listo para dictar</div>
        </div>

        <script>
            (function() {{
                const componentId = '{component_id}';
                let recognition = null;
                let isListening = false;

                function updateStatus(message, isRecording = false) {{
                    const statusEl = document.getElementById(`voiceStatus_${{componentId}}`);
                    const btnEl = document.getElementById(`voiceBtn_${{componentId}}`);
                    if (statusEl) {{
                        statusEl.textContent = message;
                        statusEl.className = isRecording ? 'voice-status recording' : 'voice-status';
                    }}
                    if (btnEl) {{
                        btnEl.disabled = isRecording;
                        btnEl.className = isRecording ? 'voice-button recording' : 'voice-button';
                    }}
                }}

                function initializeRecognition() {{
                    // Verificar compatibilidad
                    window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    
                    if (!window.SpeechRecognition) {{
                        updateStatus('❌ Reconocimiento de voz no disponible');
                        return false;
                    }}

                    recognition = new window.SpeechRecognition();
                    recognition.lang = 'es-ES';
                    recognition.interimResults = false;
                    recognition.maxAlternatives = 1;
                    recognition.continuous = false;

                    recognition.onstart = function() {{
                        isListening = true;
                        updateStatus('🎤 Escuchando... Habla ahora', true);
                    }};

                    recognition.onend = function() {{
                        isListening = false;
                        updateStatus('Listo para dictar');
                    }};

                    recognition.onerror = function(event) {{
                        isListening = false;
                        console.error('Speech recognition error:', event.error);
                        let errorMsg = '❌ Error en reconocimiento';
                        
                        switch(event.error) {{
                            case 'no-speech':
                                errorMsg = '❌ No se detectó voz';
                                break;
                            case 'network':
                                errorMsg = '❌ Error de conexión';
                                break;
                            case 'not-allowed':
                                errorMsg = '❌ Micrófono no permitido';
                                break;
                            default:
                                errorMsg = `❌ Error: ${{event.error}}`;
                        }}
                        updateStatus(errorMsg);
                    }};

                    recognition.onresult = function(event) {{
                        const transcript = event.results[0][0].transcript.trim();
                        updateStatus(`✅ Texto capturado: "${{transcript}}"`);
                        
                        // Buscar el textarea del chat y rellenarlo
                        setTimeout(() => {{
                            try {{
                                // Buscar específicamente el input del chat de Streamlit
                                const chatInputs = document.querySelectorAll('textarea[data-testid="stChatInputTextArea"], textarea[placeholder*="Pregunta"], textarea[placeholder*="pregunta"], textarea');
                                let targetInput = null;
                                
                                // Buscar el textarea más relevante
                                for (let input of chatInputs) {{
                                    if (input.placeholder && (
                                        input.placeholder.toLowerCase().includes('pregunta') ||
                                        input.placeholder.toLowerCase().includes('chat') ||
                                        input.placeholder.toLowerCase().includes('emprendobot')
                                    )) {{
                                        targetInput = input;
                                        break;
                                    }}
                                }}
                                
                                // Si no encontró uno específico, usar el último textarea
                                if (!targetInput && chatInputs.length > 0) {{
                                    targetInput = chatInputs[chatInputs.length - 1];
                                }}

                                if (targetInput) {{
                                    // Enfocar el input y establecer el valor
                                    targetInput.focus();
                                    targetInput.value = transcript;
                                    
                                    // Disparar eventos para que Streamlit detecte el cambio
                                    ['input', 'change'].forEach(eventType => {{
                                        const event = new Event(eventType, {{ bubbles: true }});
                                        targetInput.dispatchEvent(event);
                                    }});
                                    
                                    // Buscar y hacer clic en el botón de envío
                                    setTimeout(() => {{
                                        const sendButtons = document.querySelectorAll('button[data-testid="stChatInputSubmitButton"], button[type="submit"], button[title="Submit"], button');
                                        for (let btn of sendButtons) {{
                                            if (btn.textContent.includes('Submit') || 
                                                btn.getAttribute('data-testid') === 'stChatInputSubmitButton' ||
                                                btn.querySelector('svg')) {{
                                                btn.click();
                                                break;
                                            }}
                                        }}
                                    }}, 300);
                                    
                                    updateStatus('✅ Mensaje enviado correctamente');
                                }} else {{
                                    updateStatus('❌ No se encontró el campo de chat');
                                }}
                            }} catch (error) {{
                                console.error('Error al procesar el texto:', error);
                                updateStatus('❌ Error al enviar mensaje');
                            }}
                        }}, 200);
                    }};

                    return true;
                }}

                window.handleVoice_{component_id} = function() {{
                    if (!recognition && !initializeRecognition()) {{
                        return;
                    }}

                    if (isListening) {{
                        recognition.stop();
                        return;
                    }}

                    try {{
                        recognition.start();
                    }} catch (error) {{
                        console.error('Error starting recognition:', error);
                        updateStatus('❌ Error al iniciar reconocimiento');
                    }}
                }};

                // Inicializar al cargar
                setTimeout(initializeRecognition, 500);
            }})();
        </script>
    </body>
    </html>
    """
    components.html(html_voice, height=120)

def process_user_input(user_text):
    """Procesa la entrada del usuario y genera respuesta con TTS."""
    if user_text:
        # 1) Agregamos mensaje del usuario al historial
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        # 2) Generamos respuesta del asistente
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            with st.spinner("EmprendoBot está generando ideas... 💡"):
                # Limitar historial para la API
                max_history_items_api = 15
                api_messages = []
                if st.session_state.messages and st.session_state.messages[0]["role"] == "system":
                    api_messages.append(st.session_state.messages[0])
                    user_assistant_messages = [
                        m for m in st.session_state.messages[1:] 
                        if m["role"] in ["user", "assistant"]
                    ]
                    api_messages.extend(user_assistant_messages[-(max_history_items_api - 1):])
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

            # Mostrar componente TTS para la respuesta generada
            auto_tts = st.session_state.get("auto_tts", False)
            text_to_speech_component(final_response, auto_play=auto_tts)

        # 3) Añadimos la respuesta al historial y limitamos longitud
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        max_history_streamlit = 40
        if len(st.session_state.messages) > max_history_streamlit:
            if st.session_state.messages[0]["role"] == "system":
                st.session_state.messages = (
                    [st.session_state.messages[0]] +
                    st.session_state.messages[-(max_history_streamlit - 1):]
                )
            else:
                st.session_state.messages = st.session_state.messages[-max_history_streamlit:]

# --- 5. INTERFAZ PRINCIPAL DE STREAMLIT ---

# 5.1. Título y descripción
st.title("🚀 EmprendoBot IoT Assistant")
st.caption("Tu copiloto para ideas de negocio IoT y planes de emprendimiento.")

# 5.2. Sidebar con opciones
with st.sidebar:
    st.header("⚙️ Opciones")
    st.session_state.auto_tts = st.checkbox(
        "🔊 Reproducir respuestas automáticamente", 
        value=st.session_state.get("auto_tts", False),
        help="Las respuestas se reproducirán automáticamente al generarse"
    )
    
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

# 5.3. Inicializamos historial de chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT}
    ]

# 5.4. Mostramos mensajes previos (usuario y asistente)
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            # Insertamos siempre el TTS para respuestas del asistente
            text_to_speech_component(message["content"], auto_play=False)

# 5.5. Componente de dictado de voz (antes del chat_input)
st.markdown("### 🎤 Dictado por Voz")
voice_to_text_component()

# 5.6. Caja de entrada del chat
if prompt := st.chat_input("Pregunta a EmprendoBot sobre tu idea IoT...", key="chat_input_main"):
    process_user_input(prompt)
    st.rerun()

# Procesar preguntas de ejemplo
if "example_question" in st.session_state:
    process_user_input(st.session_state.example_question)
    del st.session_state.example_question
    st.rerun()

# 5.7. Mensajes de ejemplo si no hay conversación aún
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

# 5.8. Verificación de la API Key
if not API_KEY:
    st.error("⚠️ **Configuración requerida**: Necesitas configurar tu API Key de DeepSeek en los secrets de Streamlit.")
    with st.expander("📋 Instrucciones de configuración"):
        st.markdown("""
        1. Ve a tu app en Streamlit Cloud  
        2. Abre **Settings** > **Secrets**  
        3. Agrega tu API key en formato TOML:
        ```toml
        DEEPSEEK_API_KEY = "tu-api-key-deepseek-aquí"
        ```
        4. Guarda y reinicia la app  
        """)
