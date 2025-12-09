# NIM 데이터 연동 로직 점검 결과

## 전체 데이터 흐름

### 1. 백엔드 - NIM 계산 (`backend/kpi_calculator.py`)

#### `calculate_nim()` 함수 (라인 375-532)
- ✅ 이자수익 계정 검색: '이자수익', '대출이자수익', '여신이자수익' 등
- ✅ 이자비용 계정 검색: '이자비용', '예금이자비용', '차입이자비용' 등
- ✅ 이자생성자산 검색: '대출금', '여신', '자산총계' (순서대로)
- ✅ NIM 계산: (이자수익 - 이자비용) / 이자생성자산 × 100
- ✅ 전년 대비 계산 및 상태 평가
- ✅ 상세 로그 출력

**반환 형식:**
```python
{
    'value': float,           # NIM 값 (%)
    'previous_value': float,  # 전년 NIM 값
    'change': float,          # 변화량
    'change_rate': float,    # 변화율 (%)
    'status': str,            # 'excellent', 'good', 'fair', 'poor', 'error'
    'numerator': float,       # 순이자수익
    'denominator': float,     # 이자생성자산
    'unit': '%',
    'description': '순이자마진(NIM)'
}
```

#### `calculate_all_kpis()` 함수 (라인 839-876)
- ✅ 업종이 '은행업'인 경우에만 NIM 계산
- ✅ `base_kpis`에 'nim' 키로 추가
- ✅ 로그로 NIM 계산 결과 확인 가능

### 2. 백엔드 - API 엔드포인트 (`backend/app.py`)

#### `/api/kpi/<corp_code>` (라인 121-173)
- ✅ 업종 정보를 기업 정보에서 가져옴
- ✅ `KPICalculator.calculate_all_kpis(industry)` 호출
- ✅ 응답에 `industry`와 `kpis` 포함
- ✅ 은행업일 경우 NIM 값 로그 출력

**응답 형식:**
```json
{
    "status": "success",
    "corp_code": "...",
    "year": 2024,
    "industry": "은행업",
    "kpis": {
        "roa": {...},
        "roe": {...},
        "nim": {...},  // 은행업일 경우만
        "operating_margin": {...}
    },
    "trends": {...}
}
```

### 3. 프론트엔드 - 데이터 수신 및 표시 (`frontend/app.js`)

#### 대시보드 (`loadDashboard()`, 라인 302-371)
- ✅ `/api/kpi/<corp_code>` 호출
- ✅ `kpiData.kpis`에서 NIM 데이터 확인
- ✅ `appState.currentIndustry` 업데이트
- ✅ `updateKPICards(kpiData.kpis)` 호출

#### KPI 카드 업데이트 (`updateKPICards()`, 라인 411-444)
- ✅ `appState.currentIndustry === '은행업'` 확인
- ✅ 은행업일 경우:
  - `kpis.nim` 데이터 확인
  - 없으면 기본값 객체 생성
  - `updateKPICardWithLabel('debt', nimData, 'NIM', '순이자마진')` 호출
- ✅ 로그로 NIM 데이터 존재 여부 확인

#### 차트 업데이트
- ✅ `updateProfitabilityChart()` (라인 601-670)
  - 은행업: ['ROA', 'ROE', 'NIM', '영업이익률']
  - `kpis.nim?.value || 0` 사용
- ✅ `updateFinancialStructureChart()` (라인 675-726)
  - 은행업: ['NIM (순이자마진)', '영업이익률']
  - `kpis.nim?.value || 0` 사용

#### 취약점 분석 페이지 (`displayKPIComparison()`, 라인 1316-1530)
- ✅ `appState.currentIndustry === '은행업'` 확인
- ✅ 은행업일 경우 kpiList에 'nim' 포함
- ✅ `kpis.nim` 데이터 확인
- ✅ 없으면 기본값으로 표시 (은행업 NIM은 필수)
- ✅ 테이블에 NIM 행 생성

#### 보고서 페이지 (`displayReport()`, 라인 1734-1859)
- ✅ `appState.currentIndustry === '은행업'` 확인
- ✅ 은행업일 경우 NIM 카드 표시
- ✅ `kpis.nim?.value?.toFixed(2)` 사용

## 잠재적 문제점 및 개선 사항

### 1. 업종 정보 동기화
- ⚠️ `appState.currentIndustry`가 API 응답의 `industry`와 일치하지 않을 수 있음
- ✅ 개선: `loadDashboard()`에서 `kpiData.industry`로 업데이트 (라인 337)

### 2. NIM 데이터 없을 때 처리
- ✅ 은행업일 경우 기본값으로 표시하도록 처리됨
- ✅ 에러 상태도 표시하도록 처리됨

### 3. 로그 확인 포인트
백엔드 로그에서 확인:
- `🏦 [KPICalculator] 은행업 감지 - NIM 계산 시작`
- `✅ NIM 계산 완료: {...}`
- `✅ [KPI 분석] 계산된 KPI 키: ['roa', 'roe', 'nim', ...]`
- `   - NIM 값: X.XX`

프론트엔드 콘솔에서 확인:
- `📊 KPI 데이터 확인: { nim: {...} }`
- `🏦 은행업 모드 - NIM과 영업이익률 표시`
- `   - NIM 데이터: {...}`

## 테스트 체크리스트

1. ✅ 백엔드에서 NIM 계산되는지 확인
   - 터미널 로그에서 "🏦 은행업 감지" 확인
   - "✅ NIM 계산 완료" 확인

2. ✅ API 응답에 NIM 포함되는지 확인
   - 브라우저 개발자 도구 Network 탭에서 `/api/kpi/...` 응답 확인
   - `kpis.nim` 객체 존재 확인

3. ✅ 프론트엔드에서 NIM 데이터 수신 확인
   - 콘솔에서 "📊 KPI 데이터 확인" 로그 확인
   - `nim: {...}` 객체 확인

4. ✅ 화면에 NIM 표시되는지 확인
   - 대시보드: 3번째 KPI 카드에 "NIM" 표시
   - 차트: 수익성 차트에 NIM 막대 표시
   - 취약점 분석: 테이블에 NIM 행 표시
   - 보고서: NIM 카드 표시

## 디버깅 가이드

### NIM이 계산되지 않는 경우
1. 백엔드 로그 확인: "🏦 은행업 감지" 메시지 확인
2. 계정명 확인: 이자수익/이자비용 계정명이 DART 재무제표와 일치하는지 확인
3. 업종 확인: `appState.currentIndustry`가 정확히 "은행업"인지 확인

### NIM이 화면에 표시되지 않는 경우
1. 콘솔 로그 확인: "📊 KPI 데이터 확인"에서 `nim` 객체 확인
2. 업종 확인: "🏦 은행업 모드" 메시지 확인
3. HTML 요소 확인: `debt-value` 요소가 존재하는지 확인
4. 브라우저 개발자 도구에서 `appState.currentIndustry` 값 확인

