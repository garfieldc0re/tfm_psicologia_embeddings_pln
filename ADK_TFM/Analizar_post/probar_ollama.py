import requests, json

MODEL = "llama3.2:1b"

url = "http://127.0.0.1:11434/api/chat"
payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "Responde solo con: OK"}],
    "stream": False,
    "options": {"num_predict": 10}
}

r = requests.post(url, json=payload, timeout=60)
r.raise_for_status()
data = r.json()
print(data["message"]["content"])

