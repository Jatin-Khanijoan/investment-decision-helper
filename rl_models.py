"""
Extended state models for RL-based decision system.
Includes market regime, weight configuration, and RL state tracking.
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class MarketRegime(BaseModel):
    """Market regime classification based on macro conditions."""
    inflation: str  # "low", "medium", "high"
    rate_trend: str  # "falling", "stable", "rising"
    sentiment: str  # "bearish", "neutral", "bullish"
    volatility: float  # continuous value (annualized)
    
    def to_key(self) -> str:
        """Generate unique key for this regime."""
        return f"{self.inflation}_{self.rate_trend}_{self.sentiment}"
        
    def to_vector(self) -> List[float]:
        """Convert to feature vector for RL."""
        # One-hot encode categorical variables
        inflation_vec = [1.0 if self.inflation == level else 0.0 for level in ["low", "medium", "high"]]
        rate_vec = [1.0 if self.rate_trend == trend else 0.0 for trend in ["falling", "stable", "rising"]]
        sentiment_vec = [1.0 if self.sentiment == s else 0.0 for s in ["bearish", "neutral", "bullish"]]
        
        # Add volatility as continuous
        vol_vec = [self.volatility]
        
        return inflation_vec + rate_vec + sentiment_vec + vol_vec


class WeightConfiguration(BaseModel):
    """Weight configuration for a single agent."""
    agent_name: str
    base_weight: float  # Base weight from expert knowledge
    multiplier: float  # Regime-specific multiplier
    rl_weight: float  # RL-learned weight
    final_weight: float  # Final blended weight
    
    def explain(self) -> str:
        """Generate explanation for this weight."""
        return (
            f"{self.agent_name}: base={self.base_weight:.3f}, "
            f"regime_mult={self.multiplier:.2f}, rl={self.rl_weight:.3f}, "
            f"final={self.final_weight:.3f}"
        )


class DecisionRecord(BaseModel):
    """Record of a single decision for storage and evaluation."""
    decision_id: Optional[int] = None
    timestamp: str  # ISO format
    symbol: str
    sector: Optional[str] = None
    decision: str  # "BUY", "HOLD", "SELL"
    confidence: float
    weights_used: Dict[str, float]
    market_regime: str  # regime key
    agent_outputs: Dict[str, Any]
    outcome_7d: Optional[float] = None  # Return percentage after 7 days
    reward: Optional[float] = None  # Calculated reward
    evaluated: bool = False
    conversation_id: Optional[str] = None
    turn_number: Optional[int] = None


class RLState(BaseModel):
    """RL state for Thompson Sampling - tracks alpha/beta per agent per regime."""
    regime_key: str
    agent_name: str
    alpha: float = 1.0  # Success count (starts at 1 for uniform prior)
    beta: float = 1.0  # Failure count (starts at 1 for uniform prior)
    
    def get_mean_weight(self) -> float:
        """Get expected value of Beta distribution."""
        return self.alpha / (self.alpha + self.beta)
        
    def get_reliability(self) -> float:
        """Get reliability score (0-1, higher = more certain)."""
        total = self.alpha + self.beta
        # Use concentration of Beta distribution as reliability
        # Higher total observations = more reliable
        return min(1.0, total / 100.0)  # Cap at 100 observations
