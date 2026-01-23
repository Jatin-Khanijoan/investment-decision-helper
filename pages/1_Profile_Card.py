"""
Profile Card - User Profile Input for Investment Decisions
Collects user information to personalize investment recommendations.
"""
import streamlit as st
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import USER_PROFILE_FILE

st.set_page_config(page_title="Profile Card", page_icon="👤", layout="wide")

# Initialize session state for profile
def get_default_profile():
    """Return default empty profile structure"""
    return {
        "name": "",
        "age": 30,
        "email": "",
        "gender": "Prefer not to say",
        "occupation": "",
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

def load_profile():
    """Load profile from file or return default"""
    if USER_PROFILE_FILE.exists():
        try:
            with open(USER_PROFILE_FILE, 'r') as f:
                saved = json.load(f)
                # Merge with defaults to handle any missing keys
                default = get_default_profile()
                default.update(saved)
                return default
        except:
            return get_default_profile()
    return get_default_profile()

def save_profile(profile):
    """Save profile to file"""
    # Ensure parent directory exists
    USER_PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USER_PROFILE_FILE, 'w') as f:
        json.dump(profile, f, indent=2)

# Load profile into session state
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = load_profile()

st.title("👤 Profile Card")
st.markdown("*Complete your profile to get personalized investment recommendations*")

# Profile completion indicator
profile = st.session_state.user_profile
required_fields = ['name', 'age', 'occupation', 'salary', 'risk_tolerance']
completed = sum(1 for f in required_fields if profile.get(f))
completion_pct = int((completed / len(required_fields)) * 100)

st.progress(completion_pct / 100)
st.caption(f"Profile {completion_pct}% complete")

# Create tabs for different profile sections
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Basic Info",
    "Financial Status",
    "Risk Profile",
    "Portfolio",
    "Goals & Preferences"
])

with tab1:
    st.subheader("Personal Information")

    col1, col2 = st.columns(2)

    with col1:
        profile['name'] = st.text_input(
            "Full Name *",
            value=profile.get('name', ''),
            help="Your full name"
        )

        profile['age'] = st.number_input(
            "Age *",
            min_value=18,
            max_value=100,
            value=profile.get('age', 30),
            help="Your current age"
        )

        profile['gender'] = st.selectbox(
            "Gender",
            options=["Male", "Female", "Other", "Prefer not to say"],
            index=["Male", "Female", "Other", "Prefer not to say"].index(
                profile.get('gender', 'Prefer not to say')
            )
        )

        profile['email'] = st.text_input(
            "Email",
            value=profile.get('email', ''),
            help="Your email address"
        )

    with col2:
        profile['occupation'] = st.text_input(
            "Occupation *",
            value=profile.get('occupation', ''),
            help="Your current job/profession"
        )

        profile['education'] = st.selectbox(
            "Education Level",
            options=[
                "High School",
                "Bachelor's Degree",
                "Master's Degree",
                "Doctorate",
                "Professional Certification",
                "Other"
            ],
            index=[
                "High School", "Bachelor's Degree", "Master's Degree",
                "Doctorate", "Professional Certification", "Other"
            ].index(profile.get('education', "Bachelor's Degree"))
        )

        profile['marital_status'] = st.selectbox(
            "Marital Status",
            options=["Single", "Married", "Divorced", "Widowed"],
            index=["Single", "Married", "Divorced", "Widowed"].index(
                profile.get('marital_status', 'Single')
            )
        )

        profile['country'] = st.selectbox(
            "Country",
            options=["India", "USA", "UK", "Other"],
            index=["India", "USA", "UK", "Other"].index(
                profile.get('country', 'India')
            )
        )

