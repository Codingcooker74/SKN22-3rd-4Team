"""
Investment insights page with AI Analyst Chatbot and Report Generator
ChatConnector 통합 - 프롬프트 인젝션 방어 및 세션 관리 포함
"""

import streamlit as st
import pandas as pd
import sys
from datetime import datetime
from pathlib import Path
import uuid

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ChatConnector 로드 (보안 레이어 포함)
try:
    from core.chat_connector import ChatConnector, ChatRequest, get_chat_connector
    from core.input_validator import ThreatLevel
    CONNECTOR_AVAILABLE = True
except ImportError:
    try:
        from src.core.chat_connector import ChatConnector, ChatRequest, get_chat_connector
        from src.core.input_validator import ThreatLevel
        CONNECTOR_AVAILABLE = True
    except ImportError as e:
        CONNECTOR_AVAILABLE = False
        CONNECTOR_ERROR = str(e)

# 레거시 임포트 (fallback)
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

    # ChatConnector 사용 가능 여부 확인
    if CONNECTOR_AVAILABLE:
        render_chatbot_secure()
    elif RAG_AVAILABLE:
        st.warning("⚠️ 보안 레이어 로드 실패. 기본 모드로 실행합니다.")
        render_chatbot_legacy()
    else:
        st.error(f"RAG 모듈 로드 실패: {IMPORT_ERROR}")
        st.info("pip install openai supabase 를 실행하세요")


def render_chatbot_secure():
    """Render AI Analyst Chatbot with ChatConnector (secure mode)"""

    st.markdown("### 🤖 AI 금융 애널리스트")
    st.caption("gpt-4.1-mini 기반 | 프롬프트 인젝션 방어 활성화 🛡️")

    # 세션 정보 표시
    col1, col2, col3 = st.columns(3)
    
    # 세션 ID 초기화
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:16]
    
    # ChatConnector 초기화
    if "chat_connector" not in st.session_state:
        try:
            st.session_state.chat_connector = get_chat_connector(strict_mode=False)
        except Exception as e:
            st.error(f"ChatConnector 초기화 실패: {e}")
            return
    
    connector = st.session_state.chat_connector
    session_info = connector.get_session_info(st.session_state.session_id)
    
    with col1:
        msg_count = session_info.get("message_count", 0) if session_info else 0
        st.metric("💬 대화 수", msg_count)
    
    with col2:
        warnings = session_info.get("warnings", 0) if session_info else 0
        st.metric("⚠️ 경고", warnings)
    
    with col3:
        status = "🟢 정상" if not (session_info and session_info.get("is_blocked")) else "🔴 차단"
        st.metric("상태", status)

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

    # 추천 질문이 선택되었는지 확인
    suggested = st.session_state.pop("suggested_question", None)

    # Chat History Container
    if st.session_state.chat_history:
        chat_container = st.container(height=400)
        with chat_container:
            for i, msg in enumerate(st.session_state.chat_history):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

                    # 에러 메시지 표시 (보안 관련)
                    if msg.get("error_code"):
                        error_code = msg["error_code"]
                        if error_code == "INPUT_REJECTED":
                            st.warning("⚠️ 입력이 보안 정책에 의해 필터링되었습니다.")
                        elif error_code == "RATE_LIMITED":
                            st.warning("⏱️ 요청 제한에 도달했습니다. 잠시 후 다시 시도하세요.")

                    # Chart data
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

                    # Downloadable report
                    if msg.get("report"):
                        report_type = msg.get("report_type", "md")

                        if report_type == "pdf":
                            report_data = msg["report"]
                            mime_type = "application/pdf"
                            file_ext = "pdf"
                            label = "📥 분석 레포트 다운로드 (PDF)"
                        else:
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

        # Generate response via ChatConnector
        try:
            with st.spinner("분석 중... (시간이 걸릴 수 있습니다)"):
                request = ChatRequest(
                    session_id=st.session_state.session_id,
                    message=prompt,
                    use_rag=True
                )
                response = connector.process_message(request)

            if response.success:
                # Add assistant message with report and report_type
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": response.content,
                        "report": response.report,
                        "report_type": response.report_type,
                        "chart_data": response.chart_data,
                    }
                )
            else:
                # 실패 응답 처리
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": response.content,
                        "error_code": response.error_code,
                    }
                )

            # Rerun to update chat history in container
            st.rerun()

        except Exception as e:
            st.error(f"응답 생성 실패: {e}")

    # Control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ 대화 초기화"):
            st.session_state.chat_history = []
            connector.clear_session(st.session_state.session_id)
            st.rerun()
    
    with col2:
        if st.button("🔄 세션 새로고침"):
            st.session_state.session_id = str(uuid.uuid4())[:16]
            st.session_state.chat_history = []
            st.rerun()


def render_chatbot_legacy():
    """Render AI Analyst Chatbot (legacy mode without security layer)"""

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

    # Chat History Container
    if st.session_state.chat_history:
        chat_container = st.container(height=400)
        with chat_container:
            for i, msg in enumerate(st.session_state.chat_history):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

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

                    if msg.get("report"):
                        report_type = msg.get("report_type", "md")

                        if report_type == "pdf":
                            report_data = msg["report"]
                            mime_type = "application/pdf"
                            file_ext = "pdf"
                            label = "📥 분석 레포트 다운로드 (PDF)"
                        else:
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

    if suggested:
        prompt = suggested

    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        try:
            with st.spinner("분석 중... (시간이 걸릴 수 있습니다)"):
                result = st.session_state.chatbot.chat(prompt, use_rag=True)

            if isinstance(result, dict):
                content = result["content"]
                report = result.get("report")
                report_type = result.get("report_type", "md")
            else:
                content = result
                report = None
                report_type = "md"

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

            st.rerun()

        except Exception as e:
            st.error(f"응답 생성 실패: {e}")

    # Clear chat button
    if st.button("🗑️ 대화 초기화"):
        st.session_state.chat_history = []
        st.session_state.chatbot.clear_history()
        st.rerun()
