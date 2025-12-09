#!/bin/bash

# DART 재무제표 분석 시스템 종료 스크립트

echo "=================================="
echo "🛑 DART 재무제표 분석 시스템 종료"
echo "=================================="
echo ""

# 작업 디렉토리 설정
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 백엔드 서버 종료
if [ -f "server.pid" ]; then
    SERVER_PID=$(cat server.pid)
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "🛑 백엔드 서버 종료 중... (PID: $SERVER_PID)"
        kill $SERVER_PID 2>/dev/null
        sleep 1
        
        # 강제 종료 (필요시)
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            kill -9 $SERVER_PID 2>/dev/null
        fi
        
        echo -e "${GREEN}✅ 백엔드 서버 종료 완료${NC}"
    else
        echo -e "${YELLOW}⚠️  백엔드 서버가 이미 종료되었습니다.${NC}"
    fi
    rm server.pid
else
    echo -e "${YELLOW}⚠️  server.pid 파일을 찾을 수 없습니다.${NC}"
    
    # 포트로 찾아서 종료
    if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "포트 5001을 사용하는 프로세스를 종료합니다..."
        lsof -ti:5001 | xargs kill -9 2>/dev/null
        echo -e "${GREEN}✅ 포트 5001 정리 완료${NC}"
    fi
fi
echo ""

# 프론트엔드 서버 종료
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "🛑 프론트엔드 서버 종료 중... (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null
        sleep 1
        
        # 강제 종료 (필요시)
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            kill -9 $FRONTEND_PID 2>/dev/null
        fi
        
        echo -e "${GREEN}✅ 프론트엔드 서버 종료 완료${NC}"
    else
        echo -e "${YELLOW}⚠️  프론트엔드 서버가 이미 종료되었습니다.${NC}"
    fi
    rm frontend.pid
else
    echo -e "${YELLOW}⚠️  frontend.pid 파일을 찾을 수 없습니다.${NC}"
    
    # 포트로 찾아서 종료
    if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "포트 8080을 사용하는 프로세스를 종료합니다..."
        lsof -ti:8080 | xargs kill -9 2>/dev/null
        echo -e "${GREEN}✅ 포트 8080 정리 완료${NC}"
    fi
fi
echo ""

# 로그 파일 정리 (선택사항)
if [ -f "server.log" ]; then
    echo "📝 서버 로그 파일 유지: server.log"
fi
if [ -f "frontend.log" ]; then
    echo "📝 프론트엔드 로그 파일 유지: frontend.log"
fi
echo ""

echo "=================================="
echo -e "${GREEN}✅ 모든 서버가 종료되었습니다!${NC}"
echo "=================================="
echo ""
