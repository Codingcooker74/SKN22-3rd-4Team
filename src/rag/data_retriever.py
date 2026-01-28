"""
Data Retriever - 기업 데이터 통합 수집 모듈 (병렬 처리 최적화)
Supabase, VectorStore, GraphRAG, Finnhub 데이터를 병렬로 수집하여 성능을 극대화합니다.
"""

import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from supabase import Client
import os

logger = logging.getLogger(__name__)


class DataRetriever:
    """기업 분석에 필요한 모든 데이터를 병렬로 수집하는 유틸리티 클래스"""

    def __init__(
        self, supabase: Client, vector_store=None, graph_rag=None, finnhub=None
    ):
        self.supabase = supabase
        self.vector_store = vector_store
        self.graph_rag = graph_rag
        self.finnhub = finnhub

    def get_company_context_parallel(
        self, ticker: str, include_finnhub: bool = True, include_rag: bool = True
    ) -> Dict:
        """
        여러 소스에서 기업 데이터를 병렬로 수집합니다.
        기존 순차 호출 방식보다 수 초 이상 빠릅니다.
        """
        ticker = ticker.upper()
        results = {}

        # 병렬 실행을 위한 작업 정의
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 1. 기본 기업 정보 및 관계 (GraphRAG 또는 DB)
            info_future = executor.submit(self._fetch_company_info, ticker)
            rel_future = executor.submit(self._fetch_relationships, ticker)

            # 2. RAG 컨텍스트 (VectorStore)
            rag_future = None
            if include_rag and self.vector_store:
                rag_future = executor.submit(
                    self.vector_store.similarity_search,
                    f"Latest business overview and risks for {ticker}",
                    k=3,
                )

            # 3. 실시간 시세 및 지표 (Finnhub)
            quote_future = None
            rec_future = None
            target_future = None
            news_future = None
            metrics_future = None
            peers_future = None

            if include_finnhub and self.finnhub:
                quote_future = executor.submit(self.finnhub.get_quote, ticker)
                rec_future = executor.submit(
                    self.finnhub.get_recommendation_trends, ticker
                )
                target_future = executor.submit(self.finnhub.get_price_target, ticker)
                news_future = executor.submit(self.finnhub.get_company_news, ticker)
                metrics_future = executor.submit(
                    self.finnhub.get_basic_financials, ticker
                )
                peers_future = executor.submit(self.finnhub.get_company_peers, ticker)

            # 결과 수집
            results["company"] = info_future.result()
            results["relationships"] = rel_future.result()

            if rag_future:
                try:
                    docs = rag_future.result()
                    results["rag_context"] = (
                        "\n".join([d.get("content", "")[:500] for d in docs])
                        if docs
                        else ""
                    )
                except Exception:
                    results["rag_context"] = ""

            if include_finnhub and self.finnhub:
                results["finnhub"] = {
                    "quote": quote_future.result() if quote_future else {},
                    "recommendations": rec_future.result() if rec_future else [],
                    "price_target": target_future.result() if target_future else {},
                    "news": news_future.result()[:5] if news_future else [],
                    "metrics": metrics_future.result() if metrics_future else {},
                    "peers": peers_future.result() if peers_future else [],
                }

            # 재무 데이터 (ID가 필요하므로 info 결과 대기 후 필요시 호출)
            if results["company"] and "id" in results["company"]:
                company_id = results["company"]["id"]
                # 재무 데이터도 병렬 수집
                results["financials"] = self._fetch_financial_data_parallel(company_id)
            else:
                results["financials"] = {"annual": [], "quarterly": [], "prices": []}

        return results

    def _fetch_company_info(self, ticker: str) -> Optional[Dict]:
        """기본 정보 수집"""
        if self.graph_rag:
            try:
                return self.graph_rag.get_company(ticker)
            except Exception:
                pass

        try:
            res = (
                self.supabase.table("companies")
                .select("*")
                .eq("ticker", ticker)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception:
            return None

    def _fetch_relationships(self, ticker: str) -> List[Dict]:
        """관계 정보 수집"""
        if self.graph_rag:
            try:
                data = self.graph_rag.find_relationships(ticker)
                return (
                    (data.get("outgoing", []) + data.get("incoming", []))
                    if data
                    else []
                )
            except Exception:
                pass

        try:
            out = (
                self.supabase.table("company_relationships")
                .select("*")
                .eq("source_ticker", ticker)
                .execute()
            )
            inc = (
                self.supabase.table("company_relationships")
                .select("*")
                .eq("target_ticker", ticker)
                .execute()
            )
            return (out.data or []) + (inc.data or [])
        except Exception:
            return []

    def _fetch_financial_data_parallel(self, company_id: str) -> Dict:
        """재무 데이터를 병렬로 수집"""
        with ThreadPoolExecutor(max_workers=3) as executor:
            ann_f = executor.submit(
                lambda: self.supabase.table("annual_reports")
                .select("*")
                .eq("company_id", company_id)
                .order("fiscal_year", desc=True)
                .limit(3)
                .execute()
            )
            qrt_f = executor.submit(
                lambda: self.supabase.table("quarterly_reports")
                .select("*")
                .eq("company_id", company_id)
                .order("fiscal_year", desc=True)
                .order("fiscal_quarter", desc=True)
                .limit(4)
                .execute()
            )
            prc_f = executor.submit(
                lambda: self.supabase.table("stock_prices")
                .select("*")
                .eq("company_id", company_id)
                .order("price_date", desc=True)
                .limit(5)
                .execute()
            )

            return {
                "annual": ann_f.result().data or [],
                "quarterly": qrt_f.result().data or [],
                "prices": prc_f.result().data or [],
            }
