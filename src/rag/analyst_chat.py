"""
Analyst Chatbot - 애널리스트/기자 스타일 챗봇
Uses gpt-4.1-mini with RAG context
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from openai import OpenAI
from supabase import create_client, Client
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
        response = self.openai_client.embeddings.create(model=self.embedding_model, input=text)
        return response.data[0].embedding

    def _search_documents(self, query: str, limit: int = 5) -> List[Dict]:
        """Search relevant documents from Supabase"""
        try:
            query_embedding = self._get_embedding(query)

            result = self.supabase.rpc(
                "match_documents", {"query_embedding": query_embedding, "match_count": limit}
            ).execute()

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Document search error: {e}")
            return []

    def _get_company_info(self, ticker: str) -> Optional[Dict]:
        """Get company information from Supabase"""
        try:
            result = (
                self.supabase.table("companies").select("*").eq("ticker", ticker.upper()).execute()
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
                context_parts.append(f"\n## 회사 정보: {company.get('company_name', ticker)}")
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
                        context_parts.append(f"- Strong Buy: {latest.get('strongBuy', 0)}")
                        context_parts.append(f"- Buy: {latest.get('buy', 0)}")
                        context_parts.append(f"- Hold: {latest.get('hold', 0)}")
                        context_parts.append(f"- Sell: {latest.get('sell', 0)}")

                    # Price target
                    target = self.finnhub.get_price_target(ticker)
                    if target and "targetMean" in target:
                        context_parts.append(f"\n## 목표주가")
                        context_parts.append(f"- 평균: ${target.get('targetMean', 0):.2f}")
                        context_parts.append(f"- 최고: ${target.get('targetHigh', 0):.2f}")
                        context_parts.append(f"- 최저: ${target.get('targetLow', 0):.2f}")

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

    def _extract_ticker(self, query: str) -> Optional[str]:
        """Extract company ticker from user query using LLM"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.0-mini",  # 가볍고 빠른 모델 사용
                messages=[
                    {
                        "role": "system",
                        "content": "Extract the company ticker symbol from the query. Return ONLY the ticker (e.g., AAPL). If no specific company is mentioned, return NOTHING.",
                    },
                    {"role": "user", "content": query},
                ],
                max_tokens=10,
                temperature=0.0,
            )
            ticker = response.choices[0].message.content.strip()
            # Remove punctuation
            ticker = ticker.replace(".", "").replace("'", "").replace('"', "")

            if ticker and ticker != "NOTHING" and len(ticker) <= 5:
                # Validation: check against Finnhub if available
                if self.finnhub:
                    try:
                        profile = self.finnhub.get_company_profile(ticker)
                        if not profile:
                            return None
                    except:
                        pass
                return ticker
            return None
        except Exception as e:
            logger.warning(f"Ticker extraction failed: {e}")
            return None

    def chat(self, message: str, ticker: Optional[str] = None, use_rag: bool = True) -> str:
        """
        Process user message and generate response

        Args:
            message: User's question
            ticker: Optional company ticker for context
            use_rag: Whether to use RAG for context

        Returns:
            Analyst-style response
        """
        try:
            # Auto-detect ticker if not provided
            if not ticker and use_rag:
                detected_ticker = self._extract_ticker(message)
                if detected_ticker:
                    ticker = detected_ticker.upper()
                    logger.info(f"Auto-detected ticker: {ticker}")

            # Build context
            context = self._build_context(message, ticker) if use_rag else ""

            # Build messages
            messages = [{"role": "system", "content": self.system_prompt}]

            # Add conversation history (last 6 messages)
            messages.extend(self.conversation_history[-6:])

            # Add current message with context
            if context:
                user_content = f"[컨텍스트]\n{context}\n\n[질문]\n{message}"
            else:
                user_content = message

            messages.append({"role": "user", "content": user_content})

            # Generate response
            response = self.openai_client.chat.completions.create(
                model=self.model, messages=messages, max_completion_tokens=2000
            )

            assistant_message = response.choices[0].message.content

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})

            return assistant_message

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"

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
        print(f"   System Prompt: {len(chatbot.system_prompt)} chars")

        # Test chat
        print("\n📝 테스트 질문: '애플의 최근 실적은 어때?'")
        response = chatbot.chat("애플의 최근 실적은 어때?", ticker="AAPL")
        print(f"\n🤖 응답:\n{response}")

    except Exception as e:
        print(f"❌ 오류: {e}")
