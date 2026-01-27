"""
Finnhub MCP Server
Finnhub API를 사용하여 주식 시장 데이터를 제공하는 MCP 서버입니다.
"""

from typing import Optional, List, Dict, Any
import os
import finnhub
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# API 키 확인
API_KEY = os.getenv("FINNHUB_API_KEY")
if not API_KEY:
    raise ValueError("FINNHUB_API_KEY가 환경 변수(.env)에 설정되지 않았습니다.")

# Finnhub 클라이언트 초기화
finnhub_client = finnhub.Client(api_key=API_KEY)

# MCP 서버 초기화
mcp = FastMCP("Finnhub Stock Data")

@mcp.tool()
def get_stock_quote(symbol: str) -> Dict[str, Any]:
    """
    특정 주식 티커의 실시간 시세 정보를 조회합니다.
    
    Args:
        symbol: 주식 티커 (예: AAPL, TSLA)
        
    Returns:
        현재가(c), 전일종가(pc), 시가(o), 고가(h), 저가(l), 등락률(dp) 등을 포함한 딕셔너리
    """
    try:
        quote = finnhub_client.quote(symbol)
        
        # 보기 쉽게 키 매핑 (선택 사항)
        return {
            "symbol": symbol,
            "current_price": quote.get("c"),
            "change": quote.get("d"),
            "percent_change": quote.get("dp"),
            "high": quote.get("h"),
            "low": quote.get("l"),
            "open": quote.get("o"),
            "previous_close": quote.get("pc"),
            "timestamp": quote.get("t")
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

@mcp.tool()
def get_company_profile(symbol: str) -> Dict[str, Any]:
    """
    기업의 기본 프로필 정보(산업, 시가총액, 웹사이트 등)를 조회합니다.
    
    Args:
        symbol: 주식 티커
    """
    try:
        profile = finnhub_client.company_profile2(symbol=symbol)
        return profile
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

@mcp.tool()
def get_price_target(symbol: str) -> Dict[str, Any]:
    """
    애널리스트들의 목표 주가 및 투자의견 컨센서스를 조회합니다.
    
    Args:
        symbol: 주식 티커
    """
    try:
        target = finnhub_client.price_target(symbol)
        return target
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

@mcp.tool()
def get_company_news(symbol: str, from_date: str, to: str) -> List[Dict[str, Any]]:
    """
    특정 기업의 관련 뉴스를 조회합니다.
    
    Args:
        symbol: 주식 티커
        from_date: 시작 날짜 (YYYY-MM-DD)
        to: 종료 날짜 (YYYY-MM-DD)
    """
    try:
        # API 호출 시 파라미터 이름 매핑 (_from)
        news = finnhub_client.company_news(symbol, _from=from_date, to=to)
        return news[:10]  # 최근 10개만 반환
    except Exception as e:
        return [{"error": str(e), "symbol": symbol}]

@mcp.tool()
def get_market_news(category: str = "general") -> List[Dict[str, Any]]:
    """
    시장 전체 뉴스를 조회합니다.
    
    Args:
        category: 뉴스 카테고리 (general, forex, crypto, merger)
    """
    try:
        news = finnhub_client.general_news(category, min_id=0)
        return news[:10]
    except Exception as e:
        return [{"error": str(e)}]

if __name__ == "__main__":
    # MCP 서버 실행
    mcp.run()
