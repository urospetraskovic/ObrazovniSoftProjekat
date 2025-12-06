#!/bin/bash

# Start SOLO Quiz Generator Application

echo ""
echo "========================================"
echo "SOLO Taxonomy Quiz Generator"
echo "========================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    echo "Please install Python from https://python.org/"
    exit 1
fi

echo "Starting backend server..."
cd backend
python3 app.py &
BACKEND_PID=$!

sleep 3

echo "Starting frontend server..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "Services started!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:5000"
echo "========================================"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
