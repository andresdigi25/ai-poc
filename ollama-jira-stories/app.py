import requests

PROMPT = """Actúa como un desarrollador senior que genera historias de usuario de Jira.
Dado un requerimiento, escribe una historia de Jira siguiendo este formato:

Título: [breve resumen]
Como [rol] quiero [objetivo] para [beneficio]
Criterios de aceptación:
- [Criterio 1]
- [Criterio 2]

Requerimiento: Crear sistema de login seguro con autenticación de dos factores.
"""

response = requests.post(
    "http://ollama:11434/api/generate",
    json={"model": "llama3", "prompt": PROMPT}
)

for line in response.iter_lines():
    if line:
        print(line.decode())