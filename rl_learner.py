"""
Thompson Sampling-based RL learner for adaptive weight selection.
Uses Beta distributions to model agent reliability per regime.
"""
import numpy as np
from typing import Dict, Optional
import logging
from rl_models import MarketRegime, RLState, DecisionRecord
from database import DatabaseManager
from weights_config import ALL_AGENTS, normalize_weights

logger = logging.getLogger(__name__)


class ThompsonSamplingLearner:
    """
    Thompson Sampling learner for agent weight adaptation.
    Maintains Beta distributions (alpha, beta) for each agent in each regime.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize Thompson Sampling learner.
        
        Args:
            db_manager: Database manager for persistence
        """
        self.db = db_manager
        # Cache of RL states: {regime_key: {agent_name: {alpha, beta}}}
        self.states_cache = {}
        
    def get_regime_key(self, regime: MarketRegime) -> str:
        """Convert regime to unique key."""
        return regime.to_key()
        
    def _load_state(self, regime_key: str, agent_name: str) -> RLState:
        """
        Load RL state from database or create new one.
        
        Args:
            regime_key: Market regime key
            agent_name: Agent name
            
        Returns:
            RLState with alpha and beta
        """
        # Check cache first
        if regime_key in self.states_cache:
            if agent_name in self.states_cache[regime_key]:
                cached = self.states_cache[regime_key][agent_name]
                return RLState(
                    regime_key=regime_key,
                    agent_name=agent_name,
                    alpha=cached["alpha"],
                    beta=cached["beta"]
                )
        
        # Load from database
        db_state = self.db.get_rl_state(regime_key, agent_name)
        
        if db_state:
            state = RLState(
                regime_key=regime_key,
                agent_name=agent_name,
                alpha=db_state["alpha"],
                beta=db_state["beta"]
            )
        else:
            # Create new state with uniform prior (alpha=1, beta=1)
            state = RLState(
                regime_key=regime_key,
                agent_name=agent_name,
                alpha=1.0,
                beta=1.0
            )
            
        # Update cache
        if regime_key not in self.states_cache:
            self.states_cache[regime_key] = {}
        self.states_cache[regime_key][agent_name] = {
            "alpha": state.alpha,
            "beta": state.beta
        }
        
        return state
        
    def _save_state(self, state: RLState):
        """
        Save RL state to database and cache.
        
        Args:
            state: RLState to save
        """
        self.db.update_rl_state(
            state.regime_key,
            state.agent_name,
            state.alpha,
            state.beta
        )
        
        # Update cache
        if state.regime_key not in self.states_cache:
            self.states_cache[state.regime_key] = {}
        self.states_cache[state.regime_key][state.agent_name] = {
            "alpha": state.alpha,
            "beta": state.beta
        }
        
    def select_weights(self, regime: MarketRegime) -> Dict[str, float]:
        """
        Sample weights from Beta distributions using Thompson Sampling.
        
        Args:
            regime: Current market regime
            
        Returns:
            Dictionary of sampled weights (normalized to sum to 1)
        """
        regime_key = self.get_regime_key(regime)
        sampled_weights = {}
        
        for agent in ALL_AGENTS:
            state = self._load_state(regime_key, agent)
            
            # Sample from Beta(alpha, beta) distribution
            # Beta distribution represents our belief about the agent's "quality"
            sample = np.random.beta(state.alpha, state.beta)
            sampled_weights[agent] = sample
            
        # Normalize to sum to 1
        normalized = normalize_weights(sampled_weights)
        
        logger.debug(
            f"Sampled weights for {regime_key}, "
            f"top 3: {sorted(normalized.items(), key=lambda x: x[1], reverse=True)[:3]}"
        )
        
        return normalized
        
    def update(self, decision_record: DecisionRecord, reward: float):
        """
        Update agent beliefs based on decision outcome.
        
        Uses reward to update alpha (success) and beta (failure) parameters.
        
        Args:
            decision_record: Record of the decision
            reward: Calculated reward (-0.8 to +1.7)
        """
        regime_key = decision_record.market_regime
        weights_used = decision_record.weights_used
        
        # Normalize reward to [0, 1] range for Beta update
        # Original range: -0.8 to 1.7 (total 2.5)
        # Map to 0-1: (reward + 0.8) / 2.5
        normalized_reward = (reward + 0.8) / 2.5
        normalized_reward = max(0.0, min(1.0, normalized_reward))  # Clamp to [0, 1]
        
        logger.info(
            f"Updating RL states for {regime_key}, "
            f"reward={reward:.3f}, normalized={normalized_reward:.3f}"
        )
        
        # Update each agent based on its contribution (weight)
        for agent in ALL_AGENTS:
            if agent not in weights_used:
                continue
                
            state = self._load_state(regime_key, agent)
            weight_contribution = weights_used[agent]
            
            # Update alpha and beta based on weighted reward
            # Higher weight = more attribution to this agent
            if normalized_reward > 0.5:
                # Positive outcome: increase alpha
                alpha_increment = weight_contribution * (normalized_reward - 0.5) * 2
                state.alpha += alpha_increment
            else:
                # Negative outcome: increase beta
                beta_increment = weight_contribution * (0.5 - normalized_reward) * 2
                state.beta += beta_increment
                
            # Save updated state
            self._save_state(state)
            
        logger.info(f"Updated {len(weights_used)} agent states for {regime_key}")
        
    def get_statistics(self, regime: MarketRegime) -> Dict[str, Dict[str, float]]:
        """
        Get learning statistics for a regime.
        
        Args:
            regime: Market regime
            
        Returns:
            Dictionary with statistics per agent
        """
        regime_key = self.get_regime_key(regime)
        stats = {}
        
        for agent in ALL_AGENTS:
            state = self._load_state(regime_key, agent)
            stats[agent] = {
                "alpha": state.alpha,
                "beta": state.beta,
                "mean_weight": state.get_mean_weight(),
                "reliability": state.get_reliability(),
                "total_observations": state.alpha + state.beta - 2,  # Subtract prior
            }
            
        return stats


