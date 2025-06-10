# LangChain Document Q&A System with Ollama (Local LLMs)
# No OpenAI API key required - runs completely locally!

import os
import streamlit as st
from typing import List, Optional
from langchain.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings, OllamaEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import Ollama
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import tempfile
import requests

class OllamaDocumentQASystem:
    """A complete document Q&A system using Ollama (local LLMs)"""
    
    def __init__(self, model_name: str = "llama2", embedding_type: str = "huggingface"):
        """Initialize the Q&A system with Ollama model"""
        self.model_name = model_name
        self.embedding_type = embedding_type
        
        # Check if Ollama is running
        if not self._check_ollama_connection():
            raise ConnectionError("Ollama is not running. Please start Ollama first!")
        
        # Initialize Ollama LLM
        self.llm = Ollama(
            model=model_name,
            temperature=0.1,
            callbacks=[StreamingStdOutCallbackHandler()],
            # Additional Ollama parameters
            num_ctx=4096,  # Context window
            num_predict=512,  # Max tokens to predict
        )
        
        # Initialize embeddings
        if embedding_type == "huggingface":
            # Free, local embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
        else:
            # Ollama embeddings (if supported by your model)
            self.embeddings = OllamaEmbeddings(model=model_name)
        
        self.vectorstore = None
        self.qa_chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    def _check_ollama_connection(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
        except:
            pass
        return []
    
    def pull_model(self, model_name: str) -> bool:
        """Download a model using Ollama"""
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "pull", model_name], 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minutes timeout
            )
            return result.returncode == 0
        except:
            return False
    
    def load_documents(self, file_paths: List[str]) -> List:
        """Load documents from various file types"""
        documents = []
        
        for file_path in file_paths:
            try:
                if file_path.endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                elif file_path.endswith(('.txt', '.md')):
                    loader = TextLoader(file_path, encoding='utf-8')
                else:
                    st.warning(f"Unsupported file type: {file_path}")
                    continue
                
                docs = loader.load()
                documents.extend(docs)
                print(f"Loaded {len(docs)} documents from {file_path}")
                
            except Exception as e:
                st.error(f"Error loading {file_path}: {str(e)}")
        
        return documents
    
    def split_documents(self, documents: List) -> List:
        """Split documents into chunks for better processing"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks")
        return chunks
    
    def create_vectorstore(self, chunks: List) -> None:
        """Create vector embeddings and store them"""
        print("Creating embeddings... This may take a moment for the first run.")
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory="./chroma_db_ollama"
        )
        print("Vector store created successfully")
    
    def setup_qa_chain(self, chain_type: str = "conversational") -> None:
        """Set up the question-answering chain"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized. Call create_vectorstore first.")
        
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        if chain_type == "conversational":
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                memory=self.memory,
                return_source_documents=True,
                verbose=True
            )
        else:
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                verbose=True
            )
        
        print(f"QA chain ({chain_type}) set up successfully")
    
    def ask_question(self, question: str) -> dict:
        """Ask a question and get an answer"""
        if not self.qa_chain:
            raise ValueError("QA chain not initialized. Call setup_qa_chain first.")
        
        try:
            if isinstance(self.qa_chain, ConversationalRetrievalChain):
                result = self.qa_chain({"question": question})
            else:
                result = self.qa_chain({"query": question})
            
            return {
                "answer": result.get("answer", ""),
                "source_documents": result.get("source_documents", []),
                "chat_history": result.get("chat_history", [])
            }
        except Exception as e:
            return {"error": str(e)}
    
    def process_documents(self, file_paths: List[str]) -> bool:
        """Complete pipeline to process documents"""
        try:
            documents = self.load_documents(file_paths)
            if not documents:
                return False
            
            chunks = self.split_documents(documents)
            self.create_vectorstore(chunks)
            self.setup_qa_chain("conversational")
            
            return True
        except Exception as e:
            print(f"Error processing documents: {str(e)}")
            return False


