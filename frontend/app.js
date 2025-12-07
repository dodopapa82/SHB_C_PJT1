/**
 * DART 재무제표 분석 시스템 - Frontend JavaScript
 * API 연동, 차트 렌더링, UI 제어
 */

// ===========================
// Configuration
// ===========================
const CONFIG = {
    // API 설정
    API_BASE_URL: (window.location.protocol === 'file:' || window.location.hostname === 'localhost' || window.location.hostname === '') 
        ? 'http://localhost:5001/api' 
        : `${window.location.origin}/api`,
    
    // 기본값 설정
    DEFAULT_YEAR: new Date().getFullYear() - 1, // 전년도
    DEFAULT_INDUSTRY: 'default',
    DEFAULT_REPORT_CODE: '11011',
    
    // 검색 설정
    MIN_SEARCH_LENGTH: 1,
    MAX_SEARCH_RESULTS: 20,
    SEARCH_DEBOUNCE_MS: 300,
    
    // 차트 설정
    CHART_COLORS: {
        primary: 'rgba(0, 71, 255, 0.8)',
        secondary: 'rgba(0, 194, 255, 0.8)',
        success: 'rgba(0, 200, 81, 0.8)',
        warning: 'rgba(255, 165, 0, 0.8)',
        danger: 'rgba(255, 75, 75, 0.8)'
    }
};

// Global State
const appState = {
    currentCorpCode: null,
    currentCorpName: null,
    currentCorpNameEng: null,
    currentStockCode: null,
    currentIndustry: CONFIG.DEFAULT_INDUSTRY,
    currentYear: CONFIG.DEFAULT_YEAR,
    companyInfo: null,  // 전체 기업 정보
    financialData: null, // 재무제표 데이터
    kpiData: null,
    weaknessData: null,
    reportData: null
};

// Charts
let profitabilityChart = null;
let financialStructureChart = null;

// ===========================
// Utility Functions
// ===========================

/**
 * API 호출 헬퍼
 */
async function fetchAPI(endpoint) {
    showLoading();
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API 호출 오류:', error);
        alert('데이터를 불러오는데 실패했습니다. 백엔드 서버가 실행 중인지 확인해주세요.');
        throw error;
    } finally {
        hideLoading();
    }
}

/**
 * 로딩 표시
 */
function showLoading() {
    document.getElementById('loading-overlay').classList.remove('hidden');
}

/**
 * 로딩 숨김
 */
function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

/**
 * 숫자 포맷팅
 */
function formatNumber(num) {
    if (num >= 1000000000000) {
        return (num / 1000000000000).toFixed(1) + '조';
    } else if (num >= 100000000) {
        return (num / 100000000).toFixed(1) + '억';
    } else if (num >= 10000) {
        return (num / 10000).toFixed(1) + '만';
    }
    return num.toLocaleString();
}

/**
 * 페이지 전환
 */
function navigateTo(pageName) {
    console.log(`🔄 페이지 전환: ${pageName}`);
    console.log('📌 현재 기업:', {
        corpCode: appState.currentCorpCode,
        corpName: appState.currentCorpName
    });
    
    // 모든 페이지 숨기기
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // 선택된 페이지 표시
    const targetPage = document.getElementById(`${pageName}-page`);
    if (targetPage) {
        targetPage.classList.add('active');
    } else {
        console.error(`❌ ${pageName}-page 엘리먼트를 찾을 수 없음`);
    }
    
    // 네비게이션 활성화 상태 업데이트
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    const navLink = document.querySelector(`[data-page="${pageName}"]`);
    if (navLink) {
        navLink.classList.add('active');
    }
    
    // 페이지별 데이터 로드
    if (appState.currentCorpCode) {
        console.log(`✅ 기업 코드 있음, ${pageName} 페이지 로드 시작`);
        switch(pageName) {
            case 'dashboard':
                loadDashboard();
                break;
            case 'financial':
                loadFinancialStatement();
                break;
            case 'weakness':
                loadWeaknessAnalysis();
                break;
            case 'report':
                loadReport();
                break;
        }
    } else {
        console.warn('⚠️  기업 코드 없음 - 데이터 로드 건너뜀');
    }
}

// ===========================
// Search Page
// ===========================

/**
 * 기업 검색
 */
async function searchCompany(query) {
    if (!query || query.trim() === '') {
        document.getElementById('search-results').classList.add('hidden');
        return;
    }
    
    console.log('🔍 검색 시작:', query);
    
    try {
        const data = await fetchAPI(`/search?q=${encodeURIComponent(query)}`);
        console.log('✅ 검색 결과:', data);
        displaySearchResults(data.results);
    } catch (error) {
        console.error('❌ 검색 오류:', error);
    }
}

/**
 * 검색 결과 표시
 */
function displaySearchResults(results) {
    const resultsDiv = document.getElementById('search-results');
    
    if (!results || results.length === 0) {
        resultsDiv.innerHTML = '<div class="search-result-item">검색 결과가 없습니다.</div>';
        resultsDiv.classList.remove('hidden');
        console.log('⚠️  검색 결과 없음');
        return;
    }
    
    console.log(`📋 검색 결과 ${results.length}개 표시`);
    
    resultsDiv.innerHTML = results.map((company, index) => {
        const corpCode = company.corp_code || '';
        const corpName = company.corp_name || '알 수 없음';
        const corpNameEng = company.corp_name_eng || '';
        const stockCode = company.stock_code || '';
        const industry = company.industry || CONFIG.DEFAULT_INDUSTRY;
        
        console.log(`  ${index + 1}. ${corpName} (${stockCode}) - ${industry}`);
        
        return `
        <div class="search-result-item" 
             data-index="${index}" 
             data-corp-code="${corpCode}" 
             data-corp-name="${escapeHtml(corpName)}" 
             data-corp-name-eng="${escapeHtml(corpNameEng)}"
             data-stock-code="${stockCode}"
             data-industry="${industry}">
            <div class="result-name">${escapeHtml(corpName)} ${corpNameEng ? '(' + escapeHtml(corpNameEng) + ')' : ''}</div>
            <div class="result-code">종목코드: ${stockCode || 'N/A'} | 업종: ${industry || 'N/A'}</div>
        </div>
        `;
    }).join('');
    
    // 이벤트 리스너 추가
    resultsDiv.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', function() {
            const corpCode = this.getAttribute('data-corp-code');
            const corpName = this.getAttribute('data-corp-name');
            const corpNameEng = this.getAttribute('data-corp-name-eng');
            const stockCode = this.getAttribute('data-stock-code');
            const industry = this.getAttribute('data-industry');
            
            console.log('👆 검색 결과 클릭:', {
                corpCode, corpName, corpNameEng, stockCode, industry
            });
            
            selectCompany(corpCode, corpName, industry, stockCode, corpNameEng);
        });
    });
    
    resultsDiv.classList.remove('hidden');
}

/**
 * HTML 특수문자 이스케이프
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * 기업 선택
 */
function selectCompany(corpCode, corpName, industry, stockCode = null, corpNameEng = null) {
    console.log('🎯 기업 선택 시작:', { corpCode, corpName, industry, stockCode, corpNameEng });
    
    // 필수 정보 검증
    if (!corpCode || !corpName) {
        console.error('❌ 필수 정보 누락:', { corpCode, corpName });
        alert('기업 정보가 올바르지 않습니다.');
        return;
    }
    
    // 기업 정보 저장
    appState.currentCorpCode = corpCode;
    appState.currentCorpName = corpName;
    appState.currentCorpNameEng = corpNameEng || '';
    appState.currentStockCode = stockCode || '';
    appState.currentIndustry = industry || CONFIG.DEFAULT_INDUSTRY;
    appState.companyInfo = null; // 초기화 - API에서 다시 로드
    
    console.log('✅ appState 업데이트 완료:', {
        corpCode: appState.currentCorpCode,
        corpName: appState.currentCorpName,
        corpNameEng: appState.currentCorpNameEng,
        stockCode: appState.currentStockCode,
        industry: appState.currentIndustry
    });
    
    // 검색 결과 숨기기
    document.getElementById('search-results').classList.add('hidden');
    document.getElementById('search-input').value = '';
    
    console.log('🚀 대시보드로 이동...');
    // 대시보드로 이동
    navigateTo('dashboard');
}

