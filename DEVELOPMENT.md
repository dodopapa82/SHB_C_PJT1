# 🛠 개발자 가이드

## 프로젝트 아키텍처

```
┌─────────────────┐
│  Frontend       │  HTML5 + CSS3 + Vanilla JS
│  (Port 8080)    │  Chart.js for visualization
└────────┬────────┘
         │
         │ HTTP REST API
         │
┌────────▼────────┐
│  Backend        │  Flask (Python)
│  (Port 5000)    │  CORS enabled
└────────┬────────┘
         │
    ┌────┴────┬──────────┬────────────┐
    │         │          │            │
┌───▼──┐  ┌──▼───┐  ┌───▼────┐  ┌───▼────┐
│ DART │  │ KPI  │  │Weakness│  │ Utils  │
│ API  │  │ Calc │  │Analyzer│  │        │
└──────┘  └──────┘  └────────┘  └────────┘
```

---

## 백엔드 모듈 구조

### 📄 `app.py` - Flask 메인 서버
- REST API 엔드포인트 정의
- CORS 설정
- 에러 핸들링

**주요 엔드포인트:**
- `GET /api/search?q={query}` - 기업 검색
- `GET /api/company/{corp_code}` - 기업 정보
- `GET /api/financial/{corp_code}` - 재무제표
- `GET /api/kpi/{corp_code}` - KPI 분석
- `GET /api/weakness/{corp_code}` - 취약점 분석
- `GET /api/report/{corp_code}` - 종합 보고서

### 📄 `dart_api.py` - DART API 연동
```python
class DARTApi:
    def search_company(query: str) -> List[Dict]
    def get_financial_statement(corp_code: str, year: int) -> Dict
    def get_company_info(corp_code: str) -> Dict
    def get_multi_year_financial(corp_code: str, years: List[int]) -> Dict
```

### 📄 `kpi_calculator.py` - KPI 계산 엔진
```python
class KPICalculator:
    def calculate_roa() -> Dict
    def calculate_roe() -> Dict
    def calculate_debt_ratio() -> Dict
    def calculate_current_ratio() -> Dict
    def calculate_operating_margin() -> Dict
    def calculate_net_profit_margin() -> Dict
    def calculate_all_kpis() -> Dict
    def get_trend_analysis() -> Dict
```

**KPI 계산 로직:**
- ROA = (당기순이익 / 총자산) × 100
- ROE = (당기순이익 / 자본총계) × 100
- 부채비율 = (부채총계 / 자본총계) × 100
- 유동비율 = (유동자산 / 유동부채) × 100

### 📄 `weakness_analyzer.py` - 취약점 분석 엔진
```python
class WeaknessAnalyzer:
    def analyze_all() -> Dict
    def get_improvement_priorities() -> List[Dict]
    
    # Private methods
    def _check_high_debt_ratio()
    def _check_low_profitability()
    def _check_liquidity_risk()
    def _check_declining_trend()
    def _check_negative_cashflow()
    def _calculate_risk_level() -> Dict
```

**취약점 Rule Engine:**
- R01: 높은 부채비율 (> 업종평균 + 20%)
- R02: 현금흐름 위험 (2년 연속 음수)
- R03: ROE 저하 (3년 연속 감소)
- R04: 낮은 수익성 (업종 하위 25%)
- R05: 유동성 부족 (유동비율 < 100%)

---

## 프론트엔드 구조

### 📄 `index.html` - 메인 HTML
4개 페이지 구조:
1. **Search Page** - 기업 검색
2. **Dashboard Page** - KPI 대시보드
3. **Weakness Page** - 취약점 분석
4. **Report Page** - 종합 보고서

### 📄 `style.css` - 스타일시트
**디자인 시스템:**
- Primary Color: `#0047FF`
- Focus Color: `#00C2FF`
- Success: `#00C851`
- Warning: `#FFA500`
- Error: `#FF4B4B`

**반응형 브레이크포인트:**
- Desktop: 1440px
- Tablet: 768px
- Mobile: 480px

### 📄 `app.js` - JavaScript 로직
```javascript
// State Management
const appState = {
    currentCorpCode: null,
    currentCorpName: null,
    currentIndustry: 'default',
    currentYear: 2023,
    kpiData: null,
    weaknessData: null,
    reportData: null
}

// Main Functions
async function searchCompany(query)
function selectCompany(corpCode, corpName, industry)
async function loadDashboard()
async function loadWeaknessAnalysis()
async function loadReport()
function navigateTo(pageName)

// Chart Functions
function updateProfitabilityChart(kpis)
function updateFinancialStructureChart(kpis)
```

