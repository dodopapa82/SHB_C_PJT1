"""
취약점 분석 엔진
Rule Engine 기반으로 재무 취약점을 탐지하고 분석합니다.

[재무제표 기준]
- 연결 재무상태표 (Consolidated Balance Sheet)
- 연결 포괄손익계산서 (Consolidated Comprehensive Income Statement)
- 연결 현금흐름표 (Consolidated Cash Flow Statement)
- DART Open API 기준 (fs_div=CFS)
"""

from typing import Dict, List
from kpi_calculator import KPICalculator


class WeaknessAnalyzer:
    """재무 취약점 분석 클래스 (연결재무제표 기준)"""
    
    # 업종별 평균 기준 (연결 재무제표 & 포괄손익계산서 기준)
    # 출처: 한국거래소 상장사 평균, DART 연결재무제표(CFS) 기준
    # 업데이트: 2024년 기준, 최근 3개년 평균값
    INDUSTRY_BENCHMARKS = {
        '반도체 제조업': {
            'roa': 5.0,              # 총자산순이익률 (연결 기준, 2023년 반도체 불황 반영)
            'roe': 8.5,              # 자기자본순이익률 (연결 기준)
            'debt_ratio': 45.0,      # 부채비율 (연결 기준, 낮아짐)
            'current_ratio': 180.0,  # 유동비율
            'operating_margin': 8.0, # 영업이익률 (포괄손익계산서 기준, 불황 반영)
            'net_profit_margin': 6.0 # 순이익률
        },
        '전자제품 제조업': {
            'roa': 4.5,
            'roe': 8.0,
            'debt_ratio': 50.0,
            'current_ratio': 150.0,
            'operating_margin': 7.0,
            'net_profit_margin': 5.5
        },
        '자동차 제조업': {
            'roa': 2.5,              # 자본집약적 산업
            'roe': 6.5,
            'debt_ratio': 120.0,     # 높은 부채비율
            'current_ratio': 100.0,  # 낮은 유동비율
            'operating_margin': 4.5,
            'net_profit_margin': 3.5
        },
        '인터넷 서비스업': {
            'roa': 8.0,              # 고수익 산업
            'roe': 15.0,
            'debt_ratio': 30.0,      # 낮은 부채비율
            'current_ratio': 250.0,  # 높은 유동성
            'operating_margin': 18.0,
            'net_profit_margin': 15.0
        },
        '게임 소프트웨어 개발 및 공급업': {
            'roa': 9.0,
            'roe': 16.0,
            'debt_ratio': 25.0,
            'current_ratio': 300.0,
            'operating_margin': 20.0,
            'net_profit_margin': 16.0
        },
        '은행업': {
            'roa': 0.6,              # 금융업 특성
            'roe': 8.0,
            'debt_ratio': 1000.0,    # 금융업은 부채비율이 매우 높음
            'current_ratio': 100.0,
            'operating_margin': 35.0,
            'net_profit_margin': 25.0
        },
        '증권업': {
            'roa': 1.2,
            'roe': 7.5,
            'debt_ratio': 500.0,
            'current_ratio': 150.0,
            'operating_margin': 30.0,
            'net_profit_margin': 22.0
        },
        '종합 건설업': {
            'roa': 2.0,
            'roe': 7.0,
            'debt_ratio': 180.0,
            'current_ratio': 110.0,
            'operating_margin': 5.0,
            'net_profit_margin': 4.0
        },
        '의약품 제조업': {
            'roa': 4.0,
            'roe': 9.0,
            'debt_ratio': 60.0,
            'current_ratio': 200.0,
            'operating_margin': 12.0,
            'net_profit_margin': 10.0
        },
        '화학물질 및 화학제품 제조업': {
            'roa': 3.5,
            'roe': 7.5,
            'debt_ratio': 90.0,
            'current_ratio': 140.0,
            'operating_margin': 8.0,
            'net_profit_margin': 6.5
        },
        '전기 통신업': {
            'roa': 3.0,
            'roe': 8.5,
            'debt_ratio': 110.0,
            'current_ratio': 90.0,
            'operating_margin': 12.0,
            'net_profit_margin': 9.0
        },
        '항공 운송업': {
            'roa': 1.5,
            'roe': 5.0,
            'debt_ratio': 250.0,
            'current_ratio': 80.0,
            'operating_margin': 3.0,
            'net_profit_margin': 2.0
        },
        '종합 소매업': {
            'roa': 2.5,
            'roe': 7.0,
            'debt_ratio': 130.0,
            'current_ratio': 100.0,
            'operating_margin': 4.5,
            'net_profit_margin': 3.0
        },
        '식료품 제조업': {
            'roa': 3.0,
            'roe': 8.0,
            'debt_ratio': 100.0,
            'current_ratio': 130.0,
            'operating_margin': 7.0,
            'net_profit_margin': 5.5
        },
        '제조업': {
            'roa': 3.5,
            'roe': 8.0,
            'debt_ratio': 100.0,
            'current_ratio': 130.0,
            'operating_margin': 8.0,
            'net_profit_margin': 6.0
        },
        'default': {
            'roa': 4.0,
            'roe': 9.0,
            'debt_ratio': 100.0,
            'current_ratio': 130.0,
            'operating_margin': 8.0,
            'net_profit_margin': 6.0
        }
    }
    
    def __init__(self, kpi_data: Dict, industry: str = 'default', historical_data: List[Dict] = None):
        """
        Args:
            kpi_data: KPI 계산 결과
            industry: 업종명
            historical_data: 과거 데이터 (시계열 분석용)
        """
        self.kpis = kpi_data
        self.industry = industry
        self.historical_data = historical_data or []
        self.benchmark = self.INDUSTRY_BENCHMARKS.get(industry, self.INDUSTRY_BENCHMARKS['default'])
        self.weaknesses = []
    
    def analyze_all(self) -> Dict:
        """
        전체 취약점 분석 실행
        
        Returns:
            취약점 분석 결과
        """
        self.weaknesses = []
        
        # Rule 기반 취약점 검사
        self._check_high_debt_ratio()
        self._check_low_profitability()
        self._check_liquidity_risk()
        self._check_declining_trend()
        self._check_negative_cashflow()
        
        # 종합 평가
        risk_level = self._calculate_risk_level()
        
        return {
            'weaknesses': self.weaknesses,
            'risk_level': risk_level,
            'total_issues': len(self.weaknesses),
            'critical_issues': len([w for w in self.weaknesses if w['severity'] == 'critical']),
            'warning_issues': len([w for w in self.weaknesses if w['severity'] == 'warning']),
            'info_issues': len([w for w in self.weaknesses if w['severity'] == 'info']),
            'benchmark': self.benchmark
        }
    
    def _check_high_debt_ratio(self):
        """Rule R01: 높은 부채비율 검사"""
        debt_ratio = self.kpis.get('debt_ratio', {})
        value = debt_ratio.get('value', 0)
        benchmark = self.benchmark['debt_ratio']
        
        if value > benchmark * 1.2:  # 업종평균 + 20%
            self.weaknesses.append({
                'rule_id': 'R01',
                'title': '높은 부채비율 위험',
                'severity': 'critical',
                'category': '재무구조',
                'description': f'부채비율이 {value:.2f}%로 업종평균({benchmark:.2f}%)보다 20% 이상 높습니다.',
                'current_value': value,
                'benchmark_value': benchmark,
                'recommendation': '부채 감축 계획을 수립하고, 자본 확충을 고려해야 합니다.',
                'impact': '높은 부채비율은 재무 건전성을 저해하고 이자비용 부담을 증가시킵니다.'
            })
        elif value > benchmark:
            self.weaknesses.append({
                'rule_id': 'R01',
                'title': '부채비율 주의 필요',
                'severity': 'warning',
                'category': '재무구조',
                'description': f'부채비율이 {value:.2f}%로 업종평균({benchmark:.2f}%)보다 높습니다.',
                'current_value': value,
                'benchmark_value': benchmark,
                'recommendation': '부채비율 상승 추이를 모니터링하고 관리가 필요합니다.',
                'impact': '부채비율 증가는 재무 리스크를 높일 수 있습니다.'
            })
    
    def _check_low_profitability(self):
        """Rule R04: 낮은 수익성 검사"""
        roa = self.kpis.get('roa', {})
        roe = self.kpis.get('roe', {})
        operating_margin = self.kpis.get('operating_margin', {})
        
        roa_value = roa.get('value', 0)
        roe_value = roe.get('value', 0)
        op_margin_value = operating_margin.get('value', 0)
        
        # ROA 검사
        if roa_value < self.benchmark['roa'] * 0.5:  # 업종평균의 50% 미만
            self.weaknesses.append({
                'rule_id': 'R04-1',
                'title': '낮은 총자산이익률 (ROA)',
                'severity': 'critical',
                'category': '수익성',
                'description': f'ROA가 {roa_value:.2f}%로 업종평균({self.benchmark["roa"]:.2f}%)의 절반에도 미치지 못합니다.',
                'current_value': roa_value,
                'benchmark_value': self.benchmark['roa'],
                'recommendation': '자산 활용도를 높이고 수익성 개선 방안을 마련해야 합니다.',
                'impact': '낮은 ROA는 자산 운용의 비효율성을 나타냅니다.'
            })
        
        # ROE 검사
        if roe_value < self.benchmark['roe'] * 0.5:
            self.weaknesses.append({
                'rule_id': 'R04-2',
                'title': '낮은 자기자본이익률 (ROE)',
                'severity': 'critical',
                'category': '수익성',
                'description': f'ROE가 {roe_value:.2f}%로 업종평균({self.benchmark["roe"]:.2f}%)의 절반에도 미치지 못합니다.',
                'current_value': roe_value,
                'benchmark_value': self.benchmark['roe'],
                'recommendation': '자본 효율성을 높이고 순이익 증대 전략이 필요합니다.',
                'impact': '낮은 ROE는 주주 가치 창출 능력이 부족함을 의미합니다.'
            })
        
        # 영업이익률 검사
        if op_margin_value < self.benchmark['operating_margin'] * 0.5:
            self.weaknesses.append({
                'rule_id': 'R04-3',
                'title': '낮은 영업이익률',
                'severity': 'warning',
                'category': '수익성',
                'description': f'영업이익률이 {op_margin_value:.2f}%로 업종평균({self.benchmark["operating_margin"]:.2f}%)보다 매우 낮습니다.',
                'current_value': op_margin_value,
                'benchmark_value': self.benchmark['operating_margin'],
                'recommendation': '원가 절감 및 가격 정책 재검토가 필요합니다.',
                'impact': '낮은 영업이익률은 핵심 사업의 경쟁력 약화를 시사합니다.'
            })
    
    def _check_liquidity_risk(self):
        """유동성 위험 검사"""
        current_ratio = self.kpis.get('current_ratio', {})
        value = current_ratio.get('value', 0)
        
        if value < 100:  # 유동비율 100% 미만
            self.weaknesses.append({
                'rule_id': 'R05',
                'title': '유동성 부족 위험',
                'severity': 'critical',
                'category': '유동성',
                'description': f'유동비율이 {value:.2f}%로 100% 미만입니다. 단기 지급능력에 문제가 있을 수 있습니다.',
                'current_value': value,
                'benchmark_value': 100.0,
                'recommendation': '단기 자금 조달 계획을 마련하고 유동자산을 확보해야 합니다.',
                'impact': '단기 채무 상환 능력이 부족하여 유동성 위기 가능성이 있습니다.'
            })
        elif value < self.benchmark['current_ratio'] * 0.8:
            self.weaknesses.append({
                'rule_id': 'R05',
                'title': '유동성 주의 필요',
                'severity': 'warning',
                'category': '유동성',
                'description': f'유동비율이 {value:.2f}%로 업종평균({self.benchmark["current_ratio"]:.2f}%)보다 낮습니다.',
                'current_value': value,
                'benchmark_value': self.benchmark['current_ratio'],
                'recommendation': '유동성 관리를 강화하고 단기 자산/부채 구조를 개선해야 합니다.',
                'impact': '유동성 악화는 자금 운용의 어려움으로 이어질 수 있습니다.'
            })
    
    def _check_declining_trend(self):
        """Rule R03: ROE 하락 추세 검사"""
        if len(self.historical_data) >= 3:
            roe_trend = []
            for data in self.historical_data[-3:]:  # 최근 3년
                roe = data.get('roe', {}).get('value', 0)
                roe_trend.append(roe)
            
            # 3년 연속 감소 체크
            if len(roe_trend) == 3 and roe_trend[0] > roe_trend[1] > roe_trend[2]:
                self.weaknesses.append({
                    'rule_id': 'R03',
                    'title': 'ROE 지속 하락 추세',
                    'severity': 'critical',
                    'category': '트렌드',
                    'description': f'ROE가 3년 연속 감소하고 있습니다 ({roe_trend[0]:.2f}% → {roe_trend[1]:.2f}% → {roe_trend[2]:.2f}%).',
                    'current_value': roe_trend[2],
                    'benchmark_value': roe_trend[0],
                    'recommendation': '수익성 개선을 위한 구조조정 및 사업 전략 재검토가 시급합니다.',
                    'impact': '지속적인 수익성 악화는 기업 경쟁력 저하를 의미합니다.'
                })
    
    def _check_negative_cashflow(self):
        """Rule R02: 현금흐름 위험 검사"""
        # 샘플 데이터에서는 현금흐름 정보가 제한적이므로 
        # 실제 데이터가 있을 때 구현
        pass
    
    def _calculate_risk_level(self) -> Dict:
        """
        종합 위험도 계산
        
        Returns:
            위험도 평가 결과
        """
        critical_count = len([w for w in self.weaknesses if w['severity'] == 'critical'])
        warning_count = len([w for w in self.weaknesses if w['severity'] == 'warning'])
        
        # 위험도 점수 계산 (critical: 10점, warning: 5점, info: 1점)
        risk_score = critical_count * 10 + warning_count * 5
        
        if risk_score >= 30:
            level = 'high'
            label = '높음'
            color = '#FF4B4B'
            message = '심각한 재무 취약점이 발견되었습니다. 즉각적인 대응이 필요합니다.'
        elif risk_score >= 15:
            level = 'medium'
            label = '보통'
            color = '#FFA500'
            message = '일부 재무 취약점이 발견되었습니다. 개선 계획 수립이 권장됩니다.'
        elif risk_score > 0:
            level = 'low'
            label = '낮음'
            color = '#FFD700'
            message = '경미한 주의사항이 있습니다. 지속적인 모니터링이 필요합니다.'
        else:
            level = 'safe'
            label = '안전'
            color = '#00C851'
            message = '재무 상태가 양호합니다.'
        
        return {
            'level': level,
            'label': label,
            'score': risk_score,
            'color': color,
            'message': message
        }
    
    def get_improvement_priorities(self) -> List[Dict]:
        """
        개선 우선순위 제안
        
        Returns:
            우선순위별 개선 과제
        """
        # critical 우선, 그 다음 warning
        sorted_weaknesses = sorted(
            self.weaknesses, 
            key=lambda x: (0 if x['severity'] == 'critical' else 1 if x['severity'] == 'warning' else 2)
        )
        
        priorities = []
        for idx, weakness in enumerate(sorted_weaknesses[:5], 1):  # 상위 5개
            priorities.append({
                'rank': idx,
                'title': weakness['title'],
                'category': weakness['category'],
                'severity': weakness['severity'],
                'recommendation': weakness['recommendation']
            })
        
        return priorities

