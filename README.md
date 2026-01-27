# 📊 미국 재무제표 분석 및 투자 인사이트 봇

> AI 기반 미국 상장사 재무제표 분석 및 투자 조언 플랫폼

## 🎯 프로젝트 목표

미국 상장 기업의 방대한 재무 데이터와 시장 정보를 AI로 분석하여, 투자자에게 실질적인 인사이트를 제공하는 대화형 플랫폼을 구축합니다.

### 핵심 기능

1. **💬 AI Financial Analyst**: Finnhub 실시간 데이터와 내부 재무 DB를 결합한 RAG 챗봇 (자연어 질문에서 티커 자동 분석)
2. **📊 투자 리포트 생성**: 전문 애널리스트 수준의 기업 분석 보고서 자동 생성 (`gpt-5-nano` / `gpt-4o-mini`)
3. **🌐 GraphRAG**: 기업 간 공급망/경쟁 관계 분석 및 시각화
4. **📈 실시간 마켓 데이터**: Finnhub API를 통한 최신 주가, 뉴스, 재무 지표 조회 (MCP 기반)
5. **🔍 Text-to-SQL**: 자연어 질의를 통한 복잡한 재무 재표 검색

---

## ✅ 진행 상황

### Phase 1: 기본 인프라 구축 ✅ 완료

- [x] Streamlit 기반 반응형 웹 UI
- [x] 다크/라이트 모드 지원
- [x] 모듈화된 프로젝트 구조 설계

### Phase 2: 데이터 파이프라인 ✅ 완료

- [x] **Supabase**: 103개 주요 기업 재무 데이터(10-K, 10-Q) DB 구축
- [x] **Finnhub API**: 실시간 주가, 뉴스, 컨센서스 데이터 연동
- [x] 기존 RapidAPI 및 SEC 직접 수집 방식에서 Finnhub로 통합 완료

### Phase 3: AI 및 RAG 엔진 ✅ 완료

- [x] **Vector Store**: Supabase pgvector 기반 문서 검색
- [x] **GraphRAG**: NetworkX 기반 기업 관계망 분석
- [x] **Report Generator**: 멀티 모델(Fallback 지원) 기반 투자 리포트 작성 엔진

### Phase 4: UI/UX 고도화 🔄 진행 중

- [x] 챗봇 UI 개선 (입력창 고정, 티커 자동 인식)
- [x] 그래프 시각화 인터랙티브 기능
- [x] 프로젝트 문서 및 레거시 코드 정리 완료
- [ ] 사용자 맞춤형 대시보드 (예정)

---

## 🗂 프로젝트 구조 (요약)

상세 구조는 [STRUCTURE.md](./STRUCTURE.md)를 참조하세요.

```
SKN22-3rd-4Team/
├── app.py                    # Main App
├── models/
│   └── settings.py           # AI Model Configs
├── src/
│   ├── data/                 # Finnhub & Supabase Clients
│   ├── rag/                  # Analyst Chat, Report Gen, GraphRAG
│   ├── ui/                   # Streamlit Pages
│   └── utils/
└── .env                      # API Keys
```

---

## 🔧 설치 및 실행

### 1. 환경 설정

```bash
# 가상환경 생성 (권장)
conda create -n finance_bot python=3.12
conda activate finance_bot

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (.env)

```env
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...
FINNHUB_API_KEY=...
```

### 3. 앱 실행

```bash
streamlit run app.py
```

---

## 🌐 API 및 서비스

| 서비스 | 용도 | 상태 |
|--------|------|------|
| **Supabase** | 재무제표 DB & Vector Store | ✅ 연동 완료 |
| **Finnhub** | 실시간 주가, 뉴스, 재무 지표 | ✅ 연동 완료 |
| **OpenAI** | LLM (Chat, Report, SQL) | ✅ 연동 완료 |

---

## 📝 라이선스

MIT License
