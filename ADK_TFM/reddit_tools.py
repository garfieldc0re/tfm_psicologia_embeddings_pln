# reddit_tools.py

import os
import csv
import time
from datetime import datetime
from typing import Any, Dict, List

import praw
from dotenv import load_dotenv
from prawcore.exceptions import Forbidden, NotFound, Redirect, TooManyRequests

PostDict = Dict[str, Any]


# 1. Cargar variables de entorno desde reddit.env, para que vaya desde cualquier directorio 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "reddit.env"))


REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# 2. Crear el cliente de Reddit (PRAW)
def _crear_cliente_reddit() -> praw.Reddit:
    """Crea y devuelve un cliente de Reddit usando las credenciales de reddit.env."""
    if not (REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET and REDDIT_USER_AGENT):
        raise RuntimeError(
            "Faltan credenciales de Reddit. Revisa el archivo 'reddit.env' "
            "y comprueba que tiene REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET y REDDIT_USER_AGENT."
        )

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
        check_for_async=False,
    )
    return reddit

# 3. TOOL 1 para ADK (CORREGIDA: multi-búsqueda + deduplicado)
def buscar_subreddits_psicologia(
    termino_busqueda: str = "",
    incluir_idiomas: str = "es,en",
    max_subreddits: int = 100,
    min_suscriptores: int = 300,
) -> List[Dict]:
    """
    Tool ADK: Busca subreddits relacionados con psicología / salud mental
    y devuelve una lista de subreddits en formato estructurado.

    Estrategia:
    1) Varias búsquedas cortas (mejor que OR gigante).
    2) Deduplicado.
    3) Filtro por relevancia temática usando title + public_description.
    """
    reddit = _crear_cliente_reddit()

    idiomas_permitidos = {
        idioma.strip().lower()
        for idioma in incluir_idiomas.split(",")
        if idioma.strip()
    }

    # Palabras clave para filtrar subreddits realmente relacionados
    keywords_subreddit = [
        "psychology", "psychological", "psychologist",
        "mental health", "mentalhealth",
        "therapy", "therapist", "counseling", "counsellor", "psychotherapy",
        "psychiatry", "psychiatrist",
        "psicologia", "psicología", "psicologo", "psicólogo", "psicóloga",
        "salud mental", "terapia", "terapeuta", "psicoterapia",
        "psiquiatria", "psiquiatría", "psiquiatra",
        "ansiedad", "depresion", "depresión", "trauma", "toc", "tdah", "adhd", "autism", "tea",
    ]

    # Subreddits genéricos a excluir (suelen colarse siempre)
    blacklist = {
        "askreddit", "todayilearned", "aww", "memes", "jokes",
        "askscience", "science", "futurology", "writingprompts",
        "amitheasshole"
    }

    queries = [
        "psychology",
        "mental health",
        "therapy",
        "therapist",
        "counseling",
        "psychotherapy",
        "psychiatry",
        "psicologia",
        "psicología",
        "salud mental",
        "terapia",
        "psicoterapia",
        "psiquiatria",
        "psiquiatría",
    ]

    if termino_busqueda and termino_busqueda.strip():
        queries.insert(0, termino_busqueda.strip())

    candidatos: Dict[str, Any] = {}
    limite_por_query = max(50, max_subreddits * 5)

    for q in queries:
        q = q.strip()
        if not q:
            continue

        try:
            for sub in reddit.subreddits.search(q, limit=limite_por_query):
                key = (sub.display_name or "").lower().strip()
                if key and key not in candidatos:
                    candidatos[key] = sub
        except Exception:
            pass

        try:
            for sub in reddit.subreddits.search_by_name(q, include_nsfw=False, exact=False):
                key = (sub.display_name or "").lower().strip()
                if key and key not in candidatos:
                    candidatos[key] = sub
        except Exception:
            pass

    resultados: List[Dict] = []

    for key, sub in candidatos.items():
        try:
            # Excluir genéricos
            if key in blacklist:
                continue

            # Evitar NSFW
            if bool(getattr(sub, "over18", False)):
                continue

            subs = int(getattr(sub, "subscribers", 0) or 0)
            if subs < int(min_suscriptores):
                continue

            lang = (getattr(sub, "lang", "") or "").lower().strip()
            if idiomas_permitidos and lang and lang not in idiomas_permitidos:
                continue

            titulo = (getattr(sub, "title", "") or "").strip()
            desc = (getattr(sub, "public_description", "") or "").strip()
            texto_ref = f"{titulo}\n{desc}".lower()

            # ✅ Filtro clave: debe contener keywords relacionadas
            if not any(k in texto_ref for k in keywords_subreddit):
                continue

            resultados.append(
                {
                    "nombre": sub.display_name,
                    "titulo": titulo,
                    "descripcion": desc,
                    "suscriptores": subs,
                    "nsfw": bool(getattr(sub, "over18", False)),
                    "idioma": lang or "desconocido",
                    "url": f"https://www.reddit.com{sub.url}",
                }
            )
        except Exception:
            continue

    resultados.sort(key=lambda x: x.get("suscriptores", 0), reverse=True)
    return resultados[:max_subreddits]



# 2. tool 3? o 2?    


def guardar_posts_en_csv(
    posts: List[Dict[str, Any]],
    nombre_fichero: str = "posts_psicologia.csv",
) -> str:
    """
    Tool 3: guarda la lista de posts en un fichero CSV.

    Columnas: subreddit, id, titulo, texto, url, score, num_comentarios, creado_utc.
    Devuelve la ruta absoluta del fichero creado.
    """
    if not posts:
        raise ValueError("La lista de posts está vacía; no hay nada que guardar.")

    campos = [
        "subreddit",
        "id",
        "titulo",
        "texto",
        "url",
        "score",
        "num_comentarios",
        "creado_utc",
    ]

    with open(nombre_fichero, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for p in posts:
            fila = {campo: p.get(campo, "") for campo in campos}
            writer.writerow(fila)

    return os.path.abspath(nombre_fichero)
