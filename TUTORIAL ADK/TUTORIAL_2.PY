import os
from dotenv import load_dotenv
import asyncio
print("🔑 Cargando API Keys desde archivos .env...\n")

# --- Cargar cada archivo .env independiente ---
load_dotenv(dotenv_path="google.env")
load_dotenv(dotenv_path="openAI.env")
load_dotenv(dotenv_path="anthropic.env")

# --- Leer valores cargados ---
google_key = os.getenv("GOOGLE_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
vertex_flag = os.getenv("GOOGLE_GENAI_USE_VERTEXAI")

# --- Mostrar estado ---
print("📋 Estado de las API Keys:")
print(f"   Google (Gemini): {'✅' if google_key else '❌'}")
print(f"   Anthropic: {'✅' if anthropic_key else '❌'}")
print(f"   OpenAI: {'✅' if openai_key else '❌'}")
print(f"   Google VertexAI Flag: {vertex_flag}")

# 👉 AQUÍ DEFINIMOS EL MODELO, FUERA DE LA FUNCIÓN
MODEL_GEMINI = "gemini-2.5-flash"

# o el modelo que estéis usando

#CREAR AGENTES CON DIFERENTES MODELOS
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

async def call_agent_async(query: str, runner, user_id, session_id):
    """Envía una consulta al agente e imprime la respuesta final."""
    print(f"\n>>> Consulta del usuario: {query}")

    # Prepara el mensaje del usuario en el formato de ADK
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "El agente no produjo una respuesta final." # Valor por defecto

    # Concepto clave: run_async ejecuta la lógica del agente y genera eventos.
    # Iteramos a través de los eventos para encontrar la respuesta final.
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        # Puedes descomentar la línea de abajo para ver *todos* los eventos durante la ejecución
        # print(f"  [Evento] Autor: {event.author}, Tipo: {type(event).__name__}, Final: {event.is_final_response()}, Contenido: {event.content}")

        # Concepto clave: is_final_response() marca el mensaje que concluye el turno.
        if event.is_final_response():
            if event.content and event.content.parts:
                # Se asume que la respuesta de texto está en la primera parte
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate: # Maneja posibles errores/escalamientos
                final_response_text = f"El agente escaló: {event.error_message or 'Sin mensaje específico.'}"
            # Agrega más validaciones aquí si es necesario (por ejemplo, códigos de error específicos)
            break # Deja de procesar eventos una vez encontrada la respuesta final

    print(f"<<< Respuesta del agente: {final_response_text}")

# Example: Defining the basic Agent
refranes_agent = LlmAgent(
    model=MODEL_GEMINI,
    name="psychology_emotion",
    description="Te digo una frase y me das un número que represente la connotación emocional de esa palabra donde 0 es muy negativa y 100 muy positiva"
)

#CREAR UNA SESIÓN PARA UTILIZAR EL AGENTE
async def main():
    #CREAR UNA SESIÓN PARA UTILIZAR EL AGENTE
    session_service = InMemorySessionService()

    APP_NAME = "test_gemini"
    USER_ID = "user_1"
    SESSION_ID = "session_001"  # Using a fixed ID for simplicity

    # Create the specific session where the conversation will happen
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # Runner: This is the main component that manages the interaction with the agent.
    runner_gemini = Runner(
        agent=refranes_agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    # (Opcional) Probar una consulta al agente desde aquí:
    await call_agent_async("Amo estar con mis amigos", runner_gemini, USER_ID, SESSION_ID)

if __name__ == "__main__":
    asyncio.run(main())