with tab2:
    st.subheader("Financial Information")

    col1, col2 = st.columns(2)

    with col1:
        profile['salary'] = st.number_input(
            "Annual Salary (INR) *",
            min_value=0,
            max_value=100000000,
            value=profile.get('salary', 0),
            step=100000,
            help="Your annual income before taxes"
        )

        profile['monthly_take_home'] = st.number_input(
            "Monthly Take-Home (INR)",
            min_value=0,
            max_value=10000000,
            value=profile.get('monthly_take_home', 0),
            step=5000,
            help="Monthly income after taxes"
        )

        profile['savings_rate'] = st.slider(
            "Savings Rate (%)",
            min_value=0,
            max_value=80,
            value=profile.get('savings_rate', 20),
            help="Percentage of income you save monthly"
        )

        profile['net_worth'] = st.number_input(
            "Estimated Net Worth (INR)",
            min_value=0,
            max_value=1000000000,
            value=profile.get('net_worth', 0),
            step=100000,
            help="Total assets minus liabilities"
        )

    with col2:
        profile['emergency_fund_months'] = st.number_input(
            "Emergency Fund (Months of Expenses)",
            min_value=0,
            max_value=24,
            value=profile.get('emergency_fund_months', 6),
            help="How many months can you survive without income?"
        )

        st.markdown("**Retirement Account Balances (INR)**")

        profile['epf_balance'] = st.number_input(
            "EPF Balance",
            min_value=0,
            value=profile.get('epf_balance', 0),
            step=10000
        )

        profile['ppf_balance'] = st.number_input(
            "PPF Balance",
            min_value=0,
            value=profile.get('ppf_balance', 0),
            step=10000
        )

        profile['nps_balance'] = st.number_input(
            "NPS Balance",
            min_value=0,
            value=profile.get('nps_balance', 0),
            step=10000
        )

with tab3:
    st.subheader("Risk Profile Assessment")

    st.markdown("""
    Understanding your risk tolerance helps us recommend appropriate investments.
    Answer the following questions honestly.
    """)

    col1, col2 = st.columns(2)

    with col1:
        profile['risk_tolerance'] = st.slider(
            "Risk Tolerance (1-10) *",
            min_value=1,
            max_value=10,
            value=profile.get('risk_tolerance', 5),
            help="1 = Very Conservative, 10 = Very Aggressive"
        )

        # Display risk label
        risk_labels = {
            (1, 2): ("Very Conservative", "You prefer guaranteed returns over growth"),
            (3, 4): ("Conservative", "You accept minimal risk for moderate returns"),
            (5, 6): ("Moderate", "You balance risk and return"),
            (7, 8): ("Aggressive", "You accept higher risk for higher returns"),
            (9, 10): ("Very Aggressive", "You maximize growth potential")
        }

        for range_tuple, (label, desc) in risk_labels.items():
            if profile['risk_tolerance'] in range(range_tuple[0], range_tuple[1] + 1):
                st.info(f"**{label}**: {desc}")
                profile['risk_label'] = label
                break

        profile['investment_experience'] = st.selectbox(
            "Investment Experience",
            options=["Beginner", "Intermediate", "Advanced", "Expert"],
            index=["Beginner", "Intermediate", "Advanced", "Expert"].index(
                profile.get('investment_experience', 'Beginner')
            )
        )

    with col2:
        st.markdown("**How would you react if your portfolio dropped 20%?**")
        reaction = st.radio(
            "Market Drop Reaction",
            options=[
                "Sell everything immediately",
                "Sell some to reduce risk",
                "Hold and wait",
                "Buy more at lower prices"
            ],
            index=2,
            label_visibility="collapsed"
        )
        profile['market_drop_reaction'] = reaction

        st.markdown("**Investment Time Horizon**")
        profile['investment_horizon'] = st.selectbox(
            "Time Horizon",
            options=["< 1 year", "1-3 years", "3-5 years", "5-10 years", "10+ years"],
            index=["< 1 year", "1-3 years", "3-5 years", "5-10 years", "10+ years"].index(
                profile.get('investment_horizon', '5-10 years')
            ),
            label_visibility="collapsed"
        )

