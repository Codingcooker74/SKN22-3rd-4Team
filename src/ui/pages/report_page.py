"""
Investment Report Generation Page
"""

import streamlit as st
from rag.report_generator import ReportGenerator
from utils.pdf_utils import create_pdf


def render():
    """Render Report Generator Page"""
    st.markdown('<h1 class="main-header">📊 레포트 생성</h1>', unsafe_allow_html=True)
    st.caption("gpt-5-nano 기반 | 구조화된 투자 리서치 보고서 생성")

    st.markdown("---")

    col1, col2 = st.columns([3, 1])

    with col1:
        ticker = st.text_input(
            "분석할 회사 티커", placeholder="AAPL, MSFT...", key="report_ticker_main"
        )

    with col2:
        generate_btn = st.button(
            "📝 레포트 생성",
            type="primary",
            use_container_width=True,
            key="gen_btn_main",
        )

    if generate_btn and ticker:
        try:
            generator = ReportGenerator()

            # Check if multiple tickers (comma separated)
            if "," in ticker:
                tickers = [t.strip().upper() for t in ticker.split(",") if t.strip()]
                if len(tickers) > 1:
                    with st.spinner(
                        f"⚖️ {', '.join(tickers)} 비교 분석 레포트 생성 중..."
                    ):
                        report = generator.generate_comparison_report(tickers)
                        file_prefix = f"comparison_{'_'.join(tickers)}"
                else:
                    with st.spinner(f"📊 {tickers[0]} 분석 레포트 생성 중..."):
                        report = generator.generate_report(tickers[0])
                        file_prefix = f"{tickers[0]}_analysis_report"
            else:
                with st.spinner(f"📊 {ticker.upper()} 분석 레포트 생성 중..."):
                    report = generator.generate_report(ticker.upper())
                    file_prefix = f"{ticker.upper()}_analysis_report"

            st.markdown("---")
            st.markdown(report)

            # Download button
            try:
                pdf_bytes = create_pdf(report)
                mime_type = "application/pdf"
                file_ext = "pdf"
                label = "📥 레포트 다운로드 (PDF)"
            except:
                pdf_bytes = report.encode("utf-8")
                mime_type = "text/markdown"
                file_ext = "md"
                label = "📥 레포트 다운로드 (MD)"

            st.download_button(
                label=label,
                data=pdf_bytes,
                file_name=f"{file_prefix}.{file_ext}",
                mime=mime_type,
            )

        except Exception as e:
            st.error(f"레포트 생성 실패: {e}")

    elif generate_btn:
        st.warning("티커를 입력해주세요")
