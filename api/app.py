# Import required FastAPI components for building the API
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
# Import Pydantic for data validation and settings management
from pydantic import BaseModel
# Import OpenAI client for interacting with OpenAI's API
from openai import OpenAI
import os
import sys
import tempfile
import shutil
from typing import Optional, Dict, Any
import asyncio
import json
import uuid

# # Add current directory to Python path for local imports (needed for Vercel deployment)
# current_dir = os.path.dirname(os.path.abspath(__file__))
# if current_dir not in sys.path:
#     sys.path.insert(0, current_dir)

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import aimakerspace components
from aimakerspace import PDFLoader, CharacterTextSplitter, VectorDatabase
from aimakerspace.openai_utils import EmbeddingModel, ChatOpenAI as AIMakerSpaceChatOpenAI

# Import LangGraph agent
from langgraph_agent import PDFAgent

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

# Initialize PDF Agent
pdf_agent = PDFAgent(pdf_databases)

# Define the data model for chat requests using Pydantic
# This ensures incoming request data is properly validated
class ChatRequest(BaseModel):
    developer_message: str  # Message from the developer/system
    user_message: str      # Message from the user
    model: Optional[str] = "gpt-4o-mini"  # Optional model selection with default
    api_key: str          # OpenAI API key for authentication

class PDFChatRequest(BaseModel):
    message: str
    model: str = "gpt-4o-mini"
    api_key: str
    tavily_api_key: str
    pdf_id: str
    system_message: str = "You are a helpful assistant that can answer questions about uploaded PDF documents and search the web for additional information when needed. Format your responses using markdown for better readability - use headers, bullet points, code blocks, and emphasis where appropriate."

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
    """Chat with a specific PDF using RAG and web search capabilities"""
    try:
        # Check if PDF exists
        if request.pdf_id not in pdf_databases:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        # Stream response from the agent
        async def generate_response():
            try:
                async for chunk in pdf_agent.stream_agent(
                    pdf_id=request.pdf_id,
                    user_message=request.message,
                    system_message=request.system_message,
                    openai_api_key=request.api_key,
                    tavily_api_key=request.tavily_api_key,
                    model_name=request.model
                ):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                print(f"Agent error: {e}")
                # Fallback to simple RAG if agent fails
                pdf_data = pdf_databases[request.pdf_id]
                vector_db = pdf_data['vector_db']
                
                # Retrieve relevant chunks
                relevant_chunks = vector_db.search_by_text(request.message, k=3, return_as_text=True)
                context = "\n\n".join(relevant_chunks)
                
                # Create simple prompt
                prompt = f"Context from PDF:\n{context}\n\nQuestion: {request.message}\n\nAnswer:"
                
                # Use OpenAI directly for fallback
                import openai
                client = openai.OpenAI(api_key=request.api_key)
                
                response = client.chat.completions.create(
                    model=request.model,
                    messages=[
                        {"role": "system", "content": request.system_message},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True
                )
                
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield f"data: {chunk.choices[0].delta.content}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate_response(), media_type="text/plain")
        
    except Exception as e:
        print(f"Chat PDF error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

# Define a health check endpoint to verify API status
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "features": ["chat", "pdf_rag"]}

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the server on all network interfaces (0.0.0.0) on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Vercel handler for serverless deployment
try:
    from mangum import Adapter
    handler = Adapter(app)
except ImportError:
    # mangum not available, skip handler creation
    pass
