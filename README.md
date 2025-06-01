# EmprendoBot IoT

EmprendoBot IoT es un asistente web interactivo, desarrollado con Streamlit, que utiliza la API de DeepSeek para brindar recomendaciones y guías sobre emprendimientos en el ámbito del Internet de las Cosas (IoT).

## Descripción breve

EmprendoBot IoT está diseñado específicamente para:
- Generar ideas de negocios basadas en IoT.
- Ayudar a formular propuestas de valor enfocadas en soluciones conectadas.
- Sugerir componentes clave de un plan de negocio (análisis de mercado, modelo de ingresos, proyecciones).
- Explicar tecnologías IoT relevantes (sensores, plataformas de conectividad, análisis de datos, seguridad).
- Identificar desafíos y riesgos propios de emprendimientos IoT y cómo mitigarlos.

Cada solicitud del usuario —p. ej., “Ideas de IoT para agricultura”— se envía junto a un prompt de sistema especializado que indica al modelo DeepSeek actuar como “asistente experto en emprendimiento IoT”. De esta forma, las respuestas siempre se mantienen alineadas con el dominio IoT.

## Características principales

- **Interfaz web con Streamlit**: sencilla y responsive, permite escribir o dictar preguntas y mostrar respuestas con efecto de “escritura” dinámica.
- **API DeepSeek (modelo `deepseek-chat`)**: genera contenido en español, adaptado al contexto de IoT y negocios.
- **Reconocimiento de Voz (ASR)**: permite al usuario dictar sus preguntas utilizando la Web Speech API del navegador.
- **Reproducción de voz (TTS)**: convierte cada respuesta en audio mediante la API de síntesis de voz del navegador, con opción de reproducción automática.
- **Historial de conversación**: mantiene hasta 40 intercambios en memoria y envía siempre los últimos 15 mensajes a la API para preservar contexto sin sobrecargar tokens.
- **Ajustes de modelo**: controles para modificar `max_tokens` (longitud de la respuesta) y `temperature` (nivel de creatividad).

## Instalación y ejecución

1.  **Clonar el repositorio**
    ```bash
    git clone https://github.com/TU_USUARIO/EmprendoBot-IoT.git
    cd EmprendoBot-IoT
    ```

2.  **Instalar dependencias**
    ```bash
    pip install streamlit requests
    ```

3.  **Configurar la API Key de DeepSeek**

    *   **Opción 1: Secrets de Streamlit (Recomendado para despliegue)**
        Crear un archivo `.streamlit/secrets.toml` en la raíz del proyecto con el siguiente contenido:
        ```toml
        DEEPSEEK_API_KEY = "tu-deepseek-api-key-aqui"
        ```

    *   **Opción 2: Variable de entorno (Para desarrollo local)**
        Exportar la variable de entorno:
        ```bash
        export DEEPSEEK_API_KEY="tu-deepseek-api-key-aqui"
        ```
        (En Windows, usa `set DEEPSEEK_API_KEY="tu-deepseek-api-key-aqui"` en CMD o `$env:DEEPSEEK_API_KEY="tu-deepseek-api-key-aqui"` en PowerShell).

4.  **Iniciar la aplicación**
    ```bash
    streamlit run app.py
    ```
    Luego, abrir en el navegador la URL que Streamlit indique (por defecto `http://localhost:8501`).

## Uso

1.  **Ingresar pregunta**:
    *   Escribe tu pregunta en el campo de chat (ej: “¿Qué idea de negocio IoT podría implementar en una granja?”).
    *   O haz clic en el botón del micrófono 🎤 para dictar tu pregunta. (Necesitarás otorgar permiso al navegador para usar el micrófono).
2.  **Enviar**: Presiona Enter o espera a que la voz se procese.
3.  **Respuesta**: EmprendoBot IoT procesará el contexto (incluyendo el prompt especializado) y mostrará la respuesta con un efecto de escritura.
4.  **Audio**: Si la opción “🔊 Reproducir respuestas automáticamente” está activada, la respuesta se escuchará en voz alta. También puedes hacer clic en "🔊 Escuchar" en cualquier respuesta del bot.

## Resumen de la arquitectura

### Prompt de sistema especializado
```text
Eres EmprendoBot, un asistente experto en emprendimiento con un fuerte enfoque en el Internet de las Cosas (IoT). ...
