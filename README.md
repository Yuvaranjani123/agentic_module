# 🏥 Enterprise Insurance RAG System

## Professional-Grade Retrieval-Augmented Generation Platform for Insurance Documents

A production-ready, modular RAG (Retrieval-Augmented Generation) system designed specifically for insurance document processing and intelligent query resolution. Built with Django REST Framework backend and Streamlit frontend, featuring multi-agent architecture, deterministic premium calculations, and advanced document comparison capabilities.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40.2-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)


---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Running the Application](#-running-the-application)
- [Complete Workflow](#-complete-workflow)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Configuration](#-configuration)
- [Advanced Features](#-advanced-features)
- [Troubleshooting](#-troubleshooting)
- [Development Guidelines](#-development-guidelines)
- [Performance Optimization](#-performance-optimization)
- [Security](#-security)
- [License](#-license)
- [Support & Contact](#-support--contact)

---

## 🎯 Overview

The **Enterprise Insurance RAG System** is a sophisticated document intelligence platform designed to transform how insurance organizations handle policy documents, premium calculations, and multi-product comparisons. Built with scalability, modularity, and production-readiness in mind, this system leverages cutting-edge AI technologies to provide accurate, contextual answers while maintaining deterministic calculations for critical business operations.

### What Makes This System Unique?

- **🤖 Multi-Agent Architecture**: Intelligent query routing to specialized agents (retrieval, premium calculation, policy comparison)
- **💰 Deterministic Premium Calculations**: Exact, auditable premium computations from Excel workbooks with mixed age format support
- **📊 Advanced Document Processing**: Intelligent table detection, extraction, and human-in-the-loop review
- **🔍 Semantic Search**: Context-aware document retrieval with real-time evaluation metrics
- **🏢 Product-Based Architecture**: Unified databases per product for superior cross-document search
- **📈 Production-Ready**: Comprehensive logging, error handling, and scalable REST API design

### Use Cases

- **Customer Service**: Instant, accurate answers to policy-related questions
- **Premium Quotation**: Real-time premium calculations for various policy configurations
- **Product Comparison**: Side-by-side analysis of multiple insurance products
- **Compliance & Training**: Quick access to policy terms, conditions, and coverage details
- **Sales Support**: Intelligent product recommendations based on customer queries

---

## ✨ Key Features

### Core Capabilities


### Core Capabilities

#### 📄 **Intelligent Document Processing**
- **PDF Parsing**: Advanced table and text extraction with intelligent content merging
- **Human-in-the-Loop**: Manual review interface for table extraction accuracy
- **Document Classification**: Automatic categorization (Policy, Brochure, Prospectus, Terms & Conditions)
- **Batch Processing**: ZIP file upload for multi-document ingestion
- **Excel Support**: Premium calculator workbook registry with automatic discovery

#### 🧠 **Multi-Agent Intelligence**
- **Orchestrated Routing**: Intelligent query classification and agent selection
- **Retrieval Agent**: Context-aware document search with conversation memory
- **Premium Calculator Agent**: Deterministic calculations from Excel workbooks
  - **Mixed Format Support**: Handles both exact ages and age bands in same workbook
  - **Flexible Policy Types**: Individual and family floater policies
  - **Auto-Detection**: Intelligent format recognition and age matching
- **Comparison Agent**: Multi-product analysis with premium integration

#### 🔍 **Advanced Retrieval**
- **Semantic Chunking**: Intelligent text segmentation using cosine similarity
- **Vector Storage**: Persistent ChromaDB with efficient similarity search
- **Real-Time Evaluation**: Comprehensive quality metrics including:
  - Term Coverage Analysis
  - Query Coverage Scoring
  - Semantic Similarity Measurement
  - Result Diversity Assessment
- **Document Type Filtering**: Precise result filtering by document category
- **Conversation Memory**: Contextual follow-up query support

#### 💼 **Production Features**
- **REST API Design**: Clean separation of concerns with comprehensive endpoints
- **Comprehensive Logging**: File and console logging with configurable levels
- **Error Handling**: Robust exception management with detailed error messages
- **CORS Support**: Secure cross-origin resource sharing configuration
- **Azure OpenAI Integration**: Enterprise-grade embedding and chat models

---

## 🏗️ Architecture

### System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                                │
│  ┌────────────────────┐              ┌────────────────────┐          │
│  │  Ingestion UI      │              │  Retrieval UI      │          │
│  │  (Streamlit)       │              │  (Streamlit)       │          │
│  │  Port: 8501        │              │  Port: 8502        │          │
│  └──────────┬─────────┘              └─────────┬──────────┘          │
└─────────────┼────────────────────────────────────┼───────────────────┘
              │                                    │
              │          HTTP REST API             │
              │                                    │
┌─────────────┴────────────────────────────────────┴───────────────────┐
│                      Django Backend (Port: 8000)                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Agent Orchestrator                          │  │
│  │  (Intelligent Query Routing & Intent Classification)          │  │
│  └─────┬──────────────────┬──────────────────┬───────────────────┘  │
│        │                  │                  │                       │
│  ┌─────▼──────┐    ┌─────▼──────┐    ┌─────▼──────┐               │
│  │ Retrieval  │    │  Premium   │    │ Comparison │               │
│  │   Agent    │    │ Calculator │    │   Agent    │               │
│  └─────┬──────┘    └─────┬──────┘    └─────┬──────┘               │
│        │                  │                  │                       │
│  ┌─────▼───────────────────▼──────────────────▼──────────────────┐  │
│  │                  Service Layer                                │  │
│  │  • Document Retriever  • Excel Parser  • Response Builder   │  │
│  │  • Query Enhancer      • Age Matcher   • Premium Comparator  │  │
│  │  • Memory Manager      • Conversation  • Document Comparator │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                   Core Services                               │  │
│  │  • Ingestion API   • Chunking Service  • Logging Utility    │  │
│  │  • Retrieval API   • Embedding Service • Evaluation Engine   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└──────────────┬────────────────────────────────┬─────────────────────┘
               │                                │
    ┌──────────▼───────────┐        ┌──────────▼──────────┐
    │   Azure OpenAI       │        │    ChromaDB         │
    │  • Embeddings Model  │        │  • Vector Store     │
    │  • Chat Model        │        │  • Collections      │
    └──────────────────────┘        └─────────────────────┘
                                              │
                            ┌─────────────────▼──────────────────┐
                            │       File Storage                  │
                            │  • Extracted Tables (CSV)          │
                            │  • Extracted Text                  │
                            │  • Premium Workbooks (Excel)       │
                            │  • Logs & Metadata                 │
                            └────────────────────────────────────┘
```

### Modular Frontend Architecture

```
frontend/
├── ingestion_run.py (238 lines) - Main orchestration
├── services/
│   ├── api_client.py - Backend communication
│   ├── ingestion_pipeline.py - Workflow orchestration
│   └── file_manager.py - File operations
└── components/
    └── ingestion/
        ├── file_uploader.py - Upload UI components
        ├── pdf_processor.py - PDF workflow UI
        └── zip_processor.py - Batch processing UI

[79% code reduction achieved through modularization]
```

---

## 🛠️ Technology Stack

### Backend Technologies
- **Framework**: Django 5.1.4 with Django REST Framework 3.15.2
- **Database**: SQLite (development) / PostgreSQL-ready (production)
- **Vector Store**: ChromaDB 0.5.23
- **AI/ML**: 
  - LangChain 0.3.27 & LangChain-OpenAI 0.2.11
  - scikit-learn 1.5.2 (semantic chunking)
- **Document Processing**: 
  - pdfplumber 0.11.4 (PDF parsing)
  - pandas 2.2.3 (table manipulation)
- **API**: RESTful API with CORS support (django-cors-headers 4.6.0)

### Frontend Technologies
- **UI Framework**: Streamlit 1.40.2
- **HTTP Client**: requests 2.32.3
- **Configuration**: python-dotenv 1.0.1

### Infrastructure & Tools
- **AI Provider**: Azure OpenAI (embeddings & chat completion)
- **Logging**: Comprehensive file & console logging
- **Environment**: Virtual environment (venv)
- **Version Control**: Git

---

## 📦 Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **RAM**: Minimum 8GB (16GB recommended for large documents)
- **Disk Space**: 5GB+ for dependencies and document storage
- **Operating System**: Windows, macOS, or Linux

### Azure Services
- **Azure OpenAI Account** with:
  - Text embedding model deployment (e.g., `text-embedding-ada-002`)
  - Chat completion model deployment (e.g., `gpt-35-turbo` or `gpt-4`)
  - Sufficient quota for production workloads
  - API access keys and endpoint URL

### Development Tools
- **Git**: For version control
- **Code Editor**: VS Code (recommended) or any IDE with Python support
- **Terminal**: PowerShell (Windows) / Bash (macOS/Linux)
- **Browser**: Modern browser for Streamlit UIs (Chrome, Firefox, Edge)

---

## 🚀 Installation & Setup

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/Yuvaranjani123/rag_module_1.git
cd rag_module_1
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Windows (Command Prompt):
venv\Scripts\activate.bat

# macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

### Step 4: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your credentials
# Use your preferred text editor (notepad, vim, nano, etc.)
notepad .env  # Windows
nano .env     # macOS/Linux
```

**Required Environment Variables:**

```ini
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key-here
AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS=text-embedding-ada-002
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-35-turbo
AZURE_OPENAI_TEXT_VERSION=2023-05-15
AZURE_OPENAI_CHAT_API_VERSION=2023-05-15

# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here-generate-unique-string
DEBUG=False

# API Configuration
API_BASE=http://localhost:8000

# Logging Configuration
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# ChromaDB Configuration
ANONYMIZED_TELEMETRY=False
```

**Generate Django Secret Key:**
```python
# Run in Python shell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 5: Database Setup

```bash
# Navigate to backend directory
cd backend

# Run database migrations
python manage.py migrate

# Create superuser (optional, for Django admin)
python manage.py createsuperuser

# Return to project root
cd ..
```

### Step 6: Verify Installation

```bash
# Test Django server
cd backend
python manage.py check

# Test imports
python -c "import chromadb, langchain, pdfplumber; print('All imports successful!')"
```

---

## 🏃 Running the Application

### Production Start (Recommended)

Open **three separate terminals** and run the following commands:

**Terminal 1 - Django Backend:**
```bash
cd backend
python manage.py runserver
```
**✅ Backend Available**: http://localhost:8000

**Terminal 2 - Document Ingestion UI:**
```bash
# From project root
streamlit run frontend/ingestion_run.py --server.port 8501
```
**✅ Ingestion UI**: http://localhost:8501

**Terminal 3 - Document Retrieval UI:**
```bash
# From project root
streamlit run frontend/retrieval_run.py --server.port 8502
```
**✅ Retrieval UI**: http://localhost:8502

### Development Start (Debug Mode)

```bash
# Set debug mode in .env
DEBUG=True
LOG_LEVEL=DEBUG

# Start services with verbose logging
```

### Quick Start Script (Windows PowerShell)

```powershell
# Save as start-app.ps1
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python manage.py runserver"
Start-Sleep 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "streamlit run frontend/ingestion_run.py --server.port 8501"
Start-Sleep 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "streamlit run frontend/retrieval_run.py --server.port 8502"
```

---

## 📖 Complete Workflow

### Phase 1: Document Ingestion (Port 8501)

#### A. Single PDF Upload

1. **Configure Product**
   - Enter product/database name (e.g., "ActivAssure")
   - This creates a unified database for the product

2. **Upload PDF Document**
   - Select PDF file from local system
   - Auto-detection of output directory

3. **Select Document Type**
   - Policy Document
   - Brochure
   - Prospectus
   - Terms & Conditions
   - Premium Calculation (Excel)
   - Claim Form
   - Certificate
   - Custom (specify your own)

4. **Analysis Phase**
   - Automatic table detection
   - Page count analysis
   - Content preview generation

5. **Extraction Phase**
   - **Tables**: Extracted to CSV files with page mapping
   - **Text**: Extracted to individual text files per page

6. **Human-in-the-Loop Review** (if tables detected)
   - Review extracted tables
   - Edit table-to-file mapping
   - Mark review as complete

7. **Chunking & Embedding**
   - Semantic chunking with cosine similarity
   - Azure OpenAI embedding generation
   - Document type metadata tagging
   - ChromaDB storage

8. **Completion**
   - Collection size confirmation
   - Output directory location
   - Ready for retrieval

#### B. Batch Processing (ZIP Upload)

1. **Upload ZIP File**
   - Contains multiple PDFs and/or Excel files
   - Auto-extraction to temp directory

2. **Document Labeling**
   - Assign document type to each file
   - Excel files default to "premium-calculation"
   - Custom types supported

3. **Batch Processing**
   - Process all or selected files
   - Progress tracking with status updates
   - Individual file success/failure reporting

4. **Results Summary**
   - Total processed count
   - Success/failure breakdown
   - Automatic cleanup

### Phase 2: Premium Calculator Setup

1. **Upload Excel Workbook**
   - Via ZIP batch processing or dedicated endpoint
   - Registered in premium calculator registry

2. **Workbook Structure**
   - Multiple sheets for different compositions
   - Age columns (exact ages or age bands)
   - Sum insured columns (e.g., 5L, 10L, 25L)
   - Mixed formats supported per sheet

3. **Verification**
   - Automatic format detection
   - Age matching validation
   - Ready for calculations

### Phase 3: Document Retrieval & Querying (Port 8502)

1. **Auto-Detection**
   - System scans for available ChromaDB collections
   - Lists all ingested products

2. **Product Selection**
   - Choose product database to query
   - Multiple product support

3. **Query Configuration**
   - **Result Count**: 1-10 sources
   - **Document Type Filter**: Optional filtering
   - **Evaluation**: Real-time metrics (enabled by default)

4. **Query Types**

   **A. Document Questions**
   ```
   "What are the exclusions in the policy?"
   "Explain the claim settlement process"
   "What is covered under maternity benefits?"
   ```

   **B. Premium Calculations**
   ```
   "Calculate premium for 2 adults aged 35 and 40 with 1 child aged 7, sum insured 10L"
   "What is the premium for an individual aged 30 with 5L cover?"
   "Premium for family floater 2 adults + 2 children, sum insured 25L"
   ```

   **C. Policy Comparisons**
   ```
   "Compare ActivAssure and ActivFit policies"
   "Which policy is better for senior citizens?"
   "Compare premiums for both products for family of 4"
   ```

5. **Response Display**
   - **Answer**: AI-generated contextual response
   - **Sources**: Detailed source citations with:
     - Content excerpt
     - Page number
     - Document type
     - Chunking method
     - Semantic similarity score
   - **Evaluation Metrics** (if enabled):
     - Term Coverage percentage
     - Query Coverage score
     - Diversity measurement
     - Average semantic similarity
     - Covered terms analysis

6. **Conversation History**
   - Expandable history section
   - Previous Q&A pairs
   - Context-aware follow-ups

---

## 📡 API Documentation


### Base URL
```
http://localhost:8000
```

### Ingestion Endpoints

#### 1. Extract Tables from PDF

**Endpoint**: `POST /api/extract_tables/`

**Description**: Extracts all tables from a PDF document and saves them as CSV files with page mapping.

**Request Body**:
```json
{
  "pdf_path": "/path/to/document.pdf",
  "output_dir": "/path/to/output/directory"
}
```

**Response**:
```json
{
  "message": "Tables extracted successfully",
  "tables_found": 15,
  "output_dir": "/path/to/output/directory"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/extract_tables/ \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_path": "media/input/policy.pdf",
    "output_dir": "media/output/ActivAssure"
  }'
```

#### 2. Extract Text from PDF

**Endpoint**: `POST /api/extract_text/`

**Description**: Extracts text content from all pages and saves as individual text files.

**Request Body**:
```json
{
  "pdf_path": "/path/to/document.pdf",
  "output_dir": "/path/to/output/directory"
}
```

**Response**:
```json
{
  "message": "Text extracted successfully",
  "pages_processed": 25,
  "output_dir": "/path/to/output/directory"
}
```

#### 3. Chunk and Embed Content

**Endpoint**: `POST /api/chunk_and_embed/`

**Description**: Performs semantic chunking and generates embeddings for storage in ChromaDB.

**Request Body**:
```json
{
  "output_dir": "/path/to/extracted/content",
  "chroma_db_dir": "/path/to/chroma/database",
  "doc_type": "policy",
  "doc_name": "ActivAssure"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Chunking and embedding completed successfully",
  "collection_size": 245,
  "chunks_created": 187,
  "doc_type": "policy"
}
```

**Document Types**:
- `policy` - Policy documents
- `brochure` - Marketing brochures
- `prospectus` - Product prospectus
- `terms` - Terms & conditions
- `premium-calculation` - Premium workbooks
- `claim-form` - Claim forms
- `certificate` - Certificates
- Custom types supported

#### 4. Upload Premium Excel

**Endpoint**: `POST /api/upload_premium_excel/`

**Description**: Uploads Excel workbook to premium calculator registry.

**Request**: `multipart/form-data`
```
excel: [Excel file]
doc_name: "ActivAssure"
```

**Response**:
```json
{
  "message": "Premium workbook uploaded successfully",
  "filename": "ActivAssure_premium_chart.xlsx",
  "doc_name": "ActivAssure",
  "sheets_found": ["Individual", "2 Adults", "2 Adults + 1 Child"]
}
```

### Retrieval & Agent Endpoints

#### 5. Orchestrated Agent Query

**Endpoint**: `POST /agents/query/`

**Description**: Main query endpoint with intelligent routing to specialized agents.

**Request Body**:
```json
{
  "query": "Calculate premium for 2 adults aged 35 and 40 with 1 child aged 7, sum insured 10L",
  "chroma_db_dir": "/path/to/chroma/db/ActivAssure",
  "k": 5,
  "doc_type": "policy",
  "exclude_doc_types": ["brochure"],
  "evaluate": true,
  "conversation_id": "user_session_123"
}
```

**Response (Retrieval Agent)**:
```json
{
  "agent": "retrieval",
  "intent": "document_query",
  "query": "What are the exclusions?",
  "answer": "Based on the policy documents, the exclusions include...",
  "sources": [
    {
      "content": "The following are not covered under this policy...",
      "page": 15,
      "doc_type": "policy",
      "table": null,
      "chunking_method": "semantic",
      "chunk_idx": 42,
      "similarity": 0.89
    }
  ],
  "evaluation": {
    "term_coverage": 0.92,
    "query_coverage": 0.88,
    "diversity": 0.75,
    "avg_semantic_similarity": 0.834,
    "covered_terms": ["exclusions", "policy", "coverage"],
    "semantic_similarities": [0.89, 0.85, 0.82, 0.78, 0.77]
  }
}
```

**Response (Premium Calculator Agent)**:
```json
{
  "agent": "premium_calculator",
  "intent": "premium_calculation",
  "query": "Calculate premium for 2 adults aged 35 and 40...",
  "answer": "**Premium Calculation Result**\n\n**Policy Type:** Family Floater\n**Composition:** 2 Adults + 1 Child\n**Sum Insured:** ₹1,000,000\n**Eldest Age:** 40 (36-40)\n\n**Gross Premium:** ₹16,579.00\n**GST (18%):** ₹2,984.22\n**Total Premium:** ₹19,563.22",
  "policy_type": "family_floater",
  "composition": "2 Adults + 1 Child",
  "gross_premium": 16579.0,
  "gst_amount": 2984.22,
  "total_premium": 19563.22,
  "sum_insured": 1000000,
  "eldest_age": 40
}
```

**Response (Comparison Agent)**:
```json
{
  "agent": "comparison",
  "intent": "policy_comparison",
  "query": "Compare ActivAssure and ActivFit",
  "answer": "**Policy Comparison: ActivAssure vs ActivFit**\n\n**Coverage Features:**\n- ActivAssure offers wider coverage including...\n- ActivFit focuses on preventive care with...\n\n**Premium Comparison:**\n- ActivAssure: ₹19,563\n- ActivFit: ₹21,450\n\n**Recommendation:** ActivAssure provides better value for families...",
  "products_compared": ["ActivAssure", "ActivFit"],
  "comparison_type": "with_premiums",
  "premium_calculations": {
    "ActivAssure": 19563.22,
    "ActivFit": 21450.00
  }
}
```

#### 6. Clear Conversation History

**Endpoint**: `POST /agents/clear_conversation/`

**Request Body**:
```json
{
  "chroma_db_dir": "/path/to/chroma/db",
  "conversation_id": "user_session_123"
}
```

**Response**:
```json
{
  "message": "Conversation history cleared",
  "conversation_id": "user_session_123"
}
```

#### 7. Get Conversation History

**Endpoint**: `GET /agents/conversation_history/?chroma_db_dir=path&conversation_id=session_id`

**Response**:
```json
{
  "history": [
    {
      "role": "user",
      "content": "What is the premium?",
      "timestamp": "2025-10-31T10:30:00"
    },
    {
      "role": "assistant",
      "content": "The premium for your configuration is ₹19,563",
      "timestamp": "2025-10-31T10:30:02"
    }
  ],
  "count": 2
}
```

#### 8. Evaluation Summary

**Endpoint**: `GET /agents/evaluation_summary/?chroma_db_dir=path`

**Response**:
```json
{
  "total_queries": 150,
  "avg_term_coverage": 0.87,
  "avg_query_coverage": 0.82,
  "avg_diversity": 0.76,
  "avg_semantic_similarity": 0.84
}
```

### Python SDK Examples

#### Complete Ingestion Workflow
```python
import requests
import os

API_BASE = "http://localhost:8000"

def ingest_document(pdf_path, product_name, doc_type="policy"):
    """Complete document ingestion workflow."""
    
    # Setup directories
    output_dir = f"media/output/{product_name}"
    chroma_db_dir = f"media/output/chroma_db/{product_name}"
    
    # 1. Extract tables
    response = requests.post(
        f"{API_BASE}/api/extract_tables/",
        json={"pdf_path": pdf_path, "output_dir": output_dir}
    )
    print(f"Tables: {response.json()}")
    
    # 2. Extract text
    response = requests.post(
        f"{API_BASE}/api/extract_text/",
        json={"pdf_path": pdf_path, "output_dir": output_dir}
    )
    print(f"Text: {response.json()}")
    
    # 3. Chunk and embed
    response = requests.post(
        f"{API_BASE}/api/chunk_and_embed/",
        json={
            "output_dir": output_dir,
            "chroma_db_dir": chroma_db_dir,
            "doc_type": doc_type,
            "doc_name": product_name
        }
    )
    print(f"Embedding: {response.json()}")
    
    return chroma_db_dir

# Usage
chroma_path = ingest_document("policy.pdf", "ActivAssure", "policy")
```

#### Query with Evaluation
```python
def query_with_evaluation(query, chroma_db_dir, k=5):
    """Query with real-time evaluation metrics."""
    
    response = requests.post(
        f"{API_BASE}/agents/query/",
        json={
            "query": query,
            "chroma_db_dir": chroma_db_dir,
            "k": k,
            "evaluate": True
        }
    )
    
    result = response.json()
    
    print(f"Agent: {result['agent']}")
    print(f"Answer: {result['answer']}")
    
    if 'evaluation' in result:
        eval_data = result['evaluation']
        print(f"\nEvaluation Metrics:")
        print(f"  Term Coverage: {eval_data['term_coverage']:.2%}")
        print(f"  Query Coverage: {eval_data['query_coverage']:.2%}")
        print(f"  Diversity: {result['evaluation']['diversity']:.2%}")
    
    return result

# Usage
result = query_with_evaluation(
    "What are the maternity benefits?",
    "media/output/chroma_db/ActivAssure"
)
```

#### Premium Calculation
```python
def calculate_premium(ages, sum_insured_lakhs, policy_type="family_floater"):
    """Calculate insurance premium."""
    
    query = f"Calculate premium for "
    if policy_type == "family_floater" and len(ages) > 1:
        adults = [age for age in ages if age >= 18]
        children = [age for age in ages if age < 18]
        query += f"{len(adults)} adults aged {', '.join(map(str, adults))}"
        if children:
            query += f" with {len(children)} child"
            if len(children) > 1:
                query += "ren"
            query += f" aged {', '.join(map(str, children))}"
    else:
        query += f"individual aged {ages[0]}"
    
    query += f", sum insured {sum_insured_lakhs}L"
    
    response = requests.post(
        f"{API_BASE}/agents/query/",
        json={"query": query}
    )
    
    return response.json()

# Usage
result = calculate_premium([35, 40, 7], 10, "family_floater")
print(f"Total Premium: ₹{result['total_premium']:,.2f}")
```

---

## 📁 Project Structure


```
rag_module/
├── backend/                          # Django REST API Backend
│   ├── agents/                       # 🤖 Multi-Agent System
│   │   ├── retrieval_agent.py       # Document Q&A agent with memory
│   │   ├── comparison_agent.py      # Multi-product comparison agent
│   │   ├── orchestrator.py          # Intelligent query routing
│   │   ├── views.py                 # Agent API endpoints
│   │   ├── urls.py                  # Agent URL routing
│   │   ├── calculators/             # Premium calculation modules
│   │   │   ├── calculator_base.py   # Main calculator orchestration
│   │   │   ├── excel_parser.py      # Excel workbook parsing
│   │   │   ├── age_matcher.py       # Age band matching logic
│   │   │   └── __init__.py          # Calculator exports
│   │   ├── retrievers/              # Document retrieval modules
│   │   │   ├── document_retriever.py   # ChromaDB document search
│   │   │   ├── query_enhancer.py       # Query preprocessing
│   │   │   ├── conversation_memory.py  # Session management
│   │   │   └── __init__.py
│   │   └── comparators/             # Comparison modules
│   │       ├── document_comparator.py  # Document-based comparison
│   │       ├── premium_comparator.py   # Premium comparison logic
│   │       ├── response_builder.py     # Answer formatting
│   │       └── __init__.py
│   ├── backend/                      # Django project configuration
│   │   ├── settings.py              # ⚙️ Django settings & CORS
│   │   ├── urls.py                  # Main URL routing
│   │   ├── wsgi.py                  # WSGI application entry
│   │   └── asgi.py                  # ASGI application entry
│   ├── config/                       # Configuration modules
│   │   ├── prompt_config.py         # AI prompt templates
│   │   └── __init__.py
│   ├── evaluation/                   # 📊 Evaluation metrics
│   │   ├── metrics.py               # Retrieval quality metrics
│   │   └── __init__.py
│   ├── ingestion/                    # 📄 Document ingestion app
│   │   ├── views.py                 # Ingestion API endpoints
│   │   ├── service.py               # Chunking & embedding service
│   │   ├── utils.py                 # PDF processing utilities
│   │   ├── models.py                # Data models
│   │   ├── urls.py                  # URL routing
│   │   └── migrations/              # Database migrations
│   ├── retriever/                    # 🔍 Document retrieval app
│   │   ├── views.py                 # Retrieval API endpoints
│   │   ├── models.py                # Data models
│   │   ├── urls.py                  # URL routing
│   │   └── migrations/              # Database migrations
│   ├── logs/                         # 📝 Logging utilities
│   │   ├── utils.py                 # Logging configuration
│   │   ├── models.py                # Log models
│   │   ├── app.log                  # Application logs (generated)
│   │   └── migrations/              # Database migrations
│   ├── utils/                        # Shared utilities
│   ├── media/                        # Media file storage
│   │   └── logs/                    # Premium workbook registry
│   │       └── activ_assure_premium_chart.xlsx
│   ├── manage.py                    # Django management script
│   └── db.sqlite3                   # SQLite database
│
├── frontend/                         # 🎨 Streamlit UI (Modularized)
│   ├── ingestion_run.py             # 📥 Document ingestion UI (238 lines)
│   ├── retrieval_run.py             # 🔎 Document retrieval UI
│   ├── services/                    # Business logic services
│   │   ├── api_client.py            # Backend API communication (190 lines)
│   │   ├── ingestion_pipeline.py   # Ingestion orchestration (305 lines)
│   │   └── file_manager.py          # File operations (150 lines)
│   └── components/                  # Reusable UI components
│       └── ingestion/
│           ├── file_uploader.py     # Upload UI components
│           ├── pdf_processor.py     # PDF workflow UI (330 lines)
│           └── zip_processor.py     # Batch processing UI (400+ lines)
│
├── media/                            # 💾 File storage (auto-created)
│   ├── input/                       # Uploaded PDF files
│   ├── output/                      # Processed files
│   │   ├── [ProductName]/           # Product-specific output
│   │   │   ├── table_*.csv          # Extracted tables
│   │   │   ├── page_*_text.txt      # Extracted text
│   │   │   ├── table_file_map.csv   # Table mapping
│   │   │   └── all_chunks_preview.txt
│   │   ├── chroma_db/               # Vector databases
│   │   │   └── [ProductName]/       # Product-specific ChromaDB
│   │   │       ├── chroma.sqlite3   # ChromaDB SQLite
│   │   │       └── [collection_id]/ # Collection data
│   │   └── temp/                    # Temporary extraction folder
│   └── logs/                        # Log files
│
├── scripts/                          # Utility scripts
├── venv/                            # Python virtual environment
├── .env                             # Environment variables (create from .env.example)
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore rules
├── requirements.txt                 # Python dependencies
├── run_tests.py                     # 🧪 Test runner with colored output
├── LICENSE.txt                      # MIT License
├── README.md                        # This file
├── PUBLICATION_GUIDE.md             # Publication guidelines
├── INSURANCE_RAG_PUBLICATION.md     # Project publication documentation
├── TESTING_GUIDE.md                 # Comprehensive testing documentation
├── TESTING_QUICK_REFERENCE.md       # Quick command reference
└── HOW_TO_ADD_YOUR_OWN_TESTS.md     # Guide for writing new tests
```

### Key Directory Descriptions

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `backend/agents/` | Multi-agent system core | `orchestrator.py`, `retrieval_agent.py`, `comparison_agent.py` |
| `backend/agents/calculators/` | Premium calculation engine | `calculator_base.py`, `excel_parser.py`, `age_matcher.py` |
| `backend/ingestion/` | Document processing pipeline | `service.py` (chunking), `utils.py` (PDF parsing) |
| `backend/ingestion/tests/` | Ingestion module tests | `test_views.py`, `test_service.py`, `test_utils.py` |
| `backend/retriever/` | Vector search & retrieval | `views.py` (query endpoints) |
| `backend/retriever/tests/` | Retriever module tests | `test_views.py`, `test_internal.py`, `test_evaluator.py` |
| `backend/evaluation/` | Quality metrics | `metrics.py` (term coverage, diversity, similarity) |
| `backend/logs/` | Logging infrastructure | `utils.py` (logging setup), `app.log` (logs) |
| `frontend/services/` | Business logic layer | `api_client.py`, `ingestion_pipeline.py`, `file_manager.py` |
| `frontend/components/` | Reusable UI components | `pdf_processor.py`, `zip_processor.py` |
| `media/output/chroma_db/` | Vector databases | Per-product ChromaDB collections |

---

## 🧪 Testing

### Comprehensive Test Suite

The project includes a production-ready testing infrastructure with 35+ test cases covering ingestion and retrieval modules. All tests are organized in a modular structure with files under 300 lines for maintainability.

#### Test Organization

```
backend/
├── ingestion/tests/          # Ingestion module tests
│   ├── __init__.py
│   ├── test_views.py        # API endpoint tests (~250 lines)
│   ├── test_service.py      # ChunkerEmbedder tests (~130 lines)
│   └── test_utils.py        # Utility function tests (~80 lines)
└── retriever/tests/          # Retriever module tests
    ├── __init__.py
    ├── test_views.py         # API endpoint tests (~180 lines)
    ├── test_internal.py      # Internal query tests (~180 lines)
    └── test_evaluator.py     # Evaluation tests (~80 lines)
```

#### Running Tests

**Quick Start:**
```bash
# Run all tests
python run_tests.py

# Run tests with verbose output
python run_tests.py --verbose

# Run with coverage report
python run_tests.py --coverage

# Run specific module tests
python run_tests.py ingestion
python run_tests.py retriever

# Run specific test file
python run_tests.py ingestion.tests.test_views

# Run specific test class
python run_tests.py ingestion.tests.test_views.PDFUploadAPITests

# Run specific test method
python run_tests.py ingestion.tests.test_views.PDFUploadAPITests.test_upload_pdf_success
```

**Using Django's test command directly:**
```bash
cd backend
python manage.py test
python manage.py test ingestion.tests
python manage.py test ingestion.tests.test_views.PDFUploadAPITests
```

#### Test Coverage

| Module | Test Files | Test Count | Coverage Areas |
|--------|-----------|------------|----------------|
| **Ingestion** | 3 files | 20+ tests | PDF upload, table extraction, text extraction, chunking |
| **Retriever** | 3 files | 15+ tests | Query processing, evaluation metrics, filtering |
| **Total** | 6 files | 35+ tests | Full API and service layer coverage |

#### Key Test Features

- **Modular Organization**: Tests split into focused files (<300 lines each)
- **Comprehensive Mocking**: External services (Azure OpenAI, ChromaDB) properly mocked
- **API Testing**: Complete coverage of REST endpoints
- **Service Testing**: Unit tests for core business logic
- **Utility Testing**: Tests for helper functions and utilities
- **Colored Output**: Easy-to-read test results with visual indicators

#### Testing Documentation

For detailed testing information, see:
- **TESTING_GUIDE.md**: Complete beginner's guide to testing concepts and practices
- **TESTING_QUICK_REFERENCE.md**: Command reference and troubleshooting
- **HOW_TO_ADD_YOUR_OWN_TESTS.md**: Step-by-step guide for writing new tests

#### Example Test Output

```
============================================================
                   RAG Module Test Runner
============================================================

Running: All Tests
Command: python.exe manage.py test --verbosity=1 --keepdb
Found 35 test(s).
Using existing test database for alias 'default'...
...................................
--------------------------------------------------------------
Ran 35 tests in 0.245s

OK
Preserving test database for alias 'default'...

============================================================
✅ All tests passed!
============================================================
```

---

## ⚙️ Configuration

### Environment Variables (.env)

#### Azure OpenAI Configuration
```ini
# Azure OpenAI Endpoint
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Azure OpenAI API Key
AZURE_OPENAI_KEY=your-api-key-here

# Deployment Names
AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS=text-embedding-ada-002
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-35-turbo  # or gpt-4

# API Versions
AZURE_OPENAI_TEXT_VERSION=2023-05-15
AZURE_OPENAI_CHAT_API_VERSION=2023-05-15
```

#### Django Configuration
```ini
# Django Secret Key (generate unique)
DJANGO_SECRET_KEY=django-insecure-your-secret-key-here

# Debug Mode (False for production)
DEBUG=False

# Allowed Hosts (comma-separated)
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### Application Configuration
```ini
# API Base URL
API_BASE=http://localhost:8000

# Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# ChromaDB Telemetry (disable for privacy)
ANONYMIZED_TELEMETRY=False
```

### Django Settings Customization

#### CORS Configuration (`backend/settings.py`)
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8501",  # Ingestion UI
    "http://localhost:8502",  # Retrieval UI
]
```

#### Media Files Configuration
```python
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
```

#### Logging Configuration
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/app.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

---

## 🚀 Advanced Features

### 1. Premium Calculator - Mixed Age Format Support

The premium calculator intelligently handles different age formats within the same workbook:

#### Format 1: Exact Ages
```
| Age Band | 5L  | 10L  | 25L   |
|----------|-----|------|-------|
| 18       | 687 | 1275 | 2580  |
| 19       | 687 | 1275 | 2580  |
| 20       | 687 | 1275 | 2580  |
```

#### Format 2: Age Bands
```
| Age Band | 5L    | 10L   | 25L    |
|----------|-------|-------|--------|
| 18-25    | 6887  | 12750 | 25803  |
| 26-30    | 7200  | 13500 | 27500  |
| 31-35    | 7800  | 14800 | 30200  |
```

**Automatic Detection**: The system detects which format each sheet uses and applies appropriate matching logic.

### 2. Semantic Chunking Algorithm

Custom semantic chunking using cosine similarity:

```python
# Simplified pseudocode
for each sentence in document:
    calculate_embedding(sentence)
    if cosine_similarity(current_chunk, sentence) < threshold:
        create_new_chunk()
    else:
        append_to_current_chunk(sentence)
```

**Benefits**:
- Context-aware chunk boundaries
- Improved retrieval relevance
- Better semantic coherence

### 3. Real-Time Evaluation Metrics

#### Term Coverage
Measures what percentage of query terms appear in retrieved documents:
```python
term_coverage = len(covered_terms) / len(query_terms)
```

#### Query Coverage
Evaluates how well results cover the query intent:
```python
query_coverage = sum(term_frequencies) / len(query_terms)
```

#### Diversity
Measures result variety to avoid redundancy:
```python
diversity = 1 - (avg_pairwise_similarity)
```

#### Semantic Similarity
Cosine similarity between query and each result:
```python
similarity = cosine_similarity(query_embedding, result_embedding)
```

### 4. Conversation Memory

Context-aware follow-up queries using conversation history:

```python
# Example conversation flow
User: "What is the waiting period?"
Agent: "The waiting period is 30 days for illness and 90 days for pre-existing conditions."

User: "What about maternity?"  # System understands context
Agent: "For maternity benefits, there is a waiting period of 9 months from policy inception."
```

### 5. Product Comparison with Premium Integration

Automatic premium calculation for multi-product comparison:

```python
comparison_agent.compare_with_premium_calculation(
    query="Compare ActivAssure and ActivFit for family of 4",
    product_names=["ActivAssure", "ActivFit"],
    premium_params={
        'policy_type': 'family_floater',
        'members': [{'age': 35}, {'age': 33}, {'age': 7}, {'age': 5}],
        'sum_insured': 1000000
    }
)
```

**Output**: Side-by-side comparison with calculated premiums for both products.

---

## 🐛 Troubleshooting

### Common Issues & Solutions

#### 1. Django Server Won't Start

**Symptoms**:
- "Port 8000 is already in use"
- "ModuleNotFoundError"
- Import errors

**Solutions**:
```bash
# Check if port is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # macOS/Linux

# Kill process using port
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # macOS/Linux

# Verify virtual environment
which python                   # Should point to venv
pip list                       # Check installed packages

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 2. Streamlit Connection Errors

**Symptoms**:
- "Connection refused to http://localhost:8000"
- "CORS policy blocked"

**Solutions**:
```python
# Check Django CORS settings (backend/settings.py)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "http://localhost:8502",
]

# Verify Django is running
curl http://localhost:8000/api/  # Should return API response

# Check API_BASE in .env
API_BASE=http://localhost:8000  # No trailing slash
```

#### 3. Azure OpenAI Errors

**Symptoms**:
- "Invalid API key"
- "Deployment not found"
- "Rate limit exceeded"

**Solutions**:
```bash
# Verify credentials in .env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=<your-key>

# Check deployment names
az cognitiveservices account deployment list \
  --name <your-resource-name> \
  --resource-group <your-rg>

# Monitor quota
# Azure Portal → Your Resource → Quotas

# Implement retry logic (already included)
# Check logs/app.log for details
```

#### 4. ChromaDB Issues

**Symptoms**:
- "Collection not found"
- "Dimension mismatch"
- "PersistentClient error"

**Solutions**:
```bash
# Clear ChromaDB cache
rm -rf media/output/chroma_db/*  # ⚠️ Deletes all data

# Check directory permissions
ls -la media/output/chroma_db/

# Verify embedding model
# Ensure AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS matches actual deployment

# Check ChromaDB version compatibility
pip show chromadb
```

#### 5. PDF Processing Errors

**Symptoms**:
- "No tables found" (when tables exist)
- Garbled text extraction
- Encoding errors

**Solutions**:
```python
# Verify PDF is not scanned image
# Use OCR for scanned documents (not included in this version)

# Check pdfplumber installation
pip install --upgrade pdfplumber

# Adjust table detection settings
# Edit backend/ingestion/utils.py:
table_settings = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "min_words_vertical": 3,
    "min_words_horizontal": 1,
}
```

#### 6. Memory Issues with Large Documents

**Symptoms**:
- "MemoryError"
- Process killed
- Slow processing

**Solutions**:
```bash
# Increase available memory
# Reduce batch size in chunking

# Process documents in smaller batches
# Split large PDFs into sections

# Monitor memory usage
top              # macOS/Linux
Task Manager     # Windows
```

### Debug Mode

Enable comprehensive logging:

```python
# .env file
DEBUG=True
LOG_LEVEL=DEBUG

# Check logs
tail -f backend/logs/app.log  # macOS/Linux
Get-Content backend/logs/app.log -Wait  # PowerShell
```

### Health Check Commands

```bash
# Django health check
python backend/manage.py check

# Test database
python backend/manage.py showmigrations

# Test imports
python -c "import chromadb, langchain, pdfplumber, pandas; print('OK')"

# Test Azure OpenAI connection
python -c "
from langchain_openai import AzureOpenAIEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()
embeddings = AzureOpenAIEmbeddings()
result = embeddings.embed_query('test')
print(f'Embedding dimension: {len(result)}')
"
```

---

## 💻 Development Guidelines

### Code Style

- **Backend**: Follow Django best practices and PEP 8
- **Frontend**: Streamlit conventions
- **Docstrings**: Google style docstrings
- **Type Hints**: Use for function signatures

### Adding New Features

#### 1. New Agent
```python
# backend/agents/my_agent.py
class MyCustomAgent:
    def __init__(self):
        # Initialize agent
        pass
    
    def process_query(self, query: str) -> Dict[str, Any]:
        # Agent logic
        return {"answer": "..."}

# Register in orchestrator.py
def route_query(self, query: str):
    if self._is_my_agent_query(query):
        return {"agent": "my_custom_agent", "intent": "custom_intent"}
```

#### 2. New API Endpoint
```python
# backend/my_app/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def my_endpoint(request):
    data = request.data
    result = process_data(data)
    return Response(result, status=200)

# backend/my_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('my-endpoint/', views.my_endpoint, name='my_endpoint'),
]
```

#### 3. New UI Component
```python
# frontend/components/my_component.py
import streamlit as st

def render_my_component(data):
    """Render custom UI component."""
    st.subheader("My Component")
    st.write(data)
    
    if st.button("Action"):
        # Handle action
        pass
```

### Testing

```bash
# Unit tests (add pytest)
pip install pytest pytest-django

# Create tests
# backend/agents/tests/test_calculator.py
import pytest
from agents.calculators import PremiumCalculator

def test_premium_calculation():
    calc = PremiumCalculator(doc_name="ActivAssure")
    result = calc.calculate_premium(
        policy_type="family_floater",
        members=[{'age': 35}, {'age': 33}],
        sum_insured=1000000
    )
    assert result['total_premium'] > 0

# Run tests
pytest backend/
```

---

## ⚡ Performance Optimization

### Caching Strategies

#### 1. Streamlit Caching
```python
@st.cache_resource
def get_cached_chunker_embedder(chroma_db_dir, output_dir, doc_type, doc_name):
    """Cached embedding function to avoid repeated API calls."""
    # Already implemented in ingestion_run.py
    pass
```

#### 2. ChromaDB Query Optimization
```python
# Use appropriate k value
results = collection.query(
    query_embeddings=embedding,
    n_results=5,  # Don't fetch more than needed
    include=["documents", "metadatas", "distances"]
)
```

#### 3. Premium Calculator Registry
```python
# Calculator automatically caches workbook parsing
calculator = PremiumCalculator(doc_name="ActivAssure")
# Subsequent calls use cached parsed data
```

### Batch Processing

```python
# Process multiple documents efficiently
for pdf_file in pdf_files:
    pipeline.extract_tables(pdf_file)
    pipeline.extract_text(pdf_file)
# Batch embed at the end
pipeline.chunk_and_embed_batch(all_documents)
```

### Database Optimization

```sql
-- Add indexes for faster queries (if using PostgreSQL)
CREATE INDEX idx_doc_type ON embeddings(doc_type);
CREATE INDEX idx_product ON embeddings(product_name);
```

---

## 🔒 Security

### Best Practices

1. **Environment Variables**: Never commit `.env` file
```bash
# .gitignore
.env
*.key
*.pem
```

2. **API Key Rotation**: Regularly rotate Azure OpenAI keys
```bash
# Azure Portal → Your Resource → Keys and Endpoint → Regenerate
```

3. **CORS Configuration**: Restrict to known origins
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "http://localhost:8502",
    # Add production URLs
]
```

4. **Input Validation**: Validate all user inputs
```python
# Example in views.py
if not query or len(query) > 1000:
    return Response({"error": "Invalid query"}, status=400)
```

5. **Rate Limiting**: Implement rate limiting for production
```bash
pip install django-ratelimit
```

### Production Deployment

#### Use PostgreSQL instead of SQLite
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'rag_db',
        'USER': 'db_user',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

#### Use Gunicorn for Django
```bash
pip install gunicorn
gunicorn backend.wsgi:application --bind 0.0.0.0:8000
```

#### Use Nginx as reverse proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE.txt](LICENSE.txt) for details.

```
MIT License

Copyright (c) 2025 [Your Organization]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 Support & Contact

### Getting Help

- **Email**: myuvaranjani@gmail.com
- **Issues**: Open an issue on GitHub repository
- **Documentation**: Check this README and PUBLICATION_GUIDE.md

### Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with clear commit messages
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit a pull request** with detailed description

### Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Error messages and stack traces
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs from `backend/logs/app.log`

---

## 🎓 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)

---

## 🙏 Acknowledgments

- **Azure OpenAI**: For providing enterprise-grade AI models
- **LangChain**: For the RAG framework and utilities
- **ChromaDB**: For vector database capabilities
- **Streamlit**: For rapid UI development
- **Django**: For robust backend framework

---

<div align="center">

**Built with ❤️ for the Insurance Industry**

[⬆ Back to Top](#-enterprise-insurance-rag-system)

</div>