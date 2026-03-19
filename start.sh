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

print_info "🌐 Starting ICP Hosting Platform..."

# Check if we're in the right directory
if [ ! -f "backend.sh" ] || [ ! -f "frontend.sh" ]; then
    print_error "backend.sh or frontend.sh not found. Please run from the root directory."
    exit 1
fi

# Stop any existing servers
print_info "Stopping existing servers..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null
pkill -f "next.*dev" 2>/dev/null
pkill -f "node.*next" 2>/dev/null
sleep 2

# Free up ports if they're still in use
if lsof -i:8000 >/dev/null 2>&1; then
    print_warning "Freeing port 8000..."
    fuser -k 8000/tcp 2>/dev/null
fi

if lsof -i:3000 >/dev/null 2>&1; then
    print_warning "Freeing port 3000..."
    fuser -k 3000/tcp 2>/dev/null
fi

sleep 2

# Start backend server
print_info "Starting backend server..."
./backend.sh
BACKEND_EXIT_CODE=$?

if [ $BACKEND_EXIT_CODE -ne 0 ]; then
    print_error "Backend startup failed!"
    exit 1
fi

print_success "Backend is running ✓"

# Start frontend server
print_info "Starting frontend server..."
./frontend.sh
FRONTEND_EXIT_CODE=$?

if [ $FRONTEND_EXIT_CODE -ne 0 ]; then
    print_error "Frontend startup failed!"
    print_warning "Backend is still running. Use './stop.sh' to stop all servers."
    exit 1
fi

print_success "Frontend is running ✓"

echo ""
print_success "🎉 ICP Hosting Platform is ready!"
print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_info "📱 Frontend:     http://localhost:3000"
print_info "🔧 Backend API:  http://localhost:8000"
print_info "📚 API Docs:     http://localhost:8000/docs"
print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_info "📋 Logs:"
print_info "   Backend: tail -f backend.log"
print_info "   Frontend: tail -f frontend.log"
print_info ""
print_info "🛑 To stop: ./stop.sh"
print_success "Ready to deploy to the Internet Computer! 🚀"