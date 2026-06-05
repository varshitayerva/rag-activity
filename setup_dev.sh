#!/bin/bash

echo "🚀 RAG Technical Support Copilot - Development Setup"
echo "======================================================"

# Check Python
echo "✓ Checking Python..."
python --version

# Create virtual environment
echo "✓ Setting up Python environment..."
cd backend
python -m venv venv
source venv/bin/activate || . venv/Scripts/activate  # Windows

# Install backend dependencies
echo "✓ Installing backend dependencies..."
pip install -r requirements.txt -q

# Check Node.js
echo "✓ Checking Node.js..."
node --version

# Install frontend dependencies
echo "✓ Installing frontend dependencies..."
cd ../frontend
npm install --silent

# Create .env file if it doesn't exist
echo "✓ Checking .env file..."
cd ..
if [ ! -f backend/.env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example backend/.env
    echo "📝 Please edit backend/.env with your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - DATABASE_URL"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit backend/.env with your API keys"
echo "2. Ensure PostgreSQL is running:"
echo "   createdb rag_db"
echo "   psql -d rag_db -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
echo "3. Ensure Redis is running (optional):"
echo "   redis-server"
echo "4. Start backend:"
echo "   cd backend"
echo "   source venv/bin/activate  # or venv/Scripts/activate on Windows"
echo "   python -m uvicorn app.main:app --reload --port 8000"
echo "5. Start frontend (in another terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo "6. Open http://localhost:3000 in your browser"
echo ""
