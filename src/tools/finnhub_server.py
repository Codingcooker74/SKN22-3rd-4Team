"""
Finnhub MCP Server
Finnhub API를 사용하여 주식 시장 데이터를 제공하는 MCP 서버입니다.
"""

import sys
import os
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Add src to path for imports
start_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if start_path not in sys.path:
    sys.path.append(start_path)

from data.finnhub_client import get_finnhub_client

# 환경 변수 로드
load_dotenv()

# API 키 확인 (Optional check as get_finnhub_client handles it, but good for fail-fast)
API_KEY = os.getenv("FINNHUB_API_KEY")

# Finnhub 클라이언트 초기화 (Singleton)
finnhub_client = get_finnhub_client()

# MCP 서버 초기화
mcp = FastMCP("Finnhub Stock Data")


@mcp.tool()
def get_stock_quote(symbol: str) -> Dict[str, Any]:
    """
    특정 주식 티커의 실시간 시세 정보를 조회합니다.
    """
    quote = finnhub_client.get_quote(symbol)
    if "error" in quote:
        return {"error": quote["error"], "symbol": symbol}

    # 키 매핑 (내부 클라이언트 반환값에 맞춤)
    return {
        "symbol": symbol,
        "current_price": quote.get("c"),
        "change": quote.get("d"),
        "percent_change": quote.get("dp"),
        "high": quote.get("h"),
        "low": quote.get("l"),
        "open": quote.get("o"),
        "previous_close": quote.get("pc"),
        "timestamp": quote.get("t"),
    }


@mcp.tool()
def get_company_profile(symbol: str) -> Dict[str, Any]:
    """기업의 기본 프로필 정보 조회"""
    return finnhub_client.get_company_profile(symbol)


@mcp.tool()
def get_price_target(symbol: str) -> Dict[str, Any]:
    """애널리스트 목표 주가 조회"""
    return finnhub_client.get_price_target(symbol)


@mcp.tool()
def get_company_news(
    symbol: str, from_date: str = None, to: str = None
) -> List[Dict[str, Any]]:
    """기업 뉴스 조회 (최근 7일 기본)"""
    # 내부 클라이언트는 to -> to_date 파라미터 사용
    return finnhub_client.get_company_news(symbol, from_date=from_date, to_date=to)[:5]


@mcp.tool()
def get_market_news(category: str = "general") -> List[Dict[str, Any]]:
    """시장 전체 뉴스 조회"""
    return finnhub_client.get_market_news(category)[:5]


if __name__ == "__main__":
    # MCP 서버 실행
    mcp.run()
