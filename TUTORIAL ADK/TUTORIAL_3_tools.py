import os
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from getpass import getpass

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

#HERRAMIENTA GOOGLESEARTCHTOOL
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

    # Crear un agente con la herramienta de búsqueda de Google
agente_search = LlmAgent(
    name="InvestigadorGoogle",
    model="gemini-2.5-flash",
    description="Un agente que usa búsqueda de Google para responder preguntas actuales",
    tools=[google_search],  # Herramienta preconstruida
    instruction=(
        "Eres un investigador experto. "
        "Usa la búsqueda de Google para encontrar información actualizada. "
        "Cita tus fuentes cuando sea posible."
    )
)

print("✅ Agente investigador creado con GoogleSearchTool")

#PRUEBA DEL AGENTE CON HERRAMIENTA DE BÚSQUEDA

# Concepto clave: SessionService almacena el historial y estado de la conversación.
# InMemorySessionService es un almacenamiento simple y no persistente para este tutorial.
session_service = InMemorySessionService()

# Definir constantes para identificar el contexto de la interacción
APP_NAME = "agente_search_tool"
USER_ID = "user_1"
SESSION_ID = "session_001" # Usando un ID fijo por simplicidad

async def main():

    # Crear la sesión específica donde ocurrirá la conversación
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # Runner: Este es el componente principal que gestiona la interacción con el agente.
    runner = Runner(
        agent=agente_search,
        app_name=APP_NAME,
        session_service=session_service
    )

    # Hacer una consulta al agente
    await call_agent_async(
        "Como se llama el nuevo papa, para 2025",
        runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID
    )


# Ejecutar main() si el archivo se ejecuta como script----------------------------------------------------
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

#EJEMPLO NUEVO: BuiltInCodeExecutor para ejecución de codigo 
from google.adk.code_executors import BuiltInCodeExecutor
# Asegúrate también de tener estos imports:
# from google.adk import LlmAgent, Runner
# from google.adk.session import InMemorySessionService

# ⬇️⬇️⬇️ AÑADIR AQUÍ LA FUNCIÓN sumar_numeros ⬇️⬇️⬇️
def sumar_numeros(a: int, b: int) -> dict:
    """
    Suma dos números enteros y devuelve el resultado de forma estructurada.

    Usa esta herramienta cuando necesites sumar dos valores enteros.
    """
    try:
        print(f"🧮 Herramienta sumar_numeros llamada con a={a}, b={b}")
        resultado = a + b
        return {
            "status": "success",
            "result": resultado,
            "operation": f"Suma de {a} + {b}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Ocurrió un error al sumar los números: {str(e)}"
        }
    
#Definiendo mi nueva herramienta de búsqueda de productos
def buscar_producto_por_nombre(nombre_producto: str) -> dict:
    """
    Busca un producto por su nombre en el catálogo y devuelve un diccionario con sus detalles.

    Usa esta herramienta si el usuario solicita información de un producto específico.

    Args:
        nombre_producto (str): Nombre del producto a buscar (no sensible a mayúsculas).

    Returns:
        dict: Diccionario con los siguientes posibles campos:
            - 'status' (str): "success" si se encontró el producto, "error" si no.
            - 'product' (dict, opcional): Detalles del producto si fue encontrado.
            - 'error_message' (str, opcional): Mensaje explicativo si no se encontró el producto.
    """
    print(f"🛍️ Buscando producto: '{nombre_producto}'")

    # Simulación de base de datos
    productos_db = {
        "laptop gamer": {
            "id": "LPG001",
            "nombre": "Laptop Gamer Pro",
            "precio": 1500,
            "stock": 10,
            "características": ["RTX 4070", "32GB RAM", "1TB SSD"]
        },
        "teclado mecánico": {
            "id": "TEC005",
            "nombre": "Teclado Mecánico RGB",
            "precio": 120,
            "stock": 25,
            "características": ["Switches Cherry MX", "RGB", "TKL"]
        },
        "monitor 4k": {
            "id": "MON003",
            "nombre": "Monitor 4K HDR",
            "precio": 400,
            "stock": 5,
            "características": ["27 pulgadas", "144Hz", "HDR10"]
        }
    }

    producto = productos_db.get(nombre_producto.lower())

    if producto:
        return {
            "status": "success",
            "product": producto
        }
    else:
        return {
            "status": "error",
            "error_message": f"Producto '{nombre_producto}' no encontrado en el catálogo."
        }

    


