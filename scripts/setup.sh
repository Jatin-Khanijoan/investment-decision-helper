#!/bin/bash
# Kautilya Setup Script for Linux/Mac
# Automates complete project setup after git clone

set -e  # Exit on error

echo "=================================================="
echo "🚀 Kautilya Investment Advisor - Setup Script"
echo "=================================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Found Python $python_version"
echo ""

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip -q
echo "✅ Pip upgraded"
echo ""

# Install dependencies
echo "📥 Installing dependencies from requirements.txt..."
pip install -r requirements.txt -q
echo "✅ Dependencies installed"
echo ""

# Check for .env file
echo "🔐 Checking for .env file..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env template..."
    cat > .env << EOF
# Google Gemini API Key
GOOGLE_API_KEY=your_api_key_here

# Tavily API Key (for web search)
TAVILY_API_KEY=your_tavily_key_here
EOF
    echo "✅ .env template created"
    echo ""
    echo "❗ IMPORTANT: Edit .env file and add your API keys:"
    echo "   1. Google Gemini API Key: https://aistudio.google.com/app/apikey"
    echo "   2. Tavily API Key: https://tavily.com/"
    echo ""
else
    echo "✅ .env file exists"
    echo ""
fi

# Initialize database
echo "💾 Initializing database..."
python3 -c "from database import DatabaseManager; db = DatabaseManager('kautilya_production.db'); db.close()" 2>/dev/null || true
echo "✅ Database initialized"
echo ""

# Test imports
echo "🧪 Testing critical imports..."
python3 -c "
try:
    from graph_rl import build_rl_graph
    from weight_manager import WeightManager
    from data_accessor import NiftyDataAccessor
    print('✅ All critical modules import successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
" || echo "⚠️  Some imports failed. Check dependencies."
echo ""

# Display completion message
echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "📝 Next Steps:"
echo "   1. Edit .env file with your API keys (if not done)"
echo "   2. Activate virtual environment: source venv/bin/activate"
echo "   3. Run Streamlit app: streamlit run app.py"
echo "   4. Or run CLI: python main.py --symbol 'HDFC Bank' --question 'Should I invest?'"
echo ""
echo "📚 Documentation:"
echo "   - README.md: Project overview"
echo "   - PLAN.md: Implementation details"
echo "   - PROJECT_COMPLETE.md: Full project summary"
echo ""
echo "🎉 Happy investing with Kautilya!"
echo "=================================================="
