#!/bin/bash

# CoT Mapping System - Start Script
echo "🚀 Starting CoT Mapping System..."

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Run ./scripts/install.sh first"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Copy .env.example to .env and configure it"
    exit 1
fi

# Check if Ollama is running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "🤖 Starting Ollama..."
    ollama serve &
    sleep 3
else
    echo "✅ Ollama is already running"
fi

# Check if model is available
if ! ollama list | grep -q "llama3.1:8b"; then
    echo "📥 Downloading Ollama model..."
    ollama pull llama3.1:8b
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the FastAPI application
echo "🔥 Starting FastAPI server..."
echo "📊 Dashboard will be available at: http://localhost:8000/dashboard"
echo "📚 API docs will be available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000