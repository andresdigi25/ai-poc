# 🧠 Talk to Your Docs (Offline)

Este proyecto permite hacer preguntas a tus archivos PDF, TXT o DOCX usando modelos de lenguaje como LLaMA 3 o Mistral localmente con **Ollama**, usando **LangChain** y **Hugging Face** embeddings.

## 🚀 Cómo usar

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Asegúrate de tener `ollama` corriendo

```bash
ollama run llama3
```

### 3. Coloca tus archivos en `docs/`

Archivos soportados: `.pdf`, `.txt`, `.docx`

### 4. Ejecutar la app

```bash
python app.py
```

### 5. Haz tus preguntas

```
👉 Tu pregunta: ¿De qué trata el documento?
🤖 Respuesta: ...
```

## 🧰 Tecnologías

- LangChain
- Hugging Face Transformers
- Ollama
- Chroma (vectorstore)
- Python

---

🎯 ¡Todo corre local y sin internet!
