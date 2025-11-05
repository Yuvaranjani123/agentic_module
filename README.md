# Advanced Dual-Agent RAG Platform for Insurance Document Intelligence

A comprehensive, modular RAG (Retrieval-Augmented Generation) system designed specifically for insurance document processing and intelligent query resolution. Built with Django REST Framework backend and Streamlit frontend, featuring dual-agent architecture (Traditional + ReAct), deterministic premium calculations, and advanced document comparison capabilities.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40.2-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)

---

## 🎯 Quick Overview

**Two Cognitive Approaches, One Platform:**

| Approach | Speed | Best For | Architecture |
|----------|-------|----------|--------------|
| **Traditional Orchestrator** | ~3-5s | Simple queries, quick answers | Single-step routing |
| **ReAct Agentic** | ~5-15s | Complex reasoning, multi-step | Thought→Action→Observation loop |

**Example Query**: *"Calculate premium for 2 adults aged 32, 45 with ₹10L coverage"*
- **Traditional**: Routes to Premium Calculator → Returns answer (3s)
- **ReAct**: Analyzes query → Identifies needed tools → Calls calculator → Validates → Returns structured answer (8s)

---

## ✨ Key Features

- 🤖 **Dual-Agent System**: Choose speed vs depth
- 🧮 **Smart Premium Calculator**: Excel-based with 15+ configurations
- 📊 **Multi-Product Comparison**: Side-by-side policy analysis
- 🔍 **Advanced Document Search**: Semantic chunking + ChromaDB
- 📈 **Real-Time Evaluation**: 3D quality metrics (coverage, similarity, diversity)
- ✅ **35+ Test Cases**: Comprehensive testing across 6 modules

---

## 🏗️ Architecture

### Dual-Agent System Architecture

The system offers **two complementary query execution paths**, each optimized for different use cases:

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                                │
│  ┌────────────────────┐  ┌────────────────────┐  ┌───────────────┐  │
│  │  Ingestion UI      │  │  Traditional UI    │  │  ReAct UI     │  │
│  │  (Streamlit)       │  │  (Streamlit)       │  │  (Streamlit)  │  │
│  │  Port: 8501        │  │  Port: 8502        │  │  Port: 8503   │  │
│  └──────────┬─────────┘  └─────────┬──────────┘  └───────┬───────┘  │
└─────────────┼────────────────────────┼──────────────────────┼─────────┘
              │                        │                      │
              │          HTTP REST API                        │
              │                        │                      │
┌─────────────┴────────────────────────┴──────────────────────┴─────────┐
│                      Django Backend (Port: 8000)                       │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │            TWO INDEPENDENT QUERY SYSTEMS                        │  │
│  ├─────────────────────────────────┬───────────────────────────────┤  │
│  │  SYSTEM 1:                      │    SYSTEM 2:                  │  │
│  │  Traditional Orchestrator       │    ReAct Agentic System       │  │
│  │  (/agents/query/)               │    (/agents/agentic/query/)   │  │
│  ├─────────────────────────────────┼───────────────────────────────┤  │
│  │  • Single-step routing          │    • Iterative reasoning      │  │
│  │  • Intent classification        │    • Thought→Action→Observe   │  │
│  │  • ONE agent per query          │    • Multi-tool chaining      │  │
│  │  • Fast (3-5s)                  │    • Comprehensive (5-15s)    │  │
│  │  • Direct agent selection       │    • Dynamic tool selection   │  │
│  │                                 │    • Learning classifier      │  │
│  └───┬──────────────┬──────────┬───┴─────┬─────────────────────────┘  │
│      │              │          │         │                             │
│  ┌───▼──────┐  ┌───▼──────┐ ┌▼─────┐ ┌─▼───────────────────────┐    │
│  │Retrieval │  │ Premium  │ │Compar│ │  ReAct Agent + Tools    │    │
│  │  Agent   │  │Calculator│ │ison  │ │  (Dynamic Reasoning     │    │
│  │          │  │  Agent   │ │Agent │ │   with Learning)        │    │
│  └──────────┘  └──────────┘ └──────┘ └─────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  Service Layer (Shared)                       │  │
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
    │  • Reasoning LLM     │        │  • Metadata Filter  │
    └──────────────────────┘        └─────────────────────┘
```

### 🎯 System Comparison

| Feature | Traditional Orchestrator | ReAct Agentic System |
|---------|-------------------------|----------------------|
| **Query Complexity** | Simple, single-objective | Complex, multi-step |
| **Execution Pattern** | One-shot routing | Iterative reasoning loop |
| **Tool Usage** | ONE tool per query | MULTIPLE tools chained |
| **LLM Invocations** | 1-2 calls | 3-10+ calls |
| **Response Time** | 3-5 seconds | 5-15 seconds |
| **Transparency** | Intent + Result | Full reasoning trace |
| **Learning Capability** | Static classification | Pattern learning enabled |
| **Best For** | Standard Q&A, calculations | Multi-step workflows |
| **Interface** | Port 8502 | Port 8503 |

### 📊 When to Use Each System

**Use Traditional Orchestrator (/agents/query/) when:**
- ✅ Query has single, clear objective
- ✅ Speed is priority
- ✅ Standard document Q&A
- ✅ Simple premium calculations
- ✅ Direct product comparisons

**Use ReAct Agentic System (/agents/agentic/query/) when:**
- 🤖 Query requires multiple sequential steps
- 🤖 Need to chain tools together
- 🤖 Want visibility into reasoning process
- 🤖 Complex decision-making with conditional logic
- 🤖 Exploratory analysis across multiple data sources

### 🔄 ReAct Iterative Reasoning Flow

```
Query: "Calculate premium for age 35, then compare with ActivFit"

