# agente_reddit_adk.py

import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types



from ADK_TFM.reddit_tools import (
    buscar_subreddits_psicologia,
    buscar_posts_actitud_psicologia,
    guardar_posts_en_csv
)

# Cargar variables desde google.env (clave de Gemini)
load_dotenv("google.env")

# Ruta base = carpeta donde está ESTE archivo (.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cargar las variables de google.env desde esa carpeta
load_dotenv(os.path.join(BASE_DIR, "google.env"))

# -----------------------------
# CONFIGURACIÓN BÁSICA DEL AGENTE
# -----------------------------
APP_NAME = "tfm_reddit_psicologia"
USER_ID = "elena_y_marta"          # puedes poner lo que quieras, solo que sea constante
SESSION_ID = "sesion_1"    # igual, un identificador de sesión
MODEL_NAME = "gemini-2.0-flash"

# (Opcional) Comprobación rápida de la API key
def _check_api_key():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No se encontró GEMINI_API_KEY ni GOOGLE_API_KEY en las variables de entorno. "
            "Configura tu clave de Gemini antes de ejecutar el agente."
        )

# -----------------------------
# CREACIÓN DEL AGENTE ADK
# -----------------------------

# 1. Creamos el agente LLM que usará la tool de Reddit
reddit_agent = LlmAgent(
    name="AgenteRedditPsicologia",
    model=MODEL_NAME,
   instruction=(
    "Eres un agente para un trabajo de fin de máster en psicología. "
    "Tu objetivo es ayudar a analizar la actitud hacia la psicología y "
    "la terapia a través de foros de Reddit.\n\n"

    "REGLAS OBLIGATORIAS:\n"
    "- Debes llamar primero a buscar_subreddits_psicologia.\n"
    "- Debes solicitar hasta 10 subreddits (max_subreddits=10) e incluir español e inglés (incluir_idiomas='es,en').\n"
    "- Debes usar TODOS los subreddits devueltos (hasta 10) y pasar sus nombres a buscar_posts_actitud_psicologia.\n"
    "- En buscar_posts_actitud_psicologia debes usar max_posts_por_subreddit=30.\n"
    "- Debes guardar TODOS los posts encontrados usando guardar_posts_en_csv con nombre_fichero='posts_varios_subreddits.csv'.\n\n"

    "Al final, NO escribas un resumen largo. Solo devuelve:\n"
    "1) Cuántos subreddits usaste\n"
    "2) Cuántos posts guardaste\n"
    "3) El nombre del archivo generado"
), 

    tools=[
    buscar_subreddits_psicologia,
    buscar_posts_actitud_psicologia,
    guardar_posts_en_csv
],


    description="Agente que busca subreddits de psicología relevantes para un TFM.",
)

# 2. Creamos el servicio de sesiones y el runner
session_service = InMemorySessionService()

# Creamos (o registramos) una sesión (versión asíncrona)
session = asyncio.run(
    session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
)

# Creamos el runner que ejecuta el agente
runner = Runner(
    agent=reddit_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

# -----------------------------
# FUNCIÓN DE AYUDA PARA HABLAR CON EL AGENTE
# -----------------------------
def preguntar_al_agente(mensaje_usuario: str) -> str:
    """
    Envía un mensaje al agente ADK y devuelve el texto final de respuesta.
    """
    content = types.Content(
        role="user",
        parts=[types.Part(text=mensaje_usuario)],
    )

    try: events = runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    )
    except Exception as e:
        print("ERROR REAL DEL MODELO:", repr(e))
        raise
    respuesta_final = "No se recibió respuesta final del agente."

    for event in events:
        if event.is_final_response():
            if event.content and event.content.parts:
                textos = []
                for part in event.content.parts:
                    # Algunas parts no tienen .text (pueden ser function_call / function_response)
                    t = getattr(part, "text", None)
                    if t:
                        textos.append(t)
                if textos:
                    respuesta_final = "\n".join(textos)

    return respuesta_final



# -----------------------------
# PRUEBA RÁPIDA DESDE TERMINAL
# -----------------------------
if __name__ == "__main__":
    _check_api_key()

    print("Lanzando prueba del agente ADK con la Tool de Reddit...\n")

    # ---------------------------------------------------------
    # DEBUG (opcional): comprobar cuántos subreddits devuelve la Tool 1
    # Actívalo quitando los # de abajo.
    # ---------------------------------------------------------
subs = buscar_subreddits_psicologia(
         incluir_idiomas="es,en",
         max_subreddits=10,
         min_suscriptores=300,  # prueba 300/500/1000 para comparar
     )
    
print("\n=== DEBUG TOOL 1 ===")
print("Subreddits devueltos por la tool:", len(subs))
print("Nombres:", [s["nombre"] for s in subs])
print("=== FIN DEBUG TOOL 1 ===\n")

pregunta = (
        "Quiero estudiar la actitud hacia la psicología y la terapia usando foros de Reddit.\n\n"
        "1) Usa buscar_subreddits_psicologia con estos parámetros:\n"
        "- incluir_idiomas='es,en'\n"
        "- max_subreddits=10\n\n"
        "2) Con los nombres de TODOS los subreddits encontrados (hasta 10), usa buscar_posts_actitud_psicologia con:\n"
        "- max_posts_por_subreddit=15\n\n"
        "3) Guarda TODOS los posts encontrados con guardar_posts_en_csv usando:\n"
        "- nombre_fichero='posts_varios_subreddits.csv'\n\n"
        "Devuélveme SOLO:\n"
        "1) Cuántos subreddits usaste\n"
        "2) Cuántos posts guardaste\n"
        "3) El nombre del archivo generado"
    )

respuesta = preguntar_al_agente(pregunta)
print("\n=== RESPUESTA DEL AGENTE ===\n") #quitar almoadilla 
print(respuesta)
