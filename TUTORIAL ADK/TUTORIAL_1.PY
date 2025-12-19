from dotenv import load_dotenv
import os

# Cargar archivo google.env explícitamente
load_dotenv("google.env")

# Obtener claves
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("❌ ERROR: No se encontró GOOGLE_API_KEY en google.env")

print("✅ Variables cargadas correctamente:")
print(f"   GOOGLE_API_KEY: {'✓' if api_key else '✗'}")
print(f"   GOOGLE_GENAI_USE_VERTEXAI: {os.getenv('GOOGLE_GENAI_USE_VERTEXAI')}")

#LIBRERÍAS DE GOOGLE
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types
import asyncio


#NOMBRE DEL AGENTE, MODELO ELEGIDO (GEMINI), CRACTERISTICAS CONCRETAS DEL AGENTE
agent_search = Agent(
    name="AgenteBuscadorSimple",
    model="gemini-2.5-flash",  # Modelo rápido y eficiente
    description="Un agente amigable que puede buscar información actualizada en Google.",
    tools=[google_search], # Herramienta de búsqueda
    instruction=(
        "Eres un asistente amigable y útil."
        "Cuando se te haga una pregunta, usa la herramienta de búsqueda de Google si es necesario."
        "Proporciona respuestas concisas y claras."
        "Si no estás seguro, busca información actualizada."
        "Siempre sé educado y profesional."
    )
)

#DEFINICÓN DEL CONTEXTO DE LA INTERACCIÓN
# Concepto clave: SessionService almacena el historial y estado de la conversación.
# InMemorySessionService es un almacenamiento simple y no persistente para este tutorial.
session_service = InMemorySessionService()

# Definir constantes para identificar el contexto de la interacción
APP_NAME = "mi_primer_agente"
USER_ID = "user_1"
SESSION_ID = "session_001" # Usando un ID fijo por simplicidad

# ===========================================================
# 2. CREAR EL SERVICIO DE SESIÓN (MEMORIA TEMPORAL)
# ===========================================================
# Concepto clave:
# SessionService almacena el historial y estado de la conversación.
# InMemorySessionService es un almacenamiento simple y NO PERSISTENTE.
session_service = InMemorySessionService()

# Información para identificar la sesión
APP_NAME = "mi_primer_agente"
USER_ID = "user_1"
SESSION_ID = "session_001"

# ===========================================================
# 3. FUNCIÓN ASÍNCRONA DONDE SE USA 'await'
# ===========================================================
async def main():

    # Crear la sesión real donde ocurrirá la conversación
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    print(f"Sesión creada: App='{APP_NAME}', Usuario='{USER_ID}', Sesión='{SESSION_ID}'")

    # Aquí luego añadiremos llamadas al agente con Runner
    # ...

# ===========================================================
# 4. EJECUTAR TODO
# ===========================================================
asyncio.run(main())

# Runner: Este es el componente principal que gestiona la interacción con el agente.
runner = Runner(agent=agent_search,
                app_name=APP_NAME,
                session_service=session_service)

print(f"Runner creado para el agente '{runner.agent.name}'.")

# EJEMPLO: Enviando mensajes al agente
events = runner.run(user_id=USER_ID,
          session_id=SESSION_ID,
          new_message=types.Content(role='user', parts=[types.Part(text="Quién es el presidente de Francia?")]))

for event in events:
    if event.is_final_response():
        if event.grounding_metadata.grounding_chunks:
            for _ in event.grounding_metadata.grounding_chunks:
                print(f"Grounding Chunk: {_.web.title}")
        # Extraer la respuesta final del agente
        else:
            print("No es necesario el uso de grounding.")                 
        final_response = event.content.parts[0].text
        print("Agent Response: ", final_response)

#EJEMPLO 2
events = runner.run(user_id=USER_ID,
          session_id=SESSION_ID,
          new_message=types.Content(role='user', parts=[types.Part(text="¿Qué te pregunté antes?")]))

for event in events:
    if event.is_final_response():
        if event.grounding_metadata.grounding_chunks:
            for _ in event.grounding_metadata.grounding_chunks:
                print(f"Grounding Chunk: {_.web.title}")
        # Extraer la respuesta final del agente
        else:
            print("No es necesario el uso de grounding.")                 
        final_response = event.content.parts[0].text
        print("Agent Response: ", final_response)