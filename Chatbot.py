import streamlit as st
import requests
import json
import speech_recognition as sr
import pyttsx3
import time
import threading

# --- PRIMERA LLAMADA A STREAMLIT DEBE SER set_page_config ---
st.set_page_config(page_title="EmprendoBot IoT", layout="wide", initial_sidebar_state="expanded")

# --- Configuración API DeepSeek ---
API_KEY = 'sk-53751d5c6f344a5dbc0571de9f51313e' # TU API KEY DE DEEPSEEK
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

# --- Definición de Funciones Cacheadas y de Inicialización ---
@st.cache_resource
def init_tts_engine():
    try:
        engine = pyttsx3.init()
        # Opcional: Configurar voz en español si está disponible
        voices = engine.getProperty('voices')
        for voice in voices:
            # Intenta ser más flexible con la detección del idioma
            if any(lang in voice.languages for lang in [b'es-ES', b'es-MX', b'es-US', b'es_ES', b'es_MX', b'es_US']) or \
               any(name_part in voice.name.lower() for name_part in ['spanish', 'español']):
                engine.setProperty('voice', voice.id)
                # st.sidebar.caption(f"Voz TTS: {voice.name}") # Feedback opcional
                break
        return engine
    except Exception as e:
        st.warning(f"Error al inicializar el motor TTS: {e}. La salida de voz podría no funcionar.")
        return None

@st.cache_resource
def init_stt_recognizer():
    return sr.Recognizer()

@st.cache_resource
def init_stt_microphone():
    try:
        return sr.Microphone()
    except Exception as e:
        st.warning(f"No se pudo inicializar el micrófono: {e}. El reconocimiento de voz podría no funcionar.")
        return None

# --- Inicialización de Recursos ---
tts_engine = init_tts_engine()
recognizer = init_stt_recognizer()
microphone = init_stt_microphone()

# --- Variable global para el hilo de TTS ---
tts_thread = None

def tts_task(engine, text_to_speak):
    """Tarea que se ejecutará en un hilo separado para TTS."""
    try:
        engine.say(text_to_speak)
        engine.runAndWait()
    except RuntimeError as e:
        if "run loop already started" in str(e).lower():
            print(f"TTS Thread Warning: {e}")
        else:
            print(f"TTS Thread RuntimeError: {e}")
    except Exception as e:
        print(f"TTS Thread Exception: {e}")

def speak_text_threaded(text):
    """Convierte texto a voz en un hilo separado, intentando detener el anterior."""
    global tts_thread, tts_engine # Asegurarse de que tts_engine es accesible
    if tts_engine and st.session_state.get("tts_enabled", True):
        # Si hay un hilo anterior, intentar detener el motor y esperar que termine el hilo
        if tts_thread is not None and tts_thread.is_alive():
            st.info("Voz anterior en proceso, intentando detener...")
            tts_engine.stop() # Intenta detener el motor de voz
            tts_thread.join(timeout=1.0) # Espera un poco a que termine
            if tts_thread.is_alive():
                st.warning("La voz anterior no pudo ser detenida rápidamente.")
                # No iniciar una nueva voz si la anterior no se detiene para evitar conflictos.
                # O podrías decidir iniciarla de todas formas, pero puede causar problemas.
                return


        # Crear y iniciar el nuevo hilo
        tts_thread = threading.Thread(target=tts_task, args=(tts_engine, text))
        tts_thread.start()


def listen_to_speech_streamlit(timeout=7, phrase_time_limit=10):
    if not microphone:
        st.error("Micrófono no disponible.")
        return None
    with microphone as source:
        try:
            # st.info("Ajustando ruido ambiental...") # Puede ser un poco molesto cada vez
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
        except Exception as e:
            st.warning(f"No se pudo ajustar el ruido ambiental: {e}. Continuand...")

        st.info("🎤 Escuchando... (Habla ahora)")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            with st.spinner("Procesando tu voz..."):
                text = recognizer.recognize_google(audio, language='es-ES')
            st.success(f"Has dicho: {text}")
            return text
        except sr.WaitTimeoutError:
            st.warning("No se detectó audio. Intenta de nuevo.")
            return None
        except sr.UnknownValueError:
            st.warning("No pude entender lo que dijiste. Intenta de nuevo.")
            return None
        except sr.RequestError as e:
            st.error(f"Error con el servicio de reconocimiento de voz; {e}")
            return None
        except Exception as e:
            st.error(f"Ocurrió un error inesperado al escuchar: {e}")
            return None

def get_deepseek_response(prompt_messages):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    data = {
        "model": MODEL_NAME,
        "messages": prompt_messages,
        "max_tokens": st.session_state.get("max_tokens", 1500), # Aumentado un poco por defecto para respuestas más elaboradas
        "temperature": st.session_state.get("temperature", 0.7),
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=90) # Timeout aumentado
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
        st.error(f"Error al decodificar la respuesta JSON. Respuesta: {response.text if 'response' in locals() else 'No response object'}")
        return "Lo siento, recibí una respuesta malformada de EmprendoBot."
    except Exception as e:
        st.error(f"Un error inesperado ocurrió al contactar la API: {e}")
        return "Lo siento, ocurrió un error inesperado."

