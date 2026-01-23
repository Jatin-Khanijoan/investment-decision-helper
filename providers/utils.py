import json
import sys
from pathlib import Path

# Add parent directory for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import STOCKS_FILE

NIFTY50_SYMBOLS = {
    "Reliance Industries": "RELIANCE",
    "HDFC Bank": "HDFCBANK",
    "Bharti Airtel": "BHARTIARTL",
    "Tata Consultancy Services": "TCS",
    "ICICI Bank": "ICICIBANK",
    "State Bank of India": "SBIN",
    "Bajaj Finance": "BAJFINANCE",
    "Infosys": "INFY",
    "Hindustan Unilever": "HINDUNILVR",
    "ITC": "ITC",
    "Larsen & Toubro": "LT",
    "Maruti Suzuki": "MARUTI",
    "Mahindra & Mahindra": "M&M",
    "Kotak Bank": "KOTAKBANK",
    "Sun Pharmaceutical": "SUNPHARMA",
    "HCL Technologies": "HCLTECH",
    "UltraTech Cement": "ULTRACEMCO",
    "Axis Bank": "AXISBANK",
    "Bajaj Finserv": "BAJAJFINSV",
    "Eternal": "ETERNAL",
    "NTPC": "NTPC",
    "Adani Ports & SEZ": "ADANIPORTS",
    "Titan": "TITAN",
    "Adani Enterprises": "ADANIENT",
    "Oil & Natural Gas Corporation": "ONGC",
    "Bharat Electronics": "BEL",
    "JSW Steel": "JSWSTEEL",
    "Power Grid Corporation of India": "POWERGRID",
    "Wipro": "WIPRO",
    "Tata Motors": "TATAMOTORS",
    "Bajaj Auto": "BAJAJ-AUTO",
    "Coal India": "COALINDIA",
    "Asian Paints": "ASIANPAINT",
    "Nestle": "NESTLEIND",
    "Tata Steel": "TATASTEEL",
    "Jio Financial Services": "JIOFIN",
    "Grasim Industries": "GRASIM",
    "Eicher Motors": "EICHERMOT",
    "SBI Life Insurance": "SBILIFE",
    "Trent": "TRENT",
    "HDFC Life Insurance": "HDFCLIFE",
    "Hindalco Industries": "HINDALCO",
    "Tech Mahindra": "TECHM",
    "Cipla": "CIPLA",
    "Shriram Finance": "SHRIRAMFIN",
    "Tata Consumer Products": "TATACONSUM",
    "Apollo Hospitals": "APOLLOHOSP",
    "Hero Motocorp": "HEROMOTOCO",
    "Dr Reddys Laboratories": "DRREDDY",
    "Indusind Bank": "INDUSINDBK",
}


def load_universe(path: str = None) -> dict[str, str]:
    stocks_path = Path(path) if path else STOCKS_FILE
    if stocks_path.exists():
        with open(stocks_path) as f:
            companies = json.load(f)
            return {NIFTY50_SYMBOLS.get(c, c): c for c in companies}
    return NIFTY50_SYMBOLS


def validate_symbol(symbol: str, universe: dict) -> bool:
    # Check both keys and values since universe can be symbol->name or name->symbol
    return symbol in universe or symbol in universe.values()
