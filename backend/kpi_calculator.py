"""
KPI 계산 엔진
재무제표 데이터를 기반으로 핵심 재무지표(KPI)를 계산합니다.
"""

from typing import Dict, List, Optional
import json


class KPICalculator:
    """재무 KPI 계산 클래스"""
    
    def __init__(self, financial_data: Dict):
        """
        Args:
            financial_data: DART API에서 가져온 재무제표 데이터
        """
        self.data = financial_data
        self.accounts = {}
        
        # 계정과목 파싱
        if 'list' in financial_data:
            for item in financial_data['list']:
                account_name = item.get('account_nm', '')
                current_amount = self._parse_amount(item.get('thstrm_amount', '0'))
                previous_amount = self._parse_amount(item.get('frmtrm_amount', '0'))
                
                self.accounts[account_name] = {
                    'current': current_amount,
                    'previous': previous_amount
                }
    
    def _parse_amount(self, amount_str: str) -> float:
        """
        금액 문자열을 숫자로 변환
        
        Args:
            amount_str: 금액 문자열
            
        Returns:
            변환된 숫자 (단위: 원)
        """
        try:
            # 쉼표 제거 후 숫자 변환
            return float(str(amount_str).replace(',', '').replace('-', '-'))
        except (ValueError, AttributeError):
            return 0.0
    
    def _get_account_value(self, account_name: str, period: str = 'current') -> float:
        """
        계정과목 값 조회 (유사 계정과목도 검색)
        
        Args:
            account_name: 계정과목명
            period: 'current' (당기) 또는 'previous' (전기)
            
        Returns:
            계정과목 금액
        """
        # 정확한 매칭
        if account_name in self.accounts:
            return self.accounts[account_name].get(period, 0.0)
        
        # 유사 계정과목 검색 (DART 실제 데이터 대응)
        similar_names = {
            '매출액': ['매출', '수익(매출액)', '영업수익', '수익'],
            '영업이익': ['영업이익(손실)', '영업손익', '영업이익'],
            '당기순이익': ['당기순이익(손실)', '계속영업당기순이익', '당기순손익', '지배기업의 소유주에게 귀속되는 당기순이익'],
            '총포괄이익': ['총포괄손익', '당기총포괄이익', '지배기업의 소유주에게 귀속되는 총포괄이익'],
            '영업활동현금흐름': ['영업활동으로인한현금흐름', '영업활동으로 인한 현금흐름'],
            '투자활동현금흐름': ['투자활동으로인한현금흐름', '투자활동으로 인한 현금흐름'],
            '재무활동현금흐름': ['재무활동으로인한현금흐름', '재무활동으로 인한 현금흐름']
        }
        
        if account_name in similar_names:
            for similar_name in similar_names[account_name]:
                if similar_name in self.accounts:
                    return self.accounts[similar_name].get(period, 0.0)
            
            # 부분 일치 검색
            for key in self.accounts.keys():
                if any(name in key for name in similar_names[account_name]):
                    return self.accounts[key].get(period, 0.0)
        
        return 0.0
    
    def calculate_roa(self) -> Dict:
        """
        ROA (Return on Assets) - 총자산순이익률
        = (당기순이익 / 총자산) × 100
        
        Returns:
            ROA 계산 결과
        """
        # 당기
        net_income_current = self._get_account_value('당기순이익', 'current')
        total_assets_current = self._get_account_value('자산총계', 'current')
        
        # 전기
        net_income_previous = self._get_account_value('당기순이익', 'previous')
        total_assets_previous = self._get_account_value('자산총계', 'previous')
        
        if total_assets_current == 0:
            return {'value': 0, 'status': 'error', 'message': '총자산 데이터 없음'}
        
        roa_current = (net_income_current / total_assets_current) * 100
        roa_previous = (net_income_previous / total_assets_previous) * 100 if total_assets_previous != 0 else 0
        
        # 전년 대비 변화
        change = roa_current - roa_previous
        change_rate = ((change / roa_previous) * 100) if roa_previous != 0 else 0
        
        # 평가 기준
        if roa_current >= 10:
            status = 'excellent'
        elif roa_current >= 5:
            status = 'good'
        elif roa_current >= 0:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'value': round(roa_current, 2),
            'previous_value': round(roa_previous, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'numerator': net_income_current,
            'denominator': total_assets_current,
            'unit': '%',
            'description': 'ROA (총자산순이익률)'
        }
    
    def calculate_roe(self) -> Dict:
        """
        ROE (Return on Equity) - 자기자본순이익률
        = (당기순이익 / 자본총계) × 100
        
        Returns:
            ROE 계산 결과
        """
        # 당기
        net_income_current = self._get_account_value('당기순이익', 'current')
        total_equity_current = self._get_account_value('자본총계', 'current')
        
        # 전기
        net_income_previous = self._get_account_value('당기순이익', 'previous')
        total_equity_previous = self._get_account_value('자본총계', 'previous')
        
        if total_equity_current == 0:
            return {'value': 0, 'status': 'error', 'message': '자본총계 데이터 없음'}
        
        roe_current = (net_income_current / total_equity_current) * 100
        roe_previous = (net_income_previous / total_equity_previous) * 100 if total_equity_previous != 0 else 0
        
        # 전년 대비 변화
        change = roe_current - roe_previous
        change_rate = ((change / roe_previous) * 100) if roe_previous != 0 else 0
        
        # 평가 기준
        if roe_current >= 15:
            status = 'excellent'
        elif roe_current >= 10:
            status = 'good'
        elif roe_current >= 5:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'value': round(roe_current, 2),
            'previous_value': round(roe_previous, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'numerator': net_income_current,
            'denominator': total_equity_current,
            'unit': '%',
            'description': 'ROE (자기자본순이익률)'
        }
    
    def calculate_debt_ratio(self) -> Dict:
        """
        부채비율
        = (부채총계 / 자본총계) × 100
        
        Returns:
            부채비율 계산 결과
        """
        # 당기
        total_liabilities_current = self._get_account_value('부채총계', 'current')
        total_equity_current = self._get_account_value('자본총계', 'current')
        
        # 전기
        total_liabilities_previous = self._get_account_value('부채총계', 'previous')
        total_equity_previous = self._get_account_value('자본총계', 'previous')
        
        if total_equity_current == 0:
            return {'value': 0, 'status': 'error', 'message': '자본총계 데이터 없음'}
        
        debt_ratio_current = (total_liabilities_current / total_equity_current) * 100
        debt_ratio_previous = (total_liabilities_previous / total_equity_previous) * 100 if total_equity_previous != 0 else 0
        
        # 전년 대비 변화
        change = debt_ratio_current - debt_ratio_previous
        change_rate = ((change / debt_ratio_previous) * 100) if debt_ratio_previous != 0 else 0
        
        # 평가 기준 (낮을수록 좋음)
        if debt_ratio_current <= 100:
            status = 'excellent'
        elif debt_ratio_current <= 200:
            status = 'good'
        elif debt_ratio_current <= 300:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'value': round(debt_ratio_current, 2),
            'previous_value': round(debt_ratio_previous, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'numerator': total_liabilities_current,
            'denominator': total_equity_current,
            'unit': '%',
            'description': '부채비율'
        }
    
    def calculate_current_ratio(self) -> Dict:
        """
        유동비율
        = (유동자산 / 유동부채) × 100
        
        Returns:
            유동비율 계산 결과
        """
        # 당기
        current_assets_current = self._get_account_value('유동자산', 'current')
        current_liabilities_current = self._get_account_value('유동부채', 'current')
        
        # 전기
        current_assets_previous = self._get_account_value('유동자산', 'previous')
        current_liabilities_previous = self._get_account_value('유동부채', 'previous')
        
        if current_liabilities_current == 0:
            return {'value': 0, 'status': 'error', 'message': '유동부채 데이터 없음'}
        
        current_ratio_current = (current_assets_current / current_liabilities_current) * 100
        current_ratio_previous = (current_assets_previous / current_liabilities_previous) * 100 if current_liabilities_previous != 0 else 0
        
        # 전년 대비 변화
        change = current_ratio_current - current_ratio_previous
        change_rate = ((change / current_ratio_previous) * 100) if current_ratio_previous != 0 else 0
        
        # 평가 기준
        if current_ratio_current >= 200:
            status = 'excellent'
        elif current_ratio_current >= 100:
            status = 'good'
        elif current_ratio_current >= 80:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'value': round(current_ratio_current, 2),
            'previous_value': round(current_ratio_previous, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'numerator': current_assets_current,
            'denominator': current_liabilities_current,
            'unit': '%',
            'description': '유동비율'
        }
    
    def calculate_operating_margin(self) -> Dict:
        """
        영업이익률
        = (영업이익 / 매출액) × 100
        
        Returns:
            영업이익률 계산 결과
        """
        # 당기
        operating_income_current = self._get_account_value('영업이익', 'current')
        revenue_current = self._get_account_value('매출액', 'current')
        
        # 전기
        operating_income_previous = self._get_account_value('영업이익', 'previous')
        revenue_previous = self._get_account_value('매출액', 'previous')
        
        if revenue_current == 0:
            return {'value': 0, 'status': 'error', 'message': '매출액 데이터 없음'}
        
        operating_margin_current = (operating_income_current / revenue_current) * 100
        operating_margin_previous = (operating_income_previous / revenue_previous) * 100 if revenue_previous != 0 else 0
        
        # 전년 대비 변화
        change = operating_margin_current - operating_margin_previous
        change_rate = ((change / operating_margin_previous) * 100) if operating_margin_previous != 0 else 0
        
        # 평가 기준
        if operating_margin_current >= 20:
            status = 'excellent'
        elif operating_margin_current >= 10:
            status = 'good'
        elif operating_margin_current >= 5:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'value': round(operating_margin_current, 2),
            'previous_value': round(operating_margin_previous, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'numerator': operating_income_current,
            'denominator': revenue_current,
            'unit': '%',
            'description': '영업이익률'
        }
    
    def calculate_net_profit_margin(self) -> Dict:
        """
        순이익률
        = (당기순이익 / 매출액) × 100
        
        Returns:
            순이익률 계산 결과
        """
        # 당기
        net_income_current = self._get_account_value('당기순이익', 'current')
        revenue_current = self._get_account_value('매출액', 'current')
        
        # 전기
        net_income_previous = self._get_account_value('당기순이익', 'previous')
        revenue_previous = self._get_account_value('매출액', 'previous')
        
        if revenue_current == 0:
            return {'value': 0, 'status': 'error', 'message': '매출액 데이터 없음'}
        
        net_profit_margin_current = (net_income_current / revenue_current) * 100
        net_profit_margin_previous = (net_income_previous / revenue_previous) * 100 if revenue_previous != 0 else 0
        
        # 전년 대비 변화
        change = net_profit_margin_current - net_profit_margin_previous
        change_rate = ((change / net_profit_margin_previous) * 100) if net_profit_margin_previous != 0 else 0
        
        # 평가 기준
        if net_profit_margin_current >= 15:
            status = 'excellent'
        elif net_profit_margin_current >= 8:
            status = 'good'
        elif net_profit_margin_current >= 3:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'value': round(net_profit_margin_current, 2),
            'previous_value': round(net_profit_margin_previous, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'numerator': net_income_current,
            'denominator': revenue_current,
            'unit': '%',
            'description': '순이익률'
        }
    
    def calculate_all_kpis(self) -> Dict:
        """
        모든 KPI 계산
        
        Returns:
            전체 KPI 결과
        """
        return {
            'roa': self.calculate_roa(),
            'roe': self.calculate_roe(),
            'debt_ratio': self.calculate_debt_ratio(),
            'current_ratio': self.calculate_current_ratio(),
            'operating_margin': self.calculate_operating_margin(),
            'net_profit_margin': self.calculate_net_profit_margin()
        }
    
    def get_trend_analysis(self) -> Dict:
        """
        전년 대비 증감 분석 (포괄손익계산서 기준)
        
        Returns:
            트렌드 분석 결과
        """
        trends = {}
        
        # 주요 계정과목 (포괄손익계산서 포함)
        key_accounts = [
            '매출액', '영업이익', '당기순이익', 
            '자산총계', '부채총계', '자본총계',
            '총포괄이익'  # 포괄손익계산서 추가
        ]
        
        for account_name in key_accounts:
            current = self._get_account_value(account_name, 'current')
            previous = self._get_account_value(account_name, 'previous')
            
            # 데이터가 없으면 건너뛰기
            if current == 0 and previous == 0:
                continue
            
            if previous != 0:
                change_rate = ((current - previous) / previous) * 100
                trends[account_name] = {
                    'current': current,
                    'previous': previous,
                    'change': current - previous,
                    'change_rate': round(change_rate, 2),
                    'direction': 'up' if change_rate > 0 else 'down' if change_rate < 0 else 'flat'
                }
            else:
                trends[account_name] = {
                    'current': current,
                    'previous': previous,
                    'change': current,
                    'change_rate': 0,
                    'direction': 'flat'
                }
        
        return trends

