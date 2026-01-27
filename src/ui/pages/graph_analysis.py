"""
Graph analysis page with GraphRAG integration
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from rag.graph_rag import GraphRAG

    GRAPH_RAG_AVAILABLE = True
except ImportError as e:
    GRAPH_RAG_AVAILABLE = False
    IMPORT_ERROR = str(e)


def render():
    """그래프 분석 페이지 렌더링"""

    st.markdown('<h1 class="main-header">🌐 그래프 분석</h1>', unsafe_allow_html=True)

    st.markdown("SEC 공시로부터 구축된 기업 관계 및 지식 그래프 탐색")

    st.markdown("---")

    if not GRAPH_RAG_AVAILABLE:
        st.error(f"GraphRAG 모듈 로드 실패: {IMPORT_ERROR}")
        st.info("pip install openai supabase networkx 를 실행하세요")
        return

    # Initialize GraphRAG
    if "graph_rag" not in st.session_state:
        try:
            st.session_state.graph_rag = GraphRAG()
        except Exception as e:
            st.error(f"GraphRAG 초기화 실패: {e}")
            return

    graph_rag = st.session_state.graph_rag

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🔍 Graph Query")

        # Query input
        query = st.text_area(
            "기업 관계에 대해 질문하세요",
            placeholder="애플의 주요 공급업체는 어디인가요?",
            height=100,
        )

        # Company ticker
        ticker = st.text_input("컨텍스트 회사 티커 (선택사항)", placeholder="AAPL")

        if st.button("🔎 그래프 검색", type="primary", use_container_width=True):
            if query:
                with st.spinner("지식 그래프 검색 중..."):
                    result = graph_rag.query_with_context(
                        query, ticker=ticker.upper() if ticker else None
                    )

                    st.markdown("### 📊 분석 결과")
                    st.markdown(result.get("response", "결과 없음"))

                    # Show context
                    with st.expander("📋 사용된 컨텍스트"):
                        st.text(result.get("context", "없음"))
            else:
                st.warning("질문을 입력해주세요")

    with col2:
        st.markdown("### 🎯 회사 선택")

        company_ticker = st.text_input("티커 입력", placeholder="AAPL", key="relationship_ticker")

        if st.button("🔗 관계 조회"):
            if company_ticker:
                with st.spinner("관계 검색 중..."):
                    rels = graph_rag.find_relationships(company_ticker.upper())

                    if rels.get("total", 0) > 0:
                        st.success(f"총 {rels['total']}개 관계 발견")

                        # Outgoing relationships
                        if rels.get("outgoing"):
                            st.markdown("**→ 나가는 관계**")
                            for rel in rels["outgoing"][:5]:
                                st.markdown(
                                    f"- [{rel.get('relationship_type')}] → "
                                    f"{rel.get('target_company')} ({rel.get('target_ticker', '')})"
                                )

                        # Incoming relationships
                        if rels.get("incoming"):
                            st.markdown("**← 들어오는 관계**")
                            for rel in rels["incoming"][:5]:
                                st.markdown(
                                    f"- {rel.get('source_company')} ({rel.get('source_ticker', '')}) "
                                    f"[{rel.get('relationship_type')}] →"
                                )
                    else:
                        st.info("관계 데이터가 없습니다")
            else:
                st.warning("티커를 입력해주세요")

        st.markdown("---")

        st.markdown("### 📈 통계")

        if st.button("📊 통계 새로고침"):
            stats = graph_rag.get_stats()
            st.metric("회사 수", stats.get("companies", 0))
            st.metric("관계 수", stats.get("relationships", 0))
            st.metric("문서 수", stats.get("documents", 0))

    st.markdown("---")

    # Relationship details section
    st.markdown("### 🔗 관계 유형별 검색")

    col_a, col_b = st.columns(2)

    with col_a:
        search_ticker = st.text_input("회사 티커", placeholder="AAPL", key="type_search_ticker")

    with col_b:
        rel_type = st.selectbox(
            "관계 유형",
            [
                "전체",
                "partnership",
                "supplier",
                "customer",
                "competitor",
                "acquisition",
                "investment",
            ],
        )

    if st.button("🔍 유형별 검색"):
        if search_ticker:
            with st.spinner("검색 중..."):
                type_filter = None if rel_type == "전체" else rel_type
                rels = graph_rag.find_relationships(search_ticker.upper(), type_filter)

                all_rels = rels.get("outgoing", []) + rels.get("incoming", [])

                if all_rels:
                    df = pd.DataFrame(
                        [
                            {
                                "출발": r.get("source_company", ""),
                                "출발 티커": r.get("source_ticker", ""),
                                "관계": r.get("relationship_type", ""),
                                "도착": r.get("target_company", ""),
                                "도착 티커": r.get("target_ticker", ""),
                                "신뢰도": r.get("confidence", 0),
                            }
                            for r in all_rels
                        ]
                    )
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("해당 조건의 관계가 없습니다")
        else:
            st.warning("티커를 입력해주세요")

    # Sample queries
    with st.expander("💡 예시 질문"):
        st.markdown(
            """
        **관계 분석:**
        - "애플의 주요 공급업체는 어디인가요?"
        - "테슬라와 경쟁 관계에 있는 기업들은?"
        - "마이크로소프트가 인수한 회사들은?"
        
        **산업 분석:**  
        - "반도체 산업의 주요 공급망 관계는?"
        - "빅테크 기업들 간의 경쟁 구도는?"
        
        **리스크 분석:**
        - "특정 공급업체에 의존도가 높은 기업은?"
        """
        )
