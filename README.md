# Kautilya - RL-Enhanced Investment Decision System

An intelligent NIFTY50 investment advisor using multi-agent analysis with Thompson Sampling reinforcement learning for adaptive weight optimization.

## ⚡ Quick Start (New Users)

### Clone and Setup - One Command!

**Linux/Mac:**
```bash
git clone https://github.com/Jatin-Khanijoan/investment-decision-helper.git && cd investment-decision-helper && chmod +x setup.sh && ./setup.sh
```

**Windows:**
```cmd
git clone https://github.com/Jatin-Khanijoan/investment-decision-helper.git && cd investment-decision-helper && setup.bat
```

### Then:
1. **Add API Keys**: Edit `.env` file with your Gemini and Tavily API keys
2. **Activate Environment**: 
   - Linux/Mac: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate.bat`
3. **Run**: `streamlit run app.py`
4. **Open**: http://localhost:8501

That's it! 🎉

---

## 🚀 Detailed Installation

### Prerequisites
- Python 3.8 or higher
- Git
- Google Gemini API key ([Get here](https://aistudio.google.com/app/apikey))
- Tavily API key ([Get here](https://tavily.com/))

### Step-by-Step Installation

#### Linux/Mac
```bash
# Clone the repository
git clone https://github.com/Jatin-Khanijoan/investment-decision-helper.git
cd investment-decision-helper

# Run setup script
chmod +x setup.sh
./setup.sh

# Edit .env file with your API keys
nano .env  # or use your preferred editor

# Activate virtual environment
source venv/bin/activate

# Run the application
streamlit run app.py
```

#### Windows
```cmd
# Clone the repository
git clone https://github.com/Jatin-Khanijoan/investment-decision-helper.git
cd investment-decision-helper

# Run setup script
setup.bat

# Edit .env file with your API keys
notepad .env

# Activate virtual environment
venv\Scripts\activate.bat

# Run the application
streamlit run app.py
```

## 📋 Features

### Core Capabilities
- **15 Specialized Agents**: Macro, company, policy, and data quality analysis
- **RL-Enhanced Weighting**: Thompson Sampling adapts to market conditions
- **Regime Detection**: Classifies inflation, interest rates, and sentiment
- **Full Explainability**: Shows why agents are weighted as they are
- **5 Years of Data**: 1,239 trading days (2021-2026) of NIFTY 50 data
- **Interactive Dashboard**: Streamlit UI with visualizations

### Technical Stack
- **LangGraph**: Multi-agent orchestration
- **Google Gemini**: LLM-powered decision making
- **Thompson Sampling**: Bayesian RL for weight optimization
- **SQLite**: Persistent RL state storage
- **Streamlit**: Interactive web interface

## 📊 System Architecture

```
User Query → Personal Context → 15 Agents (Parallel) → RL Weighting → 
Priority Grouping (HIGH/MEDIUM/LOW) → LLM Decision → Explainable Output
```

### Key Components

**Agents** (15 total):
- Macro: Inflation, Interest Rates, GDP Growth
- Policy: Regulatory Changes
- Company: Historical, Current, Financial Performance
- Risk: Earnings Volatility, Sector Shocks, Governance
- Quality: Missing Data Detection, Completeness

**RL System**:
- Thompson Sampling learner
- Regime-specific weight adaptation
- 70% RL / 30% expert blend
- Database-backed persistence

**Explainability**:
- Plain-language regime descriptions
- Weight rationale for each agent
- RL learning proof statistics
- Priority-grouped LLM prompts

## 🎯 Usage

### Streamlit Web App
```bash
streamlit run app.py
```
Visit http://localhost:8501

### Command Line
```bash
python main.py --symbol "HDFC Bank" --question "Should I invest for 6 months?"
```

### Using RL-Enhanced Graph Programmatically
```python
from graph_rl import build_rl_graph
import asyncio

graph = build_rl_graph()

state = {
    "user_id": "user123",
    "question": "Should I invest in HDFC Bank?",
    "symbol": "HDFC Bank",
    "sector": "Banking",
    "agent_outputs": {},
    "citations": [],
    "errors": []
}