// ===========================
// Dashboard Page
// ===========================

/**
 * 대시보드 로드
 */
async function loadDashboard() {
    console.log('📊 대시보드 로드 시작');
    console.log('📌 현재 appState:', {
        corpCode: appState.currentCorpCode,
        corpName: appState.currentCorpName,
        stockCode: appState.currentStockCode,
        industry: appState.currentIndustry,
        year: appState.currentYear
    });
    
    if (!appState.currentCorpCode) {
        console.warn('⚠️  기업 코드 없음');
        alert('기업을 먼저 선택해주세요.');
        navigateTo('search');
        return;
    }
    
    try {
        console.log('🔄 API 요청 중...');
        
        // 기업 정보 및 KPI 데이터 로드
        const [companyData, kpiData] = await Promise.all([
            fetchAPI(`/company/${appState.currentCorpCode}`),
            fetchAPI(`/kpi/${appState.currentCorpCode}?year=${appState.currentYear}`)
        ]);
        
        console.log('✅ API 응답 받음:', { companyData, kpiData });
        
        // 기업 정보를 appState에 저장
        if (companyData && companyData.data) {
            appState.companyInfo = companyData.data;
            // 기본 정보 업데이트 (검색에서 못 받은 정보 보완)
            appState.currentCorpName = companyData.data.corp_name || appState.currentCorpName;
            appState.currentCorpNameEng = companyData.data.corp_name_eng || appState.currentCorpNameEng;
            appState.currentStockCode = companyData.data.stock_code || appState.currentStockCode;
            appState.currentIndustry = companyData.data.industry || appState.currentIndustry;
            
            console.log('✅ 기업 정보 업데이트:', {
                corpName: appState.currentCorpName,
                stockCode: appState.currentStockCode,
                industry: appState.currentIndustry
            });
        }
        
        appState.kpiData = kpiData;
        
        console.log('🎨 화면 업데이트 시작...');
        
        // 화면 업데이트
        updateDashboardHeader(appState.companyInfo || companyData.data);
        updateKPICards(kpiData.kpis);
        updateCharts(kpiData.kpis);
        updateTrends(kpiData.trends);
        
        console.log('✅ 대시보드 로드 완료');
        
    } catch (error) {
        console.error('❌ 대시보드 로드 오류:', error);
        alert('대시보드를 불러오는데 실패했습니다. 다시 시도해주세요.');
    }
}

/**
 * 대시보드 헤더 업데이트
 */
function updateDashboardHeader(companyInfo) {
    console.log('📝 대시보드 헤더 업데이트:', companyInfo);
    
    // 기업명 표시 (API 데이터 우선, 없으면 저장된 기업명 사용)
    const corpName = (companyInfo && companyInfo.corp_name) || appState.currentCorpName || '기업명 없음';
    const stockCode = (companyInfo && companyInfo.stock_code) || appState.currentStockCode || 'N/A';
    const industry = (companyInfo && companyInfo.industry) || appState.currentIndustry || 'N/A';
    const ceoName = (companyInfo && companyInfo.ceo_nm) || 'N/A';
    
    console.log('📊 표시할 정보:', { corpName, stockCode, industry, ceoName });
    
    const nameElement = document.getElementById('dashboard-company-name');
    const infoElement = document.getElementById('dashboard-company-info');
    
    if (nameElement) {
        nameElement.textContent = corpName;
    } else {
        console.error('❌ dashboard-company-name 엘리먼트를 찾을 수 없음');
    }
    
    // 기업 정보 표시 - 더 상세하게
    const infoText = `종목코드: ${stockCode} | 업종: ${industry} | CEO: ${ceoName}`;
    
    if (infoElement) {
        infoElement.textContent = infoText;
    } else {
        console.error('❌ dashboard-company-info 엘리먼트를 찾을 수 없음');
    }
    
    console.log('✅ 대시보드 헤더 업데이트 완료');
}

/**
 * KPI 카드 업데이트
 */
function updateKPICards(kpis) {
    console.log('📊 KPI 카드 업데이트:', kpis);
    
    // ROA
    updateKPICard('roa', kpis.roa);
    
    // ROE
    updateKPICard('roe', kpis.roe);
    
    // 부채비율
    updateKPICard('debt', kpis.debt_ratio);
    
    // 유동비율
    updateKPICard('current', kpis.current_ratio);
}

/**
 * 개별 KPI 카드 업데이트
 */
