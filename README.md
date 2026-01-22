# Kautilya: NIFTY50 Multi-Agent Investment Decision Helper

A minimal, production-lean LangGraph system that aggregates macroeconomic, policy, and company-specific signals to provide structured investment decisions for NIFTY50 stocks.

## Features

- **18 Parallel Agents**: Macro signals (inflation, rates, GDP), policy changes, company-specific data (earnings volatility, AGM, governance, shocks, historical/current data, financial performance), plus data quality assessment and missing data detection
- **Real-time Web Search**: Uses Tavily API for live data from trusted financial sources
- **Strict Source Validation**: Only accepts data from verified domains (RBI, SEBI, NSE, BSE, major financial publications)
- **Gemini 2.5 Integration**: Advanced reasoning model with CoT capabilities
- **Personalization**: User context integration from `personal.py`
- **NIFTY50 Validation**: Ensures only valid NIFTY50 symbols are processed
- **Intelligent Data Gap Detection**: Automatically identifies missing information and searches for additional data
- **File Logging**: Comprehensive logging stored in `kautilya.log` for debugging and analysis

## Installation

```bash
pip install -r requirements.txt
```

## API Keys Required

Get API keys from:

- [Google AI Studio](https://makersuite.google.com/app/apikey) for Gemini
- [Tavily](https://tavily.com/) for web search

Set environment variables:

```bash
export GEMINI_API_KEY="your-gemini-key"
export TAVILY_API_KEY="your-tavily-key"
export GEMINI_MODEL="gemini-2.0-flash-thinking-exp-1219"  # Optional
```

## Usage

```bash
python main.py \
  --user_id U123 \
  --question "Should I increase allocation to RELIANCE for the next 6 months?" \
  --symbol RELIANCE \
  --sector Energy
```

## Output Format

```json
{
  "decision": "BUY | HOLD | SELL",
  "confidence": 0.0-1.0,
  "horizon": "short | medium | long",
  "why": "3-6 bullet points explaining the decision and noting any data limitations",
  "key_factors": ["inflation", "interest_rates", ...],
  "risks": ["valuation_shock", "sector_risk", ...],
  "personalization_considerations": ["risk_tolerance", ...],
  "used_agents": ["inflation", "interest_rates", ...],
  "citations": ["https://rbi.org.in", ...]
}
```

## Source Validation Rules

### Macro Data

- RBI (rbi.org.in)
- Ministry of Finance (finmin.nic.in)
- MOSPI (mospi.gov.in)
- Major economic publications

### News & Policy

- Government sites (pib.gov.in, finmin.nic.in)
- Regulatory bodies (sebi.gov.in, nsdl.co.in)
- Financial news (economictimes.indiatimes.com, business-standard.com)

### Company Data

- NSE/BSE (nseindia.com, bseindia.com)
- Company official websites
- Bloomberg, Reuters, CNBC
- Moneycontrol, Livemint, BusinessLine

## Architecture

- **LangGraph**: Orchestrates 18 parallel agents with conditional re-decision
- **Pydantic**: Type-safe data models
- **Async Execution**: Concurrent agent processing
- **Fallback Handling**: Graceful degradation when APIs unavailable

## Testing

```bash
pytest -q tests/
```

## Logs

All agent activities and decision processes are logged to `kautilya.log` for debugging and analysis.

## Project Structure

```
kautilya/
├── main.py              # CLI entry point
├── graph.py             # LangGraph orchestration
├── llm.py               # Gemini integration
├── state.py             # Type definitions
├── personal.py          # User personalization
├── providers/
│   ├── search_utils.py  # Tavily search + validation
│   ├── macro.py         # Inflation, rates, GDP
│   ├── news.py          # Policy changes
│   ├── company.py       # Company-specific data
│   └── utils.py         # NIFTY50 validation
├── agents/              # Agent implementations
│   ├── macro_agents.py          # Economic indicators (3 agents)
│   ├── news_policy_agents.py    # Policy changes (1 agent)
│   ├── company_agents.py        # Company-specific data (9 agents)
│   ├── data_quality_agents.py   # Data quality assessment (3 agents)
│   └── missing_data_search_agent.py # Missing data detection & search (1 agent)
├── tests/               # Test suite
└── stocks.json          # NIFTY50 company list
```

## License

MIT
