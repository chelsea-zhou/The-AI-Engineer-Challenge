"""
Cache Manager for Pre-processed PDFs in Development Mode
"""

import os
import json
import pickle
from typing import Dict, Any, Optional
from pathlib import Path
from aimakerspace import PDFLoader, CharacterTextSplitter, VectorDatabase
from aimakerspace.openai_utils import EmbeddingModel

class PDFCacheManager:
    """Manages caching of processed PDFs and their vector databases for development"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            # Use the directory where this file is located + cache subdirectory
            current_file_dir = Path(__file__).parent
            cache_dir = current_file_dir / "cache"
        else:
            cache_dir = Path(cache_dir)
            
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Cache subdirectories
        self.vector_cache_dir = self.cache_dir / "vectors"
        self.metadata_cache_dir = self.cache_dir / "metadata"
        
        self.vector_cache_dir.mkdir(exist_ok=True, parents=True)
        self.metadata_cache_dir.mkdir(exist_ok=True, parents=True)
    
    def _get_cache_paths(self, pdf_id: str):
        """Get cache file paths for a given PDF ID"""
        return {
            'vector_db': self.vector_cache_dir / f"{pdf_id}_vector_db.pkl",
            'metadata': self.metadata_cache_dir / f"{pdf_id}_metadata.json",
            'chunks': self.metadata_cache_dir / f"{pdf_id}_chunks.json",
            'original_text': self.metadata_cache_dir / f"{pdf_id}_original_text.txt"
        }
    
    def cache_exists(self, pdf_id: str) -> bool:
        """Check if cache exists for a given PDF ID"""
        paths = self._get_cache_paths(pdf_id)
        return all(path.exists() for path in paths.values())
    
    def save_to_cache(self, pdf_id: str, pdf_data: Dict[str, Any]):
        """Save processed PDF data to cache"""
        try:
            paths = self._get_cache_paths(pdf_id)
            
            # Save vector database (using pickle for complex object)
            with open(paths['vector_db'], 'wb') as f:
                pickle.dump(pdf_data['vector_db'], f)
            
            # Save metadata
            metadata = {
                'filename': pdf_data['filename'],
                'api_key': pdf_data.get('api_key', ''),
                'chunks_count': len(pdf_data['chunks']),
                'original_text_length': len(pdf_data['original_text'])
            }
            with open(paths['metadata'], 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Save chunks
            with open(paths['chunks'], 'w') as f:
                json.dump(pdf_data['chunks'], f, indent=2)
            
            # Save original text
            with open(paths['original_text'], 'w', encoding='utf-8') as f:
                f.write(pdf_data['original_text'])
            
            print(f"✅ Cached PDF data for {pdf_id} ({pdf_data['filename']})")
            return True
            
        except Exception as e:
            print(f"❌ Error caching PDF {pdf_id}: {str(e)}")
            return False
    
    def load_from_cache(self, pdf_id: str) -> Optional[Dict[str, Any]]:
        """Load processed PDF data from cache"""
        try:
            if not self.cache_exists(pdf_id):
                return None
            
            paths = self._get_cache_paths(pdf_id)
            
            # Load vector database
            with open(paths['vector_db'], 'rb') as f:
                vector_db = pickle.load(f)
            
            # Load metadata
            with open(paths['metadata'], 'r') as f:
                metadata = json.load(f)
            
            # Load chunks
            with open(paths['chunks'], 'r') as f:
                chunks = json.load(f)
            
            # Load original text
            with open(paths['original_text'], 'r', encoding='utf-8') as f:
                original_text = f.read()
            
            pdf_data = {
                'filename': metadata['filename'],
                'vector_db': vector_db,
                'chunks': chunks,
                'original_text': original_text,
                'api_key': metadata.get('api_key', '')
            }
            
            print(f"✅ Loaded cached PDF data for {pdf_id} ({metadata['filename']})")
            return pdf_data
            
        except Exception as e:
            print(f"❌ Error loading cached PDF {pdf_id}: {str(e)}")
            return None
    
    def clear_cache(self, pdf_id: Optional[str] = None):
        """Clear cache for specific PDF or all cached data"""
        try:
            if pdf_id:
                # Clear specific PDF cache
                paths = self._get_cache_paths(pdf_id)
                for path in paths.values():
                    if path.exists():
                        path.unlink()
                print(f"🗑️ Cleared cache for PDF {pdf_id}")
            else:
                # Clear all cache
                import shutil
                if self.cache_dir.exists():
                    shutil.rmtree(self.cache_dir)
                    self.cache_dir.mkdir(exist_ok=True, parents=True)
                    self.vector_cache_dir.mkdir(exist_ok=True, parents=True)
                    self.metadata_cache_dir.mkdir(exist_ok=True, parents=True)
                print("🗑️ Cleared all PDF cache")
                
        except Exception as e:
            print(f"❌ Error clearing cache: {str(e)}")

async def process_and_cache_pdf(pdf_path: str, pdf_id: str, filename: str, 
                               api_key: str, cache_manager: PDFCacheManager) -> Dict[str, Any]:
    """Process a PDF and cache the results"""
    try:
        print(f"📄 Processing PDF: {filename}")
        
        # Load and process PDF using aimakerspace
        pdf_loader = PDFLoader(pdf_path)
        documents = pdf_loader.load_documents()
        
        # Extract original text from documents
        original_text = "\n\n".join([doc.text if hasattr(doc, 'text') else str(doc) for doc in documents])
        
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
        
        # Create PDF data structure
        pdf_data = {
            'filename': filename,
            'vector_db': vector_db,
            'chunks': chunks,
            'original_text': original_text,
            'api_key': api_key
        }
        
        # Save to cache
        cache_manager.save_to_cache(pdf_id, pdf_data)
        
        print(f"✅ Processed and cached PDF: {filename} ({len(chunks)} chunks)")
        return pdf_data
        
    except Exception as e:
        print(f"❌ Error processing PDF {filename}: {str(e)}")
        raise e