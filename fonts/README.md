# 폰트 설치 가이드 (Windows & macOS)

PDF 리포트 생성을 위해서는 한글 폰트가 필요합니다.

## 방법 1: 나눔 폰트 다운로드 (권장, 모든 OS)

1. [네이버 나눔고딕 다운로드 페이지](https://hangeul.naver.com/font)에서 나눔고딕 폰트를 다운로드합니다.
2. 압축을 풀고 `NanumGothic.ttf` 파일을 이 `fonts` 폴더에 복사합니다.
3. 애플리케이션을 재시작합니다.

## 방법 2: 기존 시스템 폰트 사용

### Windows

시스템에 보통 다음 폰트가 설치되어 있습니다:

- `C:\Windows\Fonts\malgun.ttf` (맑은 고딕)
- `C:\Windows\Fonts\gulim.ttc` (굴림)

폰트가 없다면:

1. Windows 설정 → 시간 및 언어 → 언어
2. 한국어 추가 후 언어팩 다운로드

### macOS

시스템에 기본 제공되는 한글 폰트:

- `/System/Library/Fonts/Supplemental/AppleGothic.ttf`
- `/System/Library/Fonts/AppleSDGothicNeo.ttc`

폰트가 없거나 접근 불가 시:

1. 시스템 환경설정 → 언어 및 지역 → 한국어 추가
2. 또는 방법 1의 나눔고딕을 프로젝트 폴더에 설치

## 폴더 구조

폰트 파일을 이 폴더에 넣으면 자동으로 인식됩니다:

예:

```
fonts/
  ├── NanumGothic.ttf  (권장, 모든 OS)
  ├── malgun.ttf       (선택, Windows)
  └── README.md        (이 파일)
```
