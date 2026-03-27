#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
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

print_header() {
    echo -e "${BOLD}${CYAN}$1${NC}"
}

# Function to kill processes on a specific port
kill_port() {
    local port=$1
    local service_name=$2
    
    if lsof -i:$port >/dev/null 2>&1; then
        print_warning "Found processes on port $port ($service_name)"
        
        # Get PIDs using the port
        local pids=$(lsof -ti:$port)
        if [ ! -z "$pids" ]; then
            print_info "Killing PIDs: $pids"
            echo "$pids" | xargs kill -9 2>/dev/null
            sleep 1
            
            # Force kill with fuser if still running
            if lsof -i:$port >/dev/null 2>&1; then
                print_warning "Force killing remaining processes on port $port"
                fuser -k $port/tcp 2>/dev/null
                sleep 1
            fi
            
            # Final check
            if lsof -i:$port >/dev/null 2>&1; then
                print_error "Failed to free port $port completely"
                return 1
            else
                print_success "Port $port ($service_name) is now free ✓"
            fi
        fi
    else
        print_info "Port $port ($service_name) is already free ✓"
    fi
    return 0
}

# Function to kill processes by name pattern
kill_processes() {
    local pattern=$1
    local description=$2
    
    local pids=$(pgrep -f "$pattern" 2>/dev/null)
    if [ ! -z "$pids" ]; then
        print_warning "Found $description processes: $pids"
        echo "$pids" | xargs kill -15 2>/dev/null  # Try graceful kill first
        sleep 2
        
        # Check if still running and force kill
        pids=$(pgrep -f "$pattern" 2>/dev/null)
        if [ ! -z "$pids" ]; then
            print_warning "Force killing $description processes: $pids"
            echo "$pids" | xargs kill -9 2>/dev/null
            sleep 1
        fi
        
        # Final check
        pids=$(pgrep -f "$pattern" 2>/dev/null)
        if [ ! -z "$pids" ]; then
            print_error "Some $description processes are still running: $pids"
        else
            print_success "$description processes stopped ✓"
        fi
    else
        print_info "No $description processes running ✓"
    fi
}

print_header "🧹 ICP Hosting Platform - Complete Cleanup & Startup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if we're in the right directory
if [ ! -f "backend.sh" ] || [ ! -f "frontend.sh" ]; then
    print_error "backend.sh or frontend.sh not found. Please run from the root directory."
    exit 1
fi

print_header "🛑 Step 1: Stopping all existing services"

# Kill specific process patterns
kill_processes "uvicorn.*app.main:app" "FastAPI/Backend"
kill_processes "uvicorn.*run:app" "FastAPI/Backend (alternate)"
kill_processes "python.*backend" "Python Backend"
kill_processes "next.*dev" "Next.js Development"
kill_processes "next.*start" "Next.js Production" 
kill_processes "node.*next" "Node.js/Next.js"
kill_processes "npm.*start" "NPM Start"
kill_processes "npm.*dev" "NPM Dev"
kill_processes "npm.*run" "NPM Run"

print_info "Waiting for graceful shutdown..."
sleep 3

print_header "🔌 Step 2: Freeing up ports"

# Kill processes on specific ports
kill_port 3000 "Frontend/Next.js"
kill_port 8000 "Backend/FastAPI"
kill_port 5432 "PostgreSQL (if local)"
kill_port 6379 "Redis (if local)"
kill_port 8080 "Alternative Web Server"
kill_port 8082 "Rosetta API"

print_info "Final cleanup wait..."
sleep 2

print_header "📋 Step 3: System status check"

# Check system resources
print_info "Checking system resources..."
if command -v free >/dev/null 2>&1; then
    echo "Memory usage:"
    free -h | grep -E "(Mem|Swap)"
fi

# Verify ports are truly free
print_info "Verifying ports are free..."
for port in 3000 8000; do
    if lsof -i:$port >/dev/null 2>&1; then
        print_error "Port $port is still in use!"
        lsof -i:$port
        exit 1
    fi
