# 🔧 화면에 데이터가 표시되지 않을 때 디버깅 가이드

## ✅ 백엔드 상태: 정상
백엔드 API는 완벽하게 작동하고 있습니다!

---

## 🔍 단계별 진단

### 1단계: 프론트엔드 서버 실행 확인

#### 확인 방법:
```bash
# 새 터미널에서
cd /Users/kimjungwoo/Work/PJT2/frontend
python -m http.server 8080
```

다음과 같은 메시지가 나와야 합니다:
```
Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/) ...
```

---

### 2단계: 테스트 페이지로 API 연결 확인

브라우저에서 열기:
```
http://localhost:8080/test.html
```

버튼들을 클릭하여 API 응답을 확인하세요.
- ✅ 모두 성공하면 → API 연결 정상
- ❌ 실패하면 → 백엔드 재시작 필요

---

### 3단계: 브라우저 개발자 도구 확인

#### 메인 페이지 열기:
```
http://localhost:8080
```

#### 개발자 도구 열기:
- **Mac**: Cmd + Option + I
- **Windows**: F12 또는 Ctrl + Shift + I

#### Console 탭에서 확인할 내용:

**정상일 때:**
```javascript
✅ DART Financial Analyzer 초기화 완료
🔗 API Base URL: http://localhost:5001/api
```

**에러가 있을 때 (예시):**
```javascript
❌ Uncaught ReferenceError: CONFIG is not defined
❌ Failed to fetch
❌ CORS policy error
```

---

### 4단계: Network 탭 확인

1. 개발자 도구의 **Network** 탭 클릭
2. 페이지 새로고침 (Cmd+R / Ctrl+R)
3. 파일 로딩 확인:
   - `index.html` - 200 OK ✅
   - `style.css` - 200 OK ✅
   - `app.js` - 200 OK ✅

4. 기업 선택 후 API 호출 확인:
   - `/api/search?q=...` - 200 OK ✅
   - `/api/company/...` - 200 OK ✅
   - `/api/kpi/...` - 200 OK ✅

---

## 🛠️ 문제별 해결 방법

### 문제 1: "Failed to fetch" 에러

**원인**: 백엔드 서버가 실행되지 않음

**해결**:
```bash
cd /Users/kimjungwoo/Work/PJT2/backend
export DART_API_KEY="33ccb4edfdf654fd7727ffce95ee093f1867c2fa"
python app.py
```

---

### 문제 2: "CORS policy" 에러

**원인**: CORS 설정 문제

**해결**: 백엔드 재시작
```bash
# Ctrl+C로 중지 후
python app.py
```

---

### 문제 3: "CONFIG is not defined" 에러

**원인**: JavaScript 파일 로딩 순서 문제

**해결**: 브라우저 강력 새로고침
- **Mac**: Cmd + Shift + R
- **Windows**: Ctrl + Shift + R

---

### 문제 4: 아무 에러도 없는데 데이터가 안 나옴

**원인**: 캐시 문제

**해결**:
1. 브라우저 캐시 완전 삭제
   - Chrome: 설정 → 개인정보 및 보안 → 인터넷 사용 기록 삭제
2. 시크릿 모드로 테스트
   - **Mac**: Cmd + Shift + N
   - **Windows**: Ctrl + Shift + N
3. 다른 브라우저로 테스트

---

## 📝 현재 상태 체크리스트

확인해주세요:

- [ ] 백엔드 서버가 http://localhost:5001 에서 실행 중
- [ ] 프론트엔드 서버가 http://localhost:8080 에서 실행 중
- [ ] 브라우저가 http://localhost:8080 접속 (localhost:5001 아님!)
- [ ] 브라우저 개발자 도구 콘솔에 에러 없음
- [ ] API 키가 설정되어 있음

---

## 🚀 빠른 재시작 (모든 것 다시)

### 터미널 1: 백엔드
```bash
cd /Users/kimjungwoo/Work/PJT2/backend
export DART_API_KEY="33ccb4edfdf654fd7727ffce95ee093f1867c2fa"
python app.py
```

### 터미널 2: 프론트엔드
```bash
cd /Users/kimjungwoo/Work/PJT2/frontend
python -m http.server 8080
```

### 브라우저
1. **모든 탭 닫기**
2. **새 탭**에서 http://localhost:8080 접속
3. **F12** → Console 탭 확인

---

## 📸 스크린샷 요청

다음을 알려주시면 정확히 해결해드립니다:

1. **브라우저 콘솔의 에러 메시지** (있다면)
2. **Network 탭의 실패한 요청** (빨간색 표시)
3. **어떤 화면이 보이는지** (완전히 비어있는지, 일부만 보이는지)

---

## 🎯 테스트 페이지 사용법

http://localhost:8080/test.html 에서:

1. **"서버 상태 확인"** 클릭
   - 성공하면 백엔드 정상 ✅
   
2. **"삼성전자 검색"** 클릭
   - 성공하면 검색 API 정상 ✅
   
3. **"삼성전자 정보"** 클릭
   - CEO 정보가 보이면 정상 ✅
   
4. **"삼성전자 KPI"** 클릭
   - ROA, ROE 등이 보이면 정상 ✅

모두 성공하는데 메인 페이지에서 안 보인다면 → 프론트엔드 JavaScript 문제

