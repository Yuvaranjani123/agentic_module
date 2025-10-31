# Django-Streamlit Insurance RAG Pipeline

A comprehensive Retrieval-Augmented Generation (RAG) system for insurance documents using Django REST API backend and Streamlit frontend.

## Architecture

```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│  Streamlit UI   │◄──────────────►│  Django Backend │
│  (Frontend)     │                │  (REST API)     │
└─────────────────┘                └─────────────────┘
         │                                   │
         │                                   │
         ▼                                   ▼
┌─────────────────┐                ┌─────────────────┐
│   User Files    │                │   ChromaDB      │
│   (PDF, etc.)   │                │   (Embeddings)  │
└─────────────────┘                └─────────────────┘
```

## Features

### Core Features
- **PDF Processing**: Automated table and text extraction with intelligent merging
- **Human-in-the-Loop**: Manual review for table extraction accuracy
- **Semantic Chunking**: Intelligent text chunking using cosine similarity and embeddings
- **Vector Storage**: ChromaDB for efficient similarity search and persistence
- **REST API**: Clean separation between backend and frontend with comprehensive logging
- **Azure OpenAI**: Integration with Azure OpenAI for embeddings and chat completion

### New Enhanced Features
- **Multi-Agent Architecture**: Intelligent query routing with specialized agents:
  - **Retrieval Agent**: Document search and question answering
  - **Premium Calculator Agent**: Deterministic premium calculations from Excel workbooks
  - **Policy Comparison Agent**: Multi-product comparison with premium integration
- **Premium Calculation**: Upload Excel premium charts and calculate premiums deterministically
  - Supports both **exact age-wise** and **age band-wise** premium rates
  - Mixed format support: Different sheets can use different age formats in same workbook
  - Individual and family floater policies
  - Automatic format detection and intelligent age matching
  - See [PREMIUM_CALCULATOR_AGE_FORMATS.md](./PREMIUM_CALCULATOR_AGE_FORMATS.md) for details
- **Policy Comparison**: Compare multiple insurance products side-by-side
  - Automatic premium calculation integration
  - Document-based feature comparison
  - Value analysis and recommendations
- **Product-Based Architecture**: Unified database per product for better cross-document search
- **Document Type Classification**: Categorize documents as Policy, Brochure, Prospectus, or Terms & Conditions during ingestion
- **Advanced Document Filtering**: Filter search results by document type for more relevant answers
- **Real-Time Evaluation Metrics**: Comprehensive retrieval quality assessment including:
  - Term Coverage Analysis
  - Query Coverage Metrics
  - Semantic Similarity Scoring
  - Result Diversity Measurement
- **Streamlined Single Interface**: Unified retrieval interface with real-time metrics (dashboard removed for simplicity)
- **Enhanced Error Handling**: Robust error handling for edge cases including empty results and evaluation failures
- **Improved User Experience**: Auto-enabled evaluation with clear feedback and sample queries

## Prerequisites

1. **Python 3.11+** with virtual environment
2. **Azure OpenAI** account with:
   - Text embedding model (e.g., text-embedding-ada-002)
   - Chat model (e.g., gpt-35-turbo)
3. **Required packages** (see requirements.txt)

## Setup

### 1. Environment Setup

```bash
# Navigate to project directory
cd rag_module_1

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your Azure OpenAI credentials
# Required variables:
# - AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# - AZURE_OPENAI_KEY=your-api-key
# - AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS=text-embedding-ada-002
# - AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-35-turbo
# - DJANGO_SECRET_KEY=your-secret-key
# - API_BASE=http://localhost:8000
```

### 3. Database Setup

```bash
cd backend
python manage.py migrate
```

## Running the Application

### Start the Services

**Terminal 1 - Django Backend:**
```bash
cd backend
python manage.py runserver
```

**Terminal 2 - Ingestion UI:**
```bash
# From project root
streamlit run frontend/ingestion_run.py --server.port 8501
```

**Terminal 3 - Retrieval UI:**
```bash
# From project root
streamlit run frontend/retrieval_run.py --server.port 8502
```

### Access the Applications

- **Django Backend**: http://localhost:8000
- **Document Ingestion**: http://localhost:8501
- **Document Retrieval**: http://localhost:8502

## Workflow

### 1. Document Ingestion (Port 8501)

1. **Upload PDF**: Upload your insurance document (auto-detects output directory)
2. **Document Type Selection**: Choose document type (Policy Document, Brochure, Prospectus, Terms & Conditions)
3. **Analysis**: Automatic table detection and content analysis
4. **Extraction**: Extract tables (CSV) and text content
5. **Review**: Human-in-the-loop table verification with editable mapping (if tables found)
6. **Processing**: Chunk content and generate embeddings using Azure OpenAI with document type tagging
7. **Storage**: Store in ChromaDB under `media/output/chroma_db/[document_name]/` with metadata

