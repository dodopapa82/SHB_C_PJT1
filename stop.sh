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

# 1. PID 파일에서 서버 종료
if [ -f "server.pid" ]; then
    SERVER_PID=$(cat server.pid)
    echo "📌 저장된 서버 PID: $SERVER_PID"
    
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "서버 프로세스 종료 중..."
        kill $SERVER_PID 2>/dev/null
        sleep 1
        
        # 강제 종료가 필요한 경우
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            echo "강제 종료 중..."
            kill -9 $SERVER_PID 2>/dev/null
        fi
        
        echo -e "${GREEN}✅ 서버가 종료되었습니다.${NC}"
    else
        echo -e "${YELLOW}⚠️  서버 프로세스가 이미 종료되었습니다.${NC}"
    fi
    
    rm server.pid
else
    echo -e "${YELLOW}⚠️  server.pid 파일을 찾을 수 없습니다.${NC}"
fi

# 2. 포트 5001을 사용하는 모든 프로세스 종료
echo ""
echo "📌 포트 5001 정리 중..."
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "포트 5001을 사용하는 프로세스 종료 중..."
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ 포트 정리 완료${NC}"
else
    echo -e "${GREEN}✅ 포트 5001은 이미 비어있습니다.${NC}"
fi

# 3. 로그 파일 정리 (선택사항)
echo ""
read -p "서버 로그 파일(server.log)을 삭제하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "server.log" ]; then
        rm server.log
        echo -e "${GREEN}✅ 로그 파일 삭제 완료${NC}"
    fi
else
    echo "로그 파일을 유지합니다."
fi

echo ""
echo "=================================="
echo -e "${GREEN}✨ 시스템 종료 완료!${NC}"
echo "=================================="
echo ""