done

print_success "All ports verified free ✓"

print_header "🚀 Step 4: Starting services"

# Check environment files
print_info "Checking environment configuration..."
if [ ! -f "backend/.env" ]; then
    print_error "Backend .env file not found!"
    print_info "Copy backend/.env.example to backend/.env and configure it"
    exit 1
fi

if [ ! -f "frontend/.env.local" ]; then
    print_warning "Frontend .env.local not found, using defaults"
fi

# Start backend server
print_info "Starting backend server..."
if [ -f "backend.log" ]; then
    mv backend.log "backend.log.old.$(date +%Y%m%d_%H%M%S)"
fi

chmod +x backend.sh
./backend.sh &
BACKEND_SCRIPT_PID=$!

print_info "Waiting for backend to initialize..."
sleep 5

# Check if backend is responding
backend_ready=false
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        backend_ready=true
        break
    fi
    print_info "Waiting for backend... ($i/30)"
    sleep 2
done

if [ "$backend_ready" = false ]; then
    print_error "Backend failed to start or is not responding!"
    print_info "Check backend.log for errors:"
    if [ -f "backend.log" ]; then
        tail -10 backend.log
    fi
    exit 1
fi

print_success "Backend is running and responding ✓"

# Start frontend server
print_info "Starting frontend server..."
if [ -f "frontend.log" ]; then
    mv frontend.log "frontend.log.old.$(date +%Y%m%d_%H%M%S)"
fi

chmod +x frontend.sh
./frontend.sh &
FRONTEND_SCRIPT_PID=$!

print_info "Waiting for frontend to initialize..."
sleep 5

# Check if frontend is responding  
frontend_ready=false
for i in {1..30}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        frontend_ready=true
        break
    fi
    print_info "Waiting for frontend... ($i/30)"
    sleep 2
done

if [ "$frontend_ready" = false ]; then
    print_error "Frontend failed to start or is not responding!"
    print_info "Check frontend.log for errors:"
    if [ -f "frontend.log" ]; then
        tail -10 frontend.log
    fi
    print_warning "Backend is still running."
    exit 1
fi

print_success "Frontend is running and responding ✓"

print_header "✅ Step 5: Startup complete!"

echo ""
print_success "🎉 ICP Hosting Platform is ready!"
print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_info "📱 Frontend:     ${BOLD}http://localhost:3000${NC}"
print_info "🔧 Backend API:  ${BOLD}http://localhost:8000${NC}"
print_info "📚 API Docs:     ${BOLD}http://localhost:8000/docs${NC}"
print_info "🧪 API Tests:    ${BOLD}cd testing && ./run_tests.sh${NC}"
print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_info "📋 Monitoring:"
print_info "   Backend logs:  ${CYAN}tail -f backend.log${NC}"
print_info "   Frontend logs: ${CYAN}tail -f frontend.log${NC}"
print_info "   Stop services: ${CYAN}./stop.sh${NC}"
print_info ""
print_success "Ready to deploy to the Internet Computer! 🚀"

# Keep the script running so servers stay alive
print_info "Both servers are running in the background."
print_info "Press Ctrl+C to stop this monitoring script (servers will continue)"
print_info "Use './stop.sh' to stop all servers cleanly"

# Trap Ctrl+C to provide a clean exit message
trap 'echo ""; print_info "Monitoring stopped. Servers are still running."; print_info "Use ${CYAN}./stop.sh${NC} to stop all servers"; exit 0' INT

# Keep script alive with periodic health checks
while true; do
    sleep 30
    
    # Optional health checks
    if ! curl -s http://localhost:8000/health >/dev/null 2>&1; then
        print_warning "Backend health check failed!"
    fi
    
    if ! curl -s http://localhost:3000 >/dev/null 2>&1; then
        print_warning "Frontend health check failed!"
    fi
done