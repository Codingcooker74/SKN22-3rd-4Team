"""
실적 발표 캘린더 페이지
yfinance를 사용하여 관심 기업(Watchlist)의 실적 발표 일정만 표시
(무료/무제한/정확성 보장)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


@st.cache_data(ttl=3600)
def get_earnings_dates_yf(ticker: str) -> pd.DataFrame:
    """
    yfinance를 이용해 특정 기업의 earnings_dates 가져오기
    실패 시 빈 DataFrame 반환
    """
    try:
        import yfinance as yf

        stock = yf.Ticker(ticker)
        # earnings_dates는 미래/과거 일정을 index(Timestamp)로 가짐
        dates_df = stock.earnings_dates
        if dates_df is None or dates_df.empty:
            return pd.DataFrame()
        return dates_df
    except Exception:
        return pd.DataFrame()


def render():
    """실적 발표 캘린더 페이지 렌더링"""

    st.markdown(
        '<h1 class="main-header">🗓️ 실적 발표 캘린더</h1>',
        unsafe_allow_html=True,
    )
    st.caption("관심 기업(Watchlist) 전용 | Yahoo Finance 데이터 기반")

    st.markdown("---")

    # 날짜 범위 선택 (분기별)
    col1, col2 = st.columns([1, 2])

    current_year = datetime.now().year
    current_month = datetime.now().month
    current_q = (current_month - 1) // 3 + 1

    with col1:
        selected_year = st.number_input(
            "연도",
            min_value=current_year - 5,
            max_value=current_year + 1,
            value=current_year,
            key="calendar_year",
        )

    with col2:
        selected_quarter_str = st.radio(
            "분기 선택",
            options=[
                "1분기 (1~3월)",
                "2분기 (4~6월)",
                "3분기 (7~9월)",
                "4분기 (10~12월)",
            ],
            index=current_q - 1,
            horizontal=True,
            key="calendar_quarter_radio",
        )
        selected_quarter_idx = int(selected_quarter_str[0])

    # 날짜 계산
    q_map = {
        1: ("01-01", "03-31"),
        2: ("04-01", "06-30"),
        3: ("07-01", "09-30"),
        4: ("10-01", "12-31"),
    }
    start_md, end_md = q_map[selected_quarter_idx]
    start_date = datetime.strptime(f"{selected_year}-{start_md}", "%Y-%m-%d").date()
    end_date = datetime.strptime(f"{selected_year}-{end_md}", "%Y-%m-%d").date()

    st.info(f"📅 조회 기간: {start_date} ~ {end_date}")

    # 관심 기업 가져오기
    watchlist = st.session_state.get("watchlist", [])

    # 안내 메시지 (User Request: 즐겨찾기한 기업만 조회됨 명시)
    st.warning(
        """
        📢 **안내: 무료 API 제한으로 인해 '관심 기업(Watchlist)'에 등록된 종목의 일정만 조회가 가능합니다.**
        
        *전체 시장 데이터를 보시려면 유료 API 구독이 필요하므로, 현재는 가장 정확하고 무료인 관심 기업 위주로 제공됩니다.*
        """
    )

    if not watchlist:
        st.error(
            "⚠️ 관심 기업이 없습니다. [홈]에서 기업을 검색하여 ⭐ 버튼을 눌러주세요."
        )
        return

    if st.button("📅 일정 조회 (관심 기업)", type="primary", use_container_width=True):
        with st.spinner(f"관심 기업 {len(watchlist)}개의 실적 일정을 조회 중입니다..."):

            results = []
            progress_bar = st.progress(0)

            for idx, ticker in enumerate(watchlist):
                # 진행률 표시
                progress_bar.progress((idx + 1) / len(watchlist))

                # yfinance 데이터 가져오기
                e_df = get_earnings_dates_yf(ticker)

                if not e_df.empty:
                    # 인덱스가 Timestamp임
                    for date_idx, row in e_df.iterrows():
                        e_date = date_idx.date()
                        # 기간 필터링
                        if start_date <= e_date <= end_date:
                            # 필요한 컬럼 추출
                            eps_est = row.get("EPS Estimate")
                            eps_act = row.get("Reported EPS")
                            surprise = row.get("Surprise(%)")

                            # 포맷팅
                            eps_est = eps_est if pd.notna(eps_est) else None
                            eps_act = eps_act if pd.notna(eps_act) else None
                            surprise = (
                                f"{surprise * 100:.1f}%" if pd.notna(surprise) else "-"
                            )

                            results.append(
                                {
                                    "발표일": e_date.strftime("%Y-%m-%d"),
                                    "티커": ticker,
                                    "시간": "-",  # yfinance earnings_dates는 시간 정보가 불명확할 때가 많음
                                    "EPS 예상": (
                                        f"{eps_est:.2f}" if eps_est is not None else "-"
                                    ),
                                    "EPS 실제": (
                                        f"{eps_act:.2f}" if eps_act is not None else "-"
                                    ),
                                    "서프라이즈": surprise,
                                }
                            )

            progress_bar.empty()

            if not results:
                st.info("선택한 기간에 관심 기업의 실적 발표가 없습니다.")
            else:
                # DataFrame 변환 및 정렬
                df = pd.DataFrame(results)
                df = df.sort_values("발표일")

                st.success(f"📊 총 {len(df)}건의 실적 일정이 검색되었습니다.")

                # 날짜별 표시
                dates = sorted(df["발표일"].unique())
                for d in dates:
                    with st.expander(f"📅 {d}", expanded=True):
                        day_df = df[df["발표일"] == d].copy()
                        # 화면 표시용 컬럼 정리
                        st.dataframe(day_df, use_container_width=True, hide_index=True)

    # 관심 기업 관리 섹션
    st.markdown("---")
    st.markdown(f"### ⭐ 내 관심 기업 ({len(watchlist)}개)")

    if watchlist:
        cols = st.columns(6)
        for i, ticker in enumerate(watchlist):
            with cols[i % 6]:
                if st.button(f"✕ {ticker}", key=f"rm_cal_{ticker}"):
                    st.session_state.watchlist.remove(ticker)
                    st.rerun()
