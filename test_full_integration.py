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
