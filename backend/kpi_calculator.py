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
    
    def calculate_nim(self) -> Dict:
        """
        NIM (Net Interest Margin) - 순이자마진 (은행 특화 지표)
        = (이자수익 - 이자비용) / 평균이자생성자산 × 100
        
        Note: DART 재무제표에서 이자수익과 이자비용 계정을 찾아야 함
        - 이자수익: 이자수익, 대출이자수익, 여신이자수익 등
        - 이자비용: 이자비용, 예금이자비용, 차입이자비용 등
        - 평균이자생성자산: 대출금, 여신 등 (간단히 총자산으로 대체)
        
        Returns:
            NIM 계산 결과
        """
        print(f"🔍 [NIM 계산] 시작 - 사용 가능한 계정: {list(self.accounts.keys())[:10]}...")
        
        # 이자수익 관련 계정 검색
        interest_income_accounts = ['이자수익', '대출이자수익', '여신이자수익', '이자수익금액']
        interest_expense_accounts = ['이자비용', '예금이자비용', '차입이자비용', '이자비용금액']
        
        interest_income = 0
        interest_expense = 0
        
        # 이자수익 찾기
        for account in interest_income_accounts:
            value = self._get_account_value(account, 'current')
            if value > 0:
                interest_income = value
                break
        
        # 부분 일치 검색
        if interest_income == 0:
            for key in self.accounts.keys():
                if any(term in key for term in ['이자수익', '대출이자', '여신이자']):
                    interest_income = self.accounts[key].get('current', 0)
                    if interest_income > 0:
                        print(f"   ✅ 이자수익 발견: {key} = {interest_income}")
                        break
        
        if interest_income == 0:
            print(f"   ⚠️  이자수익을 찾을 수 없음")
        
        # 이자비용 찾기
        for account in interest_expense_accounts:
            value = self._get_account_value(account, 'current')
            if value > 0:
                interest_expense = value
                print(f"   ✅ 이자비용 발견: {account} = {interest_expense}")
                break
        
        # 부분 일치 검색
        if interest_expense == 0:
            for key in self.accounts.keys():
                if any(term in key for term in ['이자비용', '예금이자', '차입이자']):
                    interest_expense = self.accounts[key].get('current', 0)
                    if interest_expense > 0:
                        print(f"   ✅ 이자비용 발견: {key} = {interest_expense}")
                        break
        
        if interest_expense == 0:
            print(f"   ⚠️  이자비용을 찾을 수 없음")
        
        # 평균이자생성자산 (대출금 또는 총자산 사용)
        earning_assets = self._get_account_value('대출금', 'current')
        if earning_assets == 0:
            earning_assets = self._get_account_value('여신', 'current')
        if earning_assets == 0:
            # 총자산으로 대체
            earning_assets = self._get_account_value('자산총계', 'current')
        
        if earning_assets == 0:
            print(f"   ⚠️  이자생성자산 데이터 없음 - 기본값 반환")
            return {
                'value': 0, 
                'status': 'error', 
                'message': '이자생성자산 데이터 없음',
                'unit': '%',
                'description': '순이자마진(NIM)'
            }
        
        # NIM 계산
        net_interest_income = interest_income - interest_expense
        nim_current = (net_interest_income / earning_assets) * 100 if earning_assets != 0 else 0
        
        # 이자수익이나 이자비용이 없어도 계산은 수행 (0으로 계산)
        if interest_income == 0 and interest_expense == 0:
            print(f"   ⚠️  이자수익과 이자비용 모두 없음 - 0으로 계산")
            nim_current = 0
        
        print(f"   📊 NIM 계산: 이자수익={interest_income}, 이자비용={interest_expense}, 순이자수익={net_interest_income}, 이자생성자산={earning_assets}, NIM={nim_current:.2f}%")
        
        # 전기 대비
        interest_income_prev = 0
        interest_expense_prev = 0
        earning_assets_prev = 0
        
        for account in interest_income_accounts:
            value = self._get_account_value(account, 'previous')
            if value > 0:
                interest_income_prev = value
                break
        if interest_income_prev == 0:
            for key in self.accounts.keys():
                if any(term in key for term in ['이자수익', '대출이자', '여신이자']):
                    interest_income_prev = self.accounts[key].get('previous', 0)
                    if interest_income_prev > 0:
                        break
        
        for account in interest_expense_accounts:
            value = self._get_account_value(account, 'previous')
            if value > 0:
                interest_expense_prev = value
                break
        if interest_expense_prev == 0:
            for key in self.accounts.keys():
                if any(term in key for term in ['이자비용', '예금이자', '차입이자']):
                    interest_expense_prev = self.accounts[key].get('previous', 0)
                    if interest_expense_prev > 0:
                        break
        
        earning_assets_prev = self._get_account_value('대출금', 'previous')
        if earning_assets_prev == 0:
            earning_assets_prev = self._get_account_value('여신', 'previous')
        if earning_assets_prev == 0:
            earning_assets_prev = self._get_account_value('자산총계', 'previous')
        
        net_interest_income_prev = interest_income_prev - interest_expense_prev
        nim_previous = (net_interest_income_prev / earning_assets_prev) * 100 if earning_assets_prev != 0 else 0
        
        change = nim_current - nim_previous
        change_rate = ((change / nim_previous) * 100) if nim_previous != 0 else 0
        
        # 평가 기준 (NIM: 2% 이상 우수, 1.5% 이상 양호, 1% 이상 보통)
        if nim_current >= 2.0:
            status = 'excellent'
        elif nim_current >= 1.5:
            status = 'good'
        elif nim_current >= 1.0:
            status = 'fair'
        elif nim_current > 0:
            status = 'poor'
        else:
            # 값이 0이거나 계산 실패한 경우
            status = 'error'
        
        result = {
            'value': round(nim_current, 2),
            'previous_value': round(nim_previous, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'numerator': net_interest_income,
            'denominator': earning_assets,
            'unit': '%',
            'description': '순이자마진(NIM)'
        }
        
        print(f"   ✅ NIM 계산 완료: {result}")
        return result
    
    def calculate_bis_capital_ratio(self) -> Dict:
        """
        BIS 자기자본비율 (은행 특화 지표)
        = (자기자본 / 위험가중자산) × 100
        
        Note: 실제 BIS 비율은 위험가중자산 계산이 복잡하므로,
        간소화하여 (자기자본 / 총자산) × 100으로 계산
        
        Returns:
            BIS 자기자본비율 계산 결과
        """
        total_equity = self._get_account_value('자본총계', 'current')
        total_assets = self._get_account_value('자산총계', 'current')
        
        if total_assets == 0:
            return {'value': 0, 'status': 'error', 'message': '총자산 데이터 없음'}
        
        # 간소화된 BIS 비율 (실제로는 위험가중자산 사용)
        bis_ratio = (total_equity / total_assets) * 100
        
        # 전기 대비
        total_equity_prev = self._get_account_value('자본총계', 'previous')
        total_assets_prev = self._get_account_value('자산총계', 'previous')
        bis_ratio_prev = (total_equity_prev / total_assets_prev) * 100 if total_assets_prev != 0 else 0
        
        change = bis_ratio - bis_ratio_prev
        change_rate = ((change / bis_ratio_prev) * 100) if bis_ratio_prev != 0 else 0
        
        # 평가 기준 (BIS 기준: 8% 이상 권장, 10.5% 이상 바젤3)
        if bis_ratio >= 10.5:
            status = 'excellent'
        elif bis_ratio >= 8.0:
            status = 'good'
        elif bis_ratio >= 6.0:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'value': round(bis_ratio, 2),
            'previous_value': round(bis_ratio_prev, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'unit': '%',
            'description': 'BIS 자기자본비율'
        }
    
    def calculate_soundness_ratio(self) -> Dict:
        """
        건전성 비율 (은행 특화 지표)
        = (자기자본 / 총자산) × 100
        
        Returns:
            건전성 비율 계산 결과
        """
        total_equity = self._get_account_value('자본총계', 'current')
        total_assets = self._get_account_value('자산총계', 'current')
        
        if total_assets == 0:
            return {'value': 0, 'status': 'error', 'message': '총자산 데이터 없음'}
        
        soundness_ratio = (total_equity / total_assets) * 100
        
        # 전기 대비
        total_equity_prev = self._get_account_value('자본총계', 'previous')
        total_assets_prev = self._get_account_value('자산총계', 'previous')
        soundness_ratio_prev = (total_equity_prev / total_assets_prev) * 100 if total_assets_prev != 0 else 0
        
        change = soundness_ratio - soundness_ratio_prev
        change_rate = ((change / soundness_ratio_prev) * 100) if soundness_ratio_prev != 0 else 0
        
        # 평가 기준
        if soundness_ratio >= 10:
            status = 'excellent'
        elif soundness_ratio >= 7:
            status = 'good'
        elif soundness_ratio >= 5:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'value': round(soundness_ratio, 2),
            'previous_value': round(soundness_ratio_prev, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'unit': '%',
            'description': '건전성 비율'
        }
    
    def calculate_loan_to_deposit_ratio(self) -> Dict:
        """
        예대율 (은행 특화 지표)
        = (대출금액 / 예금금액) × 100
        
        Note: DART 재무제표에서 대출과 예금 계정을 찾아야 함
        - 대출: 대출금, 여신, 대출 및 매입어음 등
        - 예금: 예금, 수신, 예금 및 기타수신 등
        
        Returns:
            예대율 계산 결과
        """
        # 대출 관련 계정 검색
        loan_accounts = ['대출금', '여신', '대출 및 매입어음', '대출채권', '여신채권']
        deposit_accounts = ['예금', '수신', '예금 및 기타수신', '예금채무', '수신채무']
        
        loans = 0
        deposits = 0
        
        # 대출금 찾기
        for account in loan_accounts:
            value = self._get_account_value(account, 'current')
            if value > 0:
                loans = value
                break
        
        # 부분 일치 검색
        if loans == 0:
            for key in self.accounts.keys():
                if any(term in key for term in ['대출', '여신']):
                    loans = self.accounts[key].get('current', 0)
                    if loans > 0:
                        break
        
        # 예금 찾기
        for account in deposit_accounts:
            value = self._get_account_value(account, 'current')
            if value > 0:
                deposits = value
                break
        
        # 부분 일치 검색
        if deposits == 0:
            for key in self.accounts.keys():
                if any(term in key for term in ['예금', '수신']):
                    deposits = self.accounts[key].get('current', 0)
                    if deposits > 0:
                        break
        
        if deposits == 0:
            return {'value': 0, 'status': 'error', 'message': '예금 데이터 없음'}
        
        ldr_ratio = (loans / deposits) * 100
        
        # 전기 대비
        loans_prev = 0
        deposits_prev = 0
        for account in loan_accounts:
            value = self._get_account_value(account, 'previous')
            if value > 0:
                loans_prev = value
                break
        if loans_prev == 0:
            for key in self.accounts.keys():
                if any(term in key for term in ['대출', '여신']):
                    loans_prev = self.accounts[key].get('previous', 0)
                    if loans_prev > 0:
                        break
        
        for account in deposit_accounts:
            value = self._get_account_value(account, 'previous')
            if value > 0:
                deposits_prev = value
                break
        if deposits_prev == 0:
            for key in self.accounts.keys():
                if any(term in key for term in ['예금', '수신']):
                    deposits_prev = self.accounts[key].get('previous', 0)
                    if deposits_prev > 0:
                        break
        
        ldr_ratio_prev = (loans_prev / deposits_prev) * 100 if deposits_prev != 0 else 0
        change = ldr_ratio - ldr_ratio_prev
        change_rate = ((change / ldr_ratio_prev) * 100) if ldr_ratio_prev != 0 else 0
        
        # 평가 기준 (예대율: 100% 이하 권장, 90% 이하 우수)
        if ldr_ratio <= 90:
            status = 'excellent'
        elif ldr_ratio <= 100:
            status = 'good'
        elif ldr_ratio <= 110:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'value': round(ldr_ratio, 2),
            'previous_value': round(ldr_ratio_prev, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'numerator': loans,
            'denominator': deposits,
            'unit': '%',
            'description': '예대율'
        }
    
    def calculate_npl_ratio(self) -> Dict:
        """
        고정이하여신(NPL) 비율 (은행 특화 지표)
        = (고정이하여신 / 총여신) × 100
        
        Note: DART 재무제표에서 고정이하여신 계정을 찾아야 함
        - 고정이하여신: 부실채권, 고정이하여신, 대손충당금 등
        
        Returns:
            NPL 비율 계산 결과
        """
        # 고정이하여신 관련 계정 검색
        npl_accounts = ['고정이하여신', '부실채권', '대손채권', '연체채권']
        total_loan_accounts = ['대출금', '여신', '대출 및 매입어음', '총여신']
        
        npl_amount = 0
        total_loans = 0
        
        # 고정이하여신 찾기
        for account in npl_accounts:
            value = self._get_account_value(account, 'current')
            if value > 0:
                npl_amount = value
                break
        
        # 부분 일치 검색
        if npl_amount == 0:
            for key in self.accounts.keys():
                if any(term in key for term in ['고정이하', '부실', '대손', '연체']):
                    npl_amount = self.accounts[key].get('current', 0)
                    if npl_amount > 0:
                        break
        
        # 총여신 찾기
        for account in total_loan_accounts:
            value = self._get_account_value(account, 'current')
            if value > 0:
                total_loans = value
                break
        
        # 부분 일치 검색
        if total_loans == 0:
            for key in self.accounts.keys():
                if any(term in key for term in ['대출', '여신']):
                    total_loans = self.accounts[key].get('current', 0)
                    if total_loans > 0:
                        break
        
        if total_loans == 0:
            return {'value': 0, 'status': 'error', 'message': '총여신 데이터 없음'}
        
        npl_ratio = (npl_amount / total_loans) * 100
        
        # 전기 대비
        npl_amount_prev = 0
        total_loans_prev = 0
        for account in npl_accounts:
            value = self._get_account_value(account, 'previous')
            if value > 0:
                npl_amount_prev = value
                break
        if npl_amount_prev == 0:
            for key in self.accounts.keys():
                if any(term in key for term in ['고정이하', '부실', '대손', '연체']):
                    npl_amount_prev = self.accounts[key].get('previous', 0)
                    if npl_amount_prev > 0:
                        break
        
        for account in total_loan_accounts:
            value = self._get_account_value(account, 'previous')
            if value > 0:
                total_loans_prev = value
                break
        if total_loans_prev == 0:
            for key in self.accounts.keys():
                if any(term in key for term in ['대출', '여신']):
                    total_loans_prev = self.accounts[key].get('previous', 0)
                    if total_loans_prev > 0:
                        break
        
        npl_ratio_prev = (npl_amount_prev / total_loans_prev) * 100 if total_loans_prev != 0 else 0
        change = npl_ratio - npl_ratio_prev
        change_rate = ((change / npl_ratio_prev) * 100) if npl_ratio_prev != 0 else 0
        
        # 평가 기준 (NPL 비율: 1% 이하 우수, 2% 이하 양호, 3% 이상 주의)
        if npl_ratio <= 1.0:
            status = 'excellent'
        elif npl_ratio <= 2.0:
            status = 'good'
        elif npl_ratio <= 3.0:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'value': round(npl_ratio, 2),
            'previous_value': round(npl_ratio_prev, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'numerator': npl_amount,
            'denominator': total_loans,
            'unit': '%',
            'description': '고정이하여신(NPL) 비율'
        }
    
    def calculate_all_kpis(self, industry: str = 'default') -> Dict:
        """
        모든 KPI 계산
        
        Args:
            industry: 업종 (은행업일 경우 특화 지표 사용)
        
        Returns:
            전체 KPI 결과
        """
        print(f"🔧 [KPICalculator] calculate_all_kpis 호출: industry={industry}")
        
        base_kpis = {
            'roa': self.calculate_roa(),
            'roe': self.calculate_roe(),
            'operating_margin': self.calculate_operating_margin(),
            'net_profit_margin': self.calculate_net_profit_margin()
        }
        
        # 은행업인 경우 특화 지표 사용 (ROA, ROE, NIM, 영업이익률)
        if industry == '은행업':
            print(f"🏦 [KPICalculator] 은행업 감지 - NIM 계산 시작")
            nim_result = self.calculate_nim()
            print(f"   - NIM 계산 결과: {nim_result}")
            base_kpis.update({
                'nim': nim_result
            })
            print(f"✅ [KPICalculator] 은행업 KPI 완료: {list(base_kpis.keys())}")
        else:
            # 일반 업종은 기존 지표 사용
            print(f"🏭 [KPICalculator] 일반 업종 - 부채비율, 유동비율 계산")
            base_kpis.update({
                'debt_ratio': self.calculate_debt_ratio(),
                'current_ratio': self.calculate_current_ratio()
            })
            print(f"✅ [KPICalculator] 일반 업종 KPI 완료: {list(base_kpis.keys())}")
        
        return base_kpis
    
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

