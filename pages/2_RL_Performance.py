"""
RL Performance Analysis page for Streamlit dashboard.
Displays backtest results, visualizations, and RL learning proof.
"""
import streamlit as st
import json
from pathlib import Path
import pandas as pd
from PIL import Image

st.set_page_config(page_title="RL Performance Analysis", page_icon="📊", layout="wide")

st.title("🤖 RL Performance Analysis")
st.markdown("*Backtesting results comparing Equal, Expert, and RL weighting systems*")

# Load results
results_file = Path("backtest_results.json")
if not results_file.exists():
    st.error("⚠️ Backtest results not found. Please run `python3 run_full_backtest.py` first.")
    st.stop()

with open(results_file, 'r') as f:
    results = json.load(f)

# Summary metrics
st.header("📈 Summary Results")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Training Phase (Jan 2021 - Dec 2023)")
    
    train_data = []
    for key, name in [('train_equal', 'Equal Weights'), 
                      ('train_expert', 'Expert Weights'),
                      ('train_rl', 'RL Weights')]:
        decisions = results[key]
        correct = sum(1 for d in decisions if (
            (d['decision'] == 'BUY' and d['outcome_7d'] > 1) or
            (d['decision'] == 'SELL' and d['outcome_7d'] < -1) or
            (d['decision'] == 'HOLD' and abs(d['outcome_7d']) < 2)
        ))
        accuracy = correct / len(decisions) * 100
        avg_reward = sum(d['reward'] for d in decisions) / len(decisions)
        
        train_data.append({
            'System': name,
            'Decisions': len(decisions),
            'Correct': correct,
            'Accuracy': f"{accuracy:.1f}%",
            'Avg Reward': f"{avg_reward:.3f}"
        })
    
    st.dataframe(pd.DataFrame(train_data), use_container_width=True, hide_index=True)

with col2:
    st.subheader("Testing Phase (Jan 2024 - Jan 2026)")
    
    test_data = []
    for key, name in [('test_equal', 'Equal Weights'), 
                      ('test_expert', 'Expert Weights'),
                      ('test_rl', 'RL Weights')]:
        decisions = results[key]
        correct = sum(1 for d in decisions if (
            (d['decision'] == 'BUY' and d['outcome_7d'] > 1) or
            (d['decision'] == 'SELL' and d['outcome_7d'] < -1) or
            (d['decision'] == 'HOLD' and abs(d['outcome_7d']) < 2)
        ))
        accuracy = correct / len(decisions) * 100
        avg_reward = sum(d['reward'] for d in decisions) / len(decisions)
        
        test_data.append({
            'System': name,
            'Decisions': len(decisions),
            'Correct': correct,
            'Accuracy': f"{accuracy:.1f}%",
            'Avg Reward': f"{avg_reward:.3f}"
        })
    
    st.dataframe(pd.DataFrame(test_data), use_container_width=True, hide_index=True)

# Key findings - compute dynamically
st.header("🔍 Key Findings")

# Calculate test metrics dynamically
test_systems = [('test_equal', 'Equal'), ('test_expert', 'Expert'), ('test_rl', 'RL')]
test_accuracies = {}
test_rewards = {}

for key, name in test_systems:
    decisions = results[key]
    correct = sum(1 for d in decisions if (
        (d['decision'] == 'BUY' and d['outcome_7d'] > 1) or
        (d['decision'] == 'SELL' and d['outcome_7d'] < -1) or
        (d['decision'] == 'HOLD' and abs(d['outcome_7d']) < 2)
    ))
    test_accuracies[name] = (correct / len(decisions)) * 100 if decisions else 0
    test_rewards[name] = sum(d['reward'] for d in decisions) / len(decisions) if decisions else 0

# Find best system
best_system = max(test_accuracies, key=test_accuracies.get)
best_acc = test_accuracies[best_system]
rl_acc = test_accuracies['RL']
rl_diff = rl_acc - test_accuracies['Equal']

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Best Test Accuracy",
        f"{best_acc:.1f}%",
        f"{best_system} Weights"
    )

