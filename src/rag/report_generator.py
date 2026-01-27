"""
Report Generator - 구조화된 투자 분석 레포트 생성
Uses gpt-5-nano
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

# Import Finnhub client
try:
    from data.finnhub_client import get_finnhub_client

    FINNHUB_AVAILABLE = True
except ImportError:
    FINNHUB_AVAILABLE = False

load_dotenv()

logger = logging.getLogger(__name__)

# Prompts directory
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class ReportGenerator:
    """
    투자 분석 레포트 생성기
    gpt-5-nano 사용
    """

    def __init__(self):
        """Initialize report generator"""

        # OpenAI client
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 필요합니다.")

        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.model = "gpt-4.1-mini"  # 레포트용 모델
        self.embedding_model = "text-embedding-3-small"

        # Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL과 SUPABASE_KEY 환경 변수가 필요합니다.")

        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Finnhub client for real-time data
        self.finnhub = None
        if FINNHUB_AVAILABLE:
            try:
                self.finnhub = get_finnhub_client()
                if not self.finnhub.api_key:
                    self.finnhub = None
            except Exception as e:
                logger.warning(f"Finnhub init failed: {e}")

        # Load system prompt
        self.system_prompt = self._load_prompt("report_generator.txt")

        logger.info("ReportGenerator initialized")

    def _load_prompt(self, filename: str) -> str:
        """Load system prompt from file"""
        prompt_path = PROMPTS_DIR / filename
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt file not found: {prompt_path}")
            return "당신은 투자 리서치 보고서를 작성하는 전문 애널리스트입니다."

    def _get_company_data(self, ticker: str) -> Dict:
        """Get all available company data"""
        data = {
            "company": None,
            "annual_reports": [],
            "quarterly_reports": [],
            "relationships": [],
            "stock_prices": [],
        }

        try:
            # Company info
            result = (
                self.supabase.table("companies")
                .select("*")
                .eq("ticker", ticker.upper())
                .execute()
            )
            if result.data:
                data["company"] = result.data[0]
                company_id = result.data[0].get("id")

                # Annual reports
                annual = (
                    self.supabase.table("annual_reports")
                    .select("*")
                    .eq("company_id", company_id)
                    .order("fiscal_year", desc=True)
                    .limit(3)
                    .execute()
                )
                data["annual_reports"] = annual.data or []

                # Quarterly reports
                quarterly = (
                    self.supabase.table("quarterly_reports")
                    .select("*")
                    .eq("company_id", company_id)
                    .order("fiscal_year", desc=True)
                    .order("fiscal_quarter", desc=True)
                    .limit(4)
                    .execute()
                )
                data["quarterly_reports"] = quarterly.data or []

                # Stock prices
                prices = (
                    self.supabase.table("stock_prices")
                    .select("*")
                    .eq("company_id", company_id)
                    .order("price_date", desc=True)
                    .limit(5)
                    .execute()
                )
                data["stock_prices"] = prices.data or []

            # Relationships
            outgoing = (
                self.supabase.table("company_relationships")
                .select("*")
                .eq("source_ticker", ticker.upper())
                .execute()
            )
            incoming = (
                self.supabase.table("company_relationships")
                .select("*")
                .eq("target_ticker", ticker.upper())
                .execute()
            )
            data["relationships"] = (outgoing.data or []) + (incoming.data or [])

        except Exception as e:
            logger.error(f"Error fetching company data: {e}")

        return data

    def _format_data_context(self, data: Dict) -> str:
        """Format company data into context string"""
        parts = []

        company = data.get("company")
        if company:
            parts.append(f"## 기업 개요")
            parts.append(f"- 회사명: {company.get('company_name', 'N/A')}")
            parts.append(f"- 티커: {company.get('ticker', 'N/A')}")
            parts.append(f"- 섹터: {company.get('sector', 'N/A')}")
            parts.append(f"- 산업: {company.get('industry', 'N/A')}")
            parts.append(f"- 시가총액: {company.get('market_cap', 'N/A')}")
            parts.append(f"- 직원 수: {company.get('employees', 'N/A')}")

        annual = data.get("annual_reports", [])
        if annual:
            parts.append(f"\n## 연간 재무 데이터")
            for report in annual[:3]:
                year = report.get("fiscal_year", "N/A")
                parts.append(f"\n### {year}년")
                parts.append(f"- 매출: {report.get('revenue', 'N/A')}")
                parts.append(f"- 영업이익: {report.get('operating_income', 'N/A')}")
                parts.append(f"- 순이익: {report.get('net_income', 'N/A')}")
                parts.append(f"- EPS: {report.get('eps', 'N/A')}")
                parts.append(f"- ROE: {report.get('roe', 'N/A')}")
                parts.append(f"- 영업이익률: {report.get('profit_margin', 'N/A')}")

        quarterly = data.get("quarterly_reports", [])
        if quarterly:
            parts.append(f"\n## 최근 분기 실적")
            for report in quarterly[:2]:
                year = report.get("fiscal_year", "N/A")
                quarter = report.get("fiscal_quarter", "N/A")
                parts.append(f"\n### {year}년 {quarter}분기")
                parts.append(f"- 매출: {report.get('revenue', 'N/A')}")
                parts.append(f"- 영업이익: {report.get('operating_income', 'N/A')}")
                parts.append(f"- 순이익: {report.get('net_income', 'N/A')}")

        relationships = data.get("relationships", [])
        if relationships:
            parts.append(f"\n## 기업 관계")
            for rel in relationships[:5]:
                parts.append(
                    f"- {rel.get('source_company')} → [{rel.get('relationship_type')}] → {rel.get('target_company')}"
                )

        prices = data.get("stock_prices", [])
        if prices and prices[0]:
            latest = prices[0]
            parts.append(f"\n## 최근 주가")
            parts.append(f"- 날짜: {latest.get('price_date', 'N/A')}")
            parts.append(f"- 종가: {latest.get('close_price', 'N/A')}")
            parts.append(f"- P/E: {latest.get('pe_ratio', 'N/A')}")
            parts.append(f"- P/B: {latest.get('pb_ratio', 'N/A')}")

        return "\n".join(parts) if parts else "데이터 없음"

    def _get_finnhub_data(self, ticker: str) -> str:
        """Get real-time data from Finnhub"""
        if not self.finnhub:
            return ""

        parts = []

        try:
            # Company profile
            profile = self.finnhub.get_company_profile(ticker.upper())
            if profile and "name" in profile:
                parts.append("## 기업 개요 (Finnhub 실시간)")
                parts.append(f"- 회사명: {profile.get('name', 'N/A')}")
                parts.append(f"- 티커: {profile.get('ticker', ticker.upper())}")
                parts.append(f"- 산업: {profile.get('finnhubIndustry', 'N/A')}")
                parts.append(
                    f"- 시가총액: ${profile.get('marketCapitalization', 0):,.0f}M"
                )
                parts.append(f"- 거래소: {profile.get('exchange', 'N/A')}")
                parts.append(f"- 웹사이트: {profile.get('weburl', 'N/A')}")

            # Real-time quote
            quote = self.finnhub.get_quote(ticker.upper())
            if quote and "c" in quote:
                current = quote.get("c", 0)
                prev_close = quote.get("pc", 0)
                change = current - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0

                parts.append("\n## 실시간 시세")
                parts.append(f"- 현재가: ${current:.2f}")
                parts.append(
                    f"- 변동: {'+' if change >= 0 else ''}{change:.2f} ({'+' if change_pct >= 0 else ''}{change_pct:.2f}%)"
                )
                parts.append(f"- 고가: ${quote.get('h', 0):.2f}")
                parts.append(f"- 저가: ${quote.get('l', 0):.2f}")
                parts.append(f"- 전일종가: ${prev_close:.2f}")

            # Basic financials
            financials = self.finnhub.get_basic_financials(ticker.upper())
            if financials and "metric" in financials:
                metrics = financials["metric"]
                parts.append("\n## 재무 지표")
                parts.append(
                    f"- P/E (TTM): {metrics.get('peBasicExclExtraTTM', 'N/A')}"
                )
                parts.append(f"- P/B: {metrics.get('pbAnnual', 'N/A')}")
                parts.append(f"- ROE: {metrics.get('roeRfy', 'N/A')}")
                parts.append(
                    f"- 배당수익률: {metrics.get('dividendYieldIndicatedAnnual', 'N/A')}%"
                )
                parts.append(f"- 52주 최고: ${metrics.get('52WeekHigh', 'N/A')}")
                parts.append(f"- 52주 최저: ${metrics.get('52WeekLow', 'N/A')}")

            # Analyst recommendations
            recs = self.finnhub.get_recommendation_trends(ticker.upper())
            if recs and len(recs) > 0:
                latest = recs[0]
                parts.append("\n## 애널리스트 추천")
                parts.append(f"- Strong Buy: {latest.get('strongBuy', 0)}")
                parts.append(f"- Buy: {latest.get('buy', 0)}")
                parts.append(f"- Hold: {latest.get('hold', 0)}")
                parts.append(f"- Sell: {latest.get('sell', 0)}")
                parts.append(f"- Strong Sell: {latest.get('strongSell', 0)}")

            # Price target
            target = self.finnhub.get_price_target(ticker.upper())
            if target and "targetMean" in target:
                parts.append("\n## 목표주가")
                parts.append(f"- 평균: ${target.get('targetMean', 0):.2f}")
                parts.append(f"- 최고: ${target.get('targetHigh', 0):.2f}")
                parts.append(f"- 최저: ${target.get('targetLow', 0):.2f}")

            # Recent news
            news = self.finnhub.get_company_news(ticker.upper())[:5]
            if news:
                parts.append("\n## 최근 뉴스")
                for article in news:
                    headline = article.get("headline", "")[:60]
                    source = article.get("source", "")
                    parts.append(f"- [{source}] {headline}")

            # Peers
            peers = self.finnhub.get_company_peers(ticker.upper())
            if peers:
                parts.append(f"\n## 경쟁사: {', '.join(peers[:7])}")

        except Exception as e:
            logger.warning(f"Finnhub data fetch error: {e}")

        return "\n".join(parts)

    def generate_report(self, ticker: str) -> str:
        """
        Generate investment analysis report for a company

        Args:
            ticker: Company ticker symbol

        Returns:
            Markdown formatted report
        """
        try:
            # Collect company data from Supabase
            data = self._get_company_data(ticker)
            context = self._format_data_context(data) if data.get("company") else ""

            # Get Finnhub real-time data (always try)
            finnhub_data = self._get_finnhub_data(ticker)

            # Combine contexts
            if context and finnhub_data:
                full_context = f"{context}\n\n---\n\n{finnhub_data}"
            elif finnhub_data:
                full_context = finnhub_data
            elif context:
                full_context = context
            else:
                return f"❌ '{ticker}' 데이터를 찾을 수 없습니다. Finnhub API 키를 확인하세요."

            # Generate report
            messages = [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": f"다음 데이터를 바탕으로 {ticker.upper()} 투자 분석 보고서를 작성해주세요.\n\n{full_context}",
                },
            ]

            report = None
            used_model = self.model

            # 1. Try Primary Model (gpt-5-nano)
            try:
                logger.info(f"Sending request to OpenAI model: {self.model}")
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "text"},
                    max_completion_tokens=3000,
                    verbosity="medium",
                    reasoning_effort="medium",
                    store=False,
                )
                report = response.choices[0].message.content

                if not report:
                    raise ValueError("Empty response from primary model")

            except Exception as e:
                logger.warning(
                    f"Primary model {self.model} failed: {e}. Falling back to gpt-4.1-mini"
                )
                used_model = "gpt-4.1-mini"
                try:
                    # 2. Try Fallback Model
                    response = self.openai_client.chat.completions.create(
                        model=used_model, messages=messages, max_tokens=3000
                    )
                    report = response.choices[0].message.content
                except Exception as e2:
                    logger.error(f"Fallback model failed: {e2}")
                    return f"❌ 레포트 생성 실패: {str(e2)}"

            if not report:
                return "❌ 레포트 생성 실패: 모델로부터 내용을 받아오지 못했습니다."

            # Add metadata
            header = f"""---
**생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**모델**: {used_model}
**티커**: {ticker}

---

"""
            return header + report

        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return f"❌ 레포트 생성 중 오류가 발생했습니다: {str(e)}"

    def generate_comparison_report(self, tickers: list) -> str:
        """Generate comparison report for multiple companies"""
        try:
            context_parts = []

            for ticker in tickers:
                context_parts.append(f"\n# {ticker.upper()}")

                # Get Supabase data
                supabase_data = self._get_company_data(ticker)
                supabase_context = (
                    self._format_data_context(supabase_data)
                    if supabase_data.get("company")
                    else ""
                )

                # Get Finnhub data
                finnhub_context = self._get_finnhub_data(ticker)

                # Combine
                if supabase_context and finnhub_context:
                    context_parts.append(supabase_context)
                    context_parts.append("---")
                    context_parts.append(finnhub_context)
                elif finnhub_context:
                    context_parts.append(finnhub_context)
                elif supabase_context:
                    context_parts.append(supabase_context)
                else:
                    context_parts.append(f"⚠️ {ticker} 데이터 없음")

            full_context = "\n".join(context_parts)

            if not full_context.strip():
                return "❌ 비교할 회사 데이터를 찾을 수 없습니다."

            messages = [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": f"다음 기업들을 비교 분석하는 보고서를 작성해주세요: {', '.join(tickers)}\n\n{full_context}",
                },
            ]

            try:
                # 1. Try Primary Model
                logger.info(f"Sending request to OpenAI model: {self.model}")
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "text"},
                    max_completion_tokens=4000,
                    verbosity="medium",
                    reasoning_effort="medium",
                    store=False,
                )
                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty response from primary model")
                return content

            except Exception as e:
                logger.warning(
                    f"Primary model {self.model} failed: {e}. Falling back to gpt-4.1-mini"
                )
                try:
                    # 2. Try Fallback Model
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4.1-mini", messages=messages, max_tokens=4000
                    )
                    content = response.choices[0].message.content
                    if not content:
                        return "❌ 비교 보고서 생성 실패: 모델로부터 내용을 받아오지 못했습니다."
                    return f"⚠️ [Fallback Model: gpt-4.1-mini]\n\n{content}"
                except Exception as e2:
                    return f"❌ 비교 보고서 생성 실패: {str(e2)}"

        except Exception as e:
            logger.error(f"Comparison report error: {e}")
            return f"❌ 비교 보고서 생성 중 오류 발생: {str(e)}"


if __name__ == "__main__":
    print("🔄 ReportGenerator 초기화 중...")

    try:
        generator = ReportGenerator()
        print(f"✅ 초기화 성공!")
        print(f"   Model: {generator.model}")
        print(f"   System Prompt: {len(generator.system_prompt)} chars")

        # Test report generation
        print("\n📝 테스트: AAPL 레포트 생성")
        report = generator.generate_report("AAPL")
        print(f"\n📊 레포트:\n{report[:500]}...")

    except Exception as e:
        print(f"❌ 오류: {e}")
