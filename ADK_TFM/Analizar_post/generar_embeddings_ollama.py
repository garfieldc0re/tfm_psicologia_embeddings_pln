import time
import pickle
import numpy as np
import pandas as pd
import ollama

RUTA_ENTRADA = "ADK_TFM/posts_listos_embeddings_textofinal.csv"
print("DEBUG → RUTA_ENTRADA =", RUTA_ENTRADA)
RUTA_SALIDA_EMB_PKL = "embeddings_textofinal.pkl"
RUTA_SALIDA_EMB_NPY = "embeddings_textofinal.npy"
RUTA_SALIDA_CSV = "posts_con_id_para_embeddings.csv"

MODELO_EMBEDDINGS = "nomic-embed-text"

# 1) Cargar CSV
df = pd.read_csv(RUTA_ENTRADA)

# Comprobación mínima
if "texto_final" not in df.columns:
    raise ValueError("No existe la columna 'texto_final' en el CSV de entrada.")

# Crear un ID estable por fila (para alinear embeddings con posts)
df = df.reset_index(drop=True)
df["row_id"] = df.index

textos = df["texto_final"].fillna("").astype(str).tolist()

print("✅ CSV cargado:", RUTA_ENTRADA)
print("Filas:", len(df))
print("Ejemplo texto_final (primeros 200 chars):")
print(textos[0][:200])
print("\n📌 Modelo embeddings:", MODELO_EMBEDDINGS)

# 2) Función con reintentos (por si alguna llamada falla)
def embed_texto(texto: str, max_reintentos: int = 3, pausa: float = 1.0):
    # Si hay textos vacíos por lo que sea, devolvemos None
    if not texto or not texto.strip():
        return None

    for intento in range(1, max_reintentos + 1):
        try:
            r = ollama.embeddings(model=MODELO_EMBEDDINGS, prompt=texto)
            return r["embedding"]
        except Exception as e:
            print(f"⚠️ Error embedding (intento {intento}/{max_reintentos}): {e}")
            time.sleep(pausa)

    return None

# 3) Generar embeddings
embeddings = []
fallos = 0

t0 = time.time()
for i, t in enumerate(textos):
    emb = embed_texto(t)

    if emb is None:
        fallos += 1
        # ponemos un vector de ceros del tamaño típico si falla; pero mejor marcarlo
        embeddings.append(None)
    else:
        embeddings.append(emb)

    # progreso cada 50
    if (i + 1) % 50 == 0:
        print(f"Progreso: {i+1}/{len(textos)}")

t1 = time.time()

print("\n✅ Embeddings generados")
print("Tiempo (s):", round(t1 - t0, 2))
print("Fallos:", fallos)

# 4) Convertir a matriz (quitando fallos si los hubiera)
# Si hay fallos, lo mejor es excluir esas filas para no meter vectores raros.
mask_ok = [e is not None for e in embeddings]
df_ok = df[mask_ok].copy()
emb_ok = np.array([e for e in embeddings if e is not None], dtype=float)

print("\n📌 Filas válidas para embeddings:", len(df_ok))
print("📌 Dimensión embedding:", emb_ok.shape[1] if len(emb_ok) > 0 else "N/A")
print("📌 Matriz final:", emb_ok.shape)

# 5) Guardar outputs
# 5.1 Guardar dataframe alineado
df_ok.to_csv(RUTA_SALIDA_CSV, index=False, encoding="utf-8")

# 5.2 Guardar embeddings
with open(RUTA_SALIDA_EMB_PKL, "wb") as f:
    pickle.dump(emb_ok, f)

np.save(RUTA_SALIDA_EMB_NPY, emb_ok)

print("\n✅ Guardado CSV:", RUTA_SALIDA_CSV)
print("✅ Guardado PKL:", RUTA_SALIDA_EMB_PKL)
print("✅ Guardado NPY:", RUTA_SALIDA_EMB_NPY)