def create_ollama_streamlit_app():
    """Streamlit web interface for Ollama-powered Q&A system"""
    
    st.set_page_config(
        page_title="Ollama Document Q&A",
        page_icon="🦙",
        layout="wide"
    )
    
    st.title("🦙 Ollama Document Q&A System")
    st.markdown("Local AI-powered document Q&A - No API keys required!")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Check Ollama connection
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                st.success("✅ Ollama is running")
                available_models = [model["name"] for model in response.json().get("models", [])]
            else:
                st.error("❌ Ollama connection failed")
                st.stop()
        except:
            st.error("❌ Ollama is not running")
            st.markdown("""
            **To start Ollama:**
            1. Install: `curl -fsSL https://ollama.ai/install.sh | sh`
            2. Start: `ollama serve`
            3. Pull a model: `ollama pull llama2`
            """)
            st.stop()
        
        # Model selection
        if available_models:
            selected_model = st.selectbox(
                "Choose Model",
                available_models,
                help="Select an Ollama model for Q&A"
            )
        else:
            st.warning("No models found. Pull a model first:")
            st.code("ollama pull llama2")
            st.stop()
        
        # Model management
        st.subheader("📦 Model Management")
        new_model = st.text_input("Pull new model:", placeholder="llama2, mistral, codellama...")
        if st.button("Pull Model"):
            if new_model:
                with st.spinner(f"Pulling {new_model}... This may take several minutes."):
                    import subprocess
                    try:
                        result = subprocess.run(
                            ["ollama", "pull", new_model], 
                            capture_output=True, 
                            text=True,
                            timeout=600
                        )
                        if result.returncode == 0:
                            st.success(f"✅ Successfully pulled {new_model}")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to pull {new_model}")
                    except subprocess.TimeoutExpired:
                        st.error("⏱️ Pull timeout - try again")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        # Embedding options
        embedding_type = st.selectbox(
            "Embedding Type",
            ["huggingface", "ollama"],
            help="HuggingFace is faster and works offline"
        )
    
    # Initialize session state
    if 'qa_system' not in st.session_state:
        st.session_state.qa_system = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # File upload section
    st.header("📁 Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        type=['txt', 'pdf', 'md'],
        help="Upload text files, PDFs, or markdown files"
    )
    
    if uploaded_files:
        if st.button("Process Documents", type="primary"):
            with st.spinner("Processing documents..."):
                # Save uploaded files temporarily
                temp_paths = []
                for uploaded_file in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_paths.append(tmp_file.name)
                
                try:
                    # Initialize QA system with Ollama
                    qa_system = OllamaDocumentQASystem(
                        model_name=selected_model,
                        embedding_type=embedding_type
                    )
                    
                    # Process documents
                    if qa_system.process_documents(temp_paths):
                        st.session_state.qa_system = qa_system
                        st.success("✅ Documents processed successfully!")
                    else:
                        st.error("❌ Failed to process documents")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                
                # Cleanup temporary files
                for path in temp_paths:
                    try:
                        os.unlink(path)
                    except:
                        pass
    
    # Q&A section
    if st.session_state.qa_system:
        st.header("❓ Ask Questions")
        
        # Display chat history
        for i, (question, answer) in enumerate(st.session_state.chat_history):
            with st.container():
                st.markdown(f"**Q{i+1}:** {question}")
                st.markdown(f"**A{i+1}:** {answer}")
                st.divider()
        
        # Question input
        question = st.text_input("Ask a question about your documents:")
        
        if question:
            if st.button("Ask", type="primary"):
                with st.spinner("🤔 Thinking... (Local AI processing)"):
                    result = st.session_state.qa_system.ask_question(question)
                    
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        answer = result["answer"]
                        st.session_state.chat_history.append((question, answer))
                        
                        # Display answer
                        st.markdown(f"**Answer:** {answer}")
                        
                        # Display sources
                        if result.get("source_documents"):
                            with st.expander("📄 Source Documents"):
                                for i, doc in enumerate(result["source_documents"]):
                                    st.markdown(f"**Source {i+1}:**")
                                    st.text(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)
                        
                        st.rerun()