### 2. Document Retrieval (Port 8502)

1. **Auto-Detection**: Automatically detects available ChromaDB collections
2. **Selection**: Choose which document collection to query
3. **Document Type Filtering**: Filter results by document type (Policy, Brochure, Prospectus, Terms)
4. **Evaluation Settings**: Enable real-time retrieval evaluation (enabled by default)
5. **Query**: Ask questions about your document with sample queries provided
6. **Search**: Semantic search through embedded content with configurable result count
7. **Answer**: AI-generated responses with detailed source citations and metadata
8. **Real-Time Metrics**: View evaluation metrics including:
   - Term Coverage (percentage of query terms found)
   - Query Coverage and Diversity scores
   - Semantic similarity scores for each source
   - Covered terms analysis

## API Endpoints

### Ingestion API (`/api/`)

#### Upload PDF Document
```bash
POST /api/upload_pdf/
Content-Type: multipart/form-data

curl -X POST http://localhost:8000/api/upload_pdf/ \
  -F "pdf=@/path/to/your/document.pdf"
```

**Response:**
```json
{
  "pdf_path": "/path/to/media/document.pdf",
  "pdf_name": "document.pdf"
}
```

#### Extract Tables from PDF
```bash
POST /api/extract_tables/
Content-Type: application/json

curl -X POST http://localhost:8000/api/extract_tables/ \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_path": "/path/to/media/document.pdf",
    "output_dir": "/path/to/output/directory"
  }'
```

**Response:**
```json
{
  "message": "Tables extracted successfully"
}
```

#### Extract Text from PDF
```bash
POST /api/extract_text/
Content-Type: application/json

curl -X POST http://localhost:8000/api/extract_text/ \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_path": "/path/to/media/document.pdf",
    "output_dir": "/path/to/output/directory"
  }'
```

**Response:**
```json
{
  "message": "Text extracted successfully"
}
```

#### Chunk and Embed Content
```bash
POST /api/chunk_and_embed/
Content-Type: application/json

curl -X POST http://localhost:8000/api/chunk_and_embed/ \
  -H "Content-Type: application/json" \
  -d '{
    "output_dir": "/path/to/extracted/content",
    "chroma_db_dir": "/path/to/chroma/database",
    "doc_type": "policy"
  }'
```

**Response:**
```json
{
  "message": "Chunking and embedding completed successfully",
  "collection_size": 245
}
```

### Retrieval API (`/retriever/`)

#### Query Embedded Documents
```bash
POST /retriever/query/
Content-Type: application/json

curl -X POST http://localhost:8000/retriever/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What does the insurance policy cover for hospital expenses?",
    "chroma_db_dir": "/path/to/chroma/database",
    "k": 5,
    "doc_type": "policy",
    "evaluate": true
  }'
```

**Response:**
```json
{
  "answer": "Based on the insurance policy documents, the hospital expenses coverage includes...",
  "sources": [
    {
      "content": "Hospital expenses are covered up to the sum insured...",
      "page": 15,
      "table": null,
      "row_index": null,
      "type": "text",
      "doc_type": "policy",
      "chunking_method": "semantic",
      "chunk_idx": 42
    }
  ],
  "evaluation": {
    "term_coverage": 0.85,
    "query_coverage": 0.92,
    "diversity": 0.78,
    "avg_semantic_similarity": 0.834,
    "covered_terms": ["hospital", "expenses", "coverage"],
    "semantic_similarities": [0.89, 0.82, 0.79]
  }
}
```

### Python Request Examples

#### Using requests library:
```python
import requests
import json

# Upload PDF
with open('insurance_policy.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/upload_pdf/',
        files={'pdf': f}
    )
    print(response.json())

# Query document
query_data = {
    "query": "What is the premium amount?",
    "chroma_db_dir": "/path/to/chroma/db",
    "k": 3
}
response = requests.post(
    'http://localhost:8000/retriever/query/',
    json=query_data
)
print(response.json())
```

## Project Structure