# --- Interfaz de Streamlit ---
st.title("🚀 EmprendoBot IoT Assistant")
st.caption("Tu copiloto para ideas de negocio IoT y planes de emprendimiento.")

# --- Sidebar para Opciones ---
with st.sidebar:
    st.header("⚙️ Opciones")
    if "tts_enabled" not in st.session_state:
        st.session_state.tts_enabled = True
    st.session_state.tts_enabled = st.toggle("Voz de EmprendoBot (TTS)", value=st.session_state.tts_enabled)
    
    st.subheader("Parámetros del Modelo")
    if "max_tokens" not in st.session_state:
        st.session_state.max_tokens = 1500
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7

    st.session_state.max_tokens = st.slider("Max Tokens (longitud respuesta)", 200, 4000, st.session_state.max_tokens, 100)
    st.session_state.temperature = st.slider("Creatividad (Temperature)", 0.1, 1.0, st.session_state.temperature, 0.1)
    
    if st.button("🧹 Limpiar Chat", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT}]
        st.success("Historial de chat limpiado.")
        if tts_thread is not None and tts_thread.is_alive(): # Detener TTS si está activo
            tts_engine.stop()
        st.rerun()

    st.markdown("---")
    st.markdown("### ¿Cómo usar EmprendoBot?")
    st.markdown("""
    - Pídele ideas de negocio IoT.
    - Pregunta cómo formular una propuesta.
    - Discute los elementos de un plan de negocio.
    - Consulta sobre tecnologías IoT.
    """)
    st.markdown("---")
    st.markdown("Desarrollado con IA y ☕")


# --- Inicializar historial de chat en session_state ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT}
    ]

# --- Mostrar mensajes del chat ---
for message in st.session_state.messages:
    if message["role"] == "system": # No mostramos el mensaje de sistema al usuario
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Lógica de interacción ---
def process_user_input(user_text):
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant", avatar="🤖"): # Avatar para el bot
            message_placeholder = st.empty()
            full_response = ""
            with st.spinner("EmprendoBot está generando ideas... 💡"):
                max_history_items_api = 15 # System prompt + últimos 7 intercambios
                api_messages = []
                if st.session_state.messages and st.session_state.messages[0]["role"] == "system":
                    api_messages.append(st.session_state.messages[0])
                    # Tomar los últimos N mensajes de usuario/asistente
                    user_assistant_messages = [m for m in st.session_state.messages[1:] if m["role"] in ["user", "assistant"]]
                    api_messages.extend(user_assistant_messages[-(max_history_items_api-1):])
                else:
                    # Si no hay mensaje de sistema, o para ser más robustos
                    api_messages.append({"role": "system", "content": SYSTEM_PROMPT_ENTREPRENEURSHIP_IOT})
                    user_assistant_messages = [m for m in st.session_state.messages if m["role"] in ["user", "assistant"]]
                    api_messages.extend(user_assistant_messages[-max_history_items_api:])
                
                assistant_response = get_deepseek_response(api_messages)
            
            # Efecto de "escribiendo"
            response_chunks = assistant_response.split(" ")
            for i, chunk in enumerate(response_chunks):
                full_response += chunk + " "
                message_placeholder.markdown(full_response + ("▌" if i < len(response_chunks) -1 else ""))
                time.sleep(0.03 if len(chunk) < 5 else 0.05) # Más lento para palabras largas
            message_placeholder.markdown(full_response.strip())

        st.session_state.messages.append({"role": "assistant", "content": full_response})

        if st.session_state.get("tts_enabled", True):
            speak_text_threaded(full_response)
        
        max_history_streamlit = 40 # System prompt + 19 intercambios
        if len(st.session_state.messages) > max_history_streamlit:
            if st.session_state.messages[0]["role"] == "system":
                st.session_state.messages = [st.session_state.messages[0]] + st.session_state.messages[-(max_history_streamlit-1):]
            else:
                st.session_state.messages = st.session_state.messages[-max_history_streamlit:]

# --- Manejo de Entradas (Texto y Voz) ---
input_container = st.container() # Para agrupar el botón de voz y el input de texto

with input_container:
    col1, col2 = st.columns([0.8, 0.2]) # Ajustar proporción si es necesario
    
    with col1:
        if prompt := st.chat_input("Pregunta a EmprendoBot sobre tu idea IoT...", key="chat_input_main"):
            process_user_input(prompt)
            st.rerun() # Asegurar que se procese y actualice completamente

    with col2:
        if microphone:
            # Usar un ID único para el botón si hay otros botones
            if st.button("🎤 Voz", use_container_width=True, key="speak_button_main", help="Habla tu consulta"):
                st.session_state.voice_input_triggered = True
        else:
            st.caption("Voz no disp.")

# Procesar entrada de voz si se activó (fuera del bloque de columnas para que ocurra después)
if st.session_state.get("voice_input_triggered", False):
    st.session_state.voice_input_triggered = False
    transcribed_text = listen_to_speech_streamlit()
    if transcribed_text:
        # Enviar el texto transcrito como si fuera un input de chat para consistencia
        # Esto puede requerir un pequeño truco o simplemente llamar a process_user_input
        # y luego un rerun para que el chat_input se limpie.
        # st.session_state.manual_input = transcribed_text # Podrías setear el valor del chat_input
        process_user_input(transcribed_text)
        st.rerun()