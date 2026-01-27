# API Reference

## Data Layer

### Finnhub MCP Server (Tools)

`src.tools.finnhub_server`

Implements Model Context Protocol (MCP) tools for real-time market data.

**Run Server:**

```bash
python src/tools/finnhub_server.py
```

#### Available Tools

- **`get_stock_quote(symbol)`**: Returns real-time price info (c, h, l, o, pc).
  - *Example Return*: `{"current_price": 150.5, "change": 2.1, ...}`
- **`get_company_profile(symbol)`**: Returns industry, market cap, and IPO details.
- **`get_price_target(symbol)`**: Returns analyst consensus and price targets.
- **`get_company_news(symbol, from_date, to)`**: Fetches company-specific news.
- **`get_market_news(category)`**: Fetches general market news.

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
# Ticker is automatically detected from the query
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
