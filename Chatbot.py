import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import time
import os
import uuid

st.set_page_config(page_title="EmprendoBot IoT", layout="wide", initial_sidebar_state="expanded")

try:
    API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except (KeyError, AttributeError):
    API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
    if not API_KEY:
        st.error("⚠️ API Key no configurada. Configura DEEPSEEK_API_KEY en tus secrets o variables de entorno.")

API_URL = 'https://api.deepseek.com/v1/chat/completions'
MODEL_NAME = "deepseek-chat"

SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT = """
Eres EmprendoBot, un asistente experto en emprendimiento con un fuerte enfoque en el Internet de las Cosas (IoT).
Tu objetivo es ayudar a los usuarios a:
1.  **Generar y refinar ideas de negocio innovadoras basadas en IoT.**
2.  **Formular propuestas de valor claras y convincentes.**
3.  **Esbozar los componentes principales de un plan de negocio.**
4.  **Discutir tecnologías IoT relevantes.**
5.  **Identificar posibles desafíos y riesgos.**
Mantén un tono profesional, alentador y práctico. Responde siempre en español.
"""

def get_deepseek_response(prompt_messages):
    if not API_KEY:
        return "❌ Error: API Key de DeepSeek no configurada."
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
    data = {
        "model": MODEL_NAME, "messages": prompt_messages,
        "max_tokens": st.session_state.get("max_tokens", 1500),
        "temperature": st.session_state.get("temperature", 0.7),
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=90)
        response.raise_for_status()
        response_json = response.json()
        if "choices" in response_json and len(response_json["choices"]) > 0:
            return response_json["choices"][0]["message"]["content"].strip()
        st.error(f"Respuesta inesperada de la API: {response_json}")
        return "Lo siento, no pude obtener una respuesta válida."
    except requests.exceptions.Timeout:
        st.error("La solicitud tardó demasiado (timeout).")
        return "Lo siento, la respuesta tardó demasiado."
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la solicitud a la API: {e}")
        return "Lo siento, hubo un problema de conexión."
    except Exception as e:
        st.error(f"Un error inesperado ocurrió: {e}")
        return "Lo siento, ocurrió un error inesperado."

def display_typing_effect(text, placeholder):
    full_response = ""
    words = text.split(" ")
    for i, word in enumerate(words):
        full_response += word + " "
        display_text = full_response + ("▌" if i < len(words) - 1 else "")
        placeholder.markdown(display_text)
        time.sleep(0.03 if len(word) < 5 else 0.05)
    placeholder.markdown(full_response.strip())
    return full_response.strip()