with tab4:
    st.subheader("Current Portfolio")

    col1, col2 = st.columns(2)

    with col1:
        profile['portfolio_value'] = st.number_input(
            "Total Portfolio Value (INR)",
            min_value=0,
            value=profile.get('portfolio_value', 0),
            step=50000,
            help="Total value of your investments"
        )

        st.markdown("**Asset Allocation (%)**")

        profile['equity_allocation'] = st.slider(
            "Equities (Stocks)",
            min_value=0,
            max_value=100,
            value=profile.get('equity_allocation', 60)
        )

        profile['mutual_fund_allocation'] = st.slider(
            "Mutual Funds",
            min_value=0,
            max_value=100,
            value=profile.get('mutual_fund_allocation', 20)
        )

        profile['bonds_fd_allocation'] = st.slider(
            "Bonds / Fixed Deposits",
            min_value=0,
            max_value=100,
            value=profile.get('bonds_fd_allocation', 10)
        )

    with col2:
        profile['cash_allocation'] = st.slider(
            "Cash / Savings",
            min_value=0,
            max_value=100,
            value=profile.get('cash_allocation', 7)
        )

        profile['gold_allocation'] = st.slider(
            "Gold / Commodities",
            min_value=0,
            max_value=100,
            value=profile.get('gold_allocation', 3)
        )

        # Show allocation total
        total_allocation = (
            profile['equity_allocation'] +
            profile['mutual_fund_allocation'] +
            profile['bonds_fd_allocation'] +
            profile['cash_allocation'] +
            profile['gold_allocation']
        )

        if total_allocation != 100:
            st.warning(f"Total allocation: {total_allocation}% (should be 100%)")
        else:
            st.success("Total allocation: 100%")

    # Stock Holdings Section
    st.markdown("---")
    st.subheader("📊 Stock Holdings")
    st.caption("Add your current stock holdings for personalized recommendations")

    # Initialize holdings in profile if not exists
    if 'holdings' not in profile:
        profile['holdings'] = []

    # Display existing holdings
    if profile['holdings']:
        st.markdown("**Your Current Holdings:**")
        for i, holding in enumerate(profile['holdings']):
            with st.expander(f"{holding.get('name', 'Stock')} ({holding.get('ticker', '')})", expanded=False):
                col_h1, col_h2, col_h3 = st.columns(3)
                with col_h1:
                    gain_loss = holding.get('gain_loss_pct', 0)
                    color = "green" if gain_loss >= 0 else "red"
                    st.markdown(f"**Value:** ₹{holding.get('value_inr', 0):,}")
                    st.markdown(f"**Gain/Loss:** <span style='color:{color}'>{gain_loss:+.1f}%</span>", unsafe_allow_html=True)
                with col_h2:
                    st.markdown(f"**Qty:** {holding.get('quantity', 0)}")
                    st.markdown(f"**Avg Buy:** ₹{holding.get('avg_buy_price', 0):,}")
                with col_h3:
                    st.markdown(f"**Current:** ₹{holding.get('current_price', 0):,}")
                    st.markdown(f"**Sector:** {holding.get('sector', 'N/A')}")

                if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                    profile['holdings'].pop(i)
                    st.session_state.user_profile = profile
                    st.rerun()

    # Add new holding form
    st.markdown("**Add New Holding:**")
    with st.form("add_holding_form"):
        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            new_ticker = st.text_input("Ticker Symbol", placeholder="e.g., TCS.NS, RELIANCE.NS")
            new_name = st.text_input("Company Name", placeholder="e.g., Tata Consultancy Services")

        with col_a2:
            new_sector = st.selectbox(
                "Sector",
                options=["IT", "Banking", "Pharma", "FMCG", "Auto", "Energy",
                         "Infrastructure", "Telecom", "Metals", "Real Estate", "Other"]
            )
            new_quantity = st.number_input("Quantity", min_value=1, value=10)

        with col_a3:
            new_avg_price = st.number_input("Avg Buy Price (INR)", min_value=1, value=100)
            new_current_price = st.number_input("Current Price (INR)", min_value=1, value=100)
            new_holding_months = st.number_input("Holding Period (Months)", min_value=0, value=6)

        submitted = st.form_submit_button("➕ Add Holding", use_container_width=True)

        if submitted and new_ticker and new_name:
            value_inr = new_quantity * new_current_price
            gain_loss_pct = ((new_current_price - new_avg_price) / new_avg_price) * 100 if new_avg_price > 0 else 0

            new_holding = {
                "ticker": new_ticker.upper(),
                "name": new_name,
                "sector": new_sector,
                "quantity": new_quantity,
                "avg_buy_price": new_avg_price,
                "current_price": new_current_price,
                "value_inr": value_inr,
                "gain_loss_pct": round(gain_loss_pct, 1),
                "holding_period_months": new_holding_months
            }
            profile['holdings'].append(new_holding)
            st.session_state.user_profile = profile
            st.success(f"Added {new_name} to holdings!")
            st.rerun()

    # Mutual Funds Section
    st.markdown("---")
    st.subheader("📈 Mutual Fund Holdings")

    if 'mutual_funds' not in profile:
        profile['mutual_funds'] = []

    if profile['mutual_funds']:
        st.markdown("**Your Mutual Funds:**")
        for i, mf in enumerate(profile['mutual_funds']):
            with st.expander(f"{mf.get('name', 'Fund')}", expanded=False):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown(f"**Type:** {mf.get('type', 'N/A')}")
                    st.markdown(f"**Value:** ₹{mf.get('value_inr', 0):,}")
                with col_m2:
                    st.markdown(f"**SIP:** ₹{mf.get('sip_amount', 0):,}/month")
                    st.markdown(f"**1Y Return:** {mf.get('returns_1yr_pct', 0):.1f}%")

                if st.button(f"🗑️ Remove", key=f"remove_mf_{i}"):
                    profile['mutual_funds'].pop(i)
                    st.session_state.user_profile = profile
                    st.rerun()

    st.markdown("**Add New Mutual Fund:**")
    with st.form("add_mf_form"):
        col_mf1, col_mf2 = st.columns(2)

        with col_mf1:
            mf_name = st.text_input("Fund Name", placeholder="e.g., Axis Bluechip Fund - Direct Growth")
            mf_type = st.selectbox(
                "Fund Type",
                options=["Large Cap Equity", "Mid Cap Equity", "Small Cap Equity",
                         "Flexi Cap", "ELSS", "Debt", "Hybrid", "Index Fund", "Other"]
            )

        with col_mf2:
            mf_value = st.number_input("Current Value (INR)", min_value=0, value=0, step=1000)
            mf_sip = st.number_input("Monthly SIP (INR)", min_value=0, value=0, step=500)
            mf_returns = st.number_input("1 Year Return (%)", min_value=-100.0, max_value=200.0, value=0.0)

        mf_submitted = st.form_submit_button("➕ Add Mutual Fund", use_container_width=True)

        if mf_submitted and mf_name:
            new_mf = {
                "name": mf_name,
                "type": mf_type,
                "value_inr": mf_value,
                "sip_amount": mf_sip,
                "returns_1yr_pct": mf_returns
            }
            profile['mutual_funds'].append(new_mf)
            st.session_state.user_profile = profile
            st.success(f"Added {mf_name}!")
            st.rerun()

    # Watchlist Section
    st.markdown("---")
    st.subheader("👀 Watchlist")

    if 'watchlist' not in profile:
        profile['watchlist'] = []

    if profile['watchlist']:
        st.markdown("**Stocks you're watching:**")
        watchlist_str = ", ".join(profile['watchlist'])
        st.info(watchlist_str)

    new_watchlist = st.text_input(
        "Enter ticker symbols (comma-separated)",
        value=", ".join(profile.get('watchlist', [])),
        placeholder="e.g., SUNPHARMA.NS, TATAMOTORS.NS, MARUTI.NS"
    )

    if new_watchlist:
        profile['watchlist'] = [t.strip().upper() for t in new_watchlist.split(",") if t.strip()]

