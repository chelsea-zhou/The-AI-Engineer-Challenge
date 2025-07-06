# Merge Instructions

## Feature: PDF Upload and RAG (Retrieval-Augmented Generation) System

### Changes Made:
- **Backend Enhancements**:
  - Added PDF processing module (`api/pdf_processor.py`) for text extraction
  - Created RAG system module (`api/rag_system.py`) using aimakerspace library
  - Updated main API (`api/app.py`) with new endpoints:
    - `/api/upload-pdf` - Upload and index PDF documents
    - `/api/rag-query` - Query indexed documents
    - `/api/rag-query-stream` - Streaming RAG queries
    - `/api/documents` - List and manage indexed documents
    - `/api/documents/{id}` - Delete specific documents
  - Added new dependencies: `aimakerspace`, `PyPDF2`, `aiofiles`
  - Updated requirements.txt with new packages

- **Frontend Enhancements**:
  - Updated main page (`frontend/app/page.tsx`) with:
    - PDF upload interface with drag-and-drop
    - Document management panel
    - Chat mode toggle (Regular Chat vs PDF RAG)
    - Document selection and deletion
    - Enhanced UI with new icons and layout
  - Added new API routes:
    - `/api/upload-pdf` - Proxy for PDF uploads
    - `/api/rag-query` - Proxy for RAG queries
    - `/api/rag-query-stream` - Proxy for streaming RAG queries
    - `/api/documents` - Proxy for document management

- **New Files Created**:
  - `api/pdf_processor.py` - PDF text extraction and processing
  - `api/rag_system.py` - RAG system with aimakerspace integration
  - `frontend/app/api/upload-pdf/route.ts` - PDF upload proxy
  - `frontend/app/api/rag-query/route.ts` - RAG query proxy
  - `frontend/app/api/rag-query-stream/route.ts` - Streaming RAG proxy
  - `frontend/app/api/documents/route.ts` - Document management proxy

### Testing:
1. **Backend Testing**:
   ```bash
   cd api
   source venv/bin/activate
   pip install -r requirements.txt
   python -m uvicorn app:app --host 0.0.0.0 --port 8000
   ```

2. **Frontend Testing**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Feature Testing**:
   - Upload a PDF file using the upload button
   - Switch to "PDF RAG" mode
   - Ask questions about the uploaded document
   - Verify streaming responses work
   - Test document management (select, delete)
   - Verify regular chat still works

4. **API Testing**:
   - Test `/api/health` endpoint
   - Test PDF upload with a sample PDF
   - Test RAG queries with questions
   - Test document listing and deletion

## Merge Routes

### Option 1: GitHub Pull Request (Recommended)
1. Push your feature branch to GitHub:
   ```bash
   git push origin feature/pdf-rag-system
   ```

2. Create a Pull Request from `feature/pdf-rag-system` to `main`
3. Review the changes in the PR
4. Ensure all tests pass
5. Merge the PR

### Option 2: GitHub CLI
```bash
# Push your feature branch
git push origin feature/pdf-rag-system

# Create PR using GitHub CLI
gh pr create --title "Feature: Add PDF Upload and RAG System" --body "This PR adds PDF upload functionality and RAG (Retrieval-Augmented Generation) system using the aimakerspace library. Users can now upload PDFs and chat with the content using AI-powered document Q&A."

# Review and merge
gh pr view
gh pr merge --merge
```

### Option 3: Local Merge
```bash
# Switch to main branch
git checkout main

# Pull latest changes
git pull origin main

# Merge your feature branch
git merge feature/pdf-rag-system

# Push to main
git push origin main
```

### Cleanup
```bash
# Delete local feature branch
git branch -d feature/pdf-rag-system

# Delete remote feature branch
git push origin --delete feature/pdf-rag-system
```

## Post-Merge Tasks
1. Update documentation to reflect new PDF RAG features
2. Test the deployed application on Vercel
3. Consider adding unit tests for the new modules
4. Monitor for any issues with the aimakerspace library integration

## Notes
- The RAG system includes fallback functionality if aimakerspace library is not available
- PDF processing includes security measures (filename sanitization)
- The system supports multiple documents per API key
- All existing chat functionality remains unchanged 