with col2:
    st.metric(
        "RL Test Accuracy",
        f"{rl_acc:.1f}%",
        f"{rl_diff:+.1f}% vs Equal"
    )

with col3:
    # Calculate avg reward difference
    rl_reward = test_rewards['RL']
    equal_reward = test_rewards['Equal']
    reward_diff = rl_reward - equal_reward
    st.metric(
        "RL Avg Reward",
        f"{rl_reward:.3f}",
        f"{reward_diff:+.3f} vs Equal"
    )

# Visualizations
st.header("📊 Visualizations")

results_dir = Path("results")
if results_dir.exists():
    tabs = st.tabs(["Accuracy Comparison", "Reward Distribution", "Regime Heatmap", "Cumulative Performance"])
    
    with tabs[0]:
        st.subheader("Accuracy Comparison")
        img_path = results_dir / "accuracy_comparison.png"
        if img_path.exists():
            st.image(str(img_path), use_container_width=True)
        else:
            st.warning("Chart not generated yet")
    
    with tabs[1]:
        st.subheader("Reward Distribution")
        img_path = results_dir / "reward_distribution.png"
        if img_path.exists():
            st.image(str(img_path), use_container_width=True)
        else:
            st.warning("Chart not generated yet")
    
    with tabs[2]:
        st.subheader("Performance by Market Regime")
        img_path = results_dir / "regime_heatmap.png"
        if img_path.exists():
            st.image(str(img_path), use_container_width=True)
            st.caption("Darker green = higher accuracy. Shows how each system performed in different market conditions.")
        else:
            st.warning("Chart not generated yet")
    
    with tabs[3]:
        st.subheader("Cumulative Accuracy Over Time")
        img_path = results_dir / "cumulative_accuracy.png"
        if img_path.exists():
            st.image(str(img_path), use_container_width=True)
            st.caption("Shows how accuracy evolved over 200 test decisions.")
        else:
            st.warning("Chart not generated yet")
else:
    st.warning("⚠️ Visualization folder not found. Run `python3 generate_visualizations.py`")

# Analysis
st.header("💡 Analysis & Interpretation")

st.markdown("""
### Performance Analysis (5-Year Backtest)

This backtest uses 5 years of NIFTY 50 data spanning diverse market conditions:

1. **Training Period (2021-2023)** 📈
   - Post-COVID recovery rally (2021)
   - Volatile 2022 with inflation concerns
   - Stabilization in 2023
   - ~300 training decisions across multiple regimes

2. **Testing Period (2024-2026)** 📊
   - Market consolidation and new highs
   - ~200 test decisions for generalization
   - RL weights frozen to test learned patterns

3. **RL Advantages** 🤖
   - Learns regime-specific weight adjustments
   - Thompson Sampling enables exploration vs exploitation balance
   - Adaptive to volatility and sentiment changes

### RL Framework Features ✅

- **Thompson Sampling**: Bayesian approach to weight optimization
- **Regime Detection**: Automatic market condition classification
- **Database Persistence**: Learned weights saved for production use
""")

# Data coverage note
st.info("""
**5-Year Data Coverage**: This backtest uses NIFTY 50 data from Jan 2021 to Jan 2026, covering:
- Post-COVID recovery (2021)
- Inflation/rate concerns (2022)
- Market stabilization (2023)
- New highs and consolidation (2024-2026)

The RL system trains on 3 years of diverse market conditions for robust weight learning.
""")

# Download options
st.header("📥 Download Results")

col1, col2 = st.columns(2)

with col1:
    if Path("backtest_comparison.md").exists():
        with open("backtest_comparison.md", 'r') as f:
            st.download_button(
                "Download Comparison Report",
                f.read(),
                "backtest_comparison.md",
                "text/markdown"
            )

with col2:
    if results_file.exists():
        with open(results_file, 'r') as f:
            st.download_button(
                "Download Raw Results (JSON)",
                f.read(),
                "backtest_results.json",
                "application/json"
            )

# Footer
st.markdown("---")
st.caption("RL-based Investment Decision System | Powered by Thompson Sampling")
