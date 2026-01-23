"""
Personal information accessor for investment decisions.
Loads user profile from saved JSON file or provides defaults.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

from config import USER_PROFILE_FILE


def load_user_profile() -> Dict[str, Any]:
    """
    Load user profile from saved JSON file.
    Returns default profile if file doesn't exist.
    """
    profile_file = USER_PROFILE_FILE

    print(f"[DEBUG personal.py] Looking for profile at: {profile_file}")
    print(f"[DEBUG personal.py] File exists: {profile_file.exists()}")

    if profile_file.exists():
        try:
            with open(profile_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading profile: {e}")

    print("[DEBUG personal.py] Using default profile (file not found or error)")
    return get_default_profile()


def get_default_profile() -> Dict[str, Any]:
    """Return default profile structure when no profile exists"""
    return {
        "name": "Guest User",
        "age": 30,
        "email": "",
        "gender": "Prefer not to say",
        "occupation": "Not specified",
        "education": "Bachelor's Degree",
        "marital_status": "Single",
        "country": "India",
        "preferred_currency": "INR",
        "salary": 0,
        "monthly_take_home": 0,
        "savings_rate": 20,
        "net_worth": 0,
        "emergency_fund_months": 6,
        "epf_balance": 0,
        "ppf_balance": 0,
        "nps_balance": 0,
        "risk_tolerance": 5,
        "risk_label": "Moderate",
        "investment_experience": "Beginner",
        "portfolio_value": 0,
        "equity_allocation": 60,
        "mutual_fund_allocation": 20,
        "bonds_fd_allocation": 10,
        "cash_allocation": 7,
        "gold_allocation": 3,
        "investment_horizon": "5-10 years",
        "primary_goal": "Wealth Creation",
        "sip_monthly": 0,
        "trade_frequency": "Quarterly",
        "tax_regime": "New Regime",
        "profile_complete": False
    }


def personal_info(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get personal information for investment decisions.

    Args:
        user_id: Optional user identifier (for future multi-user support)

    Returns:
        Dictionary containing user's personal and financial information
    """
    profile = load_user_profile()
    
    # Debug logging to trace data flow
    print(f"[DEBUG personal.py] Loaded profile keys: {list(profile.keys())}")
    print(f"[DEBUG personal.py] Profile has holdings: {len(profile.get('holdings', []))} items")
    print(f"[DEBUG personal.py] Profile has mutual_funds: {len(profile.get('mutual_funds', []))} items")
    print(f"[DEBUG personal.py] Portfolio value: ₹{profile.get('portfolio_value', 0):,}")

    # Map profile fields to the expected format for the decision system
    return {
        "user_id": user_id or "default_user",
        "name": profile.get("name", "Guest User"),
        "age": profile.get("age", 30),
        "email": profile.get("email", ""),
        "phone": "",  # Not collected for privacy
        "address": f"{profile.get('country', 'India')}",
        "gender": profile.get("gender", "Prefer not to say"),
        "occupation": profile.get("occupation", "Not specified"),
        "education": profile.get("education", "Bachelor's Degree"),
        "marital_status": profile.get("marital_status", "Single"),
        "children": 0,
        "pets": 0,
        "country": profile.get("country", "India"),
        "preferred_currency": profile.get("preferred_currency", "INR"),
        "timezone": "Asia/Kolkata",
        "salary": profile.get("salary", 0),
        "monthly_take_home_estimate": profile.get("monthly_take_home", 0),
        "savings_rate": profile.get("savings_rate", 20) / 100,
        "net_worth_estimate": profile.get("net_worth", 0),
        "emergency_fund_months": profile.get("emergency_fund_months", 6),
        "epf_balance": profile.get("epf_balance", 0),
        "ppf_balance": profile.get("ppf_balance", 0),
        "nps_balance": profile.get("nps_balance", 0),
        "pf_account": {"epf_uan": None, "ppf_account_no": None, "nps_pran": None},
        "bank": {
            "primary_bank": "Not specified",
            "savings_account_last4": None,
        },
        "demat_account": {"broker": "Not specified", "client_id_last4": None},
        "risk_profile": {
            "risk_tolerance_score": profile.get("risk_tolerance", 5),
            "risk_label": profile.get("risk_label", "Moderate"),
            "investment_experience": profile.get("investment_experience", "Beginner"),
            "market_drop_reaction": profile.get("market_drop_reaction", "Hold and wait"),
            "notes": _generate_risk_notes(profile),
        },
        "portfolio_summary": {
            "total_value": profile.get("portfolio_value", 0),
            "allocation": {
                "equities": profile.get("equity_allocation", 60) / 100,
                "mutual_funds": profile.get("mutual_fund_allocation", 20) / 100,
                "bonds_fixed_deposits": profile.get("bonds_fd_allocation", 10) / 100,
                "cash": profile.get("cash_allocation", 7) / 100,
                "gold_etf": profile.get("gold_allocation", 3) / 100,
            },
            "diversification_score": _calculate_diversification_score(profile),
            "holdings": profile.get("holdings", []),
            "mutual_funds": profile.get("mutual_funds", []),
            "watchlist": profile.get("watchlist", []),
            "recent_transactions": profile.get("recent_transactions", []),
        },
        "indian_investment_accounts": {
            "demat": profile.get("portfolio_value", 0) > 0,
            "mutual_fund_direct_plans": profile.get("mutual_fund_allocation", 0) > 0,
            "ppf_active": profile.get("ppf_balance", 0) > 0,
            "epf_active": profile.get("epf_balance", 0) > 0,
            "nps_active": profile.get("nps_balance", 0) > 0,
            "sukanya_ppf": False,
        },
        "investment_goals": {
            "provided": profile.get("primary_goal") is not None,
            "primary_goal": profile.get("primary_goal", "Wealth Creation"),
            "time_horizon": profile.get("investment_horizon", "5-10 years"),
            "target_amounts": None,
            "notes": f"Primary goal: {profile.get('primary_goal', 'Wealth Creation')}",
        },
        "market_preferences": {
            "preferred_exchange": "NSE",
            "preferred_instruments": ["equities", "mutual_funds", "ppf", "nps", "gold_etf"],
            "preferred_sectors": profile.get("preferred_sectors", []),
            "avoid_sectors": profile.get("avoid_sectors", []),
            "trade_frequency": profile.get("trade_frequency", "Quarterly"),
            "sips_active": profile.get("sip_monthly", 0) > 0,
            "sip_monthly_amount_inr": profile.get("sip_monthly", 0),
        },
        "tax_profile": {
            "tax_regime_selected": profile.get("tax_regime", "New Regime"),
            "tax_slab_estimate": _estimate_tax_slab(profile.get("salary", 0)),
            "notes": "Tax-saving instruments: ELSS (80C), PPF (80C), NPS (80CCD), HRA exemptions.",
        },
        "profile_complete": profile.get("profile_complete", False),
    }


