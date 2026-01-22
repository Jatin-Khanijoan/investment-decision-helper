#!/usr/bin/env python3
from database import DatabaseManager
from rl_learner import ThompsonSamplingLearner
from rl_models import MarketRegime

db = DatabaseManager("test_integration.db")
learner = ThompsonSamplingLearner(db)

regime = MarketRegime(
    inflation="high",
    rate_trend="rising",
    sentiment="neutral",
    volatility=0.2
)

print("Loading previously trained RL state...")
stats = learner.get_statistics(regime)

print("\nTop 5 agents by observations:")
sorted_by_obs = sorted(stats.items(), key=lambda x: x[1]["total_observations"], reverse=True)
for agent, s in sorted_by_obs[:5]:
    print(f"  {agent}: {s['total_observations']:.0f} observations, α={s['alpha']:.2f}")

db.close()
