# 📊 미국 재무제표 분석 및 투자 인사이트 봇

> AI 기반 미국 상장사 재무제표 분석 및 투자 조언 플랫폼

## 🎯 프로젝트 목표

미국 상장 기업의 방대한 재무 데이터와 시장 정보를 AI로 분석하여, 투자자에게 실질적인 인사이트를 제공하는 대화형 플랫폼을 구축합니다.

### 핵심 기능

1. **💬 AI Financial Analyst**: Finnhub 실시간 데이터와 내부 재무 DB를 결합한 RAG 챗봇 (병렬 수집 최적화로 빠른 응답)
2. **📝 투자 리포트 자동 생성**: 10-K RAG 컨텍스트를 포함한 종합 보고서 생성 (`gpt-4.1-mini` 최적화)
3. **🌐 GraphRAG**: 기업 간 공급망/경쟁 관계 분석 및 시각화
4. **📈 한국형 마켓 대시보드**: KST 기준 실시간 원화(KRW) 환율 및 주요 지표 제공
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
- [x] **Exchange API**: KST 기준 실시간 원화 환율 연동 완료

### Phase 3: AI 및 RAG 엔진 ✅ 완료

- [x] **Vector Store**: Supabase pgvector 기반 문서 검색
- [x] **GraphRAG**: NetworkX 기반 기업 관계망 분석
- [x] **Performance**: `DataRetriever` 도입으로 병렬 데이터 수집 최적화 완료

### Phase 4: 폴리싱 및 배포 🔄 진행 중

- [x] 챗봇 및 레포트 생성 속도 최적화
- [x] UI 가독성 향상 (KST 시간대 적용, 환산 가격 표시)
- [x] 프로젝트 문서 및 의존성 파일 정리 완료
- [ ] 사용자 맞춤형 포트폴리오 관리 (예정)

---

## 🗂 프로젝트 구조 (요약)

상세 구조는 [STRUCTURE.md](./STRUCTURE.md)를 참조하세요.

```text
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
| :--- | :--- | :--- |
| **Supabase** | 재무제표 DB & Vector Store | ✅ 연동 완료 |
| **Finnhub** | 실시간 주가, 뉴스, 재무 지표 | ✅ 연동 완료 |
| **OpenAI** | LLM (Chat, Report, SQL) | ✅ 연동 완료 |

---

## 📝 라이선스

MIT License