if __name__ == "__main__":
    # Test Thompson Sampling learner
    logging.basicConfig(level=logging.INFO)
    
    from rl_models import MarketRegime, DecisionRecord
    import json
    
    # Create test database
    db = DatabaseManager("test_rl.db")
    learner = ThompsonSamplingLearner(db)
    
    # Create test regime
    regime = MarketRegime(
        inflation="high",
        rate_trend="rising",
        sentiment="bearish",
        volatility=0.25
    )
    
    print(f"Testing regime: {regime.to_key()}\n")
    
    # Sample initial weights
    weights1 = learner.select_weights(regime)
    print("Initial sampled weights (top 5):")
    for agent, weight in sorted(weights1.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {agent}: {weight:.4f}")
    
    # Simulate some decisions and updates
    print("\nSimulating 5 positive outcomes...")
    for i in range(5):
        weights = learner.select_weights(regime)
        record = DecisionRecord(
            timestamp="2025-01-01",
            symbol="TEST",
            decision="BUY",
            confidence=0.8,
            weights_used=weights,
            market_regime=regime.to_key(),
            agent_outputs={}
        )
        # Positive reward
        learner.update(record, reward=1.0)
    
    # Sample again to see adaptation
    weights2 = learner.select_weights(regime)
    print("\nWeights after 5 positive outcomes (top 5):")
    for agent, weight in sorted(weights2.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {agent}: {weight:.4f}")
    
    # Get statistics
    stats = learner.get_statistics(regime)
    print("\nTop agents by reliability:")
    sorted_by_reliability = sorted(stats.items(), key=lambda x: x[1]["reliability"], reverse=True)
    for agent, agent_stats in sorted_by_reliability[:5]:
        print(f"  {agent}: reliability={agent_stats['reliability']:.3f}, "
              f"α={agent_stats['alpha']:.2f}, β={agent_stats['beta']:.2f}")
    
    db.close()
    print("\nTest completed")