Iteration 1:
  💭 THOUGHT: "I need to calculate premium first"
  🔧 ACTION: premium_calculator(age=35, sum_insured=500000)
  👁️ OBSERVATION: "Premium calculated: ₹15,000"

Iteration 2:
  💭 THOUGHT: "Now I need ActivFit premium for comparison"
  🔧 ACTION: document_retriever(query="ActivFit premium age 35", k=3)
  👁️ OBSERVATION: "ActivFit: ₹12,000 for age 35"

Iteration 3:
  💭 THOUGHT: "I have both results, can provide comparison"
  🔧 ACTION: finish
  ✅ FINAL_ANSWER: "Your premium: ₹15,000. ActivFit is ₹3,000 cheaper at ₹12,000."

Metadata: 3 iterations, 2 tools used, 8.7s execution time
```

---

## 🛠️ Technology Stack

### Backend Technologies
- **Framework**: Django 5.1.4 with Django REST Framework 3.15.2
- **Database**: SQLite (development) / PostgreSQL-compatible (scalable deployment)
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

- **Python 3.11+**, 8GB+ RAM recommended
- **Azure OpenAI**: Embedding & chat model deployments with API keys
- **Git** and modern browser for Streamlit UIs

---

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/Yuvaranjani123/rag_module_1.git
cd rag_module_1
python -m venv venv
venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate  # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# 4. Setup database
cd backend
python manage.py migrate
cd ..
```

**Key Environment Variables** (in `.env`):
```ini
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS=text-embedding-ada-002
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-35-turbo
DJANGO_SECRET_KEY=generate-using-django-command
API_BASE=http://localhost:8000
```

---

## 🏃 Usage Guide

### Start Services

```bash
# Terminal 1: Backend API
cd backend
python manage.py runserver  # http://localhost:8000

# Terminal 2: Document Ingestion
streamlit run frontend/ingestion_run.py --server.port 8501

# Terminal 3: Traditional Query Interface (Fast, 3-5s)
streamlit run frontend/retrieval_run.py --server.port 8502

# Terminal 4: ReAct Agentic Interface (Comprehensive, 5-15s)
streamlit run frontend/agentic_run.py --server.port 8503
```

### Choose Your Interface

| Interface | Port | Purpose | Use When |
|-----------|------|---------|----------|
| **Ingestion** | 8501 | Upload & process PDFs/Excel | Setting up document collections |
| **Traditional** | 8502 | Fast single-objective queries | "What is covered?", "Calculate premium" |
| **ReAct Agent** | 8503 | Complex multi-step reasoning | "Calculate, compare, recommend best" |

**Example Workflows:**

**Traditional (Port 8502)** - Single objective:
```
"What is the maternity coverage in ActivAssure?"
→ Direct retrieval → Answer in 3-5s
```

**ReAct Agent (Port 8503)** - Multi-step:
```
"Calculate premium for age 35, then compare with ActivFit"
→ Iteration 1: Calculate premium → ₹15,000
→ Iteration 2: Query ActivFit → ₹12,000
→ Final: "ActivFit is ₹3,000 cheaper"
Total time: 8s, 2 iterations
```

---


## 📡 API Endpoints (Summary)

**Base URL**: `http://localhost:8000`

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|  
| `/agents/query/` | POST | Traditional orchestrator (fast, single-step) |
| `/agents/agentic/query/` | POST | ReAct agent (multi-step reasoning) |
| `/ingestion/upload/` | POST | Upload PDF documents |
| `/ingestion/collections/` | GET | List document collections |
| `/retriever/query/` | POST | Direct document retrieval |

