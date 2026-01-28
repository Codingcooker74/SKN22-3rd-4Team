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

# 헬퍼 함수 로드
try:
    from ui.helpers.insights_helper import (
        get_suggested_questions,
        render_disclaimer,
        render_page_css,
    )
except ImportError:
    from src.ui.helpers.insights_helper import (
        get_suggested_questions,
        render_disclaimer,
        render_page_css,
    )

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


def render():
    """Render the investment insights page"""

    # ChatConnector 사용 가능 여부 확인
    if CONNECTOR_AVAILABLE:
        render_chatbot_secure()
    else:
        st.error(f"모듈 로드 실패: ChatConnector를 사용할 수 없습니다.")
        st.info("pip install openai supabase 를 실행하세요")



def render_chatbot_secure():
    """Render AI Analyst Chatbot with ChatConnector (secure mode)"""

    # CSS 적용
    render_page_css()
    
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
    
    # 헤더: 왼쪽 - 투자 인사이트 | 오른쪽 - AI 금융 애널리스트 + 세션 정보
    left_col, right_col = st.columns([1, 1])
    
    with left_col:
        st.markdown('<h1 class="main-header">� 투자 인사이트</h1>', unsafe_allow_html=True)
    
    with right_col:
        st.markdown("### 🤖 AI 금융 애널리스트")
        # 세션 정보를 한 줄에 표시
        msg_count = session_info.get("message_count", 0) if session_info else 0
        warnings = session_info.get("warnings", 0) if session_info else 0
        status = "🟢 정상" if not (session_info and session_info.get("is_blocked")) else "🔴 차단"
        
        info_col1, info_col2, info_col3 = st.columns(3)
        with info_col1:
            st.metric("💬 대화", msg_count)
        with info_col2:
            st.metric("⚠️ 경고", warnings)
        with info_col3:
            st.metric("상태", status)



    # Initialize session state for chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

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
        pass  # 채팅 히스토리가 없을 때 빈 상태

    # 추천 질문 표시 (대화가 있을 때만)
    if st.session_state.get("chat_history"):
        st.markdown("#### 💡 추천 질문")
        suggested_questions = get_suggested_questions()

        msg_count = len(st.session_state.chat_history)
        cols = st.columns(2)
        for i, question in enumerate(suggested_questions):
            with cols[i % 2]:
                if st.button(f"💬 {question}", key=f"suggest_{msg_count}_{i}", use_container_width=True):
                    st.session_state.pending_question = question
                    st.rerun()

    # Chat input - st.form 사용 (Enter 중복 방지)
    with st.form(key="chat_form", clear_on_submit=True):
        input_col, send_col = st.columns([6, 1])
        
        with input_col:
            user_input = st.text_input(
                "질문 입력",
                placeholder="'애플 등록해줘' 또는 '엔비디아와 비교해줘'를 입력해보세요.",
                label_visibility="collapsed"
            )
        
        with send_col:
            submitted = st.form_submit_button("📤", use_container_width=True)

    # Control buttons - 채팅 입력창 바로 아래
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.chat_history = []
            connector.clear_session(st.session_state.session_id)
            st.rerun()
    
    with col2:
        if st.button("🔄 세션 새로고침", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())[:16]
            st.session_state.chat_history = []
            st.rerun()

    # pending_question (추천 질문에서 온 입력) 처리
    pending = st.session_state.pop("pending_question", None)
    
    # prompt 결정
    prompt = None
    if pending:
        prompt = pending
    elif submitted and user_input.strip():
        prompt = user_input.strip()

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

    # 면책 조항 (하단 고정)
    render_disclaimer()
