from transformers import AutoTokenizer, AutoModel
import torch

MODEL_NAME = "BAAI/bge-base-en"

print(f"📥 Cargando modelo '{MODEL_NAME}' localmente...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

text = "Hola, ¿cómo estás?"
inputs = tokenizer(text, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)
embedding = outputs.last_hidden_state.mean(dim=1)

print("✅ Embedding generado localmente:")
print(embedding)