with tab5:
    st.subheader("Investment Goals & Preferences")

    col1, col2 = st.columns(2)

    with col1:
        profile['primary_goal'] = st.selectbox(
            "Primary Investment Goal",
            options=[
                "Wealth Creation",
                "Retirement Planning",
                "Child Education",
                "Home Purchase",
                "Emergency Fund",
                "Tax Saving",
                "Regular Income"
            ],
            index=[
                "Wealth Creation", "Retirement Planning", "Child Education",
                "Home Purchase", "Emergency Fund", "Tax Saving", "Regular Income"
            ].index(profile.get('primary_goal', 'Wealth Creation'))
        )

        profile['sip_monthly'] = st.number_input(
            "Monthly SIP Amount (INR)",
            min_value=0,
            value=profile.get('sip_monthly', 0),
            step=1000,
            help="How much do you invest monthly via SIP?"
        )

        profile['trade_frequency'] = st.selectbox(
            "Trading Frequency",
            options=["Daily", "Weekly", "Monthly", "Quarterly", "Yearly", "Rarely"],
            index=["Daily", "Weekly", "Monthly", "Quarterly", "Yearly", "Rarely"].index(
                profile.get('trade_frequency', 'Quarterly')
            )
        )

    with col2:
        profile['tax_regime'] = st.selectbox(
            "Tax Regime",
            options=["New Regime", "Old Regime", "Not Sure"],
            index=["New Regime", "Old Regime", "Not Sure"].index(
                profile.get('tax_regime', 'New Regime')
            )
        )

        profile['preferred_sectors'] = st.multiselect(
            "Preferred Sectors",
            options=[
                "IT", "Banking", "Pharma", "FMCG", "Auto",
                "Energy", "Infrastructure", "Telecom", "Metals", "Real Estate"
            ],
            default=profile.get('preferred_sectors', [])
        )

        profile['avoid_sectors'] = st.multiselect(
            "Sectors to Avoid",
            options=[
                "IT", "Banking", "Pharma", "FMCG", "Auto",
                "Energy", "Infrastructure", "Telecom", "Metals", "Real Estate",
                "Alcohol", "Tobacco", "Gambling"
            ],
            default=profile.get('avoid_sectors', [])
        )

