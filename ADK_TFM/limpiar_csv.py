import pandas as pd

RUTA_ENTRADA = "posts_bruto_limpio - copia.csv"
RUTA_SALIDA = "posts_listos_embeddings.csv"

# 1) Cargar CSV
df = pd.read_csv(RUTA_ENTRADA)

print("✅ CSV cargado")
print("Filas totales:", len(df))
print("Columnas:", list(df.columns))

# 2) Ver cuántos 'texto' están vacíos (NaN)
n_nan_texto = df["texto"].isna().sum()
print("\n📌 Filas con texto = NaN:", n_nan_texto)

# 3) Quitar filas donde 'texto' es NaN
df1 = df.dropna(subset=["texto"])
print("📌 Filas tras quitar NaN en texto:", len(df1))

# 4) Quitar filas donde 'texto' es solo espacios o vacío
df1["texto"] = df1["texto"].astype(str)
df2 = df1[df1["texto"].str.strip() != ""]
print("📌 Filas tras quitar texto vacío/espacios:", len(df2))

# 5) Resetear índice (orden limpio)
df2 = df2.reset_index(drop=True)

# 6) Guardar nuevo CSV limpio
df2.to_csv(RUTA_SALIDA, index=False, encoding="utf-8")

print("\n✅ Guardado:", RUTA_SALIDA)
