@echo off
REM Kautilya Setup Script for Windows
REM Automates complete project setup after git clone

echo ==================================================
echo 🚀 Kautilya Investment Advisor - Setup Script
echo ==================================================
echo.

REM Check Python version
echo 📋 Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python found
echo.

REM Create virtual environment
echo 🔧 Creating virtual environment...
if exist venv (
    echo ⚠️  Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    echo ✅ Virtual environment created
)
echo.

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated
echo.

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip -q
echo ✅ Pip upgraded
echo.

REM Install dependencies
echo 📥 Installing dependencies from requirements.txt...
pip install -r requirements.txt -q
echo ✅ Dependencies installed
echo.

REM Check for .env file
echo 🔐 Checking for .env file...
if not exist .env (
    echo ⚠️  .env file not found!
    echo 📝 Creating .env template...
    (
        echo # Google Gemini API Key
        echo GOOGLE_API_KEY=your_api_key_here
        echo.
        echo # Tavily API Key ^(for web search^)
        echo TAVILY_API_KEY=your_tavily_key_here
    ) > .env
    echo ✅ .env template created
    echo.
    echo ❗ IMPORTANT: Edit .env file and add your API keys:
    echo    1. Google Gemini API Key: https://aistudio.google.com/app/apikey
    echo    2. Tavily API Key: https://tavily.com/
    echo.
) else (
    echo ✅ .env file exists
    echo.
)

REM Initialize database
echo 💾 Initializing database...
python -c "from database import DatabaseManager; db = DatabaseManager('kautilya_production.db'); db.close()" 2>nul
echo ✅ Database initialized
echo.

REM Test imports
echo 🧪 Testing critical imports...
python -c "from graph_rl import build_rl_graph; from weight_manager import WeightManager; print('✅ All critical modules import successfully')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Some imports failed. Check dependencies.
)
echo.

REM Display completion message
echo ==================================================
echo ✅ Setup Complete!
echo ==================================================
echo.
echo 📝 Next Steps:
echo    1. Edit .env file with your API keys ^(if not done^)
echo    2. Activate virtual environment: venv\Scripts\activate.bat
echo    3. Run Streamlit app: streamlit run app.py
echo    4. Or run CLI: python main.py --symbol "HDFC Bank" --question "Should I invest?"
echo.
echo 📚 Documentation:
echo    - README.md: Project overview
echo    - PLAN.md: Implementation details
echo    - PROJECT_COMPLETE.md: Full project summary
echo.
echo 🎉 Happy investing with Kautilya!
echo ==================================================
pause
