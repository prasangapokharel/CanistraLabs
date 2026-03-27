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
        print_warning "Stopping processes on port $port ($service_name)"
        
        # Get PIDs using the port
        local pids=$(lsof -ti:$port)
        if [ ! -z "$pids" ]; then
            print_info "Gracefully stopping PIDs: $pids"
            echo "$pids" | xargs kill -15 2>/dev/null  # Graceful shutdown
            sleep 3
            
            # Force kill if still running
            pids=$(lsof -ti:$port 2>/dev/null)
            if [ ! -z "$pids" ]; then
                print_warning "Force stopping remaining PIDs: $pids"
                echo "$pids" | xargs kill -9 2>/dev/null
                sleep 1
            fi
            
            # Final cleanup with fuser
            if lsof -i:$port >/dev/null 2>&1; then
                print_warning "Final cleanup for port $port"
                fuser -k $port/tcp 2>/dev/null
                sleep 1
            fi
            
            # Verification
            if lsof -i:$port >/dev/null 2>&1; then
                print_error "Failed to stop all processes on port $port"
                lsof -i:$port
                return 1
            else
                print_success "Port $port ($service_name) stopped ✓"
            fi
        fi
    else
        print_info "Port $port ($service_name) not in use ✓"
    fi
    return 0
}

# Function to kill processes by name pattern
kill_processes() {
    local pattern=$1
    local description=$2
    
    local pids=$(pgrep -f "$pattern" 2>/dev/null)
    if [ ! -z "$pids" ]; then
        print_warning "Stopping $description processes: $pids"
        echo "$pids" | xargs kill -15 2>/dev/null  # Graceful shutdown
        sleep 2
        
        # Force kill if still running
        pids=$(pgrep -f "$pattern" 2>/dev/null)
        if [ ! -z "$pids" ]; then
            print_warning "Force stopping $description processes: $pids"
            echo "$pids" | xargs kill -9 2>/dev/null
            sleep 1
        fi
        
        # Final verification
        pids=$(pgrep -f "$pattern" 2>/dev/null)
        if [ ! -z "$pids" ]; then
            print_error "Some $description processes still running: $pids"
            return 1
        else
            print_success "$description processes stopped ✓"
        fi
    else
        print_info "No $description processes running ✓"
    fi
    return 0
}

print_header "🛑 ICP Hosting Platform - Complete Shutdown"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

print_header "🔄 Step 1: Stopping application processes"

# Stop specific process patterns (most specific first)
kill_processes "uvicorn.*app.main:app" "FastAPI Backend"
kill_processes "uvicorn.*run:app" "FastAPI Backend (alternate)"
kill_processes "python.*backend" "Python Backend"
kill_processes "next.*dev" "Next.js Development"
kill_processes "next.*start" "Next.js Production"
kill_processes "node.*next" "Node.js/Next.js"
kill_processes "npm.*start" "NPM Start"
kill_processes "npm.*dev" "NPM Dev"
kill_processes "npm.*run.*dev" "NPM Dev Scripts"
kill_processes "npm.*run.*start" "NPM Start Scripts"

# Clean up PID files
if [ -f "backend.pid" ]; then
    PID=$(cat backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        print_info "Stopping backend PID from file: $PID"
        kill $PID 2>/dev/null
    fi
    rm -f backend.pid
fi

if [ -f "frontend.pid" ]; then
    PID=$(cat frontend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        print_info "Stopping frontend PID from file: $PID"
        kill $PID 2>/dev/null
    fi
    rm -f frontend.pid
fi

print_info "Allowing graceful shutdown..."
sleep 3

print_header "🔌 Step 2: Freeing ports"

# Stop processes on key ports
kill_port 3000 "Frontend/Next.js"
kill_port 8000 "Backend/FastAPI" 
kill_port 8080 "Alternative Web"
kill_port 5173 "Vite Dev Server"
kill_port 4173 "Vite Preview"

print_info "Final cleanup wait..."
sleep 2

print_header "🧹 Step 3: Additional cleanup"

# Clean up any remaining Node.js processes that might be hanging
print_info "Cleaning up Node.js processes..."
if pgrep -f "node" >/dev/null 2>&1; then
    print_warning "Found additional Node.js processes"
    pgrep -f "node" | while read pid; do
        # Get process details
        if ps -p $pid -o pid,ppid,cmd --no-headers 2>/dev/null | grep -E "(next|npm|frontend)" >/dev/null; then
            print_info "Stopping Node.js process: $pid"
            kill -15 $pid 2>/dev/null
        fi
    done
    sleep 2
fi

# Clean up Python processes related to our backend
print_info "Cleaning up Python backend processes..."
if pgrep -f "python.*uvicorn" >/dev/null 2>&1; then
    print_warning "Found additional Python/uvicorn processes"
    pgrep -f "python.*uvicorn" | xargs kill -15 2>/dev/null
    sleep 2
    # Force kill if still running
    pgrep -f "python.*uvicorn" | xargs kill -9 2>/dev/null
fi

print_header "✅ Step 4: Verification"

# Final verification
errors=0
for port in 3000 8000; do
    if lsof -i:$port >/dev/null 2>&1; then
        print_error "Port $port is still in use:"
        lsof -i:$port
        errors=$((errors + 1))
    else
        print_success "Port $port is free ✓"
    fi
done

# Check for any remaining processes
remaining_backend=$(pgrep -f "uvicorn.*app" 2>/dev/null)
remaining_frontend=$(pgrep -f "next.*dev\|npm.*start" 2>/dev/null)

if [ ! -z "$remaining_backend" ]; then
    print_error "Backend processes still running: $remaining_backend"
    errors=$((errors + 1))
fi

if [ ! -z "$remaining_frontend" ]; then
    print_error "Frontend processes still running: $remaining_frontend"  
    errors=$((errors + 1))
fi

print_header "📊 Step 5: Cleanup summary"

if [ $errors -eq 0 ]; then
    print_success "🎉 All services stopped successfully!"
    print_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_info "✅ Ports 3000 and 8000 are free"
    print_info "✅ All application processes stopped"
    print_info "✅ System is ready for restart"
    print_info ""
    print_info "To start again: ${CYAN}./start.sh${NC}"
    echo ""
else
    print_error "⚠️  Shutdown completed with $errors issues"
    print_warning "Some processes or ports may still be in use"
    print_info "You may need to manually kill remaining processes"
    print_info "Or restart your system for a complete cleanup"
fi

# Show current port status
print_info "Current port status:"
for port in 3000 8000 5432 6379; do
    if lsof -i:$port >/dev/null 2>&1; then
        echo "  Port $port: ${RED}IN USE${NC}"
    else  
        echo "  Port $port: ${GREEN}FREE${NC}"
    fi
done

print_success "Shutdown script completed."