from langchain.document_loaders import UnstructuredFileLoader
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Ollama
from langchain.chains import RetrievalQA
import os

# === Configuración ===
DOCS_PATH = "docs/"
DB_PATH = "vectorstore/"
MODEL_NAME = "llama3"
EMBEDDING_MODEL = "BAAI/bge-base-en"

# === 1. Cargar documentos ===
docs = []
for file in os.listdir(DOCS_PATH):
    if file.endswith((".pdf", ".txt", ".docx")):
        loader = UnstructuredFileLoader(os.path.join(DOCS_PATH, file))
        docs.extend(loader.load())

# === 2. Generar embeddings ===
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# === 3. Crear vector store local ===
vectordb = Chroma.from_documents(docs, embedding=embeddings, persist_directory=DB_PATH)
vectordb.persist()

# === 4. Cargar modelo LLM con Ollama ===
llm = Ollama(model=MODEL_NAME)

# === 5. Construir sistema de QA ===
qa = RetrievalQA.from_chain_type(llm=llm, retriever=vectordb.as_retriever())

# === 6. Interacción ===
print("🧠 Pregúntale a tus documentos (escribe 'salir' para terminar)\n")
while True:
    query = input("👉 Tu pregunta: ")
    if query.lower() == "salir":
        break
    answer = qa.run(query)
    print("🤖 Respuesta:", answer)