# Save button
st.markdown("---")

col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if st.button("Save Profile", type="primary", use_container_width=True):
        profile['profile_complete'] = all([
            profile.get('name'),
            profile.get('age'),
            profile.get('occupation'),
            profile.get('salary', 0) > 0,
            profile.get('risk_tolerance')
        ])

        st.session_state.user_profile = profile
        save_profile(profile)
        st.success("Profile saved successfully!")
        st.balloons()

# Profile Summary Card
if profile.get('name'):
    st.markdown("---")
    st.subheader("Profile Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Age", profile.get('age', '-'))
        st.metric("Risk Level", profile.get('risk_label', 'Moderate'))

    with col2:
        salary = profile.get('salary', 0)
        st.metric("Annual Salary", f"₹{salary:,}" if salary else "-")
        st.metric("Experience", profile.get('investment_experience', '-'))

    with col3:
        portfolio = profile.get('portfolio_value', 0)
        st.metric("Portfolio Value", f"₹{portfolio:,}" if portfolio else "-")
        st.metric("SIP/Month", f"₹{profile.get('sip_monthly', 0):,}")

    with col4:
        st.metric("Savings Rate", f"{profile.get('savings_rate', 0)}%")
        st.metric("Horizon", profile.get('investment_horizon', '-'))

    # Holdings Summary
    holdings = profile.get('holdings', [])
    mutual_funds = profile.get('mutual_funds', [])

    if holdings or mutual_funds:
        st.markdown("---")
        st.subheader("Holdings Summary")

        if holdings:
            gainers = [h for h in holdings if h.get('gain_loss_pct', 0) > 0]
            losers = [h for h in holdings if h.get('gain_loss_pct', 0) < 0]
            total_holdings_value = sum(h.get('value_inr', 0) for h in holdings)

            col_h1, col_h2, col_h3 = st.columns(3)

            with col_h1:
                st.metric("Total Stocks", len(holdings))
                st.metric("Holdings Value", f"₹{total_holdings_value:,}")

            with col_h2:
                st.metric("Profitable", f"{len(gainers)} stocks", delta="gaining")
                if gainers:
                    best = max(gainers, key=lambda x: x.get('gain_loss_pct', 0))
                    st.caption(f"Best: {best['name']} (+{best['gain_loss_pct']:.1f}%)")

            with col_h3:
                st.metric("Loss Making", f"{len(losers)} stocks", delta="losing", delta_color="inverse")
                if losers:
                    worst = min(losers, key=lambda x: x.get('gain_loss_pct', 0))
                    st.caption(f"Worst: {worst['name']} ({worst['gain_loss_pct']:.1f}%)")

        if mutual_funds:
            total_mf_value = sum(mf.get('value_inr', 0) for mf in mutual_funds)
            total_sip = sum(mf.get('sip_amount', 0) for mf in mutual_funds)
            st.markdown(f"**Mutual Funds:** {len(mutual_funds)} funds | Total Value: ₹{total_mf_value:,} | Monthly SIP: ₹{total_sip:,}")
