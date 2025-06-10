import os
from typing import List, Dict, Any
from loguru import logger
import httpx
from pdf2image import convert_from_path
import pytesseract
from transformers import pipeline
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms import Ollama
from app.core.config import settings
from app.core.metrics import DOCUMENTS_PROCESSED, PROCESSING_TIME

class DocumentProcessor:
    def __init__(self):
        self.text_extractor = pipeline("document-question-answering")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.embeddings = HuggingFaceEmbeddings()
        self.llm = Ollama(
            base_url=settings.OLLAMA_API_URL,
            model=settings.OLLAMA_MODEL
        )
        
    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a document and return its content and metadata."""
        try:
            with PROCESSING_TIME.labels(operation="extract_text").time():
                text_content = await self._extract_text(file_path)
            
            with PROCESSING_TIME.labels(operation="extract_images").time():
                images = await self._extract_images(file_path)
            
            with PROCESSING_TIME.labels(operation="process_with_langchain").time():
                # Process text with LangChain
                chunks = self.text_splitter.split_text(text_content)
                vectorstore = FAISS.from_texts(chunks, self.embeddings)
                
                # Create QA chain
                qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=vectorstore.as_retriever()
                )
                
                # Generate summary using QA chain
                summary = qa_chain.run(
                    "Please provide a comprehensive summary of this document, "
                    "including key points and main topics."
                )
                
                # Extract key topics
                topics = qa_chain.run(
                    "What are the main topics or themes discussed in this document? "
                    "List them in order of importance."
                )
            
            DOCUMENTS_PROCESSED.labels(status="success").inc()
            
            return {
                "text_content": text_content,
                "summary": summary,
                "topics": topics,
                "images": images,
                "metadata": {
                    "page_count": len(images),
                    "file_size": os.path.getsize(file_path),
                    "chunk_count": len(chunks)
                }
            }
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            DOCUMENTS_PROCESSED.labels(status="error").inc()
            raise
    
    async def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF using OCR."""
        try:
            images = convert_from_path(file_path)
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            raise
    
    async def _extract_images(self, file_path: str) -> List[str]:
        """Extract images from PDF and save them."""
        try:
            images = convert_from_path(file_path)
            image_paths = []
            
            for i, image in enumerate(images):
                image_path = f"processed_images/{os.path.basename(file_path)}_{i}.png"
                os.makedirs("processed_images", exist_ok=True)
                image.save(image_path)
                image_paths.append(image_path)
            
            return image_paths
        except Exception as e:
            logger.error(f"Error extracting images: {str(e)}")
            raise
    
    async def query_document(self, document_id: int, query: str) -> str:
        """Query a processed document using LangChain QA chain."""
        try:
            # Load document from database
            # Create vectorstore from document chunks
            # Run query through QA chain
            # Return answer
            pass
        except Exception as e:
            logger.error(f"Error querying document: {str(e)}")
            raise 