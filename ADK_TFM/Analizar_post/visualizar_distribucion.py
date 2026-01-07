import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # <- backend sin interfaz (no necesita Tk)
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA


RUTA_EMB = "embeddings_textofinal.npy"
RUTA_POSTS = "posts_con_id_para_embeddings.csv"

# 1) Cargar datos
X = np.load(RUTA_EMB)
df = pd.read_csv(RUTA_POSTS)

print("✅ Embeddings:", X.shape)
print("✅ Posts:", df.shape)

# 2) PCA a 2D (rápido)
pca = PCA(n_components=2, random_state=42)
X2 = pca.fit_transform(X)

print("📌 Varianza explicada (2D):", pca.explained_variance_ratio_.sum())

# 3) Plot
plt.figure(figsize=(8, 6))
plt.scatter(X2[:, 0], X2[:, 1], s=8)
plt.title("Distribución de embeddings (PCA 2D)")
plt.xlabel("PC1")
plt.ylabel("PC2")
plt.tight_layout()
plt.savefig("pca_embeddings.png", dpi=200)
plt.close()

print("✅ Guardado: pca_embeddings.png")