#!/bin/bash

# DART 재무제표 분석 시스템 자동 실행 스크립트
# 백엔드 서버를 시작하고 프론트엔드를 브라우저에서 자동으로 엽니다.

echo "=================================="
echo "🚀 DART 재무제표 분석 시스템 시작"
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

# 1. Python3 확인
echo "📌 Python3 확인 중..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3가 설치되어 있지 않습니다.${NC}"
    echo "Python3를 설치한 후 다시 시도해주세요."
    exit 1
fi
echo -e "${GREEN}✅ Python3: $(python3 --version)${NC}"
echo ""

# 2. 필요한 패키지 확인
echo "📌 Python 패키지 확인 중..."
if [ -f "backend/requirements.txt" ]; then
    echo "requirements.txt 발견. 패키지 설치 확인..."
    cd backend
    python3 -m pip install -q -r requirements.txt
    cd ..
    echo -e "${GREEN}✅ 패키지 확인 완료${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt 파일을 찾을 수 없습니다.${NC}"
fi
echo ""

# 3. 환경변수 확인
echo "📌 환경변수 확인 중..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env 파일 발견${NC}"
    export $(cat .env | grep -v '^#' | xargs)
elif [ -n "$DART_API_KEY" ]; then
    echo -e "${GREEN}✅ DART_API_KEY 환경변수 설정됨${NC}"
else
    echo -e "${YELLOW}⚠️  DART API 키가 설정되지 않았습니다. 샘플 데이터로 동작합니다.${NC}"
    echo "실제 DART API를 사용하려면 .env 파일을 생성하거나 환경변수를 설정하세요."
fi
echo ""

# 4. 포트 5001 확인 및 정리
echo "📌 포트 5001 확인 중..."
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  포트 5001이 이미 사용 중입니다. 기존 프로세스를 종료합니다...${NC}"
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ 포트 정리 완료${NC}"
else
    echo -e "${GREEN}✅ 포트 5001 사용 가능${NC}"
fi
echo ""

# 5. 백엔드 서버 시작
echo "=================================="
echo "🔧 백엔드 서버 시작 중..."
echo "=================================="
cd backend

# 서버를 백그라운드에서 실행하고 PID 저장
python3 app.py > ../server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > ../server.pid

cd ..

# 서버가 준비될 때까지 대기
echo "서버 시작 대기 중..."
for i in {1..10}; do
    if curl -s http://localhost:5001 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 백엔드 서버 시작 완료!${NC}"
        echo "   URL: http://localhost:5001"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ 서버 시작 실패. server.log를 확인해주세요.${NC}"
        cat server.log
        exit 1
    fi
    sleep 1
    echo "   대기 중... ($i/10)"
done
echo ""

# 6. 포트 8080 확인 및 정리
echo "📌 포트 8080 확인 중..."
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  포트 8080이 이미 사용 중입니다. 기존 프로세스를 종료합니다...${NC}"
    lsof -ti:8080 | xargs kill -9 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ 포트 정리 완료${NC}"
else
    echo -e "${GREEN}✅ 포트 8080 사용 가능${NC}"
fi
echo ""

# 7. 프론트엔드 서버 시작
echo "=================================="
echo "🌐 프론트엔드 서버 시작 중..."
echo "=================================="
cd frontend

# 프론트엔드 서버를 백그라운드에서 실행하고 PID 저장
python3 -m http.server 8080 > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid

cd ..

# 프론트엔드 서버가 준비될 때까지 대기
echo "프론트엔드 서버 시작 대기 중..."
for i in {1..5}; do
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 프론트엔드 서버 시작 완료!${NC}"
        echo "   URL: http://localhost:8080"
        break
    fi
    if [ $i -eq 5 ]; then
        echo -e "${RED}❌ 프론트엔드 서버 시작 실패. frontend.log를 확인해주세요.${NC}"
        exit 1
    fi
    sleep 1
    echo "   대기 중... ($i/5)"
done
echo ""

# 8. 브라우저 열기
echo "=================================="
echo "🌐 브라우저 열기"
echo "=================================="
sleep 1

# OS별 브라우저 열기
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:8080
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open http://localhost:8080 2>/dev/null || sensible-browser http://localhost:8080 2>/dev/null
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    start http://localhost:8080
else
    echo -e "${YELLOW}⚠️  브라우저를 자동으로 열 수 없습니다.${NC}"
    echo "수동으로 http://localhost:8080 을 열어주세요."
fi

echo -e "${GREEN}✅ 브라우저에서 프론트엔드를 열었습니다!${NC}"
echo ""

# 9. 완료 메시지
echo "=================================="
echo "✨ 시스템 시작 완료!"
echo "=================================="
echo ""
echo "📡 백엔드 서버: http://localhost:5001"
echo "🌐 프론트엔드: http://localhost:8080"
echo "📝 백엔드 로그: server.log"
echo "📝 프론트엔드 로그: frontend.log"
echo "🔢 백엔드 PID: $SERVER_PID (server.pid에 저장됨)"
echo "🔢 프론트엔드 PID: $FRONTEND_PID (frontend.pid에 저장됨)"
echo ""
echo "서버를 종료하려면 다음 명령을 실행하세요:"
echo "  ./stop.sh"
echo "또는:"
echo "  kill $SERVER_PID $FRONTEND_PID"
echo ""
echo -e "${GREEN}🎉 준비 완료! 브라우저에서 기업을 검색해보세요!${NC}"
echo ""