**Example Request (Traditional)**:
```json
POST /agents/query/
{
  "query": "What is maternity coverage?",
  "collection_name": "ActivAssure",
  "k": 3
}
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

The project includes a robust testing infrastructure with 35+ test cases covering ingestion, retrieval, and agent modules. All tests are organized in a modular structure with files under 500 lines for maintainability.

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

## 📊 Performance Benchmarks

### Comprehensive Performance Metrics

| Component | Metric | Value | Notes |
|-----------|--------|-------|-------|
| **Document Ingestion** ||||
| Table Extraction | Speed | 30-45s/page | PDF complexity dependent |
| Table Extraction | Accuracy | 85-90% | Manual review recommended for complex tables |
| Text Extraction | Speed | 10-15s/page | Excluding tables |
| Semantic Chunking | Duration | 8-15 minutes | For 25-page document |
| Embedding Generation | Duration | 2-3 minutes | ChromaDB insert included |
| **Full Pipeline** | **Total Time** | **15-20 minutes** | Complete document processing |
| **Query Performance** ||||
| Traditional Orchestrator | Average | 3.5 seconds | Single-step retrieval |
| Traditional Orchestrator | P95 | 5 seconds | 95th percentile |
| ReAct (Simple Query) | Average | 6 seconds | 2-3 tool calls |
| ReAct (Simple Query) | P95 | 10 seconds | 95th percentile |
| ReAct (Complex Query) | Average | 12 seconds | 4-5 tool calls, multi-step reasoning |
| ReAct (Complex Query) | P95 | 15 seconds | 95th percentile |
| **Quality Metrics** ||||
| Test Coverage | Test Cases | 35+ tests | Across 13 test classes |
| Test Coverage | Modules | 6 modules | Ingestion, retrieval, agents |
| Evaluation Metrics | Dimensions | 3D assessment | Term coverage, similarity, diversity |
| Intent Classification | Accuracy | High | Pattern-based with learning capability |

**Performance Notes:**
- ReAct system is intentionally slower due to multi-step reasoning (provides more comprehensive answers)
- Semantic chunking overhead is offset by improved retrieval quality
- Table detection accuracy improves with well-structured PDFs

---

## ⚠️ Known Limitations

### Technical Limitations

**1. ReAct Agent Constraints**
- Maximum 10 reasoning iterations per query (prevents infinite loops)
- Complex multi-product comparisons may require iteration limit tuning
- No conversation history persistence across sessions

**2. Document Processing**
- Table detection accuracy: 85-90% (not 100%)
  - Complex nested tables may require manual review
  - Merged cells and irregular layouts can affect extraction
- PDF format requirements: Text-based PDFs only (no scanned images without OCR)
- Semantic chunking overhead: 8-15 minutes for large documents

**3. Query Processing**
- Query length limit: 1000 characters (enforced in API)
- Single language support: English only (embeddings and LLM optimized for English)
- Intent classification: Pattern-based, may misclassify edge cases
- Token context window: Limited by Azure OpenAI model (gpt-4/gpt-35-turbo limits)

**4. Data & Storage**
- ChromaDB: Single instance, not distributed (limited scalability)
- SQLite: Development database only, not suitable for high-concurrency scenarios
- Embedding storage: Grows linearly with document corpus size
- No automatic document versioning or update detection

---

### Performance Limitations

**1. Response Time Trade-offs**
- ReAct system 2-4x slower than Traditional (by design for thorough reasoning)
- Semantic chunking adds 8-15 minutes to ingestion pipeline
- Azure OpenAI API latency dependent on service region and load

**2. Concurrent Processing**
- Single-instance deployment limits concurrent request handling
- No built-in queue management for multiple simultaneous ingestions
- ChromaDB write operations are blocking

**3. Rate Limits**
- Azure OpenAI quota restrictions apply (Tokens Per Minute, Requests Per Minute)
- Embedding API calls rate-limited by Azure subscription tier
- No built-in retry logic for rate limit errors

---

### Deployment Limitations

**1. Infrastructure Dependencies**
- Azure OpenAI subscription required (vendor lock-in)
- Active internet connection needed for all LLM operations
- No offline mode or local LLM fallback

**2. Scalability Constraints**
- SQLite: Single-file database, not suitable for distributed deployment
- ChromaDB: File-based storage, requires shared filesystem for horizontal scaling
- No built-in load balancing or service discovery

**3. Security & Access Control**
- No built-in user authentication or authorization system
- No role-based access control (RBAC) for documents or features
- API endpoints not secured by default (requires additional implementation)
- No audit logging for compliance requirements

**4. Monitoring & Observability**
- Limited built-in logging and monitoring
- No distributed tracing across components
- No performance metrics dashboard (beyond Streamlit UI metrics)
- Manual log file analysis required for troubleshooting

---

### Functional Limitations

**1. Document Support**
- PDF only (no Word, Excel, or other formats for ingestion)
- Premium calculator Excel format specific to ActivAssure structure
- No automatic document format detection or conversion

**2. Multi-tenancy**
- No built-in support for multiple organizations or user isolation
- ChromaDB collections not segregated by user/tenant
- Shared embedding space across all documents

**3. Advanced Features Not Included**
- No document update/versioning system
- No incremental indexing (full re-ingestion required)
- No multi-language support
- No image/chart extraction from PDFs
- No automated document quality scoring
- No feedback loop for improving intent classification

---

## 🔒 Security

**Key practices:**
- Environment variables for sensitive credentials
- CORS configuration for API security
- Input validation on all endpoints

**📖 For security details**: [See Full Publication - Section 8](INSURANCE_RAG_PUBLICATION.md#8-security-best-practices)

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
- **Documentation**: Check this README.md

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
