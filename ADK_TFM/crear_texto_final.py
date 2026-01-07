import pandas as pd

RUTA_ENTRADA = "posts_listos_embeddings.csv"
RUTA_SALIDA = "posts_listos_embeddings_textofinal.csv"

# 1) Cargar CSV limpio
df = pd.read_csv(RUTA_ENTRADA)

print("✅ CSV cargado:", RUTA_ENTRADA)
print("Filas:", len(df))
print("Columnas:", list(df.columns))

# 2) Crear texto_final = titulo + ". " + texto
df["texto_final"] = (
    df["titulo"].fillna("").astype(str).str.strip()
    + ". "
    + df["texto"].fillna("").astype(str).str.strip()
)

# 3) Limpieza mínima final: quitar espacios sobrantes
df["texto_final"] = df["texto_final"].str.strip()

# 4) Comprobación rápida: ver 3 ejemplos
print("\n🧪 Ejemplos de texto_final (3 primeros):\n")
for i in range(min(3, len(df))):
    print(f"--- POST {i} ---")
    print(df.loc[i, "texto_final"][:500])  # muestra solo los primeros 500 caracteres
    print()

# 5) Guardar nuevo CSV con texto_final
df.to_csv(RUTA_SALIDA, index=False, encoding="utf-8")
print("✅ Guardado:", RUTA_SALIDA)
