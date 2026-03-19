#!/bin/bash
# ICP Hosting Platform - Setup Script
# Installs dfx and sets up the development environment

set -e

echo "================================"
echo "ICP Hosting Platform - Setup"
echo "================================"
echo ""

# Check if dfx is already installed
if command -v dfx &> /dev/null; then
    echo "✓ dfx is already installed: $(dfx --version)"
else
    echo "Installing dfx SDK..."
    curl -fsSL https://github.com/dfinity/sdk/releases/latest/download/dfx-x86_64-unknown-linux-gnu.tar.gz -o /tmp/dfx.tar.gz
    mkdir -p ~/.local/bin
    cd /tmp
    tar -xzf dfx.tar.gz
    cp dfx-x86_64-unknown-linux-gnu/dfx ~/.local/bin/
    chmod +x ~/.local/bin/dfx
    export PATH=$PATH:~/.local/bin
    echo "✓ dfx installed: $($HOME/.local/bin/dfx --version)"
fi

echo ""
echo "Installing Python dependencies..."
cd "$(dirname "$0")/.."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]" > /dev/null 2>&1

echo "✓ Python dependencies installed"

echo ""
echo "Setup complete!"
echo ""
echo "To activate the environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To start the server, run:"
echo "  python run.py"
echo ""
echo "To run tests, run:"
echo "  pytest tests/ -v"