# ⬆️⬆️⬆️ HASTA AQUÍ LA FUNCIÓN NUEVA ⬆️⬆️⬆️

AGENT_NAME = "calculator_agent"
APP_NAME = "calculator"
USER_ID = "user1234"
SESSION_ID = "session_code_exec_async"
GEMINI_MODEL = "gemini-2.5-flash"



code_agent = LlmAgent(
    name=AGENT_NAME,
    model=GEMINI_MODEL,
    tools=[sumar_numeros, buscar_producto_por_nombre],
    instruction="""Eres un agente calculadora.
Cuando necesites sumar dos números enteros, usa la herramienta sumar_numeros.
Para cualquier otro cálculo, razona paso a paso como modelo de lenguaje, sin ejecutar código Python.
Además, si el usuario te pide información sobre un producto, usa la herramienta buscar_producto_por_nombre para obtener los detalles del producto solicitado.
""",
    description="Ejecuta cálculos matemáticos usando tools y ejecución de código y busca productos en un catálogo.",
)

# Session and Runner
session_service = InMemorySessionService()

# Función asincrónica para enviar una consulta al agente y procesar los eventos que devuelve
async def call_agent_async_code(query, runner, user_id, session_id):
    # Crear el mensaje con el texto del usuario en el formato requerido por ADK
    content = types.Content(role="user", parts=[types.Part(text=query)])
    print(f"\n--- Ejecutando Consulta: {query} ---")

    # Variable para almacenar la respuesta final del agente
    final_response_text = "No se capturó una respuesta final de texto."

    # Inicia el ciclo asincrónico para procesar cada evento emitido por el agente
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        print(f"ID del Evento: {event.id}, Autor: {event.author}")

        # --- Verificar si el evento contiene partes específicas como código o resultados ---
        has_specific_part = False
        if event.content and event.content.parts:
            for part in event.content.parts:  # Iterar por todas las partes del contenido
                if part.executable_code:
                    # Si hay código ejecutable generado por el agente, lo imprimimos
                    print(
                        f"  Debug: Código generado por el agente:\n```python\n{part.executable_code.code}\n```"
                    )
                    has_specific_part = True
                elif part.code_execution_result:
                    # Si hay resultado de ejecución de código, mostrar el resultado
                    print(
                        f"  Debug: Resultado de ejecución de código: {part.code_execution_result.outcome} - Salida:\n{part.code_execution_result.output}"
                    )
                    has_specific_part = True
                elif part.text and not part.text.isspace():
                    # Si hay texto plano, lo mostramos (no se considera parte "específica")
                    print(f"  Texto: '{part.text.strip()}'")
                    # No marcamos `has_specific_part = True` aquí para no interferir con la lógica de respuesta final

        # --- Verificar si es una respuesta final (después de manejar partes específicas) ---
        # Solo consideramos esta respuesta como final si no hubo partes específicas antes
        if not has_specific_part and event.is_final_response():
            if (
                event.content
                and event.content.parts
                and event.content.parts[0].text
            ):
                final_response_text = event.content.parts[0].text.strip()
                print(f"==> Respuesta Final del Agente: {final_response_text}")
            else:
                print("==> Respuesta Final del Agente: [Sin contenido de texto en el evento final]")

    # Mensaje final de cierre
    print("-" * 30)

async def main():
    # Crear sesión
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    # Crear runner
    runner = Runner(
        agent=code_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # Aquí podrías hacer ya una llamada al agente, por ejemplo:
    # await call_agent_async("2 + 2 * 5", runner, USER_ID, SESSION_ID)

    # AQUÍ FALTABA LLAMAR A LA FUNCIÓN DE CÁLCULO 👇
    # ❌ ANTES ESTABA COMENTADO Y LA CALCULADORA NUNCA SE EJECUTABA
    # ✅ LO ACTIVAMOS PARA QUE SE HAGA LA PREGUNTA DE CÁLCULO
    await call_agent_async_code(
        "Calcula el valor de ((5 + 7 + 10) * 12) elevado a la 2",
        runner,
        USER_ID,
        SESSION_ID
    )

    await call_agent_async_code("Suma 34 y 89 usando la herramienta", runner, USER_ID, SESSION_ID)

    await call_agent_async_code("buscame un monitor 4k", runner, USER_ID, SESSION_ID)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())








