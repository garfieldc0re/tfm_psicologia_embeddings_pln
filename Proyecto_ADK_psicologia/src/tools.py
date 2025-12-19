#Funciones que operan sobre datos
# src/tools.py

# src/tools.py

from .corpus import POSTS

def cargar_posts():
    return POSTS

def filtrar_por_subreddit(subreddit: str):
    return [p for p in POSTS if p["subreddit"].lower() == subreddit.lower()]

def analizar_actitud(texto: str):
    texto = texto.lower()
    if "miedo" in texto or "ansiedad" in texto:
        return "negativa"
    if "ayudado" in texto or "ayuda" in texto or "me ha ayudado" in texto:
        return "positiva"
    return "neutra"

