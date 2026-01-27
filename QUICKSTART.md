# Quick Start Guide

## 🚀 Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd SKN22-3rd-4Team
```

### 2. Create virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root directory:

```env
# OpenAI (Required for Chat & RAG)
OPENAI_API_KEY=sk-...

# Supabase (Required for Database & Vector Store)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Finnhub (Required for Real-time Data)
FINNHUB_API_KEY=your-finnhub-key
```

## 🎯 Running the Application

### Start the Streamlit web interface

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## 📊 Usage Workflow

### 1. Home

- View project overview and dashboard.
- Check service status (Database, API Connections).

### 2. Investment Insights (Core Feature)

- **Chat with AI Analyst**: Ask questions about market trends, specific companies, or financial metrics.
  - *Example*: "How is Apple's revenue growth compared to Microsoft?"
- **Generate Reports**: Select a ticker to generate a comprehensive investment report.
  - Reports analyze financials, market sentiment, and risks using `gpt-5-nano` (or fallback).
- **Competitor Analysis**: Automatically retrieve and compare competitor data.

### 3. Graph Analysis

- Visualize relationships between companies (Suppliers, Customers, Competitors).
- Explore supply chain dependencies interactively.

### 4. SQL Query

- Use natural language to query the internal financial database.
  - *Example*: "Show me top 5 companies by Operating Margin in 2023"

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_graph_rag.py
```

## 📝 Example Code

### Using Finnhub Client

```python
from src.data.finnhub_client import get_finnhub_client

client = get_finnhub_client()
quote = client.get_quote("AAPL")
print(f"Current Price: {quote['c']}")
```

### Generating a Report

```python
from src.rag.report_generator import ReportGenerator

generator = ReportGenerator()
report = generator.generate_report("NVDA")
print(report)
```
