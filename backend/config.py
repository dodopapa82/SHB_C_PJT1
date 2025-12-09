"""
애플리케이션 설정 파일
환경변수와 기본값을 관리합니다.
"""

import os
from datetime import datetime


class Config:
    """애플리케이션 설정"""
    
    # DART API 설정
    DART_API_KEY = os.getenv('DART_API_KEY')
    DART_API_BASE_URL = 'https://opendart.fss.or.kr/api'
    
    # 서버 설정
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5001))
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
    
    # 기본값 설정
    DEFAULT_YEAR = int(os.getenv('DEFAULT_YEAR', datetime.now().year - 1))  # 전년도
    DEFAULT_INDUSTRY = os.getenv('DEFAULT_INDUSTRY', '은행업')
    DEFAULT_REPORT_CODE = os.getenv('DEFAULT_REPORT_CODE', '11011')  # 사업보고서
    
    # 캐시 설정
    CACHE_DURATION_DAYS = int(os.getenv('CACHE_DURATION_DAYS', 1))
    
    # API 제한 설정
    MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', 20))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    # CORS 설정
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    @classmethod
    def get_config_summary(cls):
        """설정 요약 출력"""
        return {
            'DART_API_CONFIGURED': bool(cls.DART_API_KEY),
            'HOST': cls.HOST,
            'PORT': cls.PORT,
            'DEBUG': cls.DEBUG,
            'DEFAULT_YEAR': cls.DEFAULT_YEAR,
            'DEFAULT_INDUSTRY': cls.DEFAULT_INDUSTRY
        }


# 설정 객체 생성
config = Config()

