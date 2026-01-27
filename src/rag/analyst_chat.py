"""
Analyst Chatbot - 애널리스트/기자 스타일 챗봇
Uses gpt-4.1-mini with RAG context
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from openai import OpenAI
from supabase import create_client, Client
import json
from dotenv import load_dotenv

# Import Finnhub client
try:
    from data.finnhub_client import get_finnhub_client, FinnhubClient

    FINNHUB_AVAILABLE = True
except ImportError:
    FINNHUB_AVAILABLE = False


load_dotenv()

logger = logging.getLogger(__name__)

# Prompts directory
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class AnalystChatbot:
    """
    애널리스트/기자 스타일로 금융 정보를 분석하고 답변하는 챗봇
    gpt-4.1-mini 사용
    """

    def __init__(self):
        """Initialize chatbot with OpenAI and Supabase"""

        # OpenAI client
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 필요합니다.")

        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.model = "gpt-4.1-mini"  # 챗봇용 모델
        self.embedding_model = "text-embedding-3-small"

        # Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL과 SUPABASE_KEY 환경 변수가 필요합니다.")

        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Finnhub client (for real-time data)
        self.finnhub = None
        if FINNHUB_AVAILABLE:
            try:
                self.finnhub = get_finnhub_client()
                if self.finnhub.api_key:
                    logger.info("Finnhub client initialized")
                else:
                    self.finnhub = None
            except Exception as e:
                logger.warning(f"Finnhub init failed: {e}")

        # Load system prompt
        self.system_prompt = self._load_prompt("analyst_chat.txt")

        # Conversation history
        self.conversation_history: List[Dict] = []

        logger.info("AnalystChatbot initialized")

    def _load_prompt(self, filename: str) -> str:
        """Load system prompt from file"""
        prompt_path = PROMPTS_DIR / filename
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt file not found: {prompt_path}")
            return "당신은 금융 분석 전문가입니다. 한국어로 답변하세요."

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        response = self.openai_client.embeddings.create(
            model=self.embedding_model, input=text
        )
        return response.data[0].embedding

    def _search_documents(self, query: str, limit: int = 5) -> List[Dict]:
        """Search relevant documents from Supabase"""
        try:
            query_embedding = self._get_embedding(query)

            result = self.supabase.rpc(
                "match_documents",
                {"query_embedding": query_embedding, "match_count": limit},
            ).execute()

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Document search error: {e}")
            return []

    def _get_company_info(self, ticker: str) -> Optional[Dict]:
        """Get company information from Supabase"""
        try:
            result = (
                self.supabase.table("companies")
                .select("*")
                .eq("ticker", ticker.upper())
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Company info error: {e}")
            return None

    def _get_relationships(self, ticker: str) -> List[Dict]:
        """Get company relationships"""
        try:
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

            return (outgoing.data or []) + (incoming.data or [])
        except Exception as e:
            logger.error(f"Relationships error: {e}")
            return []

    def _build_context(self, query: str, ticker: Optional[str] = None) -> str:
        """Build context from RAG search, company data, and real-time Finnhub data"""
        context_parts = []

        # 1. Search relevant documents
        docs = self._search_documents(query, limit=3)
        if docs:
            context_parts.append("## 관련 문서")
            for doc in docs:
                content = doc.get("content", "")[:500]
                context_parts.append(f"- {content}")

        # 2. Get company info if ticker provided
        if ticker:
            company = self._get_company_info(ticker)
            if company:
                context_parts.append(
                    f"\n## 회사 정보: {company.get('company_name', ticker)}"
                )
                context_parts.append(f"- 티커: {company.get('ticker')}")
                context_parts.append(f"- 섹터: {company.get('sector', 'N/A')}")
                context_parts.append(f"- 산업: {company.get('industry', 'N/A')}")
                context_parts.append(f"- 시가총액: {company.get('market_cap', 'N/A')}")

            # Get relationships
            relationships = self._get_relationships(ticker)
            if relationships:
                context_parts.append(f"\n## 기업 관계 ({len(relationships)}개)")
                for rel in relationships[:5]:
                    rel_type = rel.get("relationship_type", "관련")
                    source = rel.get("source_company", "")
                    target = rel.get("target_company", "")
                    context_parts.append(f"- {source} → [{rel_type}] → {target}")

            # 3. Get real-time Finnhub data
            if self.finnhub:
                try:
                    # Real-time quote
                    quote = self.finnhub.get_quote(ticker)
                    if quote and "c" in quote:
                        current = quote.get("c", 0)
                        prev_close = quote.get("pc", 0)
                        change = current - prev_close
                        change_pct = (change / prev_close * 100) if prev_close else 0

                        context_parts.append(f"\n## 실시간 시세 (Finnhub)")
                        context_parts.append(f"- 현재가: ${current:.2f}")
                        context_parts.append(
                            f"- 변동: {'+' if change >= 0 else ''}{change:.2f} ({'+' if change_pct >= 0 else ''}{change_pct:.2f}%)"
                        )
                        context_parts.append(
                            f"- 고가/저가: ${quote.get('h', 0):.2f} / ${quote.get('l', 0):.2f}"
                        )

                    # Analyst recommendations
                    recs = self.finnhub.get_recommendation_trends(ticker)
                    if recs and len(recs) > 0:
                        latest = recs[0]
                        context_parts.append(f"\n## 애널리스트 추천")
                        context_parts.append(
                            f"- Strong Buy: {latest.get('strongBuy', 0)}"
                        )
                        context_parts.append(f"- Buy: {latest.get('buy', 0)}")
                        context_parts.append(f"- Hold: {latest.get('hold', 0)}")
                        context_parts.append(f"- Sell: {latest.get('sell', 0)}")

                    # Price target
                    target = self.finnhub.get_price_target(ticker)
                    if target and "targetMean" in target:
                        context_parts.append(f"\n## 목표주가")
                        context_parts.append(
                            f"- 평균: ${target.get('targetMean', 0):.2f}"
                        )
                        context_parts.append(
                            f"- 최고: ${target.get('targetHigh', 0):.2f}"
                        )
                        context_parts.append(
                            f"- 최저: ${target.get('targetLow', 0):.2f}"
                        )

                    # Recent news (top 3)
                    news = self.finnhub.get_company_news(ticker)[:3]
                    if news:
                        context_parts.append(f"\n## 최근 뉴스")
                        for article in news:
                            headline = article.get("headline", "")[:80]
                            context_parts.append(f"- {headline}")

                except Exception as e:
                    logger.warning(f"Finnhub data fetch error: {e}")

        return "\n".join(context_parts) if context_parts else "추가 컨텍스트 없음"

    def _extract_tickers(self, query: str) -> List[str]:
        """Extract company tickers from user query using LLM"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract all company ticker symbols from the query. Return them comma-separated (e.g., AAPL, MSFT). If none, return NOTHING.",
                    },
                    {"role": "user", "content": query},
                ],
                max_tokens=20,
                temperature=0.0,
            )
            content = response.choices[0].message.content.strip()
            if "NOTHING" in content:
                return []

            tickers = [
                t.strip().replace(".", "").replace("'", "").replace('"', "").upper()
                for t in content.split(",")
            ]

            # Validation
            valid_tickers = []
            if self.finnhub:
                for t in tickers:
                    if len(t) <= 5:
                        valid_tickers.append(t)

            return valid_tickers
        except Exception as e:
            logger.warning(f"Ticker extraction failed: {e}")
            return []

    def _resolve_ticker_name(self, input_text: str) -> Optional[str]:
        """Resolve Korean name or company name to Ticker"""
        if not input_text:
            return None

        # 1. Try Exact Ticker Match First (Prioritize "AAPL", "TSLA")
        # Even if input is "Apple", if we have a ticker "APPLE" (unlikely but possible), this checks.
        # Ideally, inputs like "AAPL" should hit this.
        try:
            res = (
                self.supabase.table("companies")
                .select("ticker")
                .eq("ticker", input_text.upper())
                .execute()
            )
            if res.data:
                return res.data[0]["ticker"]
        except Exception:
            pass

        # 2. Try Korean Name Match (e.g., "애플")
        try:
            res = (
                self.supabase.table("companies")
                .select("ticker")
                .ilike("korean_name", f"%{input_text}%")
                .execute()
            )
            if res.data:
                return res.data[0]["ticker"]
        except Exception:
            pass

        # 3. Try English Company Name Match (e.g., "Apple")
        try:
            res = (
                self.supabase.table("companies")
                .select("ticker")
                .ilike("company_name", f"%{input_text}%")
                .execute()
            )
            if res.data:
                return res.data[0]["ticker"]
        except Exception:
            pass

        # 4. Heuristic: If it looks like a ticker and we found nothing in DB, assume it might be a new ticker
        # But only if it's strictly a valid ticker format
        if input_text.isascii() and len(input_text) <= 5 and " " not in input_text:
            return input_text.upper()

        # 3. Fallback to LLM
        try:
            resp = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial assistant. Return ONLY the stock ticker symbol for the given company name. If unsure, return the input itself.",
                    },
                    {
                        "role": "user",
                        "content": f"What is the ticker for '{input_text}'?",
                    },
                ],
                max_completion_tokens=10,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return input_text

    def _register_company(self, ticker: str) -> str:
        """Register company to Supabase using Finnhub data"""
        if not self.finnhub:
            return "Finnhub 클라이언트가 설정되지 않았습니다."

        try:
            # Check if already exists
            existing = (
                self.supabase.table("companies")
                .select("ticker")
                .eq("ticker", ticker)
                .execute()
            )
            if existing.data:
                return f"이미 등록된 기업입니다: {ticker}"

            # Get profile
            profile = self.finnhub.get_company_profile(ticker)
            if not profile:
                return f"Finnhub에서 기업 정보를 찾을 수 없습니다: {ticker}"

            # Insert to Supabase
            data = {
                "ticker": ticker,
                "company_name": profile.get("name", ticker),
                "sector": profile.get("finnhubIndustry", "Unknown"),
                "industry": profile.get("finnhubIndustry", "Unknown"),
                "market_cap": profile.get("marketCapitalization", 0),
                "website": profile.get("weburl", ""),
                "description": f"Registered via Chatbot. {profile.get('name')} is a company in {profile.get('finnhubIndustry')} sector.",
            }

            # Generate Korean Name via LLM
            try:
                trans_resp = self.openai_client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a translator. Return ONLY the Korean name for the company. No extra text.",
                        },
                        {
                            "role": "user",
                            "content": f"What is the common Korean name for '{profile.get('name')}' ({ticker})?",
                        },
                    ],
                    max_completion_tokens=20,
                )
                korean_name = trans_resp.choices[0].message.content.strip()
                data["korean_name"] = korean_name
            except Exception:
                pass

            self.supabase.table("companies").upsert(data).execute()
            logger.info(f"Registered company: {ticker} ({data.get('korean_name')})")
            return f"✅ 성공적으로 등록되었습니다: {profile.get('name')} ({ticker})\n한글명: {data.get('korean_name')}\n이제 이 기업에 대해 질문하거나 레포트를 생성할 수 있습니다."

        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return f"등록 중 오류가 발생했습니다: {str(e)}"

    def _get_financial_data(self, ticker: str) -> str:
        """Get real-time financial data using Finnhub (Tool)"""
        if not self.finnhub:
            return json.dumps({"error": "Finnhub client unavailable"})

        try:
            data = {}
            # 1. Quote
            quote = self.finnhub.get_quote(ticker)
            if quote:
                data["price"] = quote.get("c")
                data["change"] = quote.get("d")
                data["percent_change"] = quote.get("dp")
                data["high"] = quote.get("h")
                data["low"] = quote.get("l")

            # 2. Target Price
            target = self.finnhub.get_price_target(ticker)
            if target:
                data["target_mean"] = target.get("targetMean")
                data["target_high"] = target.get("targetHigh")
                data["target_low"] = target.get("targetLow")
                data["consensus"] = "Unknown"

            # 3. Recommendations
            recs = self.finnhub.get_recommendation_trends(ticker)
            if recs:
                latest = recs[0]
                data["recommendation"] = {
                    "strong_buy": latest.get("strongBuy"),
                    "buy": latest.get("buy"),
                    "hold": latest.get("hold"),
                    "sell": latest.get("sell"),
                    "strong_sell": latest.get("strongSell"),
                }

            # 4. Recent News
            news = self.finnhub.get_company_news(ticker)
            if news:
                data["recent_news"] = [
                    {
                        "headline": n.get("headline"),
                        "url": n.get("url"),
                        "summary": n.get("summary"),
                    }
                    for n in news[:3]
                ]

            return json.dumps(data, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return json.dumps({"error": str(e)})

    def chat(
        self, message: str, ticker: Optional[str] = None, use_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Process user message and generate response with optional report
        """

        # Tools definition
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_stock_quote",
                    "description": "Get real-time stock price (c), change (d), percent change (dp), high (h), low (l).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "Company ticker symbol (e.g. AAPL)",
                            }
                        },
                        "required": ["ticker"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_company_profile",
                    "description": "Get company profile (industry, market cap, IPO date, etc).",
                    "parameters": {
                        "type": "object",
                        "properties": {"ticker": {"type": "string"}},
                        "required": ["ticker"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_price_target",
                    "description": "Get analyst price target and consensus.",
                    "parameters": {
                        "type": "object",
                        "properties": {"ticker": {"type": "string"}},
                        "required": ["ticker"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_company_news",
                    "description": "Get recent company news.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string"},
                            "from_date": {
                                "type": "string",
                                "description": "YYYY-MM-DD",
                            },
                            "to": {"type": "string", "description": "YYYY-MM-DD"},
                        },
                        "required": ["ticker"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_market_news",
                    "description": "Get general market news.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": ["general", "forex", "crypto", "merger"],
                                "default": "general",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "register_company",
                    "description": "Register a new company to the database if the user asks to add/register it.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "The company ticker symbol to register.",
                            }
                        },
                        "required": ["ticker"],
                    },
                },
            },
        ]

        try:
            # Detect tickers if not provided (keeping legacy support for RAG context)
            # Detect tickers if not provided (keeping legacy support for RAG context)
            tickers = []
            if ticker:
                # Resolve partial/Korean ticker
                resolved = self._resolve_ticker_name(ticker)
                if resolved:
                    tickers = [resolved]
                else:
                    tickers = [ticker]  # Fallback

            # Build initial messages
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.conversation_history[-6:])

            # If explicit ticker context is available, add it (Hybrid approach)
            context = ""
            if use_rag and tickers:
                context_parts = []
                for t in tickers:
                    context_parts.append(self._build_context(message, t))
                context = "\n\n---\n\n".join(context_parts)

            user_content = message
            if context:
                # If we already have context, we might not need tools, but we allow it
                user_content = f"[컨텍스트]\n{context}\n\n[질문]\n{message}"

            messages.append({"role": "user", "content": user_content})

            # First Call (Prediction)
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_completion_tokens=2000,
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # Handle Tool Calls
            if tool_calls:
                messages.append(
                    response_message
                )  # Add the assistant's request to history

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    logger.info(f"Tool Call: {function_name} with {function_args}")

                    tool_result = ""
                    if function_name == "get_stock_quote":
                        res = self.finnhub.get_quote(function_args.get("ticker"))
                        tool_result = json.dumps(res, ensure_ascii=False)
                    elif function_name == "get_company_profile":
                        res = self.finnhub.get_company_profile(
                            function_args.get("ticker")
                        )
                        tool_result = json.dumps(res, ensure_ascii=False)
                    elif function_name == "get_price_target":
                        res = self.finnhub.get_price_target(function_args.get("ticker"))
                        tool_result = json.dumps(res, ensure_ascii=False)
                    elif function_name == "get_company_news":
                        res = self.finnhub.get_company_news(
                            function_args.get("ticker"),
                            function_args.get("from_date"),
                            function_args.get("to"),
                        )
                        tool_result = json.dumps(res[:5], ensure_ascii=False)
                    elif function_name == "get_market_news":
                        res = self.finnhub.get_market_news(
                            function_args.get("category", "general")
                        )
                        tool_result = json.dumps(res[:5], ensure_ascii=False)
                    elif function_name == "register_company":
                        tool_result = self._register_company(
                            function_args.get("ticker")
                        )
                    else:
                        tool_result = json.dumps(
                            {"error": f"Unknown function: {function_name}"}
                        )

                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": tool_result,
                        }
                    )

                # Second Call (Final Response)
                final_response = self.openai_client.chat.completions.create(
                    model=self.model, messages=messages, max_completion_tokens=2000
                )
                assistant_message = final_response.choices[0].message.content
            else:
                assistant_message = response_message.content

            # Check for Report Generation Intent (Legacy check for PDF)
            generate_report = any(
                keyword in message.lower()
                for keyword in [
                    "레포트",
                    "보고서",
                    "다운로드",
                    "파일",
                    "report",
                    "자료",
                ]
            )
            report_content = None
            if generate_report:
                # Try to extract ticker from tool calls or context
                target_ticker = None
                if tickers:
                    target_ticker = tickers[0]
                # If no legacy ticker, we can't generate report easily unless we parse tool args again.
                # For now, rely on explicit ticker input from UI or robust interaction.

                if target_ticker:
                    from rag.report_generator import ReportGenerator

                    generator = ReportGenerator()
                    report_content = generator.generate_report(target_ticker)
                    assistant_message += "\n\n(요청하신 분석 자료를 생성했습니다. 아래 버튼으로 다운로드하세요.)"

            # Update history
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append(
                {"role": "assistant", "content": assistant_message}
            )

            return {
                "content": assistant_message,
                "report": report_content,
                "tickers": tickers,
            }

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {"content": f"오류 발생: {str(e)}", "report": None}

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")


if __name__ == "__main__":
    print("🔄 AnalystChatbot 초기화 중...")
    try:
        chatbot = AnalystChatbot()
        print(f"✅ 초기화 성공!")
        print(f"   Model: {chatbot.model}")

    except Exception as e:
        print(f"❌ 오류: {e}")
