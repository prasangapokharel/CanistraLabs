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
if [ ! -d "backend" ]; then
    print_error "backend directory not found. Please run from the root directory."
    exit 1
fi

print_info "🚀 Starting ICP Hosting Backend..."

# Kill existing backend server
print_info "Stopping existing backend server..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null
if [ $? -eq 0 ]; then
    print_warning "Stopped existing backend server"
    sleep 2
fi

# Check if port 8000 is still in use
if lsof -i:8000 >/dev/null 2>&1; then
    print_warning "Port 8000 is still in use, attempting to free it..."
    fuser -k 8000/tcp 2>/dev/null
    sleep 2
fi

# Navigate to backend directory
cd backend

print_info "Installing backend dependencies..."
# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -e . >/dev/null 2>&1

print_info "Starting FastAPI server on http://localhost:8000..."

# Start backend server
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for the server to start
sleep 3

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null; then
    print_success "Backend server started successfully (PID: $BACKEND_PID)"
    print_info "Backend API docs: http://localhost:8000/docs"
    print_info "Backend logs: tail -f backend.log"
    echo $BACKEND_PID > ../backend.pid
else
    print_error "Failed to start backend server"
    print_error "Check backend.log for details: tail -f backend.log"
    exit 1
fi

# Test backend health
sleep 2
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    print_success "Backend health check passed ✓"
else
    print_warning "Backend health check failed, but server is running"
fi

print_success "Backend startup complete!"