def create_ollama_cli():
    """Command line interface for Ollama Q&A system"""
    
    print("🦙 Ollama Document Q&A System")
    print("=" * 40)
    
    # Check Ollama connection
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            raise Exception("Connection failed")
        
        models = [model["name"] for model in response.json().get("models", [])]
        print(f"✅ Ollama connected. Available models: {', '.join(models)}")
        
    except:
        print("❌ Ollama is not running!")
        print("Start Ollama with: ollama serve")
        print("Pull a model with: ollama pull llama2")
        return
    
    # Select model
    if not models:
        print("No models found. Pull a model first: ollama pull llama2")
        return
    
    print(f"\nAvailable models: {', '.join(models)}")
    model_name = input(f"Choose model [{models[0]}]: ").strip() or models[0]
    
    if model_name not in models:
        print(f"Model {model_name} not found!")
        return
    
    # Get document paths
    print("\nEnter document file paths (one per line, empty line to finish):")
    file_paths = []
    while True:
        path = input().strip()
        if not path:
            break
        if os.path.exists(path):
            file_paths.append(path)
        else:
            print(f"File not found: {path}")
    
    if not file_paths:
        print("No valid files provided!")
        return
    
    # Initialize and process
    print("\n🚀 Initializing Ollama Q&A system...")
    try:
        qa_system = OllamaDocumentQASystem(model_name=model_name)
        
        print("📄 Processing documents...")
        if not qa_system.process_documents(file_paths):
            print("❌ Failed to process documents!")
            return
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return
    
    print("✅ Ready! Ask your questions (type 'quit' to exit)")
    print("-" * 40)
    
    # Q&A loop
    while True:
        question = input("\n🤔 Question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if not question:
            continue
        
        print("🤖 Thinking...")
        result = qa_system.ask_question(question)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"\n💬 Answer: {result['answer']}")
            
            if result.get("source_documents"):
                print(f"\n📚 Sources ({len(result['source_documents'])}):")
                for i, doc in enumerate(result["source_documents"][:2]):
                    preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                    print(f"  {i+1}. {preview}")


# Setup instructions for Ollama
OLLAMA_SETUP = """
# 🦙 Ollama Setup Guide

## 1. Install Ollama
```bash
# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai
```

## 2. Start Ollama Server
```bash
ollama serve
```

## 3. Pull Models (choose one or more)
```bash
# Small, fast model (~4GB)
ollama pull llama2

# Larger, more capable model (~7GB)  
ollama pull llama2:13b

# Code-focused model
ollama pull codellama

# Fast, efficient model
ollama pull mistral

# Tiny model for testing (~1GB)
ollama pull tinyllama
```

## 4. Install Python Dependencies
```bash
pip install langchain sentence-transformers chromadb streamlit pypdf2 requests
```

## 5. Run the Application
```bash
# Web interface
streamlit run this_file.py

# Command line
python this_file.py
```

## Model Recommendations:
- **llama2**: Best balance of quality and speed
- **mistral**: Fast and efficient 
- **codellama**: Great for technical documents
- **llama2:13b**: Higher quality, slower
- **tinyllama**: Testing/development only

## Advantages of Ollama:
✅ Completely free - no API costs
✅ Runs locally - your data stays private  
✅ Works offline
✅ Multiple model options
✅ Fast after initial setup
"""

if __name__ == "__main__":
    print("🦙 Ollama Document Q&A System")
    print("Choose interface:")
    print("1. Streamlit Web Interface")
    print("2. Command Line Interface") 
    print("3. Show Setup Instructions")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        print("Starting Streamlit app...")
        print("Run: streamlit run this_file.py")
        create_ollama_streamlit_app()
    elif choice == "2":
        create_ollama_cli()
    elif choice == "3":
        print(OLLAMA_SETUP)
    else:
        print("Invalid choice!")
        print(OLLAMA_SETUP)