import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import umap
from sklearn.cluster import KMeans

RUTA_EMB = "embeddings_textofinal.npy"
RUTA_POSTS = "posts_con_id_para_embeddings.csv"

# 1) Cargar
X = np.load(RUTA_EMB)
df = pd.read_csv(RUTA_POSTS)

print("✅ Embeddings:", X.shape)
print("✅ Posts:", df.shape)

# 2) UMAP a 2D
reducer = umap.UMAP(
    n_neighbors=15,
    min_dist=0.1,
    n_components=2,
    random_state=42
)
X2 = reducer.fit_transform(X)

print("✅ UMAP listo:", X2.shape)

# 3) Clustering simple (KMeans)
k = 8  # número inicial (luego lo ajustamos)
kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
clusters = kmeans.fit_predict(X)

df["cluster"] = clusters

# 4) Guardar CSV con clusters
df.to_csv("posts_con_clusters_kmeans.csv", index=False, encoding="utf-8")
print("✅ Guardado: posts_con_clusters_kmeans.csv")

# 5) Plot UMAP
plt.figure(figsize=(8, 6))
plt.scatter(X2[:, 0], X2[:, 1], s=8, c=clusters)
plt.title(f"UMAP (2D) + KMeans (k={k})")
plt.xlabel("UMAP1")
plt.ylabel("UMAP2")
plt.tight_layout()
plt.savefig("umap_kmeans.png", dpi=200)
plt.close()

print("✅ Guardado: umap_kmeans.png")
