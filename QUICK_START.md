# 🚀 빠른 시작 가이드

## 📋 필수 사항

- **Python 3.8 이상**
- **웹 브라우저** (Chrome, Firefox, Safari 등)
- **DART API 키** (무료, [여기서 발급](https://opendart.fss.or.kr/)) - 선택사항

---

## ⚡ 1분 안에 시작하기 (자동 실행 스크립트) ⭐ 추천!

가장 빠르고 간단한 방법입니다!

```bash
# 프로젝트 루트 디렉토리에서 실행
./start.sh
```

이 명령 하나로:
- ✅ 필요한 패키지 자동 설치
- ✅ 포트 충돌 자동 해결
- ✅ 백엔드 서버 자동 시작
- ✅ 브라우저에서 프론트엔드 자동 오픈

**서버 종료:**
```bash
./stop.sh
```

---

## 📝 수동 설치 방법 (상세)

자동 실행 스크립트가 작동하지 않거나 직접 설정하고 싶은 경우:

### 1단계: DART API 키 발급 (2분)

1. [DART 오픈API](https://opendart.fss.or.kr/) 접속
2. 회원가입 및 로그인
3. 상단 메뉴 **인증키 신청/관리** 클릭
4. **인증키 신청** → 즉시 발급 (무료)
5. 발급된 API 키 복사

### 2단계: 백엔드 서버 실행 (2분)

```bash
# 터미널 1: 백엔드 서버

# 1. backend 디렉토리로 이동
cd backend

# 2. Python 가상환경 생성 (선택사항이지만 권장)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt

# 4. API 키 설정
export DART_API_KEY="발급받은_API_키"
# Windows: set DART_API_KEY=발급받은_API_키

# 5. 서버 실행
python app.py
```

서버가 `http://localhost:5000` 에서 실행됩니다.

### 3단계: 프론트엔드 실행 (1분)

```bash
# 터미널 2: 프론트엔드 서버 (새 터미널 열기)

# 1. frontend 디렉토리로 이동
cd frontend

# 2. 간단한 웹 서버 실행
python3 -m http.server 8080
```

### 4단계: 브라우저에서 접속

브라우저에서 http://localhost:8080 접속

---

## 🎯 사용 방법

### 1️⃣ 기업 검색
- 메인 화면에서 기업명 또는 종목코드 입력 (예: "삼성전자", "005930")
- 또는 하단의 **인기 검색 기업** 버튼 클릭

### 2️⃣ 대시보드 확인
- KPI 카드: ROA, ROE, 부채비율, 유동비율 한눈에 확인
- 차트: 수익성 지표 및 재무구조 시각화
- 트렌드: 전년 대비 증감률 분석

### 3️⃣ 취약점 분석
- 위험도 평가: 높음/보통/낮음/안전
- 취약점 목록: 심각/경고 등급별 분류
- 개선 우선순위: 실행 가능한 액션 아이템

### 4️⃣ 보고서 생성
- 종합 분석 리포트 자동 생성
- PDF 다운로드 (또는 인쇄: Ctrl+P)

---

## 🔧 문제 해결

### ❌ "ModuleNotFoundError" 오류
```bash
# 패키지 재설치
pip install -r requirements.txt
```

### ❌ "Connection refused" 오류
- 백엔드 서버가 실행 중인지 확인
- http://localhost:5000 접속 테스트

### ❌ "CORS" 오류
- Flask-CORS가 설치되어 있는지 확인
- 브라우저 캐시 삭제 후 새로고침

### ❌ API 데이터가 안 나옴
- DART API 키가 올바른지 확인
- 환경변수가 설정되어 있는지 확인
```bash
echo $DART_API_KEY  # 키가 출력되어야 함
```

### ❌ 샘플 데이터만 나옴
- DART API 키가 설정되지 않으면 샘플 데이터로 동작합니다
- 실제 데이터를 보려면 API 키를 반드시 설정하세요

---

## 📱 지원 브라우저

- ✅ Chrome (권장)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

---

## 💡 팁

1. **반응형 디자인**: 모바일에서도 사용 가능
2. **빠른 검색**: 종목코드로 검색하면 더 빠름
3. **비교 분석**: 여러 기업을 차례로 검색하여 비교
4. **PDF 저장**: 보고서 페이지에서 Ctrl+P로 PDF 저장

---

## 🆘 추가 도움말

더 자세한 내용은 [README.md](README.md)를 참조하세요.

문제가 해결되지 않으면 GitHub Issues에 등록해주세요.

---

**Happy Analyzing! 📊✨**