def _generate_risk_notes(profile: Dict) -> str:
    """Generate risk assessment notes based on profile"""
    age = profile.get("age", 30)
    risk = profile.get("risk_tolerance", 5)
    experience = profile.get("investment_experience", "Beginner")
    occupation = profile.get("occupation", "")

    notes = []

    # Age-based assessment
    if age < 30:
        notes.append("Young age allows for higher risk tolerance and longer recovery time.")
    elif age < 45:
        notes.append("Prime earning years suggest capacity for growth-oriented allocation.")
    elif age < 55:
        notes.append("Approaching retirement; consider gradually reducing equity exposure.")
    else:
        notes.append("Near/in retirement; capital preservation becomes more important.")

    # Risk tolerance alignment
    if risk <= 3:
        notes.append("Conservative profile - prioritize capital preservation.")
    elif risk <= 6:
        notes.append("Moderate profile - balance between growth and stability.")
    else:
        notes.append("Aggressive profile - higher equity allocation acceptable.")

    # Experience consideration
    if experience == "Beginner":
        notes.append("New to investing - recommend diversified funds over individual stocks.")

    return " ".join(notes)


def _calculate_diversification_score(profile: Dict) -> float:
    """Calculate portfolio diversification score (0-1)"""
    allocations = [
        profile.get("equity_allocation", 0),
        profile.get("mutual_fund_allocation", 0),
        profile.get("bonds_fd_allocation", 0),
        profile.get("cash_allocation", 0),
        profile.get("gold_allocation", 0),
    ]

    # Count non-zero allocations
    non_zero = sum(1 for a in allocations if a > 0)

    # Calculate Herfindahl-Hirschman Index (HHI) for concentration
    total = sum(allocations)
    if total == 0:
        return 0.0

    normalized = [a / total for a in allocations]
    hhi = sum(x ** 2 for x in normalized)

    # Convert HHI to diversification score (1 - HHI gives higher score for more diversified)
    # Scale to 0-1 range
    diversification = 1 - hhi

    # Boost score based on number of asset classes
    class_bonus = non_zero / 5 * 0.2

    return min(1.0, diversification + class_bonus)


def _estimate_tax_slab(salary: int) -> str:
    """Estimate tax slab based on salary (New Regime FY 2024-25)"""
    if salary <= 300000:
        return "Nil"
    elif salary <= 700000:
        return "5-10%"
    elif salary <= 1000000:
        return "10-15%"
    elif salary <= 1200000:
        return "15-20%"
    elif salary <= 1500000:
        return "20-25%"
    else:
        return "30%"


