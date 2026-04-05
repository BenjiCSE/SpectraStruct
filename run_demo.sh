#!/bin/bash
echo "Starting DiamondHacks demo..."
echo ""
echo "Step 1: Starting FastAPI backend on :8000"
DEMO_MODE=true uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"
echo ""
echo "Step 2: Starting Next.js frontend on :3000"
cd frontend && npm run dev &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "Open: http://localhost:3000"
echo "API:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."
wait
