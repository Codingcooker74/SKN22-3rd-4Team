"""
Supabase 데이터베이스 클라이언트
앱에서 Supabase DB에 연결하여 데이터를 조회/저장합니다.
"""

import os
from typing import Optional, List, Dict, Any
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class SupabaseClient:
    """Supabase 데이터베이스 클라이언트"""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """싱글톤 Supabase 클라이언트 반환"""
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")

            if not url or not key:
                raise ValueError("SUPABASE_URL과 SUPABASE_KEY가 설정되어야 합니다.")

            cls._instance = create_client(url, key)

        return cls._instance

    @classmethod
    def get_all_companies(cls) -> pd.DataFrame:
        """모든 기업 정보 조회"""
        client = cls.get_client()
        result = client.table("companies").select("*").order("ticker").execute()
        return pd.DataFrame(result.data)

    @classmethod
    def get_company_by_ticker(cls, ticker: str) -> Optional[Dict]:
        """티커로 기업 정보 조회"""
        client = cls.get_client()
        result = client.table("companies").select("*").eq("ticker", ticker).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_annual_reports(
        cls, company_id: str = None, ticker: str = None
    ) -> pd.DataFrame:
        """연간 재무 데이터 조회"""
        client = cls.get_client()

        query = client.table("annual_reports").select(
            "*, companies(ticker, company_name)"
        )

        if company_id:
            query = query.eq("company_id", company_id)

        result = query.order("fiscal_year", desc=True).execute()

        if not result.data:
            return pd.DataFrame()

        # DataFrame 생성 및 정리
        df = pd.DataFrame(result.data)

        # companies 정보 분리
        if "companies" in df.columns:
            df["ticker"] = df["companies"].apply(
                lambda x: x.get("ticker") if x else None
            )
            df["company_name"] = df["companies"].apply(
                lambda x: x.get("company_name") if x else None
            )
            df = df.drop(columns=["companies"])

        # 티커 필터
        if ticker and "ticker" in df.columns:
            df = df[df["ticker"] == ticker]

        return df

    @classmethod
    def get_financial_summary(cls, ticker: str) -> Dict:
        """특정 기업의 재무 요약 정보"""
        client = cls.get_client()

        # 기업 정보
        company = cls.get_company_by_ticker(ticker)
        if not company:
            return {}

        # 연간 재무 데이터
        reports = (
            client.table("annual_reports")
            .select("*")
            .eq("company_id", company["id"])
            .order("fiscal_year", desc=True)
            .limit(5)
            .execute()
        )

        return {"company": company, "annual_reports": reports.data}

    @classmethod
    def get_top_companies_by_revenue(
        cls, year: int = 2024, limit: int = 20
    ) -> pd.DataFrame:
        """매출 상위 기업 조회"""
        client = cls.get_client()

        result = (
            client.table("annual_reports")
            .select(
                "revenue, net_income, total_assets, companies(ticker, company_name)"
            )
            .eq("fiscal_year", year)
            .not_.is_("revenue", "null")
            .order("revenue", desc=True)
            .limit(limit)
            .execute()
        )

        if not result.data:
            return pd.DataFrame()

        df = pd.DataFrame(result.data)
        df["ticker"] = df["companies"].apply(lambda x: x.get("ticker") if x else None)
        df["company_name"] = df["companies"].apply(
            lambda x: x.get("company_name") if x else None
        )
        df = df.drop(columns=["companies"])

        return df

    @classmethod
    def get_financial_ratios(cls, year: int = 2024) -> pd.DataFrame:
        """주요 재무비율 조회"""
        client = cls.get_client()

        result = (
            client.table("annual_reports")
            .select(
                "profit_margin, roe, roa, debt_to_equity, companies(ticker, company_name)"
            )
            .eq("fiscal_year", year)
            .execute()
        )

        if not result.data:
            return pd.DataFrame()

        df = pd.DataFrame(result.data)
        df["ticker"] = df["companies"].apply(lambda x: x.get("ticker") if x else None)
        df["company_name"] = df["companies"].apply(
            lambda x: x.get("company_name") if x else None
        )
        df = df.drop(columns=["companies"])

        return df

    @classmethod
    def search_companies(cls, query: str) -> pd.DataFrame:
        """기업 검색 (티커, 영문명 또는 한글명으로)"""
        client = cls.get_client()

        result = (
            client.table("companies")
            .select("*")
            .or_(
                f"ticker.ilike.%{query}%,company_name.ilike.%{query}%,korean_name.ilike.%{query}%"
            )
            .execute()
        )

        return pd.DataFrame(result.data)

    @classmethod
    def execute_query(cls, query: str) -> pd.DataFrame:
        """RPC를 통한 사용자 정의 쿼리 실행 (제한적)"""
        # Supabase는 직접 SQL 실행을 지원하지 않음
        # 대신 저장 함수(RPC)를 통해 실행해야 함
        client = cls.get_client()
        # 여기서는 기본 테이블 조회만 지원
        return pd.DataFrame()


# 편의 함수
def get_supabase() -> Client:
    """Supabase 클라이언트 가져오기"""
    return SupabaseClient.get_client()


def get_companies() -> pd.DataFrame:
    """모든 기업 목록"""
    return SupabaseClient.get_all_companies()


def get_company_financials(ticker: str) -> Dict:
    """기업 재무 정보"""
    return SupabaseClient.get_financial_summary(ticker)


def get_top_revenue_companies(year: int = 2024, limit: int = 20) -> pd.DataFrame:
    """매출 상위 기업"""
    return SupabaseClient.get_top_companies_by_revenue(year, limit)
