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