```
rag_module_1/
├── backend/                    # Django REST API
│   ├── backend/               # Django project settings
│   │   ├── settings.py       # Django configuration
│   │   ├── urls.py           # Main URL routing
│   │   └── wsgi.py           # WSGI application
│   ├── config/                # Configuration files
│   │   └── prompt_config.py  # AI prompt templates
│   ├── evaluation/            # NEW: Evaluation metrics module
│   │   ├── __init__.py       # Package initialization
│   │   └── metrics.py        # Retrieval evaluation metrics
│   ├── logs/                  # Logging utilities
│   │   ├── __init__.py       # Package initialization
│   │   └── utils.py          # Logging setup and configuration
│   ├── ingestion/             # PDF processing app
│   │   ├── views.py          # API endpoints with document type support
│   │   ├── utils.py          # Processing utilities with logging
│   │   ├── service.py        # Core chunking and embedding with doc types
│   │   ├── models.py         # Data models
│   │   └── urls.py           # URL routing
│   ├── retriever/             # Document retrieval app
│   │   ├── views.py          # Query endpoints with filtering & evaluation
│   │   └── urls.py           # URL routing
│   ├── manage.py             # Django management
│   └── db.sqlite3            # SQLite database
├── frontend/                   # Streamlit UIs
│   ├── ingestion_run.py      # Document processing UI with doc type selection
│   └── retrieval_run.py      # Document query UI with evaluation metrics
├── media/                      # File storage
│   ├── input/                # Uploaded PDFs
│   └── output/               # Processed files & ChromaDB
├── venv/                      # Python virtual environment
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Configuration Options

### Django Settings (`backend/settings.py`)

- **CORS_ALLOWED_ORIGINS**: Streamlit frontend URLs
- **MEDIA_ROOT**: File upload directory
- **REST_FRAMEWORK**: API configuration

### Environment Variables

**Required in .env file:**
- **AZURE_OPENAI_ENDPOINT**: Your Azure OpenAI endpoint URL
- **AZURE_OPENAI_KEY**: Your Azure OpenAI API key
- **AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS**: Embedding model deployment name
- **AZURE_OPENAI_CHAT_DEPLOYMENT**: Chat model deployment name
- **AZURE_OPENAI_TEXT_VERSION**: API version for text operations (e.g., 2023-05-15)
- **AZURE_OPENAI_CHAT_API_VERSION**: API version for chat operations (e.g., 2023-05-15)
- **DJANGO_SECRET_KEY**: Django secret key for security
- **API_BASE**: API base URL (http://localhost:8000)
- **ANONYMIZED_TELEMETRY**: Set to False to disable ChromaDB telemetry
- **LOG_LEVEL**: Set logging level (DEBUG, INFO, WARNING, ERROR) - defaults to INFO

## Troubleshooting

### Common Issues

1. **Django server not starting**
   - Check if port 8000 is available
   - Verify .env file exists and has correct settings
   - Ensure all dependencies are installed
   - Check logs in `backend/logs/` directory

2. **Streamlit can't connect to Django**
   - Verify Django server is running
   - Check CORS settings in Django
   - Confirm API_BASE URL in environment
   - Review API logs for connection errors

3. **Azure OpenAI errors**
   - Verify API key and endpoint
   - Check model deployment names
   - Ensure sufficient quota
   - Check API version compatibility
   - Review embedding and chat model configurations

4. **ChromaDB issues**
   - Check directory permissions
   - Ensure ChromaDB directory exists
   - Verify embedding model is working
   - Check ChromaDB telemetry settings

5. **Logging issues**
   - Verify `backend/logs/utils.py` exists
   - Check log file permissions
   - Ensure LOG_LEVEL is set correctly in .env
   - Review console output for setup errors

6. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check virtual environment activation
   - Verify PYTHONPATH includes project root
   - Check for missing scikit-learn (required for semantic chunking)

5.**Path issues**
   - Ensure all directory paths in your configuration files are correct and exist.
   - Check for typos or incorrect folder names in your file paths.
   - Verify that your operating system's path separators (`/` for Linux/Mac, `\` for Windows) are used consistently.
   - Make sure your application has the necessary permissions to read/write to the specified directories.
   - If running in Docker or a virtual environment, confirm that volume mounts and working directories are set up properly.

### Debug Mode

Enable Django debug mode by setting `DEBUG=True` in settings.py for detailed error messages.

### Logging and Monitoring

The application includes comprehensive logging across all components:
- **File Logging**: Logs are written to `backend/logs/app.log`
- **Console Logging**: Real-time logging to console for development
- **Log Levels**: Configurable via LOG_LEVEL environment variable
- **Structured Logging**: Consistent format across all modules

**Key Log Events:**
- PDF upload and processing
- Table and text extraction progress
- Embedding generation and storage
- Query processing and results
- Error handling and debugging information

**Monitoring Tips:**
- Check `backend/logs/app.log` for detailed operation logs
- Use `LOG_LEVEL=DEBUG` for verbose debugging
- Monitor ChromaDB collection sizes in logs
- Track semantic vs paragraph chunking statistics

## Development

### Adding New Features

1. **Backend**: Add new views in respective Django apps
2. **Frontend**: Create new Streamlit components
3. **API**: Update URL routing and add CORS origins

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs in Django admin
3. Verify environment configuration
4. Test API endpoints individually
5.Reach out to myuvaranjani@gmail.com