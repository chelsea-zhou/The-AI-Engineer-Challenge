#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting AI Chat Application...${NC}"

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Start backend if not running
if ! check_port 8000; then
    echo -e "${YELLOW}📡 Starting backend API on port 8000...${NC}"
    cd api
    python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    sleep 3
else
    echo -e "${GREEN}✅ Backend API already running on port 8000${NC}"
fi

# Start frontend if not running
if ! check_port 3000; then
    echo -e "${YELLOW}🎨 Starting frontend on port 3000...${NC}"
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    sleep 5
else
    echo -e "${GREEN}✅ Frontend already running on port 3000${NC}"
fi

echo -e "${GREEN}🎉 Application started successfully!${NC}"
echo -e "${BLUE}📱 Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "${BLUE}🔧 Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "${BLUE}📊 API Health Check: ${GREEN}http://localhost:8000/api/health${NC}"
echo ""
echo -e "${YELLOW}💡 To stop the application, press Ctrl+C${NC}"

# Wait for user to stop
wait 