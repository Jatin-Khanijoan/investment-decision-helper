Manual Testing Guide - Phase 4 Integration
Overview
This guide provides step-by-step instructions to manually test the integration of all Phase 4 RL components.

Test 1: Full Weight Manager + RL Integration
Purpose
Verify that WeightManager correctly integrates with RL learner for dynamic weight selection.

Steps
Create test script test_full_integration.py:
#!/usr/bin/env python3
import logging
from database import DatabaseManager
from rl_learner import ThompsonSamplingLearner
from weight_manager import WeightManager
from state import AgentOutput, DecisionState
from rl_models import DecisionRecord
from reward_calculator import calculate_reward
import json
logging.basicConfig(level=logging.INFO)
# Initialize components
db = DatabaseManager("test_integration.db")
rl_learner = ThompsonSamplingLearner(db)
weight_manager = WeightManager(rl_learner=rl_learner)
# Create test agent outputs
test_outputs = {
    "inflation": AgentOutput(
        name="inflation",
        value="High inflation at 6.8%",
        confidence=0.9,
        sources=["RBI Report"]
    ),
    "interest_rates": AgentOutput(
        name="interest_rates",
        value="RBI raised repo rate by 50bps to 6.5%",
        confidence=0.95,
        sources=["RBI Press Release"]
    ),
    "current": AgentOutput(
        name="current",
        value="Q3 results missed estimates, weak guidance",
        confidence=0.8,
        sources=["Company Filing"]
    ),
    "gdp_growth": AgentOutput(
        name="gdp_growth",
        value="GDP growth slowing to 6.2%",
        confidence=0.7,
        sources=["NSO"]
    ),
}
test_state = DecisionState(
    user_id="test_user",
    question="Should I buy HDFC Bank?",
    symbol="HDFCBANK",
    sector="Banking",
    agent_outputs=test_outputs
)
print("=" * 60)
print("TEST 1: Weight Calculation WITHOUT RL")
print("=" * 60)
# Get weights without RL
final_weights_no_rl, regime, configs = weight_manager.get_final_weights(
    test_state,
    sector="banking",
    use_rl=False
)
print(f"\nDetected Regime: {regime.to_key()}")
print(f"Inflation: {regime.inflation}, Rates: {regime.rate_trend}, Sentiment: {regime.sentiment}")
print(f"\nTop 10 Weights (Without RL):")
for agent, weight in sorted(final_weights_no_rl.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {agent:30s}: {weight:.4f}")
print("\n" + "=" * 60)
print("TEST 2: Weight Calculation WITH RL (Initial)")
print("=" * 60)
# Get weights with RL (should be similar to no-RL initially)
final_weights_with_rl, regime2, configs2 = weight_manager.get_final_weights(
    test_state,
    sector="banking",
    use_rl=True,
    rl_blend_ratio=0.7
)
print(f"\nTop 10 Weights (With RL - No Training Yet):")
for agent, weight in sorted(final_weights_with_rl.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {agent:30s}: {weight:.4f}")
print("\n" + "=" * 60)
print("TEST 3: Simulate 10 Successful Decisions")
print("=" * 60)
# Simulate 10 positive outcomes to train RL
for i in range(10):
    weights, regime, _ = weight_manager.get_final_weights(
        test_state, sector="banking", use_rl=True, rl_blend_ratio=0.7
    )
    
    record = DecisionRecord(
        timestamp=f"2025-06-{i+1:02d}",
        symbol="HDFCBANK",
        sector="Banking",
        decision="SELL",  # Sell in high inflation/rising rates
        confidence=0.85,
        weights_used=weights,
        market_regime=regime.to_key(),
        agent_outputs=test_outputs
    )
    
    # Positive reward (correct SELL decision)
    reward, breakdown = calculate_reward("SELL", 1500.0, 1425.0, 0.85)
    rl_learner.update(record, reward)
    print(f"  Decision {i+1}: Reward = {reward:.3f}")
print("\n" + "=" * 60)
print("TEST 4: Weight Calculation WITH RL (After Training)")
print("=" * 60)
# Get weights after training
final_weights_trained, regime3, configs3 = weight_manager.get_final_weights(
    test_state,
    sector="banking",
    use_rl=True,
    rl_blend_ratio=0.7
)
print(f"\nTop 10 Weights (With RL - After 10 Positive Outcomes):")
for agent, weight in sorted(final_weights_trained.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {agent:30s}: {weight:.4f}")
print("\n" + "=" * 60)
print("TEST 5: RL Statistics")
print("=" * 60)
stats = rl_learner.get_statistics(regime)
print(f"\nTop 5 Agents by Mean Weight:")
sorted_by_mean = sorted(stats.items(), key=lambda x: x[1]["mean_weight"], reverse=True)
for agent, agent_stats in sorted_by_mean[:5]:
    print(f"  {agent:30s}: mean={agent_stats['mean_weight']:.4f}, "
          f"α={agent_stats['alpha']:.2f}, β={agent_stats['beta']:.2f}, "
          f"reliability={agent_stats['reliability']:.3f}")
print("\n" + "=" * 60)
print("TEST 6: Weight Configuration Details")
print("=" * 60)
print("\nSample Weight Configuration Breakdown:")
for agent in ["inflation", "interest_rates", "current"][:3]:
    config = configs3[agent]
    print(f"\n{agent}:")
    print(f"  {config.explain()}")
print("\n" + "=" * 60)
print("INTEGRATION TEST COMPLETE")
print("=" * 60)
db.close()
Run the test:
cd /home/jatin/kautilya
source venv/bin/activate
python3 test_full_integration.py
Expected Results:
✅ Regime correctly detected as high_rising_bearish
✅ Without RL: interest_rates and 
inflation
 should have highest weights (~0.18, ~0.14)
✅ With RL (initial): Similar to without RL (uniform prior)
✅ After 10 positive outcomes: Weights should adapt
✅ RL statistics show increasing alpha values
✅ No errors or crashes
Test 2: Database Persistence
Purpose
Verify RL state persists across sessions.

Steps
Check database after Test 1:
sqlite3 test_integration.db "SELECT regime_key, agent_name, alpha, beta FROM rl_state ORDER BY alpha DESC LIMIT 10;"
Expected Results:

✅ At least 15 rows (one per agent for the regime)
✅ Alpha values > 1.0 for some agents
✅ Regime key = high_rising_bearish
Test persistence - Create test_persistence.py:

#!/usr/bin/env python3
from database import DatabaseManager
from rl_learner import ThompsonSamplingLearner
from rl_models import MarketRegime
db = DatabaseManager("test_integration.db")
learner = ThompsonSamplingLearner(db)
regime = MarketRegime(
    inflation="high",
    rate_trend="rising",
    sentiment="bearish",
    volatility=0.2
)
print("Loading previously trained RL state...")
stats = learner.get_statistics(regime)
print("\nTop 5 agents by observations:")
sorted_by_obs = sorted(stats.items(), key=lambda x: x[1]["total_observations"], reverse=True)
for agent, s in sorted_by_obs[:5]:
    print(f"  {agent}: {s['total_observations']:.0f} observations, α={s['alpha']:.2f}")
db.close()
Run:
python3 test_persistence.py
Expected Results:
✅ Loads same alpha/beta values from previous test
✅ Shows observation counts
Test 3: Different Regimes
Purpose
Verify system handles multiple regimes independently.

Steps
Create test_multi_regime.py:
#!/usr/bin/env python3
from database import DatabaseManager
from rl_learner import ThompsonSamplingLearner
from weight_manager import WeightManager
from state import AgentOutput, DecisionState
db = DatabaseManager("test_integration.db")
rl_learner = ThompsonSamplingLearner(db)
weight_manager = WeightManager(rl_learner=rl_learner)
# Test Regime 1: Low inflation, stable rates, bullish
regime1_outputs = {
    "inflation": AgentOutput(name="inflation", value="Low inflation at 3.5%", confidence=0.9, sources=[]),
    "interest_rates": AgentOutput(name="interest_rates", value="Rates stable at 4.0%", confidence=0.9, sources=[]),
    "current": AgentOutput(name="current", value="Strong growth, bullish outlook", confidence=0.8, sources=[]),
}
state1 = DecisionState(
    user_id="test", question="Test", symbol="TCS", sector="IT",
    agent_outputs=regime1_outputs
)
weights1, regime1, _ = weight_manager.get_final_weights(state1, sector="it", use_rl=False)
print(f"Regime 1: {regime1.to_key()}")
print(f"Top 3 weights: {sorted(weights1.items(), key=lambda x: x[1], reverse=True)[:3]}\n")
# Test Regime 2: High inflation, rising rates, bearish (from Test 1)
regime2_outputs = {
    "inflation": AgentOutput(name="inflation", value="High inflation at 7%", confidence=0.9, sources=[]),
    "interest_rates": AgentOutput(name="interest_rates", value="Rising rates", confidence=0.9, sources=[]),
    "current": AgentOutput(name="current", value="Weak results", confidence=0.8, sources=[]),
}
state2 = DecisionState(
    user_id="test", question="Test", symbol="HDFC", sector="Banking",
    agent_outputs=regime2_outputs
)
weights2, regime2, _ = weight_manager.get_final_weights(state2, sector="banking", use_rl=False)
print(f"Regime 2: {regime2.to_key()}")
print(f"Top 3 weights: {sorted(weights2.items(), key=lambda x: x[1], reverse=True)[:3]}\n")
# Verify they're different
print(f"Regimes are different: {regime1.to_key() != regime2.to_key()}")
print(f"Weight profiles are different: {weights1 != weights2}")
db.close()
Run:
python3 test_multi_regime.py
Expected Results:
✅ Regime 1: low_stable_bullish with higher company weights
✅ Regime 2: high_rising_bearish with higher macro weights
✅ Regimes are different: True
✅ Weights are different: True
Test 4: End-to-End with Real Data
Purpose
Test with actual NIFTY data.

Steps
Create test_with_real_data.py:
#!/usr/bin/env python3
from data_accessor import NiftyDataAccessor
from datetime import datetime
accessor = NiftyDataAccessor()
# Test getting a 7-day outcome
test_date = datetime(2025, 6, 2)
price_at = accessor.get_price(test_date, 'Close')
price_after = accessor.get_price_after_days(test_date, days_ahead=7)
if price_at and price_after:
    return_pct = ((price_after - price_at) / price_at) * 100
    print(f"Date: {test_date.date()}")
    print(f"Price at decision: {price_at:.2f}")
    print(f"Price after 7 days: {price_after:.2f}")
    print(f"Return: {return_pct:.2f}%")
    
    from reward_calculator import calculate_reward
    reward, breakdown = calculate_reward("BUY", price_at, price_after, 0.8)
    print(f"\nReward for BUY decision: {reward:.3f}")
    print(f"Breakdown: {breakdown}")
else:
    print("Could not get prices (weekend/holiday)")
Run:
python3 test_with_real_data.py
Expected Results:
✅ Retrieves actual NIFTY prices
✅ Calculates real returns
✅ Computes rewards correctly
Acceptance Criteria
✅ Phase 4.5 is COMPLETE when:
Integration Test passes without errors
Weight adaptation visible after training (weights change)
Database persistence works (state survives restart)
Multiple regimes handled independently
Real data can be queried and rewards calculated
⚠️ Known Limitations
RL needs ~20+ decisions per regime to show significant adaptation
Initial weights with RL are similar to expert weights (by design)
Some dates may be missing (weekends/holidays)
Troubleshooting
Q: Weights don't change after training

Check that use_rl=True is set
Verify rl_blend_ratio > 0 (default 0.7)
Ensure rewards are being calculated (check logs)
Q: Database errors

Delete test databases: rm test_*.db
Re-run tests
Q: Import errors

Ensure virtual environment is activated: source venv/bin/activate
Check all dependencies installed: pip install -r requirements.txt