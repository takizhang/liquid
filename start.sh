#!/bin/bash

# Liquidity Monitor v2 - Start Script
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "========================================"
echo "  Liquidity Monitor v2 - Starting..."
echo "========================================"

# Check if backend venv exists
if [ ! -d "backend/venv" ]; then
    echo ""
    echo "Setting up backend virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Activate venv
cd backend
source venv/bin/activate

# Generate demo data if database doesn't exist
if [ ! -f "data/liquidity.db" ]; then
    echo ""
    echo "Generating demo data..."
    PYTHONPATH="$PROJECT_DIR" python scripts/generate_demo_data.py
fi

# Start backend
echo ""
echo "Starting backend server on http://localhost:8000..."
PYTHONPATH="$PROJECT_DIR" uvicorn api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ../frontend

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo ""
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend
echo ""
echo "Starting frontend server on http://localhost:5173..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  Servers started!"
echo "  - Backend:  http://localhost:8000"
echo "  - Frontend: http://localhost:5173"
echo "  - API Docs: http://localhost:8000/docs"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
