#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    print_error "frontend directory not found. Please run from the root directory."
    exit 1
fi

print_info "🌐 Starting ICP Hosting Frontend..."

# Kill existing frontend server
print_info "Stopping existing frontend server..."
pkill -f "next.*dev" 2>/dev/null
pkill -f "node.*next" 2>/dev/null
if [ $? -eq 0 ]; then
    print_warning "Stopped existing frontend server"
    sleep 2
fi

# Check if port 3000 is still in use
if lsof -i:3000 >/dev/null 2>&1; then
    print_warning "Port 3000 is still in use, attempting to free it..."
    fuser -k 3000/tcp 2>/dev/null
    sleep 2
fi

# Navigate to frontend directory
cd frontend

print_info "Installing frontend dependencies..."
npm install >/dev/null 2>&1

print_info "Starting Next.js development server..."

# Start frontend server
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for the server to start
sleep 5

# Check if frontend is running
if ps -p $FRONTEND_PID > /dev/null; then
    print_success "Frontend server started successfully (PID: $FRONTEND_PID)"
    print_info "Frontend URL: http://localhost:3000"
    print_info "Frontend logs: tail -f frontend.log"
    echo $FRONTEND_PID > ../frontend.pid
else
    print_error "Failed to start frontend server"
    print_error "Check frontend.log for details: tail -f frontend.log"
    exit 1
fi

# Test frontend health
sleep 3
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    print_success "Frontend health check passed ✓"
else
    print_warning "Frontend is still starting up..."
fi

print_success "Frontend startup complete!"