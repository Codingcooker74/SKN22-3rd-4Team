# Financial Analysis & Investment Insights Bot - Project Structure

## 📁 Complete Directory Structure

```text
SKN22-3rd-4Team/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables
├── .gitignore                     # Git ignore rules
├── README.md                      # Project documentation
├── QUICKSTART.md                  # Quick start guide
├── STRUCTURE.md                   # This file
├── API.md                         # API reference
├── DEVELOPMENT.md                 # Development guide
├── PROJECT_SUMMARY.md             # Project summary
├── PULL_REQUEST.md                 # PR document (Korean)
│
├── config/                        # Configuration files
│   └── settings.py               # Application settings (General)
│
├── models/                        # Model settings
│   └── settings.py               # AI Model configurations (LLM, Embeddings)
│
├── src/                          # Source code
│   ├── data/                     # Data Access Layer
│   │   ├── finnhub_client.py    # Finnhub API Client (Market/Financial Data)
│   │   ├── supabase_client.py   # Supabase DB Client
│   │   └── filing_processor.py   # SEC Filing Processor
│   │
│   ├── rag/                      # RAG & AI Logic
│   │   ├── rag_base.py          # [NEW] RAG 모듈 공통 베이스 클래스
│   │   ├── chat_tools.py        # [NEW] 챗봇용 도구(Tools) 정의
│   │   ├── analyst_chat.py      # Investment Analyst Chatbot Logic
│   │   ├── data_retriever.py    # Parallel Data Fetching Module (Optimization)
│   │   ├── graph_rag.py         # GraphRAG Implementation
│   │   ├── report_generator.py  # Investment Report Generator
│   │   └── vector_store.py      # Vector Store Operations
│   │
│   ├── sql/                      # SQL Generation
│   │   └── text_to_sql.py       # NL to SQL
│   │
│   ├── ui/                       # Streamlit UI
│   │   └── pages/               
│   │       ├── home.py          # Dashboard home
│   │       ├── insights.py      # Main Analysis & Chat Interface
│   │       └── report_page.py   # Standalone Report Generator
│   │
│   └── utils/                    # Utilities
│
├── scripts/                      # Utility scripts
└── notebooks/                   # Jupyter notebooks
```

## 🔧 Module Descriptions

### Core & Configuration

#### `models/settings.py`

- Centralized configuration for AI models (LLMs, Embeddings).
- Manages API keys and model parameters.

### Data Layer (`src/data`)

#### `finnhub_client.py`

- Handles communication with Finnhub API.
- Retrieves stock quotes, company profiles, news, and financial metrics.

#### `supabase_client.py`

- Manages connection to Supabase PostgreSQL.
- Handles data retrieval for companies and financial reports.

#### `filing_processor.py`

- Processes and parses SEC filings (10-K, 10-Q) into structured data.

### RAG Layer (`src/rag`)

#### `analyst_chat.py`

- Implements the "AI Financial Analyst" chatbot.
- Contextualizes user queries with RAG (Retrieval Augmented Generation).
- Integrates real-time data from Finnhub with tool calling.

#### `report_generator.py`

- Generates structured investment reports using `gpt-4.1-mini`.
- Combines database financials and real-time market data.

#### `graph_rag.py`

- Implements Graph Retrieval Augmented Generation.
- Analyzes relationships between companies (supply chain, competitors).

#### `vector_store.py`

- Manages semantic search functionality using Supabase pgvector.

#### `data_retriever.py`

- Orchestrates parallel data fetching from Supabase, GraphRAG, VectorStore, and Finnhub.
- Significantly reduces latency for AI responses and report generation.

#### `rag_base.py`

- Base class for all RAG-related modules.
- Centralizes client initialization (OpenAI, Supabase, Finnhub) and configuration.

#### `chat_tools.py`

- Defines the JSON structure and metadata for all chatbot tools.
- Separates tool definitions from the core chatbot logic for better maintainability.

### UI Layer (`src/ui`)

#### `insights.py`

- The core interaction page for users.
- Hosting the Chatbot and Report Generator interfaces.
- Features automatic ticker detection from natural language queries.

#### `report_page.py`

- A dedicated page for generating and viewing financial reports.
