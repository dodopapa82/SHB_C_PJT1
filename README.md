# 📊 DART 기반 재무제표 취약점 분석 플랫폼

## 🎯 프로젝트 개요

DART 공시 재무제표를 수집하여 KPI를 계산하고 취약점을 분석하는 웹 기반 대시보드 시스템입니다.

### 주요 기능
- ✅ 기업 검색 및 재무제표 조회 (DART API 연동)
- ✅ KPI 자동 계산 (ROA, ROE, 부채비율, 유동비율 등)
- ✅ 취약점 Rule Engine 기반 위험도 분석
- ✅ 시각화 대시보드 (그래프, 히트맵)
- ✅ 상세 분석 리포트 생성

## 🛠 기술 스택

### Frontend
- HTML5
- CSS3 (반응형 디자인)
- Vanilla JavaScript
- Chart.js (차트 라이브러리)

### Backend
- Python 3.8+
- Flask (웹 프레임워크)
- Requests (DART API 연동)

### API
- DART Open API (무료, API Key 필요)

## 📁 프로젝트 구조

```
PJT2/
├── backend/
│   ├── app.py                 # Flask 메인 서버
│   ├── dart_api.py            # DART API 연동 모듈
│   ├── kpi_calculator.py      # KPI 계산 엔진
│   ├── weakness_analyzer.py   # 취약점 분석 엔진
│   └── requirements.txt       # Python 의존성
├── frontend/
│   ├── index.html            # 메인 페이지
│   ├── style.css             # 스타일시트
│   └── app.js                # JavaScript 로직
├── start.sh                  # 🚀 자동 실행 스크립트
├── stop.sh                   # 🛑 서버 종료 스크립트
├── env.example               # 환경변수 예제
├── README.md                 # 프로젝트 문서
├── QUICK_START.md            # 빠른 시작 가이드
└── DEVELOPMENT.md            # 개발 가이드
```

## 🚀 설치 및 실행

### 빠른 시작 (자동 실행 스크립트) ⭐

가장 간단한 방법으로 시스템을 시작할 수 있습니다!

```bash
# 1. DART API 키 설정 (선택사항)
export DART_API_KEY="발급받은_API_키"

# 2. 자동 실행 스크립트 실행
./start.sh
```

이 스크립트는 자동으로:
- ✅ Python3 및 패키지 확인
- ✅ 포트 충돌 해결
- ✅ 백엔드 서버 시작 (http://localhost:5001)
- ✅ 프론트엔드 브라우저 자동 오픈

**서버 종료:**
```bash
./stop.sh
```

---

### 1. DART API 키 발급
1. [DART 오픈API](https://opendart.fss.or.kr/) 접속
2. 회원가입 및 로그인
3. 인증키 발급 신청 (무료, 즉시 발급)

### 2. 수동 설치 방법

#### 백엔드 설정

```bash
# 백엔드 디렉토리로 이동
cd backend

# 가상환경 생성 (선택사항)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
# 방법 1: .env 파일 사용 (권장)
cp env.example .env
# .env 파일을 열어서 DART_API_KEY를 실제 키로 변경

# 방법 2: 환경변수로 직접 설정
export DART_API_KEY="발급받은_API_키"  # Windows: set DART_API_KEY=발급받은_API_키
export PORT=5001  # 포트 변경 (선택사항)
export DEFAULT_YEAR=2023  # 기본 분석 연도 (선택사항)

# 서버 실행
python3 app.py
```

서버가 `http://localhost:5001` 에서 실행됩니다.

### 환경변수 설정 옵션

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `DART_API_KEY` | DART API 인증키 | 필수 |
| `PORT` | 서버 포트 | 5001 |
| `DEBUG` | 디버그 모드 | True |
| `DEFAULT_YEAR` | 기본 분석 연도 | 전년도 |
| `DEFAULT_INDUSTRY` | 기본 업종 | default |
| `MAX_SEARCH_RESULTS` | 최대 검색 결과 | 20 |
| `CACHE_DURATION_DAYS` | 캐시 유지 기간 (일) | 1 |

자세한 설정은 `env.example` 파일을 참조하세요.

#### 프론트엔드 실행

```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 브라우저에서 index.html 파일 열기
open index.html  # macOS
# 또는 브라우저에서 직접 파일 열기
```

## 📊 화면 구성

### 1️⃣ 기업 검색 화면
- 기업명/종목코드 검색
- 자동완성 기능
- 최근 검색 기록

### 2️⃣ 재무 대시보드
- KPI 카드 (ROA, ROE, 부채비율 등)
- 시계열 그래프
- 취약점 히트맵

### 3️⃣ 취약점 상세 분석
- 취약 항목별 상세 설명
- 업종 비교 차트
- 개선 가이드

### 4️⃣ 보고서 생성
- PDF 다운로드
- 커스터마이징 옵션

## 🔧 API 명세

### GET /api/search
기업 검색
- Query: `q` (검색어)
- Response: 기업 목록

### GET /api/financial/:corp_code
재무제표 조회
- Response: 재무제표 데이터

### GET /api/kpi/:corp_code
KPI 분석
- Response: 계산된 KPI 값

### GET /api/weakness/:corp_code
취약점 분석
- Response: 취약점 분석 결과

## 📈 KPI 계산 기준

| KPI | 계산식 | 정상범위 |
|-----|--------|----------|
| ROA | 순이익 / 총자산 × 100 | > 5% |
| ROE | 순이익 / 자본총계 × 100 | > 10% |
| 부채비율 | 부채총계 / 자본총계 × 100 | < 200% |
| 유동비율 | 유동자산 / 유동부채 × 100 | > 100% |

## ⚠️ 취약점 Rule Engine

| Rule ID | 취약점 | 기준 |
|---------|--------|------|
| R01 | 높은 부채비율 | > 업종평균 + 20% |
| R02 | 현금흐름 위험 | 2년 연속 음수 |
| R03 | ROE 저하 | 3년 연속 감소 |
| R04 | 수익성 악화 | 영업이익률 < 업종 하위 25% |

## 🎨 디자인 가이드

- **컬러**: Primary #0047FF / Focus #00C2FF / Error #FF4B4B
- **타이포**: Pretendard 폰트 사용
- **반응형**: Desktop(1440px) / Tablet(768px) / Mobile(375px)

## 📝 라이선스

본 프로젝트는 교육 및 분석 목적으로 제작되었습니다.
DART API 이용 시 금융감독원의 이용약관을 준수해야 합니다.

## 🤝 기여

이슈 및 PR은 언제든 환영합니다!

## 📞 문의

질문이나 제안사항이 있으시면 이슈를 등록해주세요.

# SHB_C_PJT1