result = asyncio.run(graph.ainvoke(state))
decision = result["decision_json"]

print(f"Decision: {decision['decision']}")
print(f"Confidence: {decision['confidence']}")
print(f"Regime: {decision['regime_detected']}")
```

## 📁 Project Structure

```
investment-decision-helper/
├── setup.sh                 # Linux/Mac setup script
├── setup.bat                # Windows setup script
├── requirements.txt         # Python dependencies
├── .env                     # API keys (create from template)
│
├── app.py                   # Streamlit web interface
├── main.py                  # CLI entry point
├── graph_rl.py              # RL-enhanced decision graph ⭐
├── graph.py                 # Original decision graph
│
├── agents/                  # 15 specialized agents
│   ├── macro_agents.py
│   ├── company_agents.py
│   ├── news_policy_agents.py
│   └── data_quality_agents.py
│
├── weight_manager.py        # RL weight orchestration
├── rl_learner.py            # Thompson Sampling learner
├── regime_detector.py       # Market regime classification
├── explainer.py             # Weight explanations
├── reward_calculator.py     # RL reward function
│
├── data_accessor.py         # NIFTY 50 data loader
├── database.py              # SQLite persistence
├── technical_indicators.py  # RSI, MACD, volatility
│
├── backtester.py            # Backtesting engine
├── evaluator.py             # Statistical analysis
├── generate_visualizations.py
│
└── pages/
    └── 3_RL_Performance.py  # Backtest results dashboard
```

## 🔬 Testing

### Run Full Backtest
```bash
python run_full_backtest.py
```
Simulates 450 decisions (3 systems × 75 train + 75 test)

### Generate Visualizations
```bash
python generate_visualizations.py
```
Creates accuracy comparisons, regime heatmaps, etc.

### Test RL Pipeline
```bash
python graph_rl.py
```
Runs end-to-end test with all components

## 📈 Performance

Based on backtesting with 1,239 days of NIFTY 50 data (2021-2026):

**Training Phase** (2021-2024, 743 days):
- Equal Weights: 60.0% accuracy
- Expert Weights: 57.3% accuracy  
- RL Weights: 54.7% accuracy (learning phase)

**Testing Phase** (2024-2026, 496 days):
- Equal Weights: 82.7% accuracy
- Expert Weights: 81.3% accuracy
- RL Weights: 81.3% accuracy

*Note: Results similar due to stable market conditions in test period. RL shows advantage in volatile regimes (see backtest_results_summary.md).*

## 🔧 Configuration

### API Keys (.env)
```
GOOGLE_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_key
```

### RL Parameters (weight_manager.py)
- `rl_blend_ratio`: 0.7 (70% RL, 30% expert)
- `uniform_prior`: α=1, β=1 (Thompson Sampling)
- `regime_multipliers`: Defined in weights_config.py

## 📚 Documentation

- **PLAN.md**: Original implementation plan (Phases 1-10)
- **PROJECT_COMPLETE.md**: Comprehensive project summary
- **phase6_implementation_plan.md**: Backtesting approach
- **phase7_walkthrough.md**: Explainability features
- **phase8_complete.md**: Evaluation results
- **backtest_results_summary.md**: Detailed backtest analysis

## 🐛 Troubleshooting

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database Issues
```bash
# Reinitialize database
rm kautilya_production.db
python -c "from database import DatabaseManager; DatabaseManager('kautilya_production.db').close()"
```

### API Key Errors
- Ensure .env file exists and contains valid keys
- Check key format (no quotes needed)
- Verify keys at provider dashboards

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- LangGraph for multi-agent orchestration
- Google Gemini for LLM capabilities
- Thompson Sampling algorithm for RL
- NIFTY 50 for historical market data

## 📞 Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/Jatin-Khanijoan/investment-decision-helper/issues)
- Documentation: See docs/ folder
- Example Usage: See example_usage.sh

---

**⚠️ Disclaimer**: This is an educational project. Investment decisions should be made with professional financial advice. Past performance does not guarantee future results.
