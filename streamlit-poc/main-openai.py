# LangChain Document Q&A System Implementation
# This is a complete, production-ready implementation

import os
import streamlit as st
from typing import List, Optional
from langchain.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import tempfile

class DocumentQASystem:
    """A complete document Q&A system using LangChain"""
    
    def __init__(self, openai_api_key: str):
        """Initialize the Q&A system with OpenAI API key"""
        self.openai_api_key = openai_api_key
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize components
        self.embeddings = OpenAIEmbeddings()
        self.llm = OpenAI(
            temperature=0,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()]
        )
        self.vectorstore = None
        self.qa_chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    def load_documents(self, file_paths: List[str]) -> List:
        """Load documents from various file types"""
        documents = []
        
        for file_path in file_paths:
            try:
                # Determine file type and use appropriate loader
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
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
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
            # Conversational chain with memory
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                memory=self.memory,
                return_source_documents=True,
                verbose=True
            )
        else:
            # Simple retrieval QA chain
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
            # Load documents
            documents = self.load_documents(file_paths)
            if not documents:
                return False
            
            # Split into chunks
            chunks = self.split_documents(documents)
            
            # Create vector store
            self.create_vectorstore(chunks)
            
            # Setup QA chain
            self.setup_qa_chain("conversational")
            
            return True
        except Exception as e:
            print(f"Error processing documents: {str(e)}")
            return False


def create_streamlit_app():
    """Create a Streamlit web interface for the Q&A system"""
    
    st.set_page_config(
        page_title="LangChain Document Q&A",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 LangChain Document Q&A System")
    st.markdown("Upload documents and ask questions using advanced AI!")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key to use the system"
        )
        
        if not api_key:
            st.warning("Please enter your OpenAI API key to continue")
            st.stop()
    
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
                
                # Initialize QA system
                qa_system = DocumentQASystem(api_key)
                
                # Process documents
                if qa_system.process_documents(temp_paths):
                    st.session_state.qa_system = qa_system
                    st.success("Documents processed successfully!")
                else:
                    st.error("Failed to process documents")
                
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
                with st.spinner("Thinking..."):
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


# Alternative: Command Line Interface
def create_cli_interface():
    """Command line interface for the Q&A system"""
    
    print("🚀 LangChain Document Q&A System")
    print("=" * 40)
    
    # Get API key
    api_key = input("Enter your OpenAI API key: ").strip()
    if not api_key:
        print("API key is required!")
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
    print("\nInitializing Q&A system...")
    qa_system = DocumentQASystem(api_key)
    
    print("Processing documents...")
    if not qa_system.process_documents(file_paths):
        print("Failed to process documents!")
        return
    
    print("✅ Ready! Ask your questions (type 'quit' to exit)")
    print("-" * 40)
    
    # Q&A loop
    while True:
        question = input("\nQuestion: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if not question:
            continue
        
        print("Thinking...")
        result = qa_system.ask_question(question)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"\n📝 Answer: {result['answer']}")
            
            # Show sources
            if result.get("source_documents"):
                print(f"\n📄 Sources ({len(result['source_documents'])}):")
                for i, doc in enumerate(result["source_documents"][:2]):  # Show first 2 sources
                    preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                    print(f"  {i+1}. {preview}")


# Installation and setup instructions
SETUP_INSTRUCTIONS = """
# Setup Instructions

## 1. Install Required Packages
```bash
pip install langchain openai chromadb tiktoken streamlit pypdf2
```

## 2. Get OpenAI API Key
- Go to https://platform.openai.com/account/api-keys
- Create a new API key
- Keep it secure!

## 3. Run the Application

### Streamlit Web Interface:
```bash
streamlit run langchain_qa.py
```

### Command Line Interface:
```python
if __name__ == "__main__":
    create_cli_interface()
```

## 4. Usage Tips
- Use clear, specific questions
- Upload multiple related documents for better context
- The system remembers conversation history
- Check source documents to verify answers

## 5. Advanced Customization
- Adjust chunk_size and chunk_overlap in split_documents()
- Change the number of retrieved documents (k parameter)
- Experiment with different chain types
- Add custom prompts for specific use cases
"""

if __name__ == "__main__":
    # Choose interface
    interface = input("Choose interface (1=Streamlit, 2=CLI): ").strip()
    
    if interface == "1":
        print("Starting Streamlit app...")
        print("Run: streamlit run this_file.py")
        create_streamlit_app()
    elif interface == "2":
        create_cli_interface()
    else:
        print("Invalid choice. Run the script again.")
        print("\nSetup Instructions:")
        print(SETUP_INSTRUCTIONS)