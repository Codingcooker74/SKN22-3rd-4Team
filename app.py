"""
Main Streamlit application for Financial Analysis Bot
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import settings
from config.logging_config import setup_logging
from ui.pages import home, insights, report_page

# Setup logging
setup_logging(settings.LOG_LEVEL)

# Page configuration
st.set_page_config(
    page_title="미국 재무제표 분석 및 투자 인사이트 봇",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #6c757d;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        font-weight: 600;
        transition: transform 0.2s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
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
    "🏠 홈": home,
    "💡 투자 인사이트 (챗봇)": insights,
    "📊 레포트 생성": report_page,
}

selected_page = st.sidebar.radio(
    "페이지 선택", list(pages.keys()), label_visibility="collapsed"
)

st.sidebar.markdown("---")

# Sidebar info
with st.sidebar:
    st.markdown("### 📊 소개")
    st.markdown(
        """
    미국 상장사 재무제표를 AI로 분석하는 애플리케이션:
    
    - **GraphRAG**: 기업 간 관계 분석
    - **Text-to-SQL**: 자연어 질의응답
    - **AI 인사이트**: 투자 추천
    """
    )

# Main content routing
if selected_page in pages:
    pages[selected_page].render()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #6c757d; padding: 1rem;'>"
    "미국 재무제표 분석 및 투자 인사이트 봇 | AI로 구동 🚀"
    "</div>",
    unsafe_allow_html=True,
)
