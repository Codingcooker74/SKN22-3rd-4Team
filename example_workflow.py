"""
Example Workflow: AI Financial Analyst Report Generation
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

try:
    from rag.report_generator import ReportGenerator
    from data.finnhub_client import get_finnhub_client
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please make sure you are running this script from the project root.")
    sys.exit(1)


def main():
    # Load environment variables
    load_dotenv()

    # Check API Keys
    if not os.getenv("FINNHUB_API_KEY"):
        print("❌ Error: FINNHUB_API_KEY not found in .env")
        return
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in .env")
        return

    ticker = "AAPL"
    print(f"🚀 Starting analysis for {ticker}...")

    # 1. Get Real-time Data
    print("\nfetching real-time data...")
    client = get_finnhub_client()
    try:
        quote = client.get_quote(ticker)
        print(f"Current Price: ${quote.get('c', 'N/A')}")
        print(f"High: ${quote.get('h', 'N/A')}")
        print(f"Low: ${quote.get('l', 'N/A')}")
    except Exception as e:
        print(f"Error fetching data: {e}")

    # 2. Generate Report
    print(f"\nGenerating AI Investment Report for {ticker}...")
    print("(This uses gpt-5-nano with automatic fallback to gpt-4o-mini)")

    try:
        generator = ReportGenerator()
        report = generator.generate_report(ticker)

        print("\n" + "=" * 50)
        print(report)
        print("=" * 50)

    except Exception as e:
        print(f"Error generating report: {e}")


if __name__ == "__main__":
    main()
