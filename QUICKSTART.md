# 🚀 퀵 스타트 가이드 (Quick Start Guide)

금융 데이터 분석 및 AI 투자 파트너 프로젝트에 오신 것을 환영합니다! 이 가이드는 로컬 환경에서 프로젝트를 빠르게 설정하고 실행하는 방법을 안내합니다.

## 📦 설치 방법

### 1. 저장소 클론 (Clone)

```bash
git clone <repository-url>
cd SKN22-3rd-4Team
```

### 2. 가상 환경 설정

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. 종속성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

루트 디렉토리에 `.env` 파일을 생성하고 아래 내용을 입력하세요 (필요한 API 키는 별도 발급 필요):

```env
# OpenAI (챗봇 및 RAG 핵심 API)
OPENAI_API_KEY=sk-...

# Supabase (데이터베이스 및 벡터 저장소)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Finnhub (실시간 주가 및 시장 데이터)
FINNHUB_API_KEY=your-finnhub-key
```

## 🎯 어플리케이션 실행

### Streamlit 웹 인터페이스 시작

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 주소로 접속하면 대시보드가 열립니다.

## 📊 주요 기능 및 사용법

### 1. 홈 (Dashboard Home)

- 전체 프로젝트 개요 및 서비스 연결 상태(DB, API)를 확인합니다.
- **실시간 환율**: 한국 투자자를 위한 주요 통화(USD, EUR, JPY 등)의 원화 환산 가격을 KST 시간 기준으로 제공합니다.

### 2. AI 인텔리전스 (Investment Insights)

- **AI 애널리스트와 대화**: 자연어로 시장 흐름이나 특정 기업에 대해 질문하세요.
  - *예시*: "엔비디아의 최근 실적과 월가 목표 주가는 어때?"
- **자동 티커 감지**: 질문 내 기업명을 자동으로 인식하여 관련된 재무/뉴스 데이터를 수집합니다.
- **주가 차트 시각화**: "애플 주가 차트 보여줘"와 같이 요청하면 최근 주가 흐름을 시각적인 그래프로 보여줍니다.
- **한국형 환율 도구**: 대화 중 "현재 환율 알려줘" 또는 "100달러는 얼마야?"와 같은 질문에 즉각 답해줍니다.

### 3. 투자 보고서 생성 (Report Generator)

- 챗봇에게 보고서 작성을 요청하거나 전용 페이지에서 티커를 입력하세요.
  - *예시*: "애플(AAPL) 투자 리포트 써줘"
- **병렬 데이터 수집**: `DataRetriever`를 통해 재무제표, 관계망(GraphRAG), 뉴스, 추천 의견을 동시에 수집하여 초고속으로 보고서를 생성합니다.
- **데이터 출처 명시**: 각 데이터가 DB(과거 실적)에서 왔는지, Finnhub(실시간 시세)에서 왔는지 명확히 표기되며 조회 시점도 제공됩니다.
- 생성된 보고서는 **가독성이 개선된 PDF로 다운로드**할 수 있습니다. (긴 텍스트 자동 줄바꿈 및 테이블 레이아웃 최적화 적용)

### 4. 관계망 분석 (Graph Analysis)

- 기업 간의 공급망(공급처, 고객사), 경쟁 관계를 시각적으로 탐색합니다.
- 특정 기업의 리스크가 어떤 경로로 전이될 수 있는지 파악하세요.

### 5. SQL 쿼리

- 자연어를 사용하여 내부 금융 데이터베이스를 직접 쿼리합니다.
  - *예시*: "2023년 영업이익률 상위 5개 기업 보여줘"

## 🧪 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 특정 기능 테스트 (예: GraphRAG)
pytest tests/unit/test_graph_rag.py
```

## 📝 코드 예시 (SDK 활용)

### 실시간 데이터 수집 예시

```python
from src.data.finnhub_client import get_finnhub_client

client = get_finnhub_client()
quote = client.get_quote("AAPL")
print(f"현재 주가: ${quote['c']}")
```

### 투자 보고서 생성 예시

```python
from src.rag.report_generator import ReportGenerator

generator = ReportGenerator()
report_md = generator.generate_report("NVDA")
print(report_md)
```