def text_to_speech_component(text, auto_play=False, component_key_suffix=""):
    clean_text = text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", " ").replace("\r", "")
    if len(clean_text) > 950: clean_text = clean_text[:947] + "..."
    component_id = f"tts_{uuid.uuid4().hex[:8]}_{component_key_suffix}"
    html_code = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <style>
        body {{ margin: 0; padding: 5px; font-family: Arial, sans-serif; }}
        .tts-container {{ display: flex; align-items: center; justify-content: flex-start; background: #f0f2f6; border-radius: 8px; padding: 8px 12px; margin-top: 8px; }}
        .tts-button {{ background: #4A90E2; border: none; color: white; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-size: 14px; margin-right: 8px; transition: background 0.3s ease; }}
        .tts-button:hover {{ background: #357ABD; }} .tts-button:disabled {{ background: #cccccc; cursor: not-allowed; }}
        .status {{ font-size: 12px; color: #555; min-height: 18px; }}
    </style></head><body><div class="tts-container">
        <button id="playBtn_{component_id}" class="tts-button" onclick="speakText_{component_id}()">🔊 Escuchar</button>
        <button id="stopBtn_{component_id}" class="tts-button" onclick="stopSpeech_{component_id}()" disabled>⏹️ Detener</button>
        <div id="status_{component_id}" class="status"></div>
    </div><script>
        const text_{component_id} = `{clean_text}`; let utterance_{component_id} = null;
        const playBtn_{component_id} = document.getElementById('playBtn_{component_id}');
        const stopBtn_{component_id} = document.getElementById('stopBtn_{component_id}');
        const statusEl_{component_id} = document.getElementById('status_{component_id}');
        function updateStatus_{component_id}(message) {{ if (statusEl_{component_id}) statusEl_{component_id}.textContent = message; }}
        function speakText_{component_id}() {{
            if (!('speechSynthesis' in window)) {{ updateStatus_{component_id}('TTS no soportado'); if(playBtn_{component_id}) playBtn_{component_id}.disabled = true; return; }}
            window.speechSynthesis.cancel();
            utterance_{component_id} = new SpeechSynthesisUtterance(text_{component_id});
            utterance_{component_id}.lang = 'es-ES'; utterance_{component_id}.rate = 0.95; utterance_{component_id}.pitch = 1.0;
            utterance_{component_id}.onstart = function() {{ if (playBtn_{component_id}) playBtn_{component_id}.disabled = true; if (stopBtn_{component_id}) stopBtn_{component_id}.disabled = false; updateStatus_{component_id}('🎤 Hablando...'); }};
            utterance_{component_id}.onend = function() {{ if (playBtn_{component_id}) playBtn_{component_id}.disabled = false; if (stopBtn_{component_id}) stopBtn_{component_id}.disabled = true; updateStatus_{component_id}('Listo.'); utterance_{component_id} = null; }};
            utterance_{component_id}.onerror = function(event) {{ if (playBtn_{component_id}) playBtn_{component_id}.disabled = false; if (stopBtn_{component_id}) stopBtn_{component_id}.disabled = true; updateStatus_{component_id}('Error TTS: ' + event.error); console.error('Error TTS:', event.error); utterance_{component_id} = null; }};
            try {{ window.speechSynthesis.speak(utterance_{component_id}); }} catch (error) {{ updateStatus_{component_id}('Error al iniciar TTS'); console.error('Error al hablar:', error); if (playBtn_{component_id}) playBtn_{component_id}.disabled = false; }}
        }}
        function stopSpeech_{component_id}() {{ if (window.speechSynthesis) window.speechSynthesis.cancel(); }}
        if ({str(auto_play).lower()}) {{ setTimeout(() => {{ if (document.getElementById('playBtn_{component_id}')) speakText_{component_id}(); }}, 500); }}
    </script></body></html>
    """
    components.html(html_code, height=65)

def voice_input_component():
    component_id = f"voice_input_{uuid.uuid4().hex[:8]}"
    html_code = f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; }}
        .voice-container {{ display: flex; align-items: center; gap: 10px; padding: 5px 0; }}
        #voiceBtn_{component_id} {{ background-color: #6C63FF; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; font-size: 20px; cursor: pointer; display: flex; justify-content: center; align-items: center; transition: background-color 0.3s ease, transform 0.1s ease; }}
        #voiceBtn_{component_id}:hover {{ background-color: #574FE0; }} #voiceBtn_{component_id}:active {{ transform: scale(0.95); }}
        #voiceBtn_{component_id}.recording {{ background-color: #FF6347; }}
        #voiceStatus_{component_id} {{ font-size: 14px; color: #555; min-width: 150px; text-align: left;}}
    </style></head><body><div class="voice-container">
        <button id="voiceBtn_{component_id}" title="Grabar pregunta por voz">🎤</button>
        <span id="voiceStatus_{component_id}"></span>
    </div><script>
        const voiceBtn = document.getElementById('voiceBtn_{component_id}'); const voiceStatus = document.getElementById('voiceStatus_{component_id}');
        let recognition;
        if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {{
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition(); recognition.continuous = false; recognition.interimResults = false; recognition.lang = 'es-ES';
            recognition.onstart = () => {{ voiceStatus.textContent = '🎙️ Escuchando...'; voiceBtn.classList.add('recording'); voiceBtn.disabled = true; }};
            recognition.onresult = (event) => {{
                const transcript = event.results[0][0].transcript; console.log("Voz reconocida:", transcript);
                voiceStatus.textContent = 'Procesando: ' + transcript.substring(0,20) + (transcript.length > 20 ? '...' : '');
                let chatTextArea = document.parentWindow.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (!chatTextArea) {{
                    console.log("Selector 'stChatInputTextArea' no hallado. Fallback...");
                    const chatInputContainer = document.parentWindow.document.querySelector('[data-testid="stChatInput"]');
                    if (chatInputContainer) chatTextArea = chatInputContainer.querySelector('textarea');
                }}
                if (chatTextArea) {{
                    console.log("Textarea encontrado:", chatTextArea); chatTextArea.value = transcript;
                    chatTextArea.dispatchEvent(new Event('input', {{ bubbles: true, cancelable: true }}));
                    chatTextArea.dispatchEvent(new Event('change', {{ bubbles: true, cancelable: true }}));
                    setTimeout(() => {{
                        chatTextArea.focus();
                        const enterEvent = new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true }});
                        chatTextArea.dispatchEvent(enterEvent);
                        console.log("Evento Enter simulado."); voiceStatus.textContent = '¡Enviado por voz!';
                    }}, 100);
                }} else {{ voiceStatus.textContent = 'Error: Campo de chat no hallado.'; console.error('Error: Textarea de stChatInput no encontrado.'); }}
            }};
            recognition.onerror = (event) => {{
                console.error('Error SR:', event.error); let errorMsg = 'Error: ' + event.error;
                if (event.error === 'no-speech') errorMsg = 'No se detectó voz.';
                else if (event.error === 'audio-capture') errorMsg = 'Error de micrófono.';
                else if (event.error === 'not-allowed') errorMsg = 'Permiso de micrófono denegado.';
                voiceStatus.textContent = errorMsg; voiceBtn.classList.remove('recording'); voiceBtn.disabled = false;
            }};
            recognition.onend = () => {{ voiceBtn.classList.remove('recording'); voiceBtn.disabled = false; }};
            voiceBtn.addEventListener('click', () => {{ try {{ if (recognition) recognition.start(); }} catch (e) {{ voiceStatus.textContent = 'Error al iniciar grabación.'; console.error("Error starting SR: ", e); voiceBtn.classList.remove('recording'); voiceBtn.disabled = false; }} }});
        }} else {{ voiceStatus.textContent = 'Voz no disponible.'; voiceBtn.disabled = true; voiceBtn.title = 'SR no disponible.'; voiceBtn.style.backgroundColor = '#ccc'; }}
    </script></body></html>
    """
    components.html(html_code, height=55)

st.title("🚀 EmprendoBot IoT Assistant")
st.caption("Tu copiloto para ideas de negocio IoT. Prueba el micrófono 🎤!")

with st.sidebar:
    st.header("⚙️ Opciones")
    auto_tts_checkbox = st.checkbox("🔊 Reproducir respuestas automáticamente", value=st.session_state.get("auto_tts", False))
    if auto_tts_checkbox != st.session_state.get("auto_tts", False): # Si cambia el valor
        st.session_state.auto_tts = auto_tts_checkbox
        st.session_state.play_audio_for_last_message = False # Resetear si se desactiva
        st.rerun() # Re-run para que el estado se propague inmediatamente

    st.subheader("Parámetros del Modelo")
    st.session_state.max_tokens = st.slider("Max Tokens", 200, 4000, st.session_state.get("max_tokens", 1500), 100)
    st.session_state.temperature = st.slider("Creatividad (Temperature)", 0.1, 1.0, st.session_state.get("temperature", 0.7), 0.1)

    if st.button("🧹 Limpiar Chat", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT}]
        st.session_state.example_question = None
        st.session_state.play_audio_for_last_message = False
        st.success("Historial de chat limpiado.")
        st.rerun()

    st.markdown("---")
    st.markdown("### ¿Cómo usar EmprendoBot?")
    st.markdown("- **💡 Ideas**: Pídele ideas de negocio IoT\n- **🗣️ Voz**: Usa el botón 🎤 para dictar.")
    st.markdown("---")
    example_questions = ["Ideas de IoT para agricultura", "Plan de negocio para hogar inteligente"]
    for i, question in enumerate(example_questions):
        if st.button(f"💬 {question}", use_container_width=True, key=f"example_{i}"):
            st.session_state.example_question = question
            st.rerun() # Necesario para procesar la pregunta de ejemplo inmediatamente
    st.markdown("---")
    st.markdown("**Desarrollado con IA y ☕**")

# Inicialización de session_state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT}]
if "auto_tts" not in st.session_state:
    st.session_state.auto_tts = False
if "example_question" not in st.session_state:
    st.session_state.example_question = None
if "play_audio_for_last_message" not in st.session_state:
    st.session_state.play_audio_for_last_message = False

# Mostrar mensajes del chat
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            autoplay_this_one = False
            # Solo auto-reproducir el último mensaje del asistente si la bandera está activa
            if i == len(st.session_state.messages) - 1 and st.session_state.get("play_audio_for_last_message", False):
                autoplay_this_one = True
                st.session_state.play_audio_for_last_message = False # Consumir la bandera

            text_to_speech_component(msg["content"], auto_play=autoplay_this_one, component_key_suffix=f"msg_{i}_{uuid.uuid4().hex[:4]}")


def process_user_input(user_text):
    if not user_text: return

    st.session_state.messages.append({"role": "user", "content": user_text})
    # No necesitamos mostrar el mensaje del usuario aquí, el rerun y el bucle lo harán.

    with st.chat_message("assistant", avatar="🤖"): # Esto es solo para el spinner y el placeholder
        message_placeholder = st.empty()
        with st.spinner("EmprendoBot está generando ideas... 💡"):
            history_for_api = [m for m in st.session_state.messages if m["role"] != "system"] # Excluir system prompt si ya fue usado
            if st.session_state.messages[0]["role"] == "system":
                 api_messages = [st.session_state.messages[0]] + history_for_api[-15:]
            else: # Si por alguna razón no está el system prompt
                 api_messages = [{"role": "system", "content": SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT}] + history_for_api[-15:]

            assistant_response = get_deepseek_response(api_messages)
        
        # El efecto de escritura se mostrará en el siguiente rerun por el bucle de mensajes
        # Pero para una UI más reactiva, podemos actualizar el placeholder aquí
        # No obstante, el TTS debe activarse después del rerun completo.
        # Por ahora, simplificamos y dejamos que el bucle maneje el display.

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    
    # Establecer la bandera para reproducir audio en el siguiente rerun si está habilitado
    if st.session_state.get("auto_tts", False):
        st.session_state.play_audio_for_last_message = True
    else:
        st.session_state.play_audio_for_last_message = False


    # Limitar historial
    max_history_streamlit = 40
    if len(st.session_state.messages) > max_history_streamlit:
        system_msg_present = st.session_state.messages[0]["role"] == "system"
        num_to_keep = max_history_streamlit - (1 if system_msg_present else 0)
        if system_msg_present:
            st.session_state.messages = [st.session_state.messages[0]] + st.session_state.messages[-num_to_keep:]
        else:
            st.session_state.messages = st.session_state.messages[-num_to_keep:]

# Procesar pregunta de ejemplo si se seleccionó
if st.session_state.example_question:
    question_to_process = st.session_state.example_question
    st.session_state.example_question = None 
    process_user_input(question_to_process)
    st.rerun() 

# Input del chat y botón de voz
user_prompt = st.chat_input("Pregunta a EmprendoBot sobre tu idea IoT...", key="chat_input_main")
voice_input_component() # El key="chat_input_main" del st.chat_input es usado por el JS

if user_prompt:
    process_user_input(user_prompt)
    st.rerun() 

if len(st.session_state.messages) <= 1 and not st.session_state.example_question: # Menor o igual a 1 (solo system)
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown("### 🏠 Hogar Inteligente\nAutomatización, seguridad...")
    with col2: st.markdown("### 🏭 Industria 4.0\nSensores, mantenimiento...")
    with col3: st.markdown("### 🌱 AgTech\nAgricultura de precisión...")

if not API_KEY:
    st.error("⚠️ **Configuración requerida**: API Key de DeepSeek en secrets.")
    with st.expander("📋 Instrucciones"):
        st.markdown("```toml\nDEEPSEEK_API_KEY = \"tu-api-key-aqui\"\n```")
