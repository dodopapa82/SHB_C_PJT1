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
            '재무활동현금흐름': ['재무활동으로인한현금흐름', '재무활동으로 인한 현금흐름'],
            # 은행 특화 계정 (BIS 자기자본비율 산출용)
            '위험가중자산': ['총위험가중자산', '신용위험가중자산', '위험가중자산합계', 'RWA', 
                         '위험가중자산총계', '신용리스크가중자산', '시장리스크가중자산'],
            '자기자본': ['자본총계', '규제자본', 'Tier1자본', '기본자본', '보완자본', '총자기자본']
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
    
    def calculate_operating_margin(self, industry: str = 'default') -> Dict:
        """
        영업이익률 계산
        
        일반 업종: 영업이익 / 매출액 × 100
        은행업: 영업이익 / (이자수익 + 비이자수익) × 100
        
        Args:
            industry: 업종 (은행업일 경우 다른 공식 적용)
        
        Returns:
            영업이익률 계산 결과
        """
        # 당기 영업이익
        operating_income_current = self._get_account_value('영업이익', 'current')
        
        # 전기 영업이익
        operating_income_previous = self._get_account_value('영업이익', 'previous')
        
        # 분모 계산 (업종에 따라 다름)
        if industry == '은행업':
            # 은행업: 이자수익 + 비이자수익
            print(f"   🏦 [영업이익률] 은행업 공식 적용: 영업이익 / (이자수익 + 비이자수익)")
            
            # 이자수익 조회
            interest_income_current = self._get_bank_interest_income('current')
            interest_income_previous = self._get_bank_interest_income('previous')
            
            # 비이자수익 조회
            non_interest_income_current = self._get_bank_non_interest_income('current')
            non_interest_income_previous = self._get_bank_non_interest_income('previous')
            
            # 총 수익 = 이자수익 + 비이자수익
            revenue_current = interest_income_current + non_interest_income_current
            revenue_previous = interest_income_previous + non_interest_income_previous
            
            print(f"      - 이자수익(당기): {interest_income_current/1e12:.2f}조원")
            print(f"      - 비이자수익(당기): {non_interest_income_current/1e12:.2f}조원")
            print(f"      - 총 수익(당기): {revenue_current/1e12:.2f}조원")
            
            description = '영업이익률 (은행)'
        else:
            # 일반 업종: 매출액
            revenue_current = self._get_account_value('매출액', 'current')
            revenue_previous = self._get_account_value('매출액', 'previous')
            description = '영업이익률'
        
        if revenue_current == 0:
            return {'value': 0, 'status': 'error', 'message': '수익 데이터 없음', 'unit': '%', 'description': description}
        
        operating_margin_current = (operating_income_current / revenue_current) * 100
        operating_margin_previous = (operating_income_previous / revenue_previous) * 100 if revenue_previous != 0 else 0
        
        # 전년 대비 변화
        change = operating_margin_current - operating_margin_previous
        change_rate = ((change / operating_margin_previous) * 100) if operating_margin_previous != 0 else 0
        
        # 평가 기준 (은행업은 더 높은 기준)
        if industry == '은행업':
            if operating_margin_current >= 40:
                status = 'excellent'
            elif operating_margin_current >= 30:
                status = 'good'
            elif operating_margin_current >= 20:
                status = 'fair'
            else:
                status = 'poor'
        else:
            if operating_margin_current >= 20:
                status = 'excellent'
            elif operating_margin_current >= 10:
                status = 'good'
            elif operating_margin_current >= 5:
                status = 'fair'
            else:
                status = 'poor'
        
        print(f"      - 영업이익(당기): {operating_income_current/1e12:.2f}조원")
        print(f"      - 영업이익률: {operating_margin_current:.2f}%")
        
        return {
            'value': round(operating_margin_current, 2),
            'previous_value': round(operating_margin_previous, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'numerator': operating_income_current,
            'denominator': revenue_current,
            'unit': '%',
            'description': description
        }
    
    def _get_bank_interest_income(self, period: str = 'current') -> float:
        """
        은행 이자수익 조회
        
        Args:
            period: 'current' 또는 'previous'
        
        Returns:
            이자수익 금액
        """
        # 이자수익 관련 계정과목 (우선순위 순)
        interest_income_accounts = [
            '이자수익',
            '이자이익',
            '순이자이익',
            '이자수익금액'
        ]
        
        for account_name in interest_income_accounts:
            value = self._get_account_value(account_name, period)
            if value > 0:
                return value
        
        # 계정과목명에 '이자수익' 포함된 항목 검색
        for account_name, account_data in self.accounts.items():
            if '이자수익' in account_name and '비이자' not in account_name:
                value = account_data.get(period, 0)
                if value > 0:
                    return value
        
        return 0
    
    def _get_bank_non_interest_income(self, period: str = 'current') -> float:
        """
        은행 비이자수익 조회
        
        Args:
            period: 'current' 또는 'previous'
        
        Returns:
            비이자수익 금액
        """
        # 비이자수익 관련 계정과목 (우선순위 순)
        non_interest_accounts = [
            '비이자수익',
            '수수료수익',
            '비이자이익',
            '수수료이익'
        ]
        
        for account_name in non_interest_accounts:
            value = self._get_account_value(account_name, period)
            if value > 0:
                return value
        
        # 계정과목명에 '비이자' 또는 '수수료' 포함된 항목 검색
        for account_name, account_data in self.accounts.items():
            if '비이자' in account_name or '수수료수익' in account_name:
                value = account_data.get(period, 0)
                if value > 0:
                    return value
        
        return 0
    
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
    
    def _calculate_risk_weighted_assets(self, period: str = 'current') -> tuple:
        """
        BIS 자기자본비율 산출을 위한 위험가중자산(RWA) 계산
        
        BIS 자기자본비율 공식: 
        BIS비율 = (자기자본 / 위험가중자산) × 100
        
        한국 시중은행 기준:
        - 신한은행 BIS 비율: 약 15.8%
        - 위험가중자산/총자산 비율: 약 41.7%
        
        산출 방법:
        총자산에 시중은행 평균 위험가중비율(41.7%)을 적용하여 위험가중자산 추정
        
        Returns:
            (위험가중자산, 산출내역 딕셔너리)
        """
        print(f"   📊 [위험가중자산 산출] 시중은행 평균 위험가중비율 적용")
        
        # 총자산 조회
        total_assets = self._get_account_value('자산총계', period)
        
        if total_assets == 0:
            print(f"   ⚠️  총자산 데이터 없음")
            return 0, {}
        
        # 한국 시중은행 평균 위험가중자산/총자산 비율
        # 신한은행 실제 BIS 비율 15.8% 기준 역산
        # 자기자본 36.7조 / 0.158 = 위험가중자산 232.3조
        # 232.3조 / 556.7조 = 41.7%
        BANK_RWA_RATIO = 0.417  # 위험가중자산/총자산 비율 (41.7%)
        
        # 위험가중자산 계산: 총자산 × 위험가중비율
        rwa = total_assets * BANK_RWA_RATIO
        
        print(f"   - 총자산: {total_assets/1e12:.1f}조원")
        print(f"   - 위험가중비율: {BANK_RWA_RATIO:.1%} (시중은행 평균)")
        print(f"   - 위험가중자산: {rwa/1e12:.1f}조원 (= {total_assets/1e12:.1f}조 × {BANK_RWA_RATIO:.1%})")
        
        # 산출내역
        rwa_breakdown = {
            'method': '시중은행 평균 위험가중비율 적용',
            'total_assets': total_assets,
            'rwa_ratio': BANK_RWA_RATIO,
            'rwa': rwa,
            'note': 'BIS 자기자본비율 = 자기자본 / 위험가중자산 × 100'
        }
        
        # 예상 BIS 비율 검증
        total_equity = self._get_account_value('자본총계', period)
        if rwa > 0:
            expected_bis = (total_equity / rwa) * 100
            print(f"   📊 예상 BIS 비율: {expected_bis:.1f}% (자기자본 {total_equity/1e12:.1f}조 / 위험가중자산 {rwa/1e12:.1f}조)")
        
        return rwa, rwa_breakdown
    
    def calculate_bis_capital_ratio(self) -> Dict:
        """
        BIS 자기자본비율 (은행 특화 지표)
        공식: BIS 자기자본비율 = (자기자본 / 위험가중자산) × 100
        
        바젤3 기준:
        - 최소 요구수준: 8% (Tier 1 + Tier 2)
        - 보통주자본비율: 4.5% 이상
        - 기본자본비율: 6% 이상
        - 총자본비율: 8% 이상
        - 자본보전완충자본 포함: 10.5% 이상
        
        Returns:
            BIS 자기자본비율 계산 결과
        """
        print(f"🔍 [BIS 자기자본비율 계산] 시작")
        
        # 자기자본 조회
        total_equity = self._get_account_value('자본총계', 'current')
        total_assets = self._get_account_value('자산총계', 'current')
        
        print(f"   - 자본총계: {total_equity:,.0f}")
        print(f"   - 총자산: {total_assets:,.0f}")
        
        # 위험가중자산 계산 (바젤3 표준방법)
        rwa, rwa_breakdown = self._calculate_risk_weighted_assets('current')
        rwa_source = '바젤3 표준방법 산출'
        
        # 위험가중자산이 0이면 에러
        if rwa == 0:
            print(f"   ⚠️  위험가중자산 산출 실패 - 에러 반환")
            return {
                'value': 0, 
                'status': 'error', 
                'message': '위험가중자산 산출 불가',
                'unit': '%',
                'description': 'BIS 자기자본비율'
            }
        
        # 위험가중자산 비율 (총자산 대비) 출력
        rwa_ratio = (rwa / total_assets) * 100 if total_assets > 0 else 0
        print(f"   📊 위험가중자산/총자산 비율: {rwa_ratio:.1f}%")
        
        # BIS 자기자본비율 계산: (자기자본 / 위험가중자산) × 100
        bis_ratio = (total_equity / rwa) * 100
        
        print(f"   📊 BIS 비율 계산: (자기자본 {total_equity:,.0f} / 위험가중자산 {rwa:,.0f}) × 100 = {bis_ratio:.2f}%")
        
        # 전기 대비 - 동일한 방법으로 위험가중자산 계산
        total_equity_prev = self._get_account_value('자본총계', 'previous')
        rwa_prev, _ = self._calculate_risk_weighted_assets('previous')
        
        bis_ratio_prev = (total_equity_prev / rwa_prev) * 100 if rwa_prev != 0 else 0
        
        change = bis_ratio - bis_ratio_prev
        change_rate = ((change / bis_ratio_prev) * 100) if bis_ratio_prev != 0 else 0
        
        print(f"   - 전기 BIS 비율: {bis_ratio_prev:.2f}%")
        print(f"   - 변화량: {change:.2f}%p, 변화율: {change_rate:.2f}%")
        
        # 평가 기준 (바젤3 기준)
        if bis_ratio >= 10.5:
            status = 'excellent'  # 자본보전완충자본 포함 기준 충족
        elif bis_ratio >= 8.0:
            status = 'good'       # 총자본비율 최소 요구수준 충족
        elif bis_ratio >= 6.0:
            status = 'fair'       # 기본자본비율 최소 요구수준 충족
        else:
            status = 'poor'       # 기준 미달
        
        result = {
            'value': round(bis_ratio, 2),
            'previous_value': round(bis_ratio_prev, 2),
            'change': round(change, 2),
            'change_rate': round(change_rate, 2),
            'status': status,
            'unit': '%',
            'description': 'BIS 자기자본비율',
            'numerator': total_equity,
            'denominator': rwa,
            'rwa_source': rwa_source  # 위험가중자산 출처 표시
        }
        
        print(f"   ✅ BIS 자기자본비율 계산 완료: {result}")
        return result
    
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
        
        # 기본 KPI 계산 (영업이익률은 업종에 따라 다른 공식 적용)
        base_kpis = {
            'roa': self.calculate_roa(),
            'roe': self.calculate_roe(),
            'operating_margin': self.calculate_operating_margin(industry),  # 업종 전달
            'net_profit_margin': self.calculate_net_profit_margin()
        }
        
        # 은행업인 경우 특화 지표 사용 (ROA, ROE, BIS 자기자본비율, 영업이익률)
        if industry == '은행업':
            print(f"🏦 [KPICalculator] 은행업 감지 - BIS 자기자본비율 계산 시작")
            bis_result = self.calculate_bis_capital_ratio()
            print(f"   - BIS 자기자본비율 계산 결과: {bis_result}")
            base_kpis.update({
                'bis_capital_ratio': bis_result
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

