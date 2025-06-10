from langchain.document_loaders import UnstructuredFileLoader
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Ollama
from langchain.chains import RetrievalQA
from tqdm import tqdm
import logging
import os

# === Configuración ===
DOCS_PATH = "docs/"
DB_PATH = "vectorstore/"
MODEL_NAME = "llama3"
EMBEDDING_MODEL = "BAAI/bge-base-en"

logging.basicConfig(level=logging.INFO)

def main():
    # === 1. Cargar documentos ===
    docs = []
    for file in tqdm(os.listdir(DOCS_PATH), desc="Cargando documentos"):
        if file.endswith((".pdf", ".txt", ".docx")):
            path = os.path.join(DOCS_PATH, file)
            try:
                loader = UnstructuredFileLoader(path)
                docs.extend(loader.load())
            except Exception as e:
                logging.error(f"Error al cargar {file}: {e}")

    # === 2. Generar embeddings ===
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    # === 3. Cargar o crear vector store local ===
    if os.path.exists(DB_PATH) and os.listdir(DB_PATH):
        vectordb = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
    else:
        vectordb = Chroma.from_documents(docs, embedding=embeddings, persist_directory=DB_PATH)
        vectordb.persist()
        logging.info("Vector store creado y persistido.")

    # === 4. Cargar modelo LLM con Ollama ===
    llm = Ollama(model=MODEL_NAME)

    # === 5. Construir sistema de QA ===
    qa = RetrievalQA.from_chain_type(llm=llm, retriever=vectordb.as_retriever())

    # === 6. Interacción ===
    print("🧠 Pregúntale a tus documentos (escribe 'salir' para terminar)\n")
    while True:
        query = input("👉 Tu pregunta: ").strip()
        if not query:
            continue
        if query.lower() == "salir":
            break
        answer = qa.run(query)
        print("🤖 Respuesta:", answer)

if __name__ == "__main__":
    main()
