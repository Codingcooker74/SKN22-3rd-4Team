"""
홈 페이지 - Supabase DB 연동
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from src.data.supabase_client import (
        SupabaseClient,
        get_companies,
        get_top_revenue_companies,
    )

    SUPABASE_AVAILABLE = True
except Exception as e:
    SUPABASE_AVAILABLE = False
    print(f"Supabase 연결 실패: {e}")

# 환율 클라이언트 import
try:
    from src.tools.exchange_rate_client import get_exchange_client

    EXCHANGE_AVAILABLE = True
except Exception as e:
    EXCHANGE_AVAILABLE = False
    print(f"환율 클라이언트 로드 실패: {e}")


def format_number(value, unit=""):
    """숫자 포맷팅 (억 단위)"""
    if pd.isna(value) or value is None:
        return "-"

    if abs(value) >= 1e12:
        return f"${value/1e12:.1f}조{unit}"
    elif abs(value) >= 1e9:
        return f"${value/1e9:.1f}B{unit}"
    elif abs(value) >= 1e6:
        return f"${value/1e6:.1f}M{unit}"
    else:
        return f"${value:,.0f}{unit}"


def render():
    """홈 페이지 렌더링"""

    # Header
    st.markdown(
        '<h1 class="main-header">📊 미국 재무제표 분석 및 투자 인사이트 봇</h1>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p class="sub-header">AI 기반 미국 상장사 재무제표 분석 도구</p>',
        unsafe_allow_html=True,
    )

    # 데이터베이스 연결 상태
    if SUPABASE_AVAILABLE:
        try:
            companies_df = get_companies()
            company_count = len(companies_df)
            # 연결 성공 시 조용히 진행
        except Exception as e:
            st.warning(f"⚠️ 데이터 로드 중 오류: {e}")
            companies_df = pd.DataFrame()
            company_count = 0
    else:
        st.warning("⚠️ Supabase 연결이 설정되지 않았습니다. .env 파일을 확인하세요.")
        companies_df = pd.DataFrame()
        company_count = 0

    st.markdown("---")

    # 메트릭 카드
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="📈 등록된 기업", value=f"{company_count}개")

    with col2:
        if SUPABASE_AVAILABLE and company_count > 0:
            try:
                annual_df = SupabaseClient.get_annual_reports()
                report_count = len(annual_df)
            except:
                report_count = 0
        else:
            report_count = 0

        st.metric(label="📊 재무 레코드", value=f"{report_count}개")

    with col3:
        st.metric(label="📅 데이터 기간", value="2020-2025")

    with col4:
        st.metric(label="🔄 마지막 업데이트", value="오늘")

    # 환율 정보 섹션
    st.markdown("---")
    st.markdown("### 💱 실시간 환율 정보")

    if EXCHANGE_AVAILABLE:
        try:
            exchange_client = get_exchange_client()
            summary = exchange_client.get_major_rates_summary()
            display_rates = summary.get("display_rates", {})
            update_time = summary.get("update_time", "N/A")

            rate_col1, rate_col2, rate_col3, rate_col4 = st.columns(4)

            with rate_col1:
                st.metric(
                    label="🇺🇸 달러 (USD/KRW)",
                    value=display_rates.get("USD/KRW", "-"),
                )

            with rate_col2:
                st.metric(
                    label="🇯🇵 엔화 (100 JPY/KRW)",
                    value=display_rates.get("JPY/KRW (100엔)", "-"),
                )

            with rate_col3:
                st.metric(
                    label="🇪🇺 유로 (EUR/KRW)",
                    value=display_rates.get("EUR/KRW", "-"),
                )

            with rate_col4:
                st.metric(
                    label="🇬🇧 파운드 (GBP/KRW)",
                    value=display_rates.get("GBP/KRW", "-"),
                )

            # 환율 정보 출처 표시
            st.caption(
                f"📅 실시간 정보 (한국시간: {update_time}) | 출처: Global Open Exchange | 기준: KRW (매매기준율)"
            )

        except Exception as e:
            st.warning(f"환율 정보를 불러올 수 없습니다: {e}")
    else:
        st.info("💱 환율 정보 서비스가 비활성화되어 있습니다.")

    st.markdown("---")

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📊 매출 상위 기업", "🔍 기업 검색", "💡 빠른 시작"])

    with tab1:
        st.markdown("### 📊 2024년 매출 상위 20개 기업")

        if SUPABASE_AVAILABLE and company_count > 0:
            try:
                top_df = get_top_revenue_companies(year=2024, limit=20)

                if not top_df.empty:
                    # 데이터 포맷팅
                    display_df = top_df[
                        [
                            "ticker",
                            "company_name",
                            "revenue",
                            "net_income",
                            "total_assets",
                        ]
                    ].copy()
                    display_df.columns = ["티커", "기업명", "매출", "순이익", "총자산"]

                    # 숫자 포맷팅
                    display_df["매출"] = display_df["매출"].apply(
                        lambda x: format_number(x)
                    )
                    display_df["순이익"] = display_df["순이익"].apply(
                        lambda x: format_number(x)
                    )
                    display_df["총자산"] = display_df["총자산"].apply(
                        lambda x: format_number(x)
                    )

                    st.dataframe(display_df, use_container_width=True, hide_index=True)

                    # 차트
                    st.markdown("### 📈 매출 비교 차트")
                    chart_df = top_df[["ticker", "revenue"]].dropna().head(10)
                    chart_df["revenue"] = chart_df["revenue"] / 1e9  # 10억 달러 단위
                    chart_df = chart_df.set_index("ticker")
                    st.bar_chart(chart_df, use_container_width=True)
                else:
                    st.info("2024년 데이터가 아직 없습니다.")
            except Exception as e:
                st.error(f"데이터 로드 오류: {e}")
        else:
            st.info("Supabase에 연결하여 데이터를 확인하세요.")

    with tab2:
        st.markdown("### 🔍 기업 검색")

        search_query = st.text_input(
            "티커 또는 기업명으로 검색", placeholder="예: AAPL, Apple, Microsoft"
        )

        if search_query and SUPABASE_AVAILABLE:
            try:
                results = SupabaseClient.search_companies(search_query)

                if not results.empty:
                    st.success(f"{len(results)}개 기업 검색됨")

                    for _, company in results.iterrows():
                        with st.expander(
                            f"📊 {company['ticker']} - {company['company_name']}"
                        ):
                            # 기업 재무 정보 조회
                            financials = SupabaseClient.get_financial_summary(
                                company["ticker"]
                            )

                            if financials and financials.get("annual_reports"):
                                reports = financials["annual_reports"]

                                col1, col2, col3 = st.columns(3)

                                # 최신 연도 데이터
                                latest = reports[0] if reports else {}

                                with col1:
                                    st.metric(
                                        "매출", format_number(latest.get("revenue"))
                                    )
                                with col2:
                                    st.metric(
                                        "순이익",
                                        format_number(latest.get("net_income")),
                                    )
                                with col3:
                                    st.metric(
                                        "총자산",
                                        format_number(latest.get("total_assets")),
                                    )

                                # 연도별 데이터 테이블
                                reports_df = pd.DataFrame(reports)
                                if not reports_df.empty:
                                    display_cols = [
                                        "fiscal_year",
                                        "revenue",
                                        "net_income",
                                        "eps",
                                    ]
                                    available_cols = [
                                        c
                                        for c in display_cols
                                        if c in reports_df.columns
                                    ]
                                    st.dataframe(
                                        reports_df[available_cols], hide_index=True
                                    )
                            else:
                                st.info("재무 데이터가 없습니다.")
                else:
                    st.warning("검색 결과가 없습니다.")
            except Exception as e:
                st.error(f"검색 오류: {e}")

    with tab3:
        st.markdown("### 💡 빠른 시작 가이드")

        st.markdown(
            """
        #### 🎯 이 앱으로 할 수 있는 것들
        
        **1. 📥 데이터 수집 (기업 등록)**
        - Finnhub API를 통한 실시간 데이터 수집 및 업데이트
        - 기업 정보, 주가, 뉴스 데이터 자동 동기화
        
        **2. 🌐 그래프 분석**
        - 기업 간 관계 시각화
        - 파트너십, 경쟁사, 공급망 분석
        
        **3. 💬 SQL 쿼리**
        - 자연어로 질문하면 SQL로 변환
        - "Apple의 지난 3년 매출은?" → 즉시 답변
        
        **4. 💡 투자 인사이트**
        - AI 기반 재무 분석 및 레포트 생성
        - 투자 추천 및 리스크 평가
        
        ---
        
        #### 📊 현재 데이터베이스 현황
        """
        )

        if SUPABASE_AVAILABLE and company_count > 0:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**등록된 기업 (일부)**")
                if not companies_df.empty:
                    st.dataframe(
                        companies_df[["ticker", "company_name"]].head(10),
                        hide_index=True,
                        use_container_width=True,
                    )

            with col2:
                st.markdown("**섹터별 분포**")
                # 섹터 정보가 있다면 표시
                if (
                    "sector" in companies_df.columns
                    and companies_df["sector"].notna().any()
                ):
                    sector_counts = companies_df["sector"].value_counts()
                    st.bar_chart(sector_counts)
                else:
                    st.info("섹터 정보가 아직 없습니다.")
        else:
            st.info(
                "데이터를 수집하려면 '투자 인사이트' 페이지에서 '애플 등록해줘'와 같이 요청하세요."
            )

        # 샘플 질문
        st.markdown("---")
        st.markdown("#### 💬 샘플 질문 (SQL 쿼리 페이지에서 시도해보세요)")

        sample_questions = [
            "Apple의 2024년 매출과 순이익은?",
            "매출 상위 10개 기업을 보여줘",
            "순이익률이 가장 높은 기업은?",
            "AAPL, MSFT, GOOGL, AMZN, NFLX의 총자산을 비교해줘",
            "2023년 대비 2024년 매출이 증가한 기업은?",
        ]

        for q in sample_questions:
            st.code(q, language=None)