def get_investment_persona(user_id: Optional[str] = None) -> str:
    """
    Generate a comprehensive investment persona description for the LLM.

    Args:
        user_id: Optional user identifier

    Returns:
        String description of the user's investment persona with portfolio details
    """
    info = personal_info(user_id)

    if not info.get("profile_complete", False):
        return "User profile incomplete. Using conservative defaults for recommendations."

    age = info.get("age", 30)
    risk_label = info["risk_profile"]["risk_label"]
    experience = info["risk_profile"]["investment_experience"]
    goal = info["investment_goals"]["primary_goal"]
    horizon = info["investment_goals"]["time_horizon"]
    salary = info.get("salary", 0)
    portfolio_summary = info["portfolio_summary"]
    portfolio_value = portfolio_summary["total_value"]

    persona = f"""
=== INVESTOR PROFILE ===
Name: {info.get('name', 'User')}
Age: {age} years old
Occupation: {info.get('occupation', 'Not specified')}
Annual Income: ₹{salary:,}
Monthly Take-Home: ₹{info.get('monthly_take_home_estimate', 0):,}
Net Worth: ₹{info.get('net_worth_estimate', 0):,}

=== RISK PROFILE ===
Risk Tolerance: {risk_label} ({info["risk_profile"]["risk_tolerance_score"]}/10)
Experience Level: {experience}
Market Drop Reaction: {info["risk_profile"].get("market_drop_reaction", "Hold and wait")}

=== INVESTMENT GOALS ===
Primary Goal: {goal}
Time Horizon: {horizon}
Monthly SIP: ₹{info["market_preferences"]["sip_monthly_amount_inr"]:,}

=== SECTOR PREFERENCES ===
Preferred Sectors: {', '.join(info["market_preferences"]["preferred_sectors"]) or 'None specified'}
Sectors to Avoid: {', '.join(info["market_preferences"]["avoid_sectors"]) or 'None'}

=== CURRENT PORTFOLIO (₹{portfolio_value:,}) ===
"""

    # Add holdings details
    holdings = portfolio_summary.get("holdings", [])
    if holdings:
        persona += "\nSTOCK HOLDINGS:\n"
        # Separate gainers and losers for easy reference
        gainers = [h for h in holdings if h.get("gain_loss_pct", 0) > 0]
        losers = [h for h in holdings if h.get("gain_loss_pct", 0) < 0]

        if losers:
            persona += "📉 LOSING POSITIONS (Need Attention):\n"
            for h in sorted(losers, key=lambda x: x.get("gain_loss_pct", 0)):
                persona += f"  - {h['name']} ({h['ticker']}): ₹{h.get('value_inr', 0):,} | "
                persona += f"Loss: {h.get('gain_loss_pct', 0):.1f}% | "
                persona += f"Held: {h.get('holding_period_months', 0)} months | "
                persona += f"Sector: {h.get('sector', 'Unknown')}\n"

        if gainers:
            persona += "📈 PROFITABLE POSITIONS:\n"
            for h in sorted(gainers, key=lambda x: x.get("gain_loss_pct", 0), reverse=True):
                persona += f"  - {h['name']} ({h['ticker']}): ₹{h.get('value_inr', 0):,} | "
                persona += f"Gain: +{h.get('gain_loss_pct', 0):.1f}% | "
                persona += f"Held: {h.get('holding_period_months', 0)} months | "
                persona += f"Sector: {h.get('sector', 'Unknown')}\n"

    # Add mutual funds
    mutual_funds = portfolio_summary.get("mutual_funds", [])
    if mutual_funds:
        persona += "\nMUTUAL FUND HOLDINGS:\n"
        for mf in mutual_funds:
            persona += f"  - {mf['name']}: ₹{mf.get('value_inr', 0):,} | "
            persona += f"SIP: ₹{mf.get('sip_amount', 0):,}/month | "
            persona += f"1Y Return: {mf.get('returns_1yr_pct', 0):.1f}%\n"

    # Add watchlist
    watchlist = portfolio_summary.get("watchlist", [])
    if watchlist:
        persona += f"\nWATCHLIST: {', '.join(watchlist)}\n"

    # Add recent transactions
    transactions = portfolio_summary.get("recent_transactions", [])
    if transactions:
        persona += "\nRECENT TRANSACTIONS:\n"
        for t in transactions[:5]:  # Last 5 transactions
            persona += f"  - {t['date']}: {t['action']} {t.get('quantity', 0)} {t['ticker']} @ ₹{t.get('price', 0)}\n"

    # Key considerations based on profile
    persona += f"""
=== KEY CONSIDERATIONS ===
{info["risk_profile"]["notes"]}

IMPORTANT FOR RECOMMENDATIONS:
- User is {age} years old with {horizon} investment horizon
- Risk appetite is {risk_label} - {'can handle volatility' if info["risk_profile"]["risk_tolerance_score"] >= 7 else 'prefers stability'}
- Has losing positions that may need review
- Focus on {goal} as primary objective
"""
    return persona.strip()


if __name__ == "__main__":
    # Test the functions
    print("Loading user profile...")
    profile = personal_info()
    print(f"\nUser: {profile['name']}")
    print(f"Age: {profile['age']}")
    print(f"Risk: {profile['risk_profile']['risk_label']}")
    print(f"Portfolio: Rs.{profile['portfolio_summary']['total_value']:,}")

    print("\n" + "=" * 50)
    print("Investment Persona:")
    persona = get_investment_persona()
    # Handle Unicode for Windows console
    print(persona.replace('₹', 'Rs.'))
