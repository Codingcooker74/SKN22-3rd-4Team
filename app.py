"""
Main Streamlit application for Financial Analysis Bot
"""

import streamlit as st
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import settings
from config.logging_config import setup_logging
from tools.scheduler_manager import init_scheduler, render_sidebar_status

# Setup logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


# ============================================================
# S&P 500 스케줄러 초기화 (앱 시작 시 1회만 실행)
# ============================================================
if "scheduler_initialized" not in st.session_state:
    init_scheduler()
    st.session_state.scheduler_initialized = True

# Page configuration
st.set_page_config(
    page_title="미국 재무제표 분석 및 투자 인사이트 봇",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Custom CSS Loading
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Load global styles
css_path = Path(__file__).parent / "src" / "ui" / "styles.css"
if css_path.exists():
    load_css(str(css_path))
else:
    # Fallback if file not found (keep basic styles)
    st.markdown(
        """
    <style>
        [data-testid="stVerticalBlock"] > [style*="flex-direction"] {
            margin-top: -2rem !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

# Sidebar navigation
# Sidebar navigation
st.sidebar.title("🏦 메뉴")
st.sidebar.markdown("---")

# Page navigation
pages = {
    "🏠 홈": "ui.pages.home",
    "💡 투자 인사이트 (챗봇)": "ui.pages.insights",
    "📅 실적 캘린더": "ui.pages.calendar_page",
    "📊 레포트 생성": "ui.pages.report_page",
}

selected_page = st.sidebar.radio(
    "페이지 선택", list(pages.keys()), label_visibility="collapsed"
)

# ============================================================
# 스케줄러 상태 표시 / 관심 기업 표시 (사이드바)
# ============================================================
st.sidebar.markdown("---")
render_sidebar_status()

st.sidebar.markdown("---")
with st.sidebar.expander("⭐ 관심 기업", expanded=True):
    # 관심 기업 초기화
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []

    watchlist = st.session_state.watchlist

    if watchlist:
        # 리스트 복사본으로 순회하여 삭제 시 문제 방지
        for ticker in list(watchlist):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"📈 {ticker}")
            with col2:
                if st.button("✕", key=f"sidebar_rm_{ticker}", help="제거"):
                    st.session_state.watchlist.remove(ticker)
                    st.rerun()
        st.caption(f"총 {len(st.session_state.watchlist)}개")
    else:
        st.caption("홈 > 기업 검색에서\n⭐ 버튼으로 추가")

st.sidebar.markdown("---")

# Main content routing (Lazy Loading)
if selected_page in pages:
    module_path = pages[selected_page]
    try:
        # importlib을 사용하여 동적 import
        import importlib

        # ui.pages가 src 패키지 아래에 있으므로 경로 조정이 필요할 수 있음
        # sys.path에 src가 이미 추가되어 있으므로 바로 import 가능
        if module_path.startswith("ui."):
            page_module = importlib.import_module(f"src.{module_path}")
        else:
            page_module = importlib.import_module(module_path)

        if hasattr(page_module, "render"):
            page_module.render()
        else:
            st.error(f"모듈 {module_path}에 render 함수가 없습니다.")

    except Exception as e:
        st.error(f"페이지 로드 실패: {e}")
        # 디버깅을 위한 상세 로그
        logger.error(f"Failed to load page {module_path}: {e}", exc_info=True)
