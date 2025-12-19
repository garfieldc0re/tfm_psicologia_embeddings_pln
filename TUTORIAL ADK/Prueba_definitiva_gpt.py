# ============================================================
# pipeline_reddit_es_en.py
# ------------------------------------------------------------
# Recupera posts de Reddit EN INGLÉS Y ESPAÑOL sobre psicología,
# los analiza con ADK + Gemini y genera un CSV final para el TFM.
# ============================================================

import os
import asyncio
import json
import pandas as pd
import praw
from dotenv import load_dotenv

print("🔑 Cargando API Keys desde .env...\n")

load_dotenv("google.env")
load_dotenv("reddit.env")

# Keys
google_key = os.getenv("GOOGLE_API_KEY")
reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
reddit_user_agent = os.getenv("REDDIT_USER_AGENT")

print("📋 Claves cargadas:")
print(f"   Google (Gemini): {'✅' if google_key else '❌'}")
print(f"   Reddit client_id: {'✅' if reddit_client_id else '❌'}")
print(f"   Reddit secret:    {'✅' if reddit_client_secret else '❌'}")
print(f"   Reddit user_agent:{'✅' if reddit_user_agent else '❌'}")
print("\n------------------------------------------------------------")

# Reddit API
reddit = praw.Reddit(
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent=reddit_user_agent,
)

# ------------------------------------------------------------
# ADK
# ------------------------------------------------------------
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

MODEL_GEMINI = "gemini-2.5-flash"

analisis_psico_agent = LlmAgent(
    model=MODEL_GEMINI,
    name="analisis_psico_reddit",
    description=(
        "Analyze Reddit posts in ENGLISH or SPANISH about psychology, therapy, or mental health. "
        "Always return a STRICT, VALID JSON with exactly these fields:\n"
        "- texto_original\n"
        "- tema_principal: 'terapia', 'diagnostico', 'opinion_general', 'otra'\n"
        "- opinion_sobre_psicologia: 'positiva', 'negativa', 'neutra', 'ambivalente'\n"
        "- ha_ido_a_terapia: 'si', 'no', 'no_se'\n"
        "- motivo_ir_terapia\n"
        "- motivo_no_ir_terapia\n"
        "- emocion_principal: 'ansiedad','tristeza','miedo','esperanza','frustracion','otra'\n"
        "- intensidad_emocion: 1–5\n"
        "- actitud_hacia_buscar_ayuda: 'a_favor','en_contra','ambivalente','no_menciona'\n"
        "NEVER add explanations or text outside the JSON."
    ),
)

# ------------------------------------------------------------
# SEARCH CONFIG — ENGLISH + SPANISH
# ------------------------------------------------------------

QUERIES_ES = [
    "psicología", "psicologo", "psicóloga", "terapia", "ansiedad", "depresión"
]

QUERIES_EN = [
    "psychology", "therapist", "therapy", "anxiety", "depression", "counseling"
]

SUBREDDITS_ES = [
    "PsicologiaES", "psicoesp", "es", "espanol", "Hispanos", "saludmental"
]

SUBREDDITS_EN = [
    "psychology", "therapy", "mentalhealth", "selfimprovement", "Advice"
]

LIMIT_ES = 20
LIMIT_EN = 20


# ------------------------------------------------------------
# SEARCH FUNCTION
# ------------------------------------------------------------
def get_posts(query, subreddit, limit):
    print(f"🔎 Searching r/{subreddit} for: {query}")
    results = []

    try:
        for s in reddit.subreddit(subreddit).search(query, sort="new", limit=limit):
            body = (s.selftext or "").strip()
            texto = f"{s.title}\n\n{body}".strip()

            results.append({
                "id": s.id,
                "subreddit": str(s.subreddit),
                "title": s.title,
                "body": body,
                "texto": texto,
                "url": f"https://www.reddit.com{s.permalink}",
            })

    except Exception as e:
        print(f"⚠️ Error with r/{subreddit}: {e}")

    print(f"   → Found {len(results)} posts.\n")
    return results


# ------------------------------------------------------------
# SEARCH PIPELINE: ENGLISH + SPANISH
# ------------------------------------------------------------
def retrieve_posts():
    all_posts = []

    print("\n🌎 BUSCANDO POSTS EN ESPAÑOL...\n")
    for sub in SUBREDDITS_ES:
        for q in QUERIES_ES:
            all_posts += get_posts(q, sub, LIMIT_ES)

    print("\n🌎 BUSCANDO POSTS EN INGLÉS...\n")
    for sub in SUBREDDITS_EN:
        for q in QUERIES_EN:
            all_posts += get_posts(q, sub, LIMIT_EN)

    print(f"\n📝 TOTAL POSTS RECUPERADOS: {len(all_posts)}\n")
    return all_posts


# ------------------------------------------------------------
# ADK CALL
# ------------------------------------------------------------
async def analizar_post(texto, runner, user_id, session_id):
    content = types.Content(role="user", parts=[types.Part(text=texto)])

    raw = None
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response():
            raw = event.content.parts[0].text
            break

    if not raw:
        return {}

    # Try JSON parse
    try:
        return json.loads(raw)
    except:
        i = raw.find("{")
        f = raw.rfind("}")
        if i != -1 and f != -1:
            try:
                return json.loads(raw[i:f+1])
            except:
                return {}
        return {}


# ------------------------------------------------------------
# MASTER PIPELINE: REDDIT → ADK → CSV
# ------------------------------------------------------------
async def main():
    posts = retrieve_posts()
    if not posts:
        print("⚠️ No posts found.")
        return

    session_service = InMemorySessionService()
    APP_NAME = "tfm_redes"
    USER_ID = "user_1"
    SESSION_ID = "session_001"

    await session_service.create_session(APP_NAME, USER_ID, SESSION_ID)

    runner = Runner(agent=analisis_psico_agent,
                    app_name=APP_NAME,
                    session_service=session_service)

    results = []

    print("\n🧠 INICIANDO ANÁLISIS ADK...\n")

    for idx, post in enumerate(posts, start=1):
        print(f"------------- {idx}/{len(posts)} -------------")
        print(post["url"])
        data = await analizar_post(post["texto"], runner, USER_ID, SESSION_ID)

        if not data:
            data = {
                "texto_original": post["texto"],
                "tema_principal": "",
                "opinion_sobre_psicologia": "",
                "ha_ido_a_terapia": "no_se",
                "motivo_ir_terapia": "",
                "motivo_no_ir_terapia": "",
                "emocion_principal": "",
                "intensidad_emocion": "",
                "actitud_hacia_buscar_ayuda": "",
            }

        data["id_post"] = post["id"]
        data["subreddit"] = post["subreddit"]
        data["url"] = post["url"]
        data["titulo"] = post["title"]

        results.append(data)

    # CSV FINAL
    out = "reddit_es_en_analizado_tfm.csv"
    pd.DataFrame(results).to_csv(out, index=False, encoding="utf-8-sig")

    print(f"\n💾 ¡CSV GENERADO!: {out}")
    print("🎉 PIPELINE COMPLETADO.")


if __name__ == "__main__":
    asyncio.run(main())