function updateKPICard(id, kpiData) {
    const valueEl = document.getElementById(`${id}-value`);
    const badgeEl = document.getElementById(`${id}-badge`);
    
    if (kpiData && kpiData.value !== undefined) {
        const currentYear = appState.currentYear || CONFIG.DEFAULT_YEAR;
        const previousYear = currentYear - 1;
        
        // 당해년/전년 수치
        const currentValue = kpiData.value || 0;
        const previousValue = kpiData.previous_value || 0;
        
        // 실제 차이 계산 (백엔드 값 우선, 없으면 직접 계산)
        const change = kpiData.change !== undefined 
            ? kpiData.change 
            : (currentValue - previousValue);
        
        const changeRate = kpiData.change_rate !== undefined 
            ? kpiData.change_rate 
            : (previousValue !== 0 ? ((change / previousValue) * 100) : 0);
        
        console.log(`📊 KPI 카드 [${id}]: 당기=${currentValue}, 전기=${previousValue}, 차이=${change.toFixed(2)}, 증감률=${changeRate.toFixed(2)}%`);
        
        // 변화 방향 및 색상
        const isPositive = change > 0;
        const changeColor = isPositive ? '#00C851' : change < 0 ? '#FF4B4B' : '#666';
        const arrow = isPositive ? '▲' : change < 0 ? '▼' : '━';
        
        // HTML 생성
        valueEl.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                <!-- 당해년 -->
                <div>
                    <div style="font-size: 0.7rem; color: #0047FF; font-weight: 600; margin-bottom: 0.25rem;">${currentYear}년 (당기)</div>
                    <div style="font-size: 2rem; font-weight: bold; color: #0047FF;">${currentValue.toFixed(2)}${kpiData.unit || ''}</div>
                </div>
                
                <!-- 전년 -->
                <div style="padding-top: 0.5rem; border-top: 1px dashed #e0e0e0;">
                    <div style="font-size: 0.65rem; color: #666; margin-bottom: 0.25rem;">${previousYear}년 (전기)</div>
                    <div style="font-size: 1.2rem; font-weight: 600; color: #888;">${previousValue.toFixed(2)}${kpiData.unit || ''}</div>
                </div>
                
                <!-- 실제 차이 -->
                <div style="padding: 0.6rem; background: ${changeColor}15; border-radius: 6px; margin-top: 0.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 0.7rem; color: #666;">전년 대비</span>
                        <span style="font-size: 1.1rem; font-weight: bold; color: ${changeColor};">
                            ${arrow} ${Math.abs(changeRate).toFixed(2)}%
                        </span>
                    </div>
                    <div style="font-size: 0.7rem; color: #666; margin-top: 0.3rem;">
                        (${change >= 0 ? '+' : ''}${change.toFixed(2)}%p)
                    </div>
                </div>
            </div>
        `;
        
        badgeEl.textContent = getStatusText(kpiData.status);
        badgeEl.className = `kpi-badge ${kpiData.status}`;
    } else {
        valueEl.textContent = 'N/A';
        badgeEl.textContent = '-';
        badgeEl.className = 'kpi-badge';
    }
}

/**
 * 상태 텍스트 변환
 */
function getStatusText(status) {
    const statusMap = {
        'excellent': '우수',
        'good': '양호',
        'fair': '보통',
        'poor': '미흡',
        'error': '오류'
    };
    return statusMap[status] || '-';
}

/**
 * 차트 업데이트
 */
function updateCharts(kpis) {
    // 수익성 차트
    updateProfitabilityChart(kpis);
    
    // 재무구조 차트
    updateFinancialStructureChart(kpis);
}

/**
 * 수익성 차트
 */
function updateProfitabilityChart(kpis) {
    const ctx = document.getElementById('profitability-chart');
    
    // 기존 차트 제거
    if (profitabilityChart) {
        profitabilityChart.destroy();
    }
    
    profitabilityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['ROA', 'ROE', '영업이익률', '순이익률'],
            datasets: [{
                label: '수익성 지표 (%)',
                data: [
                    kpis.roa?.value || 0,
                    kpis.roe?.value || 0,
                    kpis.operating_margin?.value || 0,
                    kpis.net_profit_margin?.value || 0
                ],
                backgroundColor: [
                    'rgba(0, 71, 255, 0.8)',
                    'rgba(0, 194, 255, 0.8)',
                    'rgba(51, 181, 229, 0.8)',
                    'rgba(0, 200, 81, 0.8)'
                ],
                borderColor: [
                    'rgba(0, 71, 255, 1)',
                    'rgba(0, 194, 255, 1)',
                    'rgba(51, 181, 229, 1)',
                    'rgba(0, 200, 81, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y.toFixed(2) + '%';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

/**
 * 재무구조 차트
 */
function updateFinancialStructureChart(kpis) {
    const ctx = document.getElementById('financial-structure-chart');
    
    // 기존 차트 제거
    if (financialStructureChart) {
        financialStructureChart.destroy();
    }
    
    financialStructureChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['부채비율', '유동비율'],
            datasets: [{
                label: '재무구조 (%)',
                data: [
                    kpis.debt_ratio?.value || 0,
                    kpis.current_ratio?.value || 0
                ],
                backgroundColor: [
                    'rgba(255, 75, 75, 0.8)',
                    'rgba(0, 200, 81, 0.8)'
                ],
                borderColor: [
                    'rgba(255, 75, 75, 1)',
                    'rgba(0, 200, 81, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed.toFixed(2) + '%';
                        }
                    }
                }
            }
        }
    });
}

/**
 * 트렌드 업데이트
 */
function updateTrends(trends) {
    const trendsContainer = document.getElementById('trend-cards');
    
    if (!trends || Object.keys(trends).length === 0) {
        trendsContainer.innerHTML = '<p>트렌드 데이터가 없습니다.</p>';
        return;
    }
    
    const currentYear = appState.currentYear || CONFIG.DEFAULT_YEAR;
    const previousYear = currentYear - 1;
    
    console.log('📈 트렌드 데이터 수신:', trends);
    
    trendsContainer.innerHTML = Object.entries(trends).map(([name, data]) => {
        // 실제 전년/당기 수치에서 증감 계산
        const currentValue = data.current || 0;
        const previousValue = data.previous || 0;
        const changeAmount = data.change || (currentValue - previousValue);
        const calculatedChangeRate = previousValue !== 0 
            ? ((changeAmount / previousValue) * 100) 
            : 0;
        
        // 백엔드에서 온 change_rate 또는 직접 계산한 값 사용
        const changeRate = data.change_rate !== undefined ? data.change_rate : calculatedChangeRate;
        
        const isPositive = changeAmount > 0;
        const changeColor = isPositive ? '#00C851' : changeAmount < 0 ? '#FF4B4B' : '#FFA500';
        const arrow = isPositive ? '▲' : changeAmount < 0 ? '▼' : '━';
        
        console.log(`  ${name}: 당기=${formatNumber(currentValue)}, 전기=${formatNumber(previousValue)}, 차이=${formatNumber(changeAmount)}, 증감률=${changeRate.toFixed(2)}%`);
        
        return `
            <div class="trend-card" style="padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid ${changeColor};">
                <div class="trend-name" style="font-size: 0.9rem; color: #666; margin-bottom: 1rem; font-weight: 600;">${name}</div>
                
                <!-- 당해년 -->
                <div style="margin-bottom: 0.75rem;">
                    <div style="font-size: 0.75rem; color: #0047FF; font-weight: 600; margin-bottom: 0.3rem;">${currentYear}년 (당기)</div>
                    <div style="font-size: 1.9rem; font-weight: bold; color: #0047FF;">${formatNumber(currentValue)}</div>
                </div>
                
                <!-- 전년 -->
                <div style="margin-bottom: 0.75rem; padding-top: 0.75rem; border-top: 1px dashed #e0e0e0;">
                    <div style="font-size: 0.75rem; color: #666; font-weight: 600; margin-bottom: 0.3rem;">${previousYear}년 (전기)</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #888;">${formatNumber(previousValue)}</div>
                </div>
                
                <!-- 증감 (실제 차이) -->
                <div class="trend-change" style="margin-top: 1rem; padding: 0.9rem; background: ${changeColor}15; border-radius: 8px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.85rem; color: #666; font-weight: 600;">전년 대비</span>
                        <span style="font-size: 1.4rem; font-weight: bold; color: ${changeColor};">
                            ${arrow} ${Math.abs(changeRate).toFixed(2)}%
                        </span>
                    </div>
                    <div style="font-size: 0.85rem; color: #666;">
                        ${isPositive ? '▲ 증가' : changeAmount < 0 ? '▼ 감소' : '━ 변동없음'} 
                        <strong style="color: ${changeColor};">${formatNumber(Math.abs(changeAmount))}</strong>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.75rem; color: #999;">
                        계산식: (${formatNumber(currentValue)} - ${formatNumber(previousValue)})
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    console.log('✅ 트렌드 카드 업데이트 완료');
}

// ===========================
// Financial Statement Page
// ===========================

/**
 * 재무제표 로드
 */
async function loadFinancialStatement() {
    console.log('📊 재무제표 로드 시작');
    console.log('📌 현재 기업:', {
        corpCode: appState.currentCorpCode,
        corpName: appState.currentCorpName,
        year: appState.currentYear
    });
    
    if (!appState.currentCorpCode) {
        alert('기업을 먼저 선택해주세요.');
        navigateTo('search');
        return;
    }
    
    try {
        // 기업 정보가 없으면 먼저 로드
        if (!appState.companyInfo) {
            console.log('🔄 기업 정보 로드 중...');
            const companyData = await fetchAPI(`/company/${appState.currentCorpCode}`);
            if (companyData && companyData.data) {
                appState.companyInfo = companyData.data;
                console.log('✅ 기업 정보 로드 완료:', appState.companyInfo);
            }
        }
        
        // 재무제표 데이터 로드
        console.log(`🔄 재무제표 API 요청: /financial/${appState.currentCorpCode}?year=${appState.currentYear}`);
        const response = await fetchAPI(`/financial/${appState.currentCorpCode}?year=${appState.currentYear}`);
        
        console.log('✅ 재무제표 API 응답:', response);
        
        // 응답 구조 확인
        if (response && response.data) {
            appState.financialData = response.data;
            console.log('✅ 재무제표 데이터 저장:', appState.financialData);
        } else {
            appState.financialData = response;
            console.log('⚠️  응답 구조 다름, 직접 저장:', appState.financialData);
        }
        
        // 화면 업데이트
        updateFinancialHeader();
        displayFinancialStatement(appState.financialData, 'balance'); // 기본으로 재무상태표 표시
        
    } catch (error) {
        console.error('❌ 재무제표 로드 오류:', error);
        alert('재무제표를 불러오는데 실패했습니다.');
    }
}

/**
 * 재무제표 헤더 업데이트
 */
function updateFinancialHeader() {
    const corpName = appState.currentCorpName || '기업명 없음';
    const stockCode = appState.currentStockCode ? `(${appState.currentStockCode})` : '';
    const year = appState.currentYear || CONFIG.DEFAULT_YEAR;
    
    const element = document.getElementById('financial-company-name');
    if (element) {
        element.textContent = `${corpName} ${stockCode} - ${year}년 재무제표`;
    }
}

/**
 * 재무제표 탭 전환
 */
function switchFinancialTab(tabName) {
    console.log(`🔄 재무제표 탭 전환: ${tabName}`);
    
    // 탭 활성화 상태 변경
    document.querySelectorAll('.financial-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // 재무제표 표시
    if (appState.financialData) {
        displayFinancialStatement(appState.financialData, tabName);
    }
}

/**
 * 재무제표 표시
 */
function displayFinancialStatement(data, type) {
    console.log('📊 재무제표 표시 시작:', { data, type });
    
    const container = document.getElementById('financial-content');
    
    if (!container) {
        console.error('❌ financial-content 엘리먼트를 찾을 수 없음');
        return;
    }
    
    if (!data) {
        console.warn('⚠️  재무제표 데이터 없음');
        container.innerHTML = '<p style="text-align: center; color: #666; padding: 2rem;">재무제표 데이터가 없습니다.</p>';
        return;
    }
    
    // 데이터 리스트 확인
    const accountList = data.list || [];
    console.log(`📋 계정과목 수: ${accountList.length}개`);
    
    if (accountList.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666; padding: 2rem;">재무제표 항목이 없습니다.</p>';
        return;
    }
    
    const currentYear = appState.currentYear || CONFIG.DEFAULT_YEAR;
    const previousYear = currentYear - 1;
    
    let accounts = [];
    
    // 재무제표 유형별 계정과목 필터링
    if (type === 'balance') {
        // 재무상태표 (BS)
        const balanceAccounts = [
            '자산총계', '유동자산', '비유동자산',
            '부채총계', '유동부채', '비유동부채',
            '자본총계'
        ];
        accounts = accountList.filter(item => 
            balanceAccounts.includes(item.account_nm) || item.sj_div === 'BS'
        );
        // 주요 계정만 필터링 (너무 많으면)
        if (accounts.length > 20) {
            accounts = accountList.filter(item => balanceAccounts.includes(item.account_nm));
        }
        console.log(`💼 재무상태표 계정: ${accounts.length}개`);
    } else if (type === 'income') {
        // 포괄손익계산서 (IS + CIS 통합)
        // IS와 CIS 모두 포함
        accounts = accountList.filter(item => 
            item.sj_div === 'IS' || item.sj_div === 'CIS'
        );
        
        console.log(`💰 손익/포괄손익 원본 계정: ${accounts.length}개`);
        
        // 중복 제거 및 주요 계정만 선택
        const uniqueAccounts = [];
        const seenNames = new Set();
        
        // 우선순위 계정 (표시 순서대로)
        const priorityKeywords = [
            '매출액', '매출', '수익(매출액)',
            '매출원가',
            '매출총이익',
            '판매비',
            '영업이익',
            '법인세비용차감전',
            '법인세비용',
            '당기순이익',
            '기타포괄손익',
            '총포괄이익'
        ];
        
        // 우선순위 순서대로 검색
        priorityKeywords.forEach(keyword => {
            const found = accounts.find(item => 
                item.account_nm.includes(keyword) && !seenNames.has(item.account_nm)
            );
            if (found) {
                uniqueAccounts.push(found);
                seenNames.add(found.account_nm);
            }
        });
        
        accounts = uniqueAccounts.slice(0, 20); // 최대 20개
        console.log(`💰 포괄손익계산서 계정 (필터링 후): ${accounts.length}개`);
        accounts.forEach(a => console.log(`    - ${a.account_nm}`));
    } else if (type === 'cashflow') {
        // 현금흐름표 (CF)
        const cashflowAccounts = [
            '영업활동현금흐름', '영업활동으로인한현금흐름',
            '투자활동현금흐름', '투자활동으로인한현금흐름',
            '재무활동현금흐름', '재무활동으로인한현금흐름',
            '현금및현금성자산의순증가'
        ];
        accounts = accountList.filter(item => 
            cashflowAccounts.some(name => item.account_nm.includes(name) || name.includes(item.account_nm)) ||
            item.sj_div === 'CF'
        );
        // 중복 제거
        const uniqueAccounts = [];
        const seenNames = new Set();
        accounts.forEach(item => {
            if (!seenNames.has(item.account_nm)) {
                uniqueAccounts.push(item);
                seenNames.add(item.account_nm);
            }
        });
        accounts = uniqueAccounts.slice(0, 10);
        console.log(`💵 현금흐름표 계정: ${accounts.length}개`);
    }
    
    if (accounts.length === 0) {
        console.warn('⚠️  필터링 후 계정과목 없음');
        container.innerHTML = `
            <p style="text-align: center; color: #666; padding: 2rem;">
                해당 재무제표 데이터를 찾을 수 없습니다.<br>
                <small>사용 가능한 계정: ${accountList.map(a => a.account_nm).join(', ')}</small>
            </p>
        `;
        return;
    }
    
    // 테이블 생성
    let tableHtml = `
        <div style="overflow-x: auto;">
            <table class="financial-table">
                <thead>
                    <tr>
                        <th style="width: 30%;">계정과목</th>
                        <th style="width: 25%;">${currentYear}년 (당기)</th>
                        <th style="width: 25%;">${previousYear}년 (전기)</th>
                        <th style="width: 20%;">전년 대비 증감</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // 재무상태표 구조화
    if (type === 'balance') {
        tableHtml += generateBalanceSheet(accounts, currentYear, previousYear);
    } else if (type === 'income') {
        tableHtml += generateIncomeStatement(accounts, currentYear, previousYear);
    } else if (type === 'cashflow') {
        tableHtml += generateCashflowStatement(accounts, currentYear, previousYear);
    }
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = tableHtml;
    console.log(`✅ ${type} 재무제표 표시 완료`);
}

/**
 * 재무상태표 생성
 */
function generateBalanceSheet(accounts, currentYear, previousYear) {
    console.log('💼 재무상태표 생성 시작, 계정 수:', accounts.length);
    let html = '';
    
    // 자산 섹션
    html += '<tr class="category-row"><td colspan="4" style="padding: 1rem; font-size: 1.1rem;">【 자산 】</td></tr>';
    const assetAccounts = ['자산총계', '유동자산', '비유동자산'];
    console.log('  자산 계정 필터링...');
    assetAccounts.forEach(name => {
        const account = accounts.find(a => a.account_nm === name);
        if (account) {
            html += generateFinancialRow(account, name === '자산총계');
        } else {
            console.warn(`  ⚠️  ${name} 계정 없음`);
        }
    });
    
    // 부채 섹션
    html += '<tr class="category-row"><td colspan="4" style="padding: 1rem; font-size: 1.1rem;">【 부채 】</td></tr>';
    const liabilityAccounts = ['부채총계', '유동부채', '비유동부채'];
    console.log('  부채 계정 필터링...');
    liabilityAccounts.forEach(name => {
        const account = accounts.find(a => a.account_nm === name);
        if (account) {
            html += generateFinancialRow(account, name === '부채총계');
        } else {
            console.warn(`  ⚠️  ${name} 계정 없음`);
        }
    });
    
    // 자본 섹션
    html += '<tr class="category-row"><td colspan="4" style="padding: 1rem; font-size: 1.1rem;">【 자본 】</td></tr>';
    console.log('  자본 계정 필터링...');
    const equityAccount = accounts.find(a => a.account_nm === '자본총계');
    if (equityAccount) {
        html += generateFinancialRow(equityAccount, true);
    } else {
        console.warn('  ⚠️  자본총계 계정 없음');
    }
    
    console.log('✅ 재무상태표 HTML 생성 완료');
    return html;
}

/**
 * 포괄손익계산서 생성 (IS + CIS 통합)
 */
function generateIncomeStatement(accounts, currentYear, previousYear) {
    console.log('💰 포괄손익계산서 생성 시작, 계정 수:', accounts.length);
    
    let html = '';
    
    // IS (손익계산서) 섹션
    const isAccounts = accounts.filter(a => a.sj_div === 'IS');
    if (isAccounts.length > 0) {
        html += '<tr class="category-row"><td colspan="4" style="padding: 1rem; font-size: 1.1rem;">【 손익계산서 】</td></tr>';
        isAccounts.forEach(account => {
            const isTotal = account.account_nm.includes('영업이익') || 
                           account.account_nm.includes('법인세비용차감전');
            html += generateFinancialRow(account, isTotal);
        });
    }
    
    // CIS (포괄손익계산서) 섹션
    const cisAccounts = accounts.filter(a => a.sj_div === 'CIS');
    if (cisAccounts.length > 0) {
        html += '<tr class="category-row"><td colspan="4" style="padding: 1rem; font-size: 1.1rem;">【 포괄손익 】</td></tr>';
        cisAccounts.forEach(account => {
            const isTotal = account.account_nm.includes('당기순이익') || 
                           account.account_nm.includes('총포괄이익');
            html += generateFinancialRow(account, isTotal);
        });
    }
    
    console.log('✅ 포괄손익계산서 HTML 생성 완료');
    return html;
}

/**
 * 현금흐름표 생성
 */
function generateCashflowStatement(accounts, currentYear, previousYear) {
    console.log('💵 현금흐름표 생성 시작, 계정 수:', accounts.length);
    let html = '<tr class="category-row"><td colspan="4" style="padding: 1rem; font-size: 1.1rem;">【 현금흐름표 】</td></tr>';
    
    console.log('  사용 가능한 계정:', accounts.map(a => a.account_nm).join(', '));
    
    // 우선순위 계정 (실제 DART 계정과목명 기준)
    const priorities = [
        { keywords: ['영업활동'], label: '영업활동현금흐름' },
        { keywords: ['투자활동'], label: '투자활동현금흐름' },
        { keywords: ['재무활동'], label: '재무활동현금흐름' },
        { keywords: ['현금및현금성자산의순증가', '현금의증가'], label: '현금및현금성자산의순증가' }
    ];
    
    priorities.forEach(priority => {
        const account = accounts.find(a => 
            priority.keywords.some(keyword => a.account_nm.includes(keyword))
        );
        
        if (account) {
            html += generateFinancialRow(account, priority.label.includes('순증가'));
        } else {
            console.warn(`  ⚠️  ${priority.label} 계정 없음`);
        }
    });
    
    console.log('✅ 현금흐름표 HTML 생성 완료');
    return html;
}

/**
 * 재무제표 행 생성
 */
function generateFinancialRow(account, isTotal = false) {
    if (!account) {
        console.warn('⚠️  계정 데이터 없음');
        return '';
    }
    
    const current = parseFloat(account.thstrm_amount || 0);
    const previous = parseFloat(account.frmtrm_amount || 0);
    const change = current - previous;
    const changeRate = previous !== 0 ? ((change / previous) * 100) : 0;
    
    console.log(`  ${account.account_nm}: 당기=${current.toFixed(0)}, 전기=${previous.toFixed(0)}, 차이=${change.toFixed(0)}, 증감률=${changeRate.toFixed(2)}%`);
    
    const changeClass = change > 0 ? 'positive' : change < 0 ? 'negative' : '';
    const arrow = change > 0 ? '▲' : change < 0 ? '▼' : '━';
    const rowClass = isTotal ? 'total-row' : '';
    
    return `
        <tr class="${rowClass}">
            <td style="padding-left: ${isTotal ? '1rem' : '2rem'};">${isTotal ? '■ ' : ''}${account.account_nm}</td>
            <td><strong>${formatNumber(current)}</strong></td>
            <td>${formatNumber(previous)}</td>
            <td class="${changeClass}">
                <strong>${arrow} ${formatNumber(Math.abs(change))}</strong>
                <br>
                <span style="font-size: 0.85rem;">(${changeRate >= 0 ? '+' : ''}${changeRate.toFixed(2)}%)</span>
            </td>
        </tr>
    `;
}

// ===========================
// Weakness Page
// ===========================

/**
 * 취약점 분석 로드
 */
async function loadWeaknessAnalysis() {
    if (!appState.currentCorpCode) {
        alert('기업을 먼저 선택해주세요.');
        navigateTo('search');
        return;
    }
    
    try {
        // 기업 정보가 없으면 먼저 로드
        if (!appState.companyInfo) {
            const companyData = await fetchAPI(`/company/${appState.currentCorpCode}`);
            if (companyData && companyData.data) {
                appState.companyInfo = companyData.data;
                appState.currentIndustry = companyData.data.industry || appState.currentIndustry;
            }
        }
        
        // KPI와 취약점 분석 데이터를 함께 로드
        const [kpiData, weaknessData] = await Promise.all([
            fetchAPI(`/kpi/${appState.currentCorpCode}?year=${appState.currentYear}`),
            fetchAPI(`/weakness/${appState.currentCorpCode}?year=${appState.currentYear}&industry=${appState.currentIndustry}`)
        ]);
        
        appState.kpiData = kpiData;
        appState.weaknessData = weaknessData;
        
        // 화면 업데이트
        updateWeaknessHeader();
        displayKPIComparison(kpiData.kpis, weaknessData.analysis.benchmark); // 새로운 비교 테이블
        updateRiskOverview(weaknessData.analysis);
        displayWeaknesses(weaknessData.analysis.weaknesses);
        displayPriorities(weaknessData.priorities);
        
    } catch (error) {
        console.error('취약점 분석 로드 오류:', error);
    }
}

/**
 * 취약점 페이지 헤더 업데이트
 */
function updateWeaknessHeader() {
    console.log('🔍 취약점 분석 헤더 업데이트');
    
    const corpName = appState.currentCorpName || '기업명 없음';
    const stockCode = appState.currentStockCode || 'N/A';
    const industry = appState.currentIndustry || 'N/A';
    const year = appState.currentYear || CONFIG.DEFAULT_YEAR;
    
    console.log('📊 표시할 정보:', { corpName, stockCode, industry, year });
    
    const headerText = `${corpName} (${stockCode}) - ${industry} | ${year}년 기준`;
    
    const element = document.getElementById('weakness-company-name');
    if (element) {
        element.textContent = headerText;
        console.log('✅ 취약점 분석 헤더 업데이트 완료');
    } else {
        console.error('❌ weakness-company-name 엘리먼트를 찾을 수 없음');
    }
}

/**
 * KPI 비교 테이블 표시
 */
function displayKPIComparison(kpis, benchmark) {
    console.log('📊 KPI 비교 테이블 생성:', { kpis, benchmark });
    
    const container = document.getElementById('kpi-comparison');
    if (!container) {
        console.warn('⚠️  kpi-comparison 엘리먼트를 찾을 수 없음');
        return;
    }
    
    // KPI 목록
    const kpiList = [
        { key: 'roa', name: 'ROA (총자산이익률)', unit: '%', good: 'higher' },
        { key: 'roe', name: 'ROE (자기자본이익률)', unit: '%', good: 'higher' },
        { key: 'debt_ratio', name: '부채비율', unit: '%', good: 'lower' },
        { key: 'current_ratio', name: '유동비율', unit: '%', good: 'higher' },
        { key: 'operating_margin', name: '영업이익률', unit: '%', good: 'higher' }
    ];
    
    let tableHtml = `
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
                <thead>
                    <tr style="background: linear-gradient(135deg, #0047FF 0%, #00C2FF 100%); color: white;">
                        <th style="padding: 1rem; text-align: left; font-weight: 600;">지표</th>
                        <th style="padding: 1rem; text-align: center; font-weight: 600;">현재 기업</th>
                        <th style="padding: 1rem; text-align: center; font-weight: 600;">업종 평균</th>
                        <th style="padding: 1rem; text-align: center; font-weight: 600;">차이</th>
                        <th style="padding: 1rem; text-align: center; font-weight: 600;">평가</th>
                        <th style="padding: 1rem; text-align: center; font-weight: 600;">비교 차트</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    kpiList.forEach((kpi, index) => {
        const currentValue = kpis[kpi.key]?.value || 0;
        const benchmarkValue = benchmark?.[kpi.key] || 0;
        const diff = currentValue - benchmarkValue;
        const diffPercent = benchmarkValue !== 0 ? ((diff / benchmarkValue) * 100).toFixed(1) : 0;
        
        // 평가 (높을수록 좋은지, 낮을수록 좋은지에 따라)
        let evaluation, evalColor, evalIcon;
        if (kpi.good === 'higher') {
            if (diff > 0) {
                evaluation = '우수';
                evalColor = '#00C851';
                evalIcon = '✓';
            } else if (diff > -benchmarkValue * 0.2) {
                evaluation = '양호';
                evalColor = '#33B5E5';
                evalIcon = '○';
            } else {
                evaluation = '미흡';
                evalColor = '#FF4B4B';
                evalIcon = '✗';
            }
        } else { // lower is better
            if (diff < 0) {
                evaluation = '우수';
                evalColor = '#00C851';
                evalIcon = '✓';
            } else if (diff < benchmarkValue * 0.2) {
                evaluation = '양호';
                evalColor = '#33B5E5';
                evalIcon = '○';
            } else {
                evaluation = '미흡';
                evalColor = '#FF4B4B';
                evalIcon = '✗';
            }
        }
        
        // 비교 바 차트
        const maxValue = Math.max(currentValue, benchmarkValue) * 1.2;
        const currentBarWidth = (currentValue / maxValue * 100).toFixed(1);
        const benchmarkBarWidth = (benchmarkValue / maxValue * 100).toFixed(1);
        
        const rowBg = index % 2 === 0 ? '#f8f9fa' : 'white';
        
        tableHtml += `
            <tr style="background: ${rowBg}; border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 1rem; font-weight: 600;">${kpi.name}</td>
                <td style="padding: 1rem; text-align: center;">
                    <span style="font-size: 1.3rem; font-weight: bold; color: #0047FF;">${currentValue.toFixed(2)}${kpi.unit}</span>
                </td>
                <td style="padding: 1rem; text-align: center;">
                    <span style="font-size: 1.3rem; font-weight: bold; color: #666;">${benchmarkValue.toFixed(2)}${kpi.unit}</span>
                </td>
                <td style="padding: 1rem; text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: bold; color: ${diff >= 0 ? '#0047FF' : '#FF4B4B'};">
                        ${diff >= 0 ? '+' : ''}${diff.toFixed(2)}${kpi.unit}
                    </div>
                    <div style="font-size: 0.9rem; color: #666;">
                        (${diffPercent >= 0 ? '+' : ''}${diffPercent}%)
                    </div>
                </td>
                <td style="padding: 1rem; text-align: center;">
                    <div style="display: inline-block; padding: 0.5rem 1rem; background: ${evalColor}; color: white; border-radius: 20px; font-weight: bold;">
                        ${evalIcon} ${evaluation}
                    </div>
                </td>
                <td style="padding: 1rem;">
                    <div style="margin-bottom: 0.3rem;">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span style="font-size: 0.75rem; color: #666; width: 50px;">현재</span>
                            <div style="flex: 1; background: #e0e0e0; height: 20px; border-radius: 10px; overflow: hidden;">
                                <div style="width: ${currentBarWidth}%; height: 100%; background: linear-gradient(90deg, #0047FF, #00C2FF); transition: width 0.3s;"></div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span style="font-size: 0.75rem; color: #666; width: 50px;">평균</span>
                            <div style="flex: 1; background: #e0e0e0; height: 20px; border-radius: 10px; overflow: hidden;">
                                <div style="width: ${benchmarkBarWidth}%; height: 100%; background: #999; transition: width 0.3s;"></div>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        `;
    });
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = tableHtml;
    console.log('✅ KPI 비교 테이블 생성 완료');
}

/**
 * 위험도 개요 업데이트
 */
function updateRiskOverview(analysis) {
    const riskLevel = analysis.risk_level;
    
    console.log('🎯 위험도 분석:', analysis);
    
    // 위험도 표시
    const indicator = document.getElementById('risk-indicator');
    indicator.className = `risk-indicator ${riskLevel.level}`;
    indicator.textContent = riskLevel.label[0]; // 첫 글자만 (높, 보, 낮, 안)
    
    document.getElementById('risk-label').textContent = `위험도: ${riskLevel.label}`;
    document.getElementById('risk-score').textContent = `${riskLevel.score}점`;
    document.getElementById('risk-message').textContent = riskLevel.message;
    
    // 통계
    document.getElementById('critical-count').textContent = analysis.critical_issues;
    document.getElementById('warning-count').textContent = analysis.warning_issues;
    document.getElementById('info-count').textContent = analysis.info_issues;
}

/**
 * 취약점 목록 표시
 */
function displayWeaknesses(weaknesses) {
    const container = document.getElementById('weakness-items');
    
    if (!weaknesses || weaknesses.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--success-color); font-size: 1.2rem;">✅ 발견된 취약점이 없습니다. 재무 상태가 양호합니다!</p>';
        return;
    }
    
    container.innerHTML = weaknesses.map(weakness => {
        // 수치 정보가 있는 경우 표시
        let metricsHtml = '';
        if (weakness.current_value !== undefined && weakness.benchmark_value !== undefined) {
            const diff = weakness.current_value - weakness.benchmark_value;
            const diffPercent = weakness.benchmark_value !== 0 
                ? ((diff / weakness.benchmark_value) * 100).toFixed(1) 
                : 0;
            const diffSign = diff > 0 ? '+' : '';
            const diffColor = diff > 0 ? '#FF4B4B' : '#00C851';
            
            // 부채비율의 경우 낮을수록 좋음
            const isDebtRatio = weakness.title.includes('부채');
            const actualDiffColor = isDebtRatio && diff < 0 ? '#00C851' : 
                                    isDebtRatio && diff > 0 ? '#FF4B4B' : diffColor;
            
            metricsHtml = `
                <div class="weakness-metrics" style="margin: 1rem 0; padding: 1rem; background: #f8f9fa; border-radius: 8px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
                    <div style="text-align: center;">
                        <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">현재값</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #0047FF;">${weakness.current_value.toFixed(2)}%</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">업종 평균</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #666;">${weakness.benchmark_value.toFixed(2)}%</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">차이</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: ${actualDiffColor};">
                            ${diffSign}${diff.toFixed(2)}%
                            <span style="font-size: 0.9rem;">(${diffSign}${diffPercent}%)</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // 영향도 표시
        let impactHtml = '';
        if (weakness.impact) {
            impactHtml = `
                <div class="weakness-impact" style="margin-top: 1rem; padding: 0.75rem; background: #fff3cd; border-left: 4px solid #FFA500; border-radius: 4px;">
                    <strong>⚠️ 영향도:</strong> ${weakness.impact}
                </div>
            `;
        }
        
        return `
            <div class="weakness-item ${weakness.severity}">
                <div class="weakness-header">
                    <div class="weakness-title">
                        <span style="color: #666; font-size: 0.9rem; margin-right: 0.5rem;">[${weakness.rule_id}]</span>
                        ${weakness.title}
                    </div>
                    <div class="weakness-severity ${weakness.severity}">${getSeverityText(weakness.severity)}</div>
                </div>
                <div class="weakness-description">
                    <strong>📊 ${weakness.category}</strong><br>
                    ${weakness.description}
                </div>
                ${metricsHtml}
                ${impactHtml}
                <div class="weakness-recommendation" style="margin-top: 1rem;">
                    <strong>💡 개선 방안:</strong> ${weakness.recommendation}
                </div>
            </div>
        `;
    }).join('');
}

/**
 * 심각도 텍스트 변환
 */
function getSeverityText(severity) {
    const severityMap = {
        'critical': '심각',
        'warning': '경고',
        'info': '정보'
    };
    return severityMap[severity] || severity;
}

/**
 * 개선 우선순위 표시
 */
function displayPriorities(priorities) {
    const container = document.getElementById('priority-list');
    
    if (!priorities || priorities.length === 0) {
        container.innerHTML = '<p>개선 우선순위가 없습니다.</p>';
        return;
    }
    
    container.innerHTML = priorities.map(priority => `
        <div class="priority-item">
            <div class="priority-rank">${priority.rank}</div>
            <div class="priority-content">
                <div class="priority-title">${priority.title}</div>
                <div class="priority-recommendation">${priority.recommendation}</div>
            </div>
        </div>
    `).join('');
}

// ===========================
// Report Page
// ===========================

/**
 * 보고서 로드
 */
async function loadReport() {
    if (!appState.currentCorpCode) {
        alert('기업을 먼저 선택해주세요.');
        navigateTo('search');
        return;
    }
    
    try {
        // 기업 정보가 없으면 먼저 로드
        if (!appState.companyInfo) {
            const companyData = await fetchAPI(`/company/${appState.currentCorpCode}`);
            if (companyData && companyData.data) {
                appState.companyInfo = companyData.data;
                appState.currentIndustry = companyData.data.industry || appState.currentIndustry;
            }
        }
        
        const data = await fetchAPI(
            `/report/${appState.currentCorpCode}?year=${appState.currentYear}&industry=${appState.currentIndustry}`
        );
        
        appState.reportData = data.report;
        
        // 화면 업데이트
        updateReportHeader();
        displayReport(data.report);
        
    } catch (error) {
        console.error('보고서 로드 오류:', error);
    }
}

/**
 * 보고서 헤더 업데이트
 */
function updateReportHeader() {
    console.log('📄 보고서 헤더 업데이트');
    
    const corpName = appState.currentCorpName || '기업명 없음';
    const stockCode = appState.currentStockCode ? `(${appState.currentStockCode})` : '';
    const year = appState.currentYear || CONFIG.DEFAULT_YEAR;
    
    console.log('📊 표시할 정보:', { corpName, stockCode, year });
    
    const headerText = `${corpName} ${stockCode} 종합 분석 보고서 - ${year}년`;
    
    const element = document.getElementById('report-company-name');
    if (element) {
        element.textContent = headerText;
        console.log('✅ 보고서 헤더 업데이트 완료');
    } else {
        console.error('❌ report-company-name 엘리먼트를 찾을 수 없음');
    }
}

/**
 * 보고서 표시
 */
function displayReport(report) {
    const container = document.getElementById('report-content');
    
    const company = report.company;
    const kpis = report.kpis;
    const analysis = report.weakness_analysis;
    
    // 기업명 안전하게 가져오기
    const corpName = (company && company.corp_name) || appState.currentCorpName || '기업명 없음';
    
    container.innerHTML = `
        <div style="max-width: 900px; margin: 0 auto;">
            <h2 style="text-align: center; margin-bottom: 2rem; color: var(--primary-color);">
                📊 ${corpName} 재무 분석 보고서
            </h2>
            
            <section style="margin-bottom: 2rem; padding: 1.5rem; background: var(--bg-secondary); border-radius: var(--radius-md);">
                <h3 style="margin-bottom: 1rem; color: var(--text-primary);">📌 기업 개요</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color);"><strong>기업명</strong></td>
                        <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color);">${corpName}</td>
                        <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color);"><strong>종목코드</strong></td>
                        <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color);">${(company && company.stock_code) || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color);"><strong>대표이사</strong></td>
                        <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color);">${(company && company.ceo_nm) || 'N/A'}</td>
                        <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color);"><strong>업종</strong></td>
                        <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color);">${appState.currentIndustry || 'N/A'}</td>
                    </tr>
                </table>
            </section>
            
            <section style="margin-bottom: 2rem; padding: 1.5rem; background: var(--bg-secondary); border-radius: var(--radius-md);">
                <h3 style="margin-bottom: 1rem; color: var(--text-primary);">📈 핵심 재무지표 (KPI)</h3>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                    <div style="padding: 1rem; background: white; border-radius: var(--radius-sm);">
                        <strong>ROA (총자산순이익률)</strong><br>
                        <span style="font-size: 1.5rem; color: var(--primary-color);">${kpis.roa?.value || 'N/A'}%</span>
                        <span style="margin-left: 0.5rem; padding: 0.25rem 0.5rem; background: ${getStatusColor(kpis.roa?.status)}; color: white; border-radius: 4px; font-size: 0.75rem;">
                            ${getStatusText(kpis.roa?.status)}
                        </span>
                    </div>
                    <div style="padding: 1rem; background: white; border-radius: var(--radius-sm);">
                        <strong>ROE (자기자본순이익률)</strong><br>
                        <span style="font-size: 1.5rem; color: var(--primary-color);">${kpis.roe?.value || 'N/A'}%</span>
                        <span style="margin-left: 0.5rem; padding: 0.25rem 0.5rem; background: ${getStatusColor(kpis.roe?.status)}; color: white; border-radius: 4px; font-size: 0.75rem;">
                            ${getStatusText(kpis.roe?.status)}
                        </span>
                    </div>
                    <div style="padding: 1rem; background: white; border-radius: var(--radius-sm);">
                        <strong>부채비율</strong><br>
                        <span style="font-size: 1.5rem; color: var(--primary-color);">${kpis.debt_ratio?.value || 'N/A'}%</span>
                        <span style="margin-left: 0.5rem; padding: 0.25rem 0.5rem; background: ${getStatusColor(kpis.debt_ratio?.status)}; color: white; border-radius: 4px; font-size: 0.75rem;">
                            ${getStatusText(kpis.debt_ratio?.status)}
                        </span>
                    </div>
                    <div style="padding: 1rem; background: white; border-radius: var(--radius-sm);">
                        <strong>유동비율</strong><br>
                        <span style="font-size: 1.5rem; color: var(--primary-color);">${kpis.current_ratio?.value || 'N/A'}%</span>
                        <span style="margin-left: 0.5rem; padding: 0.25rem 0.5rem; background: ${getStatusColor(kpis.current_ratio?.status)}; color: white; border-radius: 4px; font-size: 0.75rem;">
                            ${getStatusText(kpis.current_ratio?.status)}
                        </span>
                    </div>
                </div>
            </section>
            
            <section style="margin-bottom: 2rem; padding: 1.5rem; background: var(--bg-secondary); border-radius: var(--radius-md);">
                <h3 style="margin-bottom: 1rem; color: var(--text-primary);">⚠️ 취약점 분석 결과</h3>
                <div style="padding: 1.5rem; background: white; border-radius: var(--radius-sm); border-left: 4px solid ${analysis.risk_level.color};">
                    <div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 0.5rem;">
                        위험도: ${analysis.risk_level.label} (점수: ${analysis.risk_level.score})
                    </div>
                    <p style="color: var(--text-secondary);">${analysis.risk_level.message}</p>
                    <div style="margin-top: 1rem; display: flex; gap: 2rem;">
                        <div><strong>심각:</strong> ${analysis.critical_issues}건</div>
                        <div><strong>경고:</strong> ${analysis.warning_issues}건</div>
                        <div><strong>정보:</strong> ${analysis.info_issues}건</div>
                    </div>
                </div>
            </section>
            
            ${analysis.weaknesses.length > 0 ? `
            <section style="margin-bottom: 2rem; padding: 1.5rem; background: var(--bg-secondary); border-radius: var(--radius-md);">
                <h3 style="margin-bottom: 1rem; color: var(--text-primary);">🔍 주요 취약점</h3>
                ${analysis.weaknesses.slice(0, 5).map((w, idx) => `
                    <div style="padding: 1rem; background: white; border-radius: var(--radius-sm); margin-bottom: 0.5rem; border-left: 4px solid ${w.severity === 'critical' ? 'var(--error-color)' : 'var(--warning-color)'};">
                        <strong>${idx + 1}. ${w.title}</strong> <span style="background: ${w.severity === 'critical' ? 'var(--error-color)' : 'var(--warning-color)'}; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">${getSeverityText(w.severity)}</span><br>
                        <p style="margin-top: 0.5rem; color: var(--text-secondary);">${w.description}</p>
                    </div>
                `).join('')}
            </section>
            ` : ''}
            
            <section style="margin-bottom: 2rem; padding: 1.5rem; background: var(--bg-secondary); border-radius: var(--radius-md);">
                <h3 style="margin-bottom: 1rem; color: var(--text-primary);">📋 종합 의견</h3>
                <p style="line-height: 1.8; color: var(--text-primary);">
                    ${generateSummary(kpis, analysis)}
                </p>
            </section>
            
            <footer style="text-align: center; padding: 2rem; color: var(--text-secondary); font-size: 0.875rem;">
                <p>본 보고서는 DART 공시 데이터를 기반으로 자동 생성되었습니다.</p>
                <p>생성일: ${new Date().toLocaleDateString('ko-KR')}</p>
            </footer>
        </div>
    `;
}

/**
 * 상태 색상
 */
function getStatusColor(status) {
    const colorMap = {
        'excellent': '#00C851',
        'good': '#33B5E5',
        'fair': '#FFA500',
        'poor': '#FF4B4B',
        'error': '#6C757D'
    };
    return colorMap[status] || '#6C757D';
}

/**
 * 종합 의견 생성
 */
function generateSummary(kpis, analysis) {
    const riskLevel = analysis.risk_level.level;
    const criticalCount = analysis.critical_issues;
    const corpName = appState.currentCorpName || '해당 기업';
    const year = appState.currentYear || CONFIG.DEFAULT_YEAR;
    
    let summary = `${corpName}의 ${year}년 재무제표 분석 결과, `;
    
    if (riskLevel === 'high') {
        summary += `심각한 재무 위험 요소가 ${criticalCount}건 발견되었습니다. `;
        summary += `즉각적인 개선 조치가 필요하며, 특히 `;
        if (analysis.weaknesses.length > 0) {
            summary += `"${analysis.weaknesses[0].title}" 항목에 대한 집중적인 관리가 요구됩니다. `;
        }
        summary += `경영진은 부채 관리 및 수익성 개선에 집중해야 합니다.`;
    } else if (riskLevel === 'medium') {
        summary += `일부 재무 취약점이 발견되었으나 관리 가능한 수준입니다. `;
        summary += `중장기적인 개선 계획 수립을 권장합니다. `;
        summary += `예방적 재무 관리를 통해 위험 요소를 미연에 방지할 수 있습니다.`;
    } else if (riskLevel === 'low') {
        summary += `전반적으로 양호한 재무 상태를 유지하고 있습니다. `;
        summary += `다만 일부 항목에 대한 지속적인 모니터링이 필요합니다. `;
        summary += `현재의 안정적인 재무 구조를 유지하면서 성장 기회를 모색할 수 있습니다.`;
    } else {
        summary += `우수한 재무 건전성을 보이고 있습니다. `;
        summary += `현재의 재무 관리 수준을 유지하시기 바랍니다. `;
        summary += `안정적인 수익 창출과 건전한 재무 구조로 지속 가능한 성장이 기대됩니다.`;
    }
    
    return summary;
}

/**
 * PDF 다운로드 (시뮬레이션)
 */
function downloadReport() {
    alert('PDF 다운로드 기능은 추후 구현 예정입니다.\n현재 화면을 인쇄(Ctrl+P)하여 PDF로 저장할 수 있습니다.');
    window.print();
}

// ===========================
// Event Listeners
// ===========================

document.addEventListener('DOMContentLoaded', function() {
    // 네비게이션
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            navigateTo(page);
        });
    });
    
    // 검색
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value;
        if (query.length >= 2) {
            searchCompany(query);
        }
    });
    
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchCompany(e.target.value);
        }
    });
    
    searchBtn.addEventListener('click', function() {
        searchCompany(searchInput.value);
    });
    
    // 빠른 검색 버튼
    document.querySelectorAll('.quick-link-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const corpCode = this.getAttribute('data-corp');
            const corpName = this.getAttribute('data-name') || this.textContent.trim();
            const industry = this.getAttribute('data-industry') || CONFIG.DEFAULT_INDUSTRY;
            const stockCode = this.getAttribute('data-stock-code') || null;
            const corpNameEng = this.getAttribute('data-corp-name-eng') || null;
            selectCompany(corpCode, corpName, industry, stockCode, corpNameEng);
        });
    });
    
    // 기업 변경 버튼
    document.getElementById('change-company-btn').addEventListener('click', function() {
        navigateTo('search');
    });
    
    // PDF 다운로드 버튼
    document.getElementById('download-report-btn').addEventListener('click', function() {
        downloadReport();
    });
    
    // 초기 페이지 설정
    navigateTo('search');
});

// 전역 함수 노출 (HTML onclick에서 사용)
window.switchFinancialTab = switchFinancialTab;
window.navigateTo = navigateTo;

console.log('✅ DART Financial Analyzer 초기화 완료');
console.log('🔗 API Base URL:', CONFIG.API_BASE_URL);
console.log('📍 Location:', {
    protocol: window.location.protocol,
    hostname: window.location.hostname,
    origin: window.location.origin
});

