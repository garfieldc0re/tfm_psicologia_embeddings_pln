pip install google-genai python-dotenv
from dotenv import load_dotenv
import os
from google import genai

# 1. Cargar variables desde .env
load_dotenv()

# 2. Leer la API KEY
api_key = os.getenv("GOOGLE_API_KEY")
print("API Key cargada:", api_key)

# 3. Crear el cliente
client = genai.Client(api_key=api_key)
print("Cliente creado correctamente:", client)
python test_google_adk.py