---

## 데이터 흐름

### 1. 기업 검색
```
User Input → searchCompany() → 
GET /api/search → DARTApi.search_company() → 
displaySearchResults()
```

### 2. 대시보드 로드
```
selectCompany() → loadDashboard() → 
GET /api/company/{code} + GET /api/kpi/{code} → 
KPICalculator.calculate_all_kpis() → 
updateKPICards() + updateCharts()
```

### 3. 취약점 분석
```
loadWeaknessAnalysis() → 
GET /api/weakness/{code} → 
WeaknessAnalyzer.analyze_all() → 
displayWeaknesses() + displayPriorities()
```

---

## 확장 가이드

### 새로운 KPI 추가하기

1. **백엔드 (`kpi_calculator.py`)**
```python
def calculate_your_kpi(self) -> Dict:
    # 계산 로직
    value = ...
    
    # 평가 기준
    if value >= threshold:
        status = 'excellent'
    # ...
    
    return {
        'value': value,
        'status': status,
        'unit': '%',
        'description': 'Your KPI'
    }

# calculate_all_kpis()에 추가
def calculate_all_kpis(self):
    return {
        # ...
        'your_kpi': self.calculate_your_kpi()
    }
```

2. **프론트엔드 (HTML, CSS, JS)**
```html
<!-- index.html에 KPI 카드 추가 -->
<div class="kpi-card">
    <div class="kpi-header">
        <span class="kpi-label">Your KPI</span>
        <span class="kpi-badge" id="your-kpi-badge">-</span>
    </div>
    <div class="kpi-value" id="your-kpi-value">-</div>
    <div class="kpi-description">설명</div>
</div>
```

```javascript
// app.js에서 업데이트
function updateKPICards(kpis) {
    // ...
    updateKPICard('your-kpi', kpis.your_kpi);
}
```

### 새로운 취약점 Rule 추가하기

```python
# weakness_analyzer.py
def _check_your_rule(self):
    """Rule RXX: 설명"""
    # 검사 로직
    if condition:
        self.weaknesses.append({
            'rule_id': 'RXX',
            'title': '취약점 제목',
            'severity': 'critical',  # or 'warning', 'info'
            'category': '카테고리',
            'description': '상세 설명',
            'current_value': value,
            'benchmark_value': benchmark,
            'recommendation': '개선 방안',
            'impact': '영향'
        })

# analyze_all()에 추가
def analyze_all(self):
    # ...
    self._check_your_rule()
```

---

## 테스트

### 수동 테스트
```bash
# 백엔드 API 테스트
curl http://localhost:5000/api/search?q=삼성전자
curl http://localhost:5000/api/kpi/00126380

# 프론트엔드
# 브라우저에서 http://localhost:8080 접속
```

### 자동 테스트 (추후 구현)
```python
# tests/test_kpi_calculator.py
def test_calculate_roa():
    financial_data = {...}
    calculator = KPICalculator(financial_data)
    roa = calculator.calculate_roa()
    assert roa['value'] > 0
```

---

## 성능 최적화

### 백엔드
- [ ] Redis 캐싱 (재무제표 데이터)
- [ ] 비동기 처리 (다년도 데이터)
- [ ] 데이터베이스 도입 (검색 속도)

### 프론트엔드
- [ ] 코드 스플리팅
- [ ] 이미지 최적화
- [ ] Service Worker (오프라인)
- [ ] Lazy Loading (차트)

---

## 보안 고려사항

1. **API 키 보호**
   - 환경변수 사용
   - .gitignore에 추가
   - 프론트엔드에 노출 금지

2. **CORS 설정**
   - 프로덕션에서는 특정 도메인만 허용

3. **입력 검증**
   - SQL Injection 방지
   - XSS 방지

---

## 배포 가이드

### Heroku 배포
```bash
# Procfile 생성
web: cd backend && gunicorn app:app

# requirements.txt에 추가
gunicorn==21.2.0

# 배포
heroku create your-app-name
git push heroku main
```

### Docker 배포
```dockerfile
# Dockerfile (추후 작성)
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "backend/app.py"]
```

---

## 기여 가이드

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 라이선스

본 프로젝트는 교육 목적으로 제작되었습니다.
DART API 사용 시 금융감독원의 이용약관을 준수해야 합니다.

---

**Happy Coding! 💻✨**

