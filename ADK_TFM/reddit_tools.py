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
    termino_busqueda: str | None = None, 
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

    if termino_busqueda is not None and termino_busqueda.strip():
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

def detectar_idioma_simple(texto: str) -> str:
    """
    Heurística sencilla:
    - Si detecta tildes/ñ/¿/¡ o stopwords típicas -> 'es'
    - Si no -> 'en'
    """
    t = f" {texto.lower()} "

    if any(c in t for c in ["á", "é", "í", "ó", "ú", "ñ", "¿", "¡"]):
        return "es"

    marcadores_es = [" el ", " la ", " de ", " que ", " y ", " en ", " por ", " para ", " pero ", " con "]
    if any(m in t for m in marcadores_es):
        return "es"

    return "en"


# -----------------------------
# TOOL 2
# Buscar posts relevantes dentro de subreddits
# -----------------------------
def buscar_posts_actitud_psicologia(
    subreddits: List[str],
    limite_posts: int = 300,
    limite_total: int = 3000
) -> List[Dict]:

    """
    Busca posts dentro de varios subreddits que tengan relación
    con actitudes hacia la psicología / terapia.
    """
    reddit = _crear_cliente_reddit()

    palabras_clave = [
        # Inglés
        # Psicología / profesionales
        "psychology", "psychologist", "clinical psychologist",
        "mental health professional", "mental health care",
        "mental health services",

        # Terapia / proceso terapéutico
        "therapy", "therapist", "psychotherapy",
        "counseling", "counselling",
        "talk therapy", "cbt", "cognitive behavioral therapy",
        "starting therapy", "going to therapy",
        "went to therapy", "seeing a therapist",
        "in therapy", "therapy sessions",

        # Actitudes, creencias, utilidad
        "does therapy work", "does it work",
        "worth it", "helpful", "not helpful",
        "effective", "ineffective",
        "worked for me", "didn't work for me",
        "waste of money", "best decision",

        # Barreras, estigma, desconfianza
        "stigma", "stigmatized", "skeptic", "skeptical",
        "trust", "mistrust",
        "afraid to go", "hesitant to seek help",
        "embarrassed", "ashamed",
        "negative experience", "bad therapist",

        # Psiquiatría / diagnóstico (contextual)
        "psychiatrist", "psychiatry",
        "medication", "medication vs therapy",
        "diagnosed", "mental disorder",
    


        # Español
         # Psicología / profesionales
        "psicología", "psicologo", "psicólogo", "psicóloga",
        "profesional de la salud mental",
        "servicios de salud mental",

        # Terapia
        "terapia", "terapeuta", "psicoterapia",
        "terapia psicológica",
        "ir a terapia", "empezar terapia",
        "fui a terapia", "estoy en terapia",
        "sesiones de terapia",

        # Actitudes, creencias, utilidad
        "sirve la terapia", "no sirve la terapia",
        "merece la pena", "vale la pena",
        "me ayudó", "no me ayudó",
        "funciona", "no funciona",
        "experiencia positiva", "experiencia negativa",

        # Barreras y estigma
        "estigma", "estigmatizado",
        "desconfianza", "confianza",
        "vergüenza", "miedo a ir",
        "reticente", "reacio",
        "mala experiencia", "mal psicólogo",

        # Psiquiatría / diagnóstico (contextual)
        "psiquiatra", "psiquiatría",
        "medicación", "diagnóstico",
        "trastorno mental"
    ]

    posts_encontrados = []
    ids_vistos = set()  # ✅ evita duplicados dentro de la misma extracción

    for nombre_subreddit in subreddits:
        subreddit = reddit.subreddit(nombre_subreddit)

        for post in subreddit.new(limit=limite_posts):
            if post.id in ids_vistos:
                continue

            texto_total = f"{post.title} {post.selftext}".lower()

            idioma = detectar_idioma_simple(texto_total)

            if any(palabra in texto_total for palabra in palabras_clave):
                ids_vistos.add(post.id)

                posts_encontrados.append({
                    "subreddit": nombre_subreddit,
                    "id": post.id,  # ✅ tool 3 lo espera
                    "titulo": post.title,
                    "texto": post.selftext,
                    "url": f"https://www.reddit.com{post.permalink}",  # ✅ estable
                    "score": post.score,
                    "num_comentarios": post.num_comments,
                    "creado_utc": int(post.created_utc),  # ✅ tool 3 lo espera
                    "idioma": idioma,

                })

                if len(posts_encontrados) >= limite_total:
                    return posts_encontrados

    # ✅ este return va AL FINAL de la función
    return posts_encontrados



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
        "idioma", #nuevo
    ]

    with open(nombre_fichero, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for p in posts:
            fila = {campo: p.get(campo, "") for campo in campos}
            writer.writerow(fila)

    return os.path.abspath(nombre_fichero)
