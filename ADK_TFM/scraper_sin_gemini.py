from reddit_tools import (
    buscar_subreddits_psicologia,
    buscar_posts_actitud_psicologia,
    guardar_posts_en_csv
)

if __name__ == "__main__":
    # 1) subreddits (sin término específico)
    subs = buscar_subreddits_psicologia(
        incluir_idiomas="es,en",
        max_subreddits=20,
        min_suscriptores=300
    )
    nombres = [s["nombre"] for s in subs]

    subreddits_es_fijos = [
        "PsicologiaES",
        "Salud_Mental",
        "Desahogo",
        "esConversacion",
        "Spain"
    ]

    nombres = subreddits_es_fijos + nombres

    print("Subreddits:", nombres)

    # 2) posts (sube el grifo)
    posts = buscar_posts_actitud_psicologia(
    subreddits=nombres,
    limite_posts=300,
    limite_total=3000
    )
    
    print("Posts encontrados:", len(posts))

    # 3) guardar
    ruta = guardar_posts_en_csv(posts, nombre_fichero="posts_500_sin_gemini.csv")
    print("CSV guardado en:", ruta)
