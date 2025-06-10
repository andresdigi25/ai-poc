#!/bin/bash

# CoT Mapping System - Installation Script
echo "🚀 Installing CoT Mapping System..."

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
required_version="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    echo "❌ Python 3.8+ is required. Please install Python 3.8 or later."
    exit 1
fi

echo "✅ Python version: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads backups logs static/css static/js static/images templates n8n-workflows

# Copy environment file
if [ ! -f .env ]; then
    echo "⚙️ Creating environment file..."
    cp .env.example .env
    echo "📝 Please edit .env file with your email credentials"
fi

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "
from database import init_db
init_db()
print('Database initialized successfully')
"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "🤖 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    
    echo "📥 Downloading Ollama model..."
    ollama pull llama3.1:8b
else
    echo "✅ Ollama already installed"
    
    # Check if model exists
    if ! ollama list | grep -q "llama3.1:8b"; then
        echo "📥 Downloading Ollama model..."
        ollama pull llama3.1:8b
    else
        echo "✅ Ollama model already downloaded"
    fi
fi

# Check if Node.js is installed for n8n (optional)
if command -v npm &> /dev/null; then
    echo "🔄 Node.js found. You can install n8n with: npm install -g n8n"
else
    echo "⚠️ Node.js not found. Install it to use n8n automation: https://nodejs.org/"
fi

# Make scripts executable
chmod +x scripts/*.sh

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your email credentials"
echo "2. Run: ./scripts/start.sh"
echo "3. Open: http://localhost:8000/dashboard"
echo ""
echo "📧 For email automation, configure your credentials in the dashboard"
echo "🤖 For n8n workflow automation, install n8n and import the workflow"
echo ""