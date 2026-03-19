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

print_info "🛑 Stopping ICP Hosting Platform..."

# Kill backend processes
print_info "Stopping backend server..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null
pkill -f "python.*uvicorn" 2>/dev/null
if [ -f "backend.pid" ]; then
    PID=$(cat backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null
    fi
    rm -f backend.pid
fi

# Kill frontend processes
print_info "Stopping frontend server..."
pkill -f "next.*dev" 2>/dev/null
pkill -f "node.*next" 2>/dev/null
if [ -f "frontend.pid" ]; then
    PID=$(cat frontend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null
    fi
    rm -f frontend.pid
fi

# Force kill if ports are still in use
if lsof -i:8000 >/dev/null 2>&1; then
    print_warning "Force stopping processes on port 8000..."
    fuser -k 8000/tcp 2>/dev/null
fi

if lsof -i:3000 >/dev/null 2>&1; then
    print_warning "Force stopping processes on port 3000..."
    fuser -k 3000/tcp 2>/dev/null
fi

sleep 2

# Verify servers are stopped
if ! lsof -i:8000 >/dev/null 2>&1; then
    print_success "Backend stopped ✓"
else
    print_error "Backend still running on port 8000"
fi

if ! lsof -i:3000 >/dev/null 2>&1; then
    print_success "Frontend stopped ✓"
else
    print_error "Frontend still running on port 3000"
fi

print_success "🎉 All servers stopped!"