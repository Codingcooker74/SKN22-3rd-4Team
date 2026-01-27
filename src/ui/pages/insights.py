"""
Investment insights page with AI Analyst Chatbot and Report Generator
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from rag.analyst_chat import AnalystChatbot
    from rag.report_generator import ReportGenerator

    RAG_AVAILABLE = True
except ImportError as e:
    RAG_AVAILABLE = False
    IMPORT_ERROR = str(e)


def render():
    """Render the investment insights page"""

    st.markdown('<h1 class="main-header">💡 투자 인사이트</h1>', unsafe_allow_html=True)

    st.markdown("AI 애널리스트와 대화하고, 투자 분석 레포트를 생성하세요")

    st.markdown("---")

    if not RAG_AVAILABLE:
        st.error(f"RAG 모듈 로드 실패: {IMPORT_ERROR}")
        st.info("pip install openai supabase 를 실행하세요")
        return

    # Tabs for different features
    tab1, tab2, tab3 = st.tabs(["💬 AI 챗봇", "📊 레포트 생성", "⚖️ 비교 분석"])

    with tab1:
        render_chatbot()

    with tab2:
        render_report_generator()

    with tab3:
        render_comparison()


def render_chatbot():
    """Render AI Analyst Chatbot"""

    st.markdown("### 🤖 AI 금융 애널리스트")
    st.caption("gpt-4.1-mini 기반 | 애널리스트/기자 스타일 응답")

    # Company selector
    col1, col2 = st.columns([3, 1])

    with col1:
        ticker = st.text_input(
            "분석할 회사 티커 (선택사항)",
            placeholder="AAPL, MSFT, GOOGL...",
            help="특정 회사에 대해 질문하려면 티커를 입력하세요",
        )

    with col2:
        use_rag = st.checkbox("RAG 사용", value=True, help="관련 문서 검색 활성화")

    # 추천 질문
    st.markdown("#### 💡 추천 질문")
    suggested_questions = [
        "현재 주가와 목표주가 차이는 얼마인가요?",
        "최근 실적 발표 내용을 요약해주세요",
        "애널리스트들의 투자 의견은 어떤가요?",
        "주요 경쟁사와 비교했을 때 장단점은?",
        "투자 리스크 요인은 무엇인가요?",
        "배당 정책과 배당수익률은 어떤가요?",
    ]

    # 추천 질문 버튼들
    cols = st.columns(2)
    for i, question in enumerate(suggested_questions):
        with cols[i % 2]:
            if st.button(f"💬 {question}", key=f"suggest_{i}", use_container_width=True):
                st.session_state.suggested_question = question
                st.rerun()

    st.markdown("---")

    # Initialize session state for chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "chatbot" not in st.session_state:
        try:
            st.session_state.chatbot = AnalystChatbot()
        except Exception as e:
            st.error(f"챗봇 초기화 실패: {e}")
            return

    # 추천 질문이 선택되었는지 확인
    suggested = st.session_state.pop("suggested_question", None)

    # Display chat history in a scrollable container
    chat_container = st.container(height=600)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat input processing
    prompt = st.chat_input("금융 관련 질문을 입력하세요...")

    # 추천 질문 버튼을 눌렀거나, 사용자가 입력을 했을 경우
    if suggested:
        prompt = suggested

    if prompt:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Generate response
        try:
            with st.spinner("분석 중..."):
                response = st.session_state.chatbot.chat(
                    prompt, ticker=ticker.upper() if ticker else None, use_rag=use_rag
                )

            # Add assistant message
            st.session_state.chat_history.append({"role": "assistant", "content": response})

            # Rerun to update chat history in container
            st.rerun()

        except Exception as e:
            st.error(f"응답 생성 실패: {e}")

    # Clear chat button
    if st.button("🗑️ 대화 초기화"):
        st.session_state.chat_history = []
        st.session_state.chatbot.clear_history()
        st.rerun()


def render_report_generator():
    """Render Report Generator"""

    st.markdown("### 📊 투자 분석 레포트")
    st.caption("gpt-5-nano 기반 | 구조화된 투자 리서치 보고서")

    col1, col2 = st.columns([3, 1])

    with col1:
        ticker = st.text_input("회사 티커", placeholder="AAPL", key="report_ticker")

    with col2:
        generate_btn = st.button("📝 레포트 생성", type="primary", use_container_width=True)

    if generate_btn and ticker:
        try:
            generator = ReportGenerator()

            with st.spinner(f"📊 {ticker.upper()} 분석 레포트 생성 중..."):
                report = generator.generate_report(ticker.upper())

            st.markdown("---")
            st.markdown(report)

            # Download button
            st.download_button(
                label="📥 레포트 다운로드 (MD)",
                data=report,
                file_name=f"{ticker.upper()}_analysis_report.md",
                mime="text/markdown",
            )

        except Exception as e:
            st.error(f"레포트 생성 실패: {e}")

    elif generate_btn:
        st.warning("티커를 입력해주세요")


def render_comparison():
    """Render Comparison Analysis"""

    st.markdown("### ⚖️ 기업 비교 분석")

    tickers_input = st.text_input(
        "비교할 회사 티커들 (쉼표로 구분)", placeholder="AAPL, MSFT, GOOGL"
    )

    if st.button("📊 비교 분석", type="primary"):
        if tickers_input:
            tickers = [t.strip().upper() for t in tickers_input.split(",")]

            if len(tickers) < 2:
                st.warning("2개 이상의 회사를 입력해주세요")
                return

            try:
                generator = ReportGenerator()

                with st.spinner(f"⚖️ {', '.join(tickers)} 비교 분석 중..."):
                    report = generator.generate_comparison_report(tickers)

                st.markdown("---")
                st.markdown(report)

                # Download button for comparison report
                st.download_button(
                    label="📥 비교 레포트 다운로드 (MD)",
                    data=report,
                    file_name=f"comparison_{'_'.join(tickers)}.md",
                    mime="text/markdown",
                )

            except Exception as e:
                st.error(f"비교 분석 실패: {e}")
        else:
            st.warning("비교할 회사 티커를 입력해주세요")
