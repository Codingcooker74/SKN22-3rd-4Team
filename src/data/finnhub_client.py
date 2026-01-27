"""
Finnhub API Client - 실시간 주가, 뉴스, SEC 공시 데이터
https://finnhub.io
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class FinnhubClient:
    """
    Finnhub API 클라이언트
    - 실시간/과거 주가
    - 회사 뉴스
    - SEC 공시
    - 기업 프로필
    - 재무제표
    """

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_key: str = None):
        """Initialize Finnhub client"""
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")

        if self.api_key:
            self.api_key = self.api_key.strip()  # Remove whitespace

        if not self.api_key or self.api_key == "your_finnhub_api_key_here":
            logger.warning("FINNHUB_API_KEY not set. Get free key at https://finnhub.io")
            self.api_key = None

        self.session = requests.Session()

    def _request(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """Make API request"""
        if not self.api_key:
            return {"error": "Finnhub API key not configured"}

        params = params or {}
        params["token"] = self.api_key

        try:
            response = self.session.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.warning(f"Finnhub API 403 Forbidden (Premium endpoint?): {endpoint}")
                return {"error": "Prediction/Premium endpoint not available on this plan"}
            logger.error(f"Finnhub API error: {e}")
            return {"error": str(e)}
        except requests.exceptions.RequestException as e:
            logger.error(f"Finnhub API error: {e}")
            return {"error": str(e)}

    # ========== 주가 데이터 ==========

    def get_quote(self, symbol: str) -> Dict:
        """
        실시간 주가 조회
        Returns: c(현재가), h(고가), l(저가), o(시가), pc(전일종가), t(시간)
        """
        return self._request("quote", {"symbol": symbol.upper()})

    def get_candles(
        self,
        symbol: str,
        resolution: str = "D",  # 1, 5, 15, 30, 60, D, W, M
        from_date: datetime = None,
        to_date: datetime = None,
    ) -> Dict:
        """
        캔들 차트 데이터 (OHLCV)
        resolution: 1=1분, 5=5분, D=일봉, W=주봉, M=월봉
        """
        to_date = to_date or datetime.now()
        from_date = from_date or (to_date - timedelta(days=30))

        return self._request(
            "stock/candle",
            {
                "symbol": symbol.upper(),
                "resolution": resolution,
                "from": int(from_date.timestamp()),
                "to": int(to_date.timestamp()),
            },
        )

    # ========== 기업 정보 ==========

    def get_company_profile(self, symbol: str) -> Dict:
        """기업 프로필 조회"""
        return self._request("stock/profile2", {"symbol": symbol.upper()})

    def get_company_peers(self, symbol: str) -> List[str]:
        """경쟁사/유사기업 목록"""
        result = self._request("stock/peers", {"symbol": symbol.upper()})
        return result if isinstance(result, list) else []

    # ========== 뉴스 ==========

    def get_company_news(
        self, symbol: str, from_date: str = None, to_date: str = None  # YYYY-MM-DD
    ) -> List[Dict]:
        """
        기업 관련 뉴스 조회
        Returns: headline, summary, source, url, datetime
        """
        to_date = to_date or datetime.now().strftime("%Y-%m-%d")
        from_date = from_date or (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        result = self._request(
            "company-news", {"symbol": symbol.upper(), "from": from_date, "to": to_date}
        )
        return result if isinstance(result, list) else []

    def get_market_news(self, category: str = "general") -> List[Dict]:
        """
        시장 전체 뉴스
        category: general, forex, crypto, merger
        """
        result = self._request("news", {"category": category})
        return result if isinstance(result, list) else []

    # ========== SEC 공시 ==========

    def get_sec_filings(
        self,
        symbol: str = None,
        cik: str = None,
        form: str = None,  # 10-K, 10-Q, 8-K 등
        from_date: str = None,
        to_date: str = None,
    ) -> List[Dict]:
        """
        SEC 공시 목록 조회
        Returns: accessNumber, symbol, form, filedDate, acceptedDate, reportUrl
        """
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        if cik:
            params["cik"] = cik
        if form:
            params["form"] = form
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        result = self._request("stock/filings", params)
        return result if isinstance(result, list) else []

    # ========== 재무 데이터 ==========

    def get_basic_financials(self, symbol: str, metric: str = "all") -> Dict:
        """
        기본 재무 지표
        metric: all, price, valuation, margin, profitability 등
        """
        return self._request("stock/metric", {"symbol": symbol.upper(), "metric": metric})

    def get_financials_reported(self, symbol: str, freq: str = "annual") -> Dict:
        """
        실제 보고된 재무제표 데이터
        freq: annual, quarterly
        """
        return self._request("stock/financials-reported", {"symbol": symbol.upper(), "freq": freq})

    def get_earnings(self, symbol: str) -> List[Dict]:
        """실적 발표 데이터 (EPS)"""
        result = self._request("stock/earnings", {"symbol": symbol.upper()})
        return result if isinstance(result, list) else []

    # ========== 추천/분석 ==========

    def get_recommendation_trends(self, symbol: str) -> List[Dict]:
        """애널리스트 추천 트렌드 (Buy/Hold/Sell)"""
        result = self._request("stock/recommendation", {"symbol": symbol.upper()})
        return result if isinstance(result, list) else []

    def get_price_target(self, symbol: str) -> Dict:
        """목표 주가 (애널리스트 컨센서스)"""
        return self._request("stock/price-target", {"symbol": symbol.upper()})

    def get_earnings_surprises(self, symbol: str) -> List[Dict]:
        """실적 서프라이즈 데이터"""
        result = self._request("stock/earnings", {"symbol": symbol.upper()})
        return result if isinstance(result, list) else []

    # ========== 유틸리티 ==========

    def format_quote_summary(self, symbol: str) -> str:
        """주가 정보를 읽기 쉬운 텍스트로 변환"""
        quote = self.get_quote(symbol)

        if "error" in quote:
            return f"주가 조회 실패: {quote['error']}"

        current = quote.get("c", 0)
        prev_close = quote.get("pc", 0)
        change = current - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0

        arrow = "📈" if change >= 0 else "📉"

        return f"""
{arrow} **{symbol.upper()}** 실시간 시세
- 현재가: ${current:.2f}
- 변동: {'+' if change >= 0 else ''}{change:.2f} ({'+' if change_pct >= 0 else ''}{change_pct:.2f}%)
- 고가: ${quote.get('h', 0):.2f} / 저가: ${quote.get('l', 0):.2f}
- 전일종가: ${prev_close:.2f}
""".strip()

    def format_news_summary(self, symbol: str, limit: int = 5) -> str:
        """최근 뉴스를 읽기 쉬운 텍스트로 변환"""
        news = self.get_company_news(symbol)[:limit]

        if not news:
            return f"{symbol.upper()} 관련 최근 뉴스가 없습니다."

        lines = [f"📰 **{symbol.upper()}** 최근 뉴스"]
        for i, article in enumerate(news, 1):
            headline = article.get("headline", "제목 없음")
            source = article.get("source", "")
            dt = datetime.fromtimestamp(article.get("datetime", 0))
            lines.append(
                f"{i}. [{headline}]({article.get('url', '#')}) - {source} ({dt.strftime('%m/%d')})"
            )

        return "\n".join(lines)


# 싱글톤 인스턴스
_client = None


def get_finnhub_client() -> FinnhubClient:
    """Get or create Finnhub client singleton"""
    global _client
    if _client is None:
        _client = FinnhubClient()
    return _client


if __name__ == "__main__":
    print("🔄 Finnhub 클라이언트 테스트...")

    client = FinnhubClient()

    if client.api_key:
        print("✅ API 키 설정됨")

        # 테스트: Apple 주가
        print("\n📈 AAPL 주가:")
        print(client.format_quote_summary("AAPL"))

        # 테스트: 기업 프로필
        print("\n🏢 기업 프로필:")
        profile = client.get_company_profile("AAPL")
        print(f"  회사명: {profile.get('name')}")
        print(f"  산업: {profile.get('finnhubIndustry')}")
        print(f"  시가총액: ${profile.get('marketCapitalization', 0):,.0f}M")

    else:
        print("⚠️ FINNHUB_API_KEY가 설정되지 않았습니다.")
        print("   무료 API 키 발급: https://finnhub.io")
