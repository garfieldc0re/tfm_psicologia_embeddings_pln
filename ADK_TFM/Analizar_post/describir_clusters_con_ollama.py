import json
import re
import pandas as pd
import ollama

RUTA = "posts_con_clusters_hdbscan.csv"
MODELO = "llama3.2:1b"
N_EJEMPLOS = 12
MAX_CHARS = 900  # recortamos un poco para reducir “desbordes” del modelo

def extraer_primer_json(texto: str):
    """
    Extrae el primer objeto JSON { ... } del texto, aunque venga con ``` o texto extra.
    """
    # quitar fences ```...```
    texto = re.sub(r"```.*?\n", "", texto, flags=re.DOTALL)
    texto = texto.replace("```", "").strip()

    # buscar primer bloque que empiece por { y termine por }
    m = re.search(r"\{.*\}", texto, flags=re.DOTALL)
    if not m:
        return None
    candidato = m.group(0).strip()

    # intentar parsear
    try:
        return json.loads(candidato)
    except Exception:
        return None

df = pd.read_csv(RUTA)

clusters = sorted([c for c in df["cluster_hdbscan"].unique() if c != -1])
print("✅ Clusters a describir:", clusters)

resultados = {}

for c in clusters:
    sub = df[df["cluster_hdbscan"] == c].copy()
    sub = sub.sample(n=min(N_EJEMPLOS, len(sub)), random_state=42)

    ejemplos = []
    for _, row in sub.iterrows():
        titulo = str(row.get("titulo", "")).strip()
        texto_final = str(row.get("texto_final", "")).strip()
        ejemplos.append(f"TITULO: {titulo}\nTEXTO: {texto_final[:MAX_CHARS]}")

    bloque = "\n\n---\n\n".join(ejemplos)

    prompt = f"""
Devuelve SOLO un JSON válido (sin markdown, sin texto extra), con estas claves exactas:
label (string), keywords (list de 5 strings), description (string), attitude (string)

Reglas:
- label: 3–6 palabras, neutrales, descriptivas (sin “MISMO”).
- keywords: exactamente 5 keywords.
- attitude: una de [positiva, negativa, ambivalente, neutral] hacia terapia/psicología.
- description: 1–2 frases.

Posts del cluster:
{bloque}
""".strip()

    # Intentamos forzar JSON (si tu versión de ollama lo soporta)
    try:
        r = ollama.chat(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}],
            format="json"
        )
    except TypeError:
        # Si tu librería no soporta format="json", seguimos sin eso
        r = ollama.chat(
            model=MODELO,
            messages=[{"role": "user", "content": prompt}]
        )

    salida = r["message"]["content"].strip()

    data = extraer_primer_json(salida)
    if data is None:
        resultados[str(int(c))] = {"raw": salida}
    else:
        resultados[str(int(c))] = data

    print(f"✅ Cluster {c} descrito")

with open("descripciones_clusters_hdbscan_ollama.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print("✅ Guardado: descripciones_clusters_hdbscan_ollama.json")

