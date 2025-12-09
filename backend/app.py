"""
Flask 백엔드 서버
DART 재무제표 분석 API 엔드포인트 제공
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from config import config
from dart_api import DARTApi
from kpi_calculator import KPICalculator
from weakness_analyzer import WeaknessAnalyzer

app = Flask(__name__)
CORS(app)  # CORS 허용 (프론트엔드 연동)

# DART API 초기화
try:
    dart_api = DARTApi()
    print("✅ DART API 초기화 성공")
except ValueError as e:
    print(f"⚠️  DART API 키가 설정되지 않았습니다. 샘플 데이터로 동작합니다.")
    print(f"    실제 DART API를 사용하려면 환경변수를 설정하세요:")
    print(f"    export DART_API_KEY='your_api_key'")
    dart_api = None


@app.route('/')
def index():
    """API 상태 확인"""
    return jsonify({
        'status': 'ok',
        'message': 'DART 재무제표 분석 API 서버',
        'version': '1.0.0',
        'endpoints': {
            'search': '/api/search?q=기업명',
            'company': '/api/company/<corp_code>',
            'financial': '/api/financial/<corp_code>',
            'kpi': '/api/kpi/<corp_code>',
            'weakness': '/api/weakness/<corp_code>',
            'report': '/api/report/<corp_code>'
        }
    })


@app.route('/api/search', methods=['GET'])
def search_company():
    """
    기업 검색 API
    Query Parameters:
        q: 검색어 (기업명 또는 종목코드)
    """
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': '검색어를 입력해주세요.'}), 400
    
    try:
        if dart_api:
            results = dart_api.search_company(query)
        else:
            # 샘플 데이터
            results = DARTApi('sample').search_company(query)
        
        return jsonify({
            'status': 'success',
            'query': query,
            'count': len(results),
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/company/<corp_code>', methods=['GET'])
def get_company_info(corp_code):
    """
    기업 개황 조회 API
    Path Parameters:
        corp_code: 기업 고유코드
    """
    try:
        if dart_api:
            company_info = dart_api.get_company_info(corp_code)
        else:
            company_info = DARTApi('sample').get_company_info(corp_code)
        
        return jsonify({
            'status': 'success',
            'data': company_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/financial/<corp_code>', methods=['GET'])
def get_financial_statement(corp_code):
    """
    재무제표 조회 API
    Path Parameters:
        corp_code: 기업 고유코드
    Query Parameters:
        year: 사업연도 (기본값: 전년도)
    """
    year = request.args.get('year', config.DEFAULT_YEAR, type=int)
    
    try:
        if dart_api:
            financial_data = dart_api.get_financial_statement(corp_code, year)
        else:
            financial_data = DARTApi('sample').get_financial_statement(corp_code, year)
        
        return jsonify({
            'status': 'success',
            'data': financial_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kpi/<corp_code>', methods=['GET'])
def get_kpi_analysis(corp_code):
    """
    KPI 분석 API
    Path Parameters:
        corp_code: 기업 고유코드
    Query Parameters:
        year: 사업연도 (기본값: 전년도)
    """
    year = request.args.get('year', config.DEFAULT_YEAR, type=int)
    
    try:
        # 재무제표 조회
        if dart_api:
            financial_data = dart_api.get_financial_statement(corp_code, year)
        else:
            financial_data = DARTApi('sample').get_financial_statement(corp_code, year)
        
        # 업종 정보 가져오기 (기업 정보에서)
        industry = config.DEFAULT_INDUSTRY
        try:
            if dart_api:
                company_info = dart_api.get_company_info(corp_code)
                industry = company_info.get('industry', config.DEFAULT_INDUSTRY) if company_info else config.DEFAULT_INDUSTRY
            else:
                company_info = DARTApi('sample').get_company_info(corp_code)
                industry = company_info.get('industry', config.DEFAULT_INDUSTRY) if company_info else config.DEFAULT_INDUSTRY
        except Exception as e:
            print(f"⚠️  업종 정보 가져오기 실패: {e}")
        
        print(f"📊 [KPI 분석] corp_code={corp_code}, year={year}, industry={industry}")
        
        # KPI 계산 (업종 정보 전달)
        calculator = KPICalculator(financial_data)
        kpis = calculator.calculate_all_kpis(industry)
        trends = calculator.get_trend_analysis()
        
        print(f"✅ [KPI 분석] 계산된 KPI 키: {list(kpis.keys())}")
        if industry == '은행업':
            print(f"   - NIM 값: {kpis.get('nim', {}).get('value', 'N/A')}")
            print(f"   - debt_ratio 존재: {'debt_ratio' in kpis}")
            print(f"   - current_ratio 존재: {'current_ratio' in kpis}")
        
        return jsonify({
            'status': 'success',
            'corp_code': corp_code,
            'year': year,
            'industry': industry,
            'kpis': kpis,
            'trends': trends
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/weakness/<corp_code>', methods=['GET'])
def get_weakness_analysis(corp_code):
    """
    취약점 분석 API
    Path Parameters:
        corp_code: 기업 고유코드
    Query Parameters:
        year: 사업연도 (기본값: 전년도)
        industry: 업종 (기본값: default)
    """
    year = request.args.get('year', config.DEFAULT_YEAR, type=int)
    industry = request.args.get('industry', config.DEFAULT_INDUSTRY)
    
    print(f"🔍 [취약점 분석] corp_code={corp_code}, year={year}, industry={industry}")
    
    try:
        # 재무제표 조회
        if dart_api:
            financial_data = dart_api.get_financial_statement(corp_code, year)
        else:
            financial_data = DARTApi('sample').get_financial_statement(corp_code, year)
        
        # KPI 계산 (업종 정보 전달)
        calculator = KPICalculator(financial_data)
        kpis = calculator.calculate_all_kpis(industry)
        
        # 취약점 분석
        analyzer = WeaknessAnalyzer(kpis, industry)
        analysis_result = analyzer.analyze_all()
        priorities = analyzer.get_improvement_priorities()
        
        print(f"✅ [취약점 분석] 사용된 업종: {analyzer.industry}, 벤치마크: {analyzer.benchmark}")
        
        return jsonify({
            'status': 'success',
            'corp_code': corp_code,
            'year': year,
            'industry': analyzer.industry,  # 실제 사용된 업종
            'industry_requested': industry,  # 요청된 업종
            'analysis': analysis_result,
            'priorities': priorities
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/report/<corp_code>', methods=['GET'])
def get_comprehensive_report(corp_code):
    """
    종합 리포트 API
    Path Parameters:
        corp_code: 기업 고유코드
    Query Parameters:
        year: 사업연도 (기본값: 전년도)
        industry: 업종 (기본값: default)
    """
    year = request.args.get('year', config.DEFAULT_YEAR, type=int)
    industry = request.args.get('industry', config.DEFAULT_INDUSTRY)
    
    print(f"📊 [종합 리포트] corp_code={corp_code}, year={year}, industry={industry}")
    
    try:
        # 기업 정보
        if dart_api:
            company_info = dart_api.get_company_info(corp_code)
            financial_data = dart_api.get_financial_statement(corp_code, year)
        else:
            api = DARTApi('sample')
            company_info = api.get_company_info(corp_code)
            financial_data = api.get_financial_statement(corp_code, year)
        
        # KPI 계산 (업종 정보 전달)
        calculator = KPICalculator(financial_data)
        kpis = calculator.calculate_all_kpis(industry)
        trends = calculator.get_trend_analysis()
        
        # 취약점 분석
        analyzer = WeaknessAnalyzer(kpis, industry)
        analysis = analyzer.analyze_all()
        priorities = analyzer.get_improvement_priorities()
        
        print(f"✅ [종합 리포트] 사용된 업종: {analyzer.industry}, 벤치마크: {analyzer.benchmark}")
        
        # 종합 리포트
        report = {
            'company': company_info,
            'financial': {
                'year': year,
                'data': financial_data
            },
            'kpis': kpis,
            'trends': trends,
            'weakness_analysis': analysis,
            'improvement_priorities': priorities,
            'generated_at': year
        }
        
        return jsonify({
            'status': 'success',
            'report': report
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return jsonify({'error': 'API 엔드포인트를 찾을 수 없습니다.'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 에러 핸들러"""
    return jsonify({'error': '서버 내부 오류가 발생했습니다.'}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 DART 재무제표 분석 API 서버 시작")
    print("=" * 60)
    print(f"📡 서버 주소: http://localhost:{config.PORT}")
    print(f"📊 API 문서: http://localhost:{config.PORT}")
    print(f"🗓️  기본 분석 연도: {config.DEFAULT_YEAR}")
    print(f"🏭 기본 업종: {config.DEFAULT_INDUSTRY}")
    print("=" * 60)
    
    # 개발 모드로 실행
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )

