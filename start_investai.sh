#!/bin/bash
# InvestAI Complete - Startup Script

echo "🚀 Starting InvestAI Complete..."
echo ""

# Change to app directory
cd /data/inscesteAI

# Activate virtual environment
source venv/bin/activate

# Check dependencies
echo "Checking dependencies..."
pip list | grep -E "(fastapi|groq|yfinance|feedparser|APScheduler)" > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ Dependencies OK"
else
    echo "⚠ Installing dependencies..."
    pip install -r requirements.txt --quiet
fi

# Check database connection
echo "Checking database..."
python3 -c "
from api.database import execute_query
try:
    result = execute_query('SELECT 1')
    print('✓ Database connected')
except Exception as e:
    print(f'✗ Database error: {e}')
    exit(1)
"

# Start application
echo ""
echo "Starting InvestAI on port 8091..."
echo "Access: http://localhost:8091/"
echo ""
echo "Features available:"
echo "  - 🤖 Mentor Ativo (Action Cards)"
echo "  - 📊 Cenários ML (4 scenarios with projections)"
echo "  - 🎯 Watchlist with Semaphores"
echo "  - 💬 Chat IA (Groq llama-3.3-70b)"
echo "  - 📈 Radar de Mercado (10 indices + news)"
echo "  - 💰 Smart Money (volume anomalies + insiders)"
echo "  - 📋 Plano de Investimento"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run with uvicorn
exec /data/inscesteAI/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8091
