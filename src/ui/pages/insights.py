"""
Investment insights page with AI Analyst Chatbot and Report Generator
"""

import streamlit as st
import pandas as pd
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from rag.analyst_chat import AnalystChatbot
    from rag.report_generator import ReportGenerator
    from utils.pdf_utils import create_pdf

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

    # Chatbot only
    render_chatbot()


def render_chatbot():
    """Render AI Analyst Chatbot"""

    st.markdown("### 🤖 AI 금융 애널리스트")
    st.caption("gpt-4.1-mini 기반 | 애널리스트/기자 스타일 응답")

    st.info(
        "💡 **팁**: '애플 등록해줘'라고 말하면 기업을 등록할 수 있고, '엔비디아와 비교해줘'라고 하면 비교 분석을 수행합니다."
    )

    # 추천 질문
    st.markdown("#### 💡 추천 질문")
    suggested_questions = [
        "현재 주가와 목표주가 차이는 얼마인가요?",
        "최근 실적 발표 내용을 요약해주세요",
        "애널리스트들의 투자 의견은 어떤가요?",
        "주요 경쟁사와 비교했을 때 장단점은?",
        "투자 리스크 요인은 무엇인가요?",
        "애플 등록해줘 (데이터 수집)",
    ]

    # 추천 질문 버튼들
    cols = st.columns(2)
    for i, question in enumerate(suggested_questions):
        with cols[i % 2]:
            if st.button(
                f"💬 {question}", key=f"suggest_{i}", use_container_width=True
            ):
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

    # 1. Chat History Container (Show only if history exists)
    if st.session_state.chat_history:
        chat_container = st.container(height=400)
        with chat_container:
            for i, msg in enumerate(st.session_state.chat_history):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

                    # Check for chart data
                    if msg.get("chart_data"):
                        chart_data = msg["chart_data"]
                        if "c" in chart_data and "t" in chart_data:
                            ticker = chart_data.get("ticker", "Stock")
                            closes = chart_data["c"]
                            timestamps = chart_data["t"]
                            dates = [datetime.fromtimestamp(t) for t in timestamps]

                            df = pd.DataFrame({"Date": dates, "Price": closes})
                            df.set_index("Date", inplace=True)

                            st.subheader(f"📈 {ticker} 주가 추이")
                            st.line_chart(df)
                            st.caption(f"최근 {len(closes)}일/구간 데이터 ({ticker})")

                    # Check for downloadable report
                    if msg.get("report"):
                        # Check if backend already specified the type
                        report_type = msg.get("report_type", "md")

                        if report_type == "pdf":
                            # Backend already converted to PDF
                            report_data = msg["report"]
                            mime_type = "application/pdf"
                            file_ext = "pdf"
                            label = "📥 분석 레포트 다운로드 (PDF)"
                        else:
                            # Markdown format
                            report_data = (
                                msg["report"].encode("utf-8")
                                if isinstance(msg["report"], str)
                                else msg["report"]
                            )
                            mime_type = "text/markdown"
                            file_ext = "md"
                            label = "📥 분석 레포트 다운로드 (MD)"

                        st.download_button(
                            label=label,
                            data=report_data,
                            file_name=f"analysis_report_{i}.{file_ext}",
                            mime=mime_type,
                            key=f"chat_dl_{i}",
                        )
    else:
        st.info(
            "👆 추천 질문을 선택하거나, 아래 입력창에 질문을 입력하여 대화를 시작하세요."
        )

    st.markdown("---")

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
            with st.spinner("분석 중... (시간이 걸릴 수 있습니다)"):
                # Ticker is now automatically detected by the chatbot from the prompt
                result = st.session_state.chatbot.chat(prompt, use_rag=True)

            # Handle structured response from chatbot
            if isinstance(result, dict):
                content = result["content"]
                report = result.get("report")
                report_type = result.get("report_type", "md")
            else:
                content = result
                report = None
                report_type = "md"

            # Add assistant message with report and report_type
            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": content,
                    "report": report,
                    "report_type": report_type,
                    "chart_data": (
                        result.get("chart_data") if isinstance(result, dict) else None
                    ),
                }
            )

            # Rerun to update chat history in container
            st.rerun()

        except Exception as e:
            st.error(f"응답 생성 실패: {e}")

    # Clear chat button
    if st.button("🗑️ 대화 초기화"):
        st.session_state.chat_history = []
        st.session_state.chatbot.clear_history()
        st.rerun()
