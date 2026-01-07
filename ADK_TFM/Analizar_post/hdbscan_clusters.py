import numpy as np
import pandas as pd

from sklearn.preprocessing import normalize

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import hdbscan
import umap

RUTA_EMB = "embeddings_textofinal.npy"
RUTA_POSTS = "posts_con_id_para_embeddings.csv"

# Parámetros HDBSCAN (ajustables)
MIN_CLUSTER_SIZE = 15
MIN_SAMPLES = 5  # prueba 10; si pones None, HDBSCAN usa min_cluster_size

# 1) Cargar datos
X = np.load(RUTA_EMB)
# Normalizar embeddings (aprox. coseno usando euclídea)
X = normalize(X, norm="l2")

df = pd.read_csv(RUTA_POSTS)

print("✅ Embeddings:", X.shape)
print("✅ Posts:", df.shape)

# 2) HDBSCAN (clustering en el espacio original)
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=MIN_CLUSTER_SIZE,
    min_samples=MIN_SAMPLES,
    metric="euclidean",  # simple para empezar; luego podemos probar "cosine"
    prediction_data=False
)

labels = clusterer.fit_predict(X)
df["cluster_hdbscan"] = labels

n_ruido = int((labels == -1).sum())
clusters = sorted([c for c in set(labels) if c != -1])

print("\n📌 HDBSCAN terminado")
print("Clusters encontrados (sin ruido):", len(clusters))
print("IDs clusters:", clusters[:20], "..." if len(clusters) > 20 else "")
print("Puntos en ruido (-1):", n_ruido)

# 3) Guardar CSV con clusters
SALIDA_CSV = "posts_con_clusters_hdbscan.csv"
df.to_csv(SALIDA_CSV, index=False, encoding="utf-8")
print("✅ Guardado:", SALIDA_CSV)

# 4) UMAP 2D solo para visualizar (NO para clusterizar)
reducer = umap.UMAP(
    n_neighbors=15,
    min_dist=0.1,
    n_components=2,
    random_state=42
)
X2 = reducer.fit_transform(X)

# Color: ruido en gris, clusters por etiqueta
plt.figure(figsize=(8, 6))
plt.scatter(X2[:, 0], X2[:, 1], s=8, c=labels)
plt.title(f"UMAP (2D) + HDBSCAN (min_cluster_size={MIN_CLUSTER_SIZE}, min_samples={MIN_SAMPLES})")
plt.xlabel("UMAP1")
plt.ylabel("UMAP2")
plt.tight_layout()

SALIDA_PNG = "umap_hdbscan.png"
plt.savefig(SALIDA_PNG, dpi=200)
plt.close()

print("✅ Guardado:", SALIDA_PNG)
