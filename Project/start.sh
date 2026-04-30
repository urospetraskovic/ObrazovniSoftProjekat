#!/bin/bash

# Start SOLO Quiz Generator Application (Ollama + Flask backend + React frontend).
# Mirrors the manual flow documented in START_GUIDE.md.
# Designed for Git Bash on Windows.

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "========================================"
echo "SOLO Taxonomy Quiz Generator"
echo "========================================"
echo ""

# --- Prerequisites ---

if ! command -v node >/dev/null 2>&1; then
    echo "Error: Node.js is not installed (https://nodejs.org/)"
    exit 1
fi

if ! command -v powershell >/dev/null 2>&1 && ! command -v powershell.exe >/dev/null 2>&1; then
    echo "Error: PowerShell not found (needed to launch Ollama via ollama.ps1)"
    exit 1
fi

BACKEND_PY="$ROOT_DIR/backend/venv/Scripts/python.exe"
if [ ! -x "$BACKEND_PY" ]; then
    echo "Error: backend venv not found at $BACKEND_PY"
    echo "Create it with:  cd backend && python -m venv venv && venv/Scripts/python.exe -m pip install -r requirements.txt"
    exit 1
fi

# --- Cleanup on exit ---

OLLAMA_PID=""
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "Shutting down..."
    for pid in "$FRONTEND_PID" "$BACKEND_PID" "$OLLAMA_PID"; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    exit 0
}
trap cleanup INT TERM

# --- Ollama ---

echo "[1/3] Starting Ollama (via ollama.ps1)..."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ROOT_DIR/ollama.ps1" serve &
OLLAMA_PID=$!
sleep 3

# --- Backend ---

echo "[2/3] Starting backend (Flask API on :5000)..."
(cd "$ROOT_DIR/backend" && "$BACKEND_PY" app.py) &
BACKEND_PID=$!
sleep 3

# --- Frontend ---

echo "[3/3] Starting frontend (React dev server on :3000)..."
(cd "$ROOT_DIR/frontend" && npm start) &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "Services started!"
echo "  Ollama  (PID $OLLAMA_PID)   http://127.0.0.1:11435"
echo "  Backend (PID $BACKEND_PID)  http://localhost:5000"
echo "  Frontend(PID $FRONTEND_PID) http://localhost:3000"
echo ""
echo "Press Ctrl-C to stop all three."
echo "========================================"
echo ""

wait
