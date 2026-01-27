# API Reference

## Data Layer

### Finnhub Client

`src.data.finnhub_client.FinnhubClient`

Handles interaction with Finnhub API for real-time market data.

```python
from src.data.finnhub_client import get_finnhub_client

client = get_finnhub_client()
```

#### Key Methods

- `get_quote(symbol: str) -> dict`: Get real-time price data (Open, High, Low, Close).
- `get_company_profile(symbol: str) -> dict`: Get company metadata (Sector, Market Cap).
- `get_company_news(symbol: str, ...) -> list`: Get recent market news.
- `get_financial_metrics(symbol: str) -> dict`: Get basic financial ratios.

### Supabase Client

`src.data.supabase_client.SupabaseClient`

Manages database connections and vector store operations.

---

## AI & RAG Layer

### Analyst Chatbot

`src.rag.analyst_chat.AnalystChatbot`

Intelligent agent for financial analysis conversation.

```python
from src.rag.analyst_chat import AnalystChatbot

bot = AnalystChatbot()
response = bot.chat("How is Apple doing?")
```

### Report Generator

`src.rag.report_generator.ReportGenerator`

Generates comprehensive investment reports.

```python
from src.rag.report_generator import ReportGenerator

gen = ReportGenerator()
report = gen.generate_report("NVDA")
```

#### Features

- **Automatic Fallback**: Tries `gpt-5-nano` first, falls back to `gpt-4o-mini` on error.
- **Context Integration**: Combines internal DB financials with external market data.

### GraphRAG

`src.rag.graph_rag.GraphRAG`

Analyzes corporate relationships.

---

## SQL Layer

### Text-to-SQL

`src.sql.text_to_sql.TextToSQL`

Converts natural language questions into SQL queries for the financial database.
