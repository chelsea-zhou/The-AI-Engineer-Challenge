# Import required FastAPI components for building the API
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
# Import Pydantic for data validation and settings management
from pydantic import BaseModel
# Import OpenAI client for interacting with OpenAI's API
from openai import OpenAI
import os
import tempfile
import shutil
from typing import Optional, Dict, Any
import asyncio
import json
import uuid

# Import aimakerspace components
from aimakerspace.text_utils import PDFLoader, CharacterTextSplitter
from aimakerspace.vectordatabase import VectorDatabase
from aimakerspace.openai_utils.embedding import EmbeddingModel
from aimakerspace.openai_utils.chatmodel import ChatOpenAI

# Initialize FastAPI application with a title
app = FastAPI(title="OpenAI Chat API with PDF RAG")

# Configure CORS (Cross-Origin Resource Sharing) middleware
# This allows the API to be accessed from different domains/origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any origin
    allow_credentials=True,  # Allows cookies to be included in requests
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers in requests
)

# Global storage for vector databases (in production, use a proper database)
pdf_databases: Dict[str, Dict[str, Any]] = {}

# Define the data model for chat requests using Pydantic
# This ensures incoming request data is properly validated
class ChatRequest(BaseModel):
    developer_message: str  # Message from the developer/system
    user_message: str      # Message from the user
    model: Optional[str] = "gpt-4o-mini"  # Optional model selection with default
    api_key: str          # OpenAI API key for authentication

class PDFChatRequest(BaseModel):
    developer_message: str  # Message from the developer/system
    user_message: str      # Message from the user
    model: Optional[str] = "gpt-4o-mini"  # Optional model selection with default
    api_key: str          # OpenAI API key for authentication
    pdf_id: str           # ID of the PDF to use for RAG (required for PDF chat)

class PDFUploadResponse(BaseModel):
    pdf_id: str
    filename: str
    status: str
    message: str

# PDF upload endpoint
@app.post("/api/upload-pdf", response_model=PDFUploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    api_key: str = Form(...)
):
    """
    Upload and process a PDF file for RAG functionality.
    
    This endpoint:
    1. Validates the uploaded file is a PDF
    2. Extracts text using PDFLoader
    3. Chunks the text using CharacterTextSplitter
    4. Generates embeddings using EmbeddingModel
    5. Stores in VectorDatabase for future retrieval
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Generate unique ID for this PDF
        pdf_id = str(uuid.uuid4())
        
        # Create temporary file to store uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            # Load and process PDF using aimakerspace
            pdf_loader = PDFLoader(tmp_file_path)
            documents = pdf_loader.load_documents()
            
            # Split text into manageable chunks
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_texts(documents)
            
            # Initialize embedding model with API key
            os.environ["OPENAI_API_KEY"] = api_key
            embedding_model = EmbeddingModel()
            
            # Create vector database for this PDF
            vector_db = VectorDatabase(embedding_model=embedding_model)
            
            # Build vector database from text chunks
            vector_db = await vector_db.abuild_from_list(chunks)
            
            # Store in global storage (in production, use persistent storage)
            pdf_databases[pdf_id] = {
                'filename': file.filename,
                'vector_db': vector_db,
                'chunks': chunks,
                'api_key': api_key
            }
            print(f"DEBUG: Stored PDF {pdf_id}, pdf_databases now contains: {list(pdf_databases.keys())}")  # Debug log
            
            return PDFUploadResponse(
                pdf_id=pdf_id,
                filename=file.filename,
                status="success",
                message=f"PDF processed successfully. {len(chunks)} chunks created."
            )
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

# Get list of uploaded PDFs
@app.get("/api/pdfs")
async def get_pdfs():
    """
    Retrieve list of all uploaded PDFs with metadata.
    
    Returns PDF ID, filename, and number of chunks for each uploaded PDF.
    """
    print(f"DEBUG: gettting pdfs")
    result = [
        {
            "pdf_id": pdf_id,
            "filename": data["filename"],
            "chunks_count": len(data["chunks"])
        }
        for pdf_id, data in pdf_databases.items()
    ]
    print(f"DEBUG: Returning result: {result}")  # Debug log
    return result


# Delete a specific PDF
@app.delete("/api/pdfs/{pdf_id}")
async def delete_pdf(pdf_id: str):
    """
    Delete a specific PDF from storage.
    """
    if pdf_id not in pdf_databases:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    filename = pdf_databases[pdf_id]["filename"]
    del pdf_databases[pdf_id]
    
    return {"message": f"PDF '{filename}' deleted successfully"}

# Regular chat endpoint (no PDF)
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Regular chat endpoint for standard AI conversations without PDF context.
    """
    try:
        # Initialize OpenAI client with the provided API key
        client = OpenAI(api_key=request.api_key)
        
        # Regular chat messages
        messages = [
            {"role": "system", "content": request.developer_message},
            {"role": "user", "content": request.user_message}
        ]
        
        # Create an async generator function for streaming responses
        async def generate():
            # Create a streaming chat completion request
            stream = client.chat.completions.create(
                model=request.model,
                messages=messages,
                stream=True  # Enable streaming response
            )
            
            # Yield each chunk of the response as it becomes available
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        # Return a streaming response to the client
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        # Handle any errors that occur during processing
        raise HTTPException(status_code=500, detail=str(e))

# PDF chat endpoint with RAG support
@app.post("/api/chat-pdf")
async def chat_pdf(request: PDFChatRequest):
    """
    PDF chat endpoint with RAG functionality.
    
    This endpoint:
    1. Retrieves relevant chunks from the specified PDF using vector similarity search
    2. Injects retrieved context into the system prompt
    3. Generates response with enhanced context from the PDF
    """
    try:
        # Validate PDF exists
        if request.pdf_id not in pdf_databases:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        # Initialize OpenAI client with the provided API key
        client = OpenAI(api_key=request.api_key)
        
        # Get PDF data and vector database
        pdf_data = pdf_databases[request.pdf_id]
        vector_db = pdf_data['vector_db']
        
        # Retrieve relevant chunks using vector similarity search
        relevant_chunks = vector_db.search_by_text(
            request.user_message,
            k=3,  # Get top 3 most relevant chunks
            return_as_text=True
        )
        
        # Create context from retrieved chunks
        context = "\n\n".join(relevant_chunks)
        
        # Enhance the system message with PDF context
        enhanced_system_message = f"""
{request.developer_message}

You are answering questions based on the content of the uploaded PDF: {pdf_data['filename']}.

Here is the relevant context from the PDF:

{context}

Please answer the user's question based on this context. If the context doesn't contain enough information to answer the question, please say so and provide what information you can based on the available context.
"""
        
        messages = [
            {"role": "system", "content": enhanced_system_message},
            {"role": "user", "content": request.user_message}
        ]
        
        # Create an async generator function for streaming responses
        async def generate():
            # Create a streaming chat completion request
            stream = client.chat.completions.create(
                model=request.model,
                messages=messages,
                stream=True  # Enable streaming response
            )
            
            # Yield each chunk of the response as it becomes available
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        # Return a streaming response to the client
        return StreamingResponse(generate(), media_type="text/plain")
    
    except Exception as e:
        # Handle any errors that occur during processing
        raise HTTPException(status_code=500, detail=str(e))

# Define a health check endpoint to verify API status
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "features": ["chat", "pdf_rag"]}

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the server on all network interfaces (0.0.0.0) on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
