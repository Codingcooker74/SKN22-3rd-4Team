# Development Guide

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit UI Layer                     │
│  (insights, graph_analysis, sql_query, home)            │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────┐
│                  Application Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Analyst Chat │  │ Report Gen   │  │ GraphRAG     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────┐
│                    Data Layer                            │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │ Finnhub API  │  │ Supabase DB  │                     │
│  └──────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

## 🔨 Adding New Features

### Adding a New UI Page

1. Create a new file in `src/ui/pages/`:

```python
# src/ui/pages/my_feature.py
import streamlit as st

def render():
    st.markdown("# My Feature")
    # Your implementation
```

1. Import and add to navigation in `app.py`.

### Adding a New Data Source

1. Create client in `src/data/`:

```python
# src/data/my_client.py
class MyClient:
    def fetch_data(self):
        # Implementation
        pass
```

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_graph_rag.py
```

## 📊 Database Schema (Supabase)

### Key Tables

- **companies**: Ticker, Name, Sector, Industry (UUID PK)
- **annual_reports**: Yearly financial data (Revenue, Net Income, etc.)
- **quarterly_reports**: Quarterly financial data
- **stock_prices**: Daily OHLCV data
- **company_relationships**: GraphRAG relationships
- **documents**: Text chunks for Vector Search (pgvector)
- **document_sections**: Parsed sections from filings

## 🔧 Configuration

### Environment Variables (.env)

```env
OPENAI_API_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...
FINNHUB_API_KEY=...
```

### Models Settings (`models/settings.py`)

- Manage LLM models (`gpt-4o`, `gpt-5-nano`) and embedding configurations.

## 📝 Code Style

- Follow **PEP 8**.
- Use **Type Hints** (`def func(a: int) -> str:`).
- Run `black src/` before committing.

## 🐛 Debugging

- Check stdout/stderr for application logs.
- Use `st.write()` or `st.sidebar.write()` for quick UI debugging.
- Logging is configured in `config/logging_config.py`.
