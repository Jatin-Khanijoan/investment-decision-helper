"""
Weight Manager - orchestrates base weights, regime multipliers, and RL-learned weights.
Central component for the dynamic weighting system.
"""
from typing import Dict, Optional
import logging
from rl_models import MarketRegime, WeightConfiguration
from weights_config import (
    get_base_weights, 
    normalize_weights,
    validate_weights,
    AGENT_TO_CATEGORY,
    ALL_AGENTS
)
from regime_detector import RegimeDetector
from state import DecisionState

logger = logging.getLogger(__name__)


# Regime-specific multipliers for different agent categories
# Format: {regime_component: {category: multiplier}}

INFLATION_MULTIPLIERS = {
    "low": {
        "macro": 0.7,      # Less focus on macro when inflation is low
        "company": 1.2,     # More focus on company fundamentals
        "policy": 0.8,
        "data_quality": 1.0,
    },
    "medium": {
        "macro": 1.0,       # Balanced
        "company": 1.0,
        "policy": 1.0,
        "data_quality": 1.0,
    },
    "high": {
        "macro": 1.5,       # High focus on macro when inflation is high
        "company": 0.8,     # Less on company specifics
        "policy": 1.2,
        "data_quality": 1.0,
    },
}

RATE_MULTIPLIERS = {
    "falling": {
        "macro": 1.3,       # Rate changes matter
        "company": 0.9,
        "policy": 1.1,
        "data_quality": 1.0,
    },
    "stable": {
        "macro": 0.9,       # Less focus on macro when rates stable
        "company": 1.1,     # More on company
        "policy": 0.9,
        "data_quality": 1.0,
    },
    "rising": {
        "macro": 1.4,       # Rising rates very important
        "company": 0.8,
        "policy": 1.1,
        "data_quality": 1.0,
    },
}

SENTIMENT_MULTIPLIERS = {
    "bearish": {
        "macro": 1.1,      # Pay attention to macro risks
        "company": 0.95,
        "policy": 1.05,
        "data_quality": 1.1,  # Data quality more important in uncertain times
    },
    "neutral": {
        "macro": 1.0,
        "company": 1.0,
        "policy": 1.0,
        "data_quality": 1.0,
    },
    "bullish": {
        "macro": 0.9,      # Less macro focus in bullish times
        "company": 1.1,     # More on company execution
        "policy": 0.95,
        "data_quality": 0.95,
    },
}

# Sector-specific adjustments
SECTOR_MULTIPLIERS = {
    "banking": {
        "interest_rates": 1.5,  # Banking very sensitive to rates
        "inflation": 1.2,
    },
    "it": {
        "interest_rates": 1.3,  # IT sensitive to growth rates
        "current": 1.2,         # Recent performance important
    },
    "pharma": {
        "policy_changes": 1.4,  # Pharma sensitive to regulation
        "governance": 1.2,
    },
    "energy": {
        "inflation": 1.3,       # Energy linked to inflation
        "sector_shocks": 1.3,
    },
    "fmcg": {
        "gdp_growth": 1.2,      # FMCG linked to consumption
        "current": 1.1,
    },
}


class WeightManager:
    """
    Manages weight calculation combining base weights, regime multipliers,
    and RL-learned weights.
    """
    
    def __init__(self, rl_learner=None):
        """
        Initialize weight manager.
        
        Args:
            rl_learner: Optional RL learner instance for learned weights
        """
        self.rl_learner = rl_learner
        self.base_weights = get_base_weights()
        
    def get_base_weights(self) -> Dict[str, float]:
        """Get base weight configuration."""
        return self.base_weights.copy()
        
    def detect_regime(
        self, 
        state: DecisionState,
        technical_indicators: Optional[Dict[str, float]] = None
    ) -> MarketRegime:
        """
        Detect market regime from state.
        
        Args:
            state: Decision state with agent outputs
            technical_indicators: Optional technical indicators
            
        Returns:
            MarketRegime object
        """
        return RegimeDetector.detect_regime(state, technical_indicators)
        
    def apply_regime_multipliers(
        self,
        base_weights: Dict[str, float],
        regime: MarketRegime,
        sector: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Apply regime-specific multipliers to base weights.
        
        Args:
            base_weights: Base weight distribution
            regime: Detected market regime
            sector: Optional sector for sector-specific adjustments
            
        Returns:
            Adjusted weights (not normalized)
        """
        adjusted = base_weights.copy()
        
        # Apply category-level multipliers based on regime
        inflation_mults = INFLATION_MULTIPLIERS[regime.inflation]
        rate_mults = RATE_MULTIPLIERS[regime.rate_trend]
        sentiment_mults = SENTIMENT_MULTIPLIERS[regime.sentiment]
        
        for agent in ALL_AGENTS:
            category = AGENT_TO_CATEGORY[agent]
            
            # Combine multipliers (geometric mean to avoid extreme values)
            combined_mult = (
                inflation_mults[category] * 
                rate_mults[category] * 
                sentiment_mults[category]
            ) ** (1/3)  # Geometric mean
            
            adjusted[agent] *= combined_mult
            
        # Apply sector-specific adjustments
        if sector and sector.lower() in SECTOR_MULTIPLIERS:
            sector_mults = SECTOR_MULTIPLIERS[sector.lower()]
            for agent, mult in sector_mults.items():
                if agent in adjusted:
                    adjusted[agent] *= mult
                    
        logger.debug(f"Applied regime multipliers for {regime.to_key()}")
        return adjusted
        
    def get_rl_weights(
        self,
        regime: MarketRegime
    ) -> Optional[Dict[str, float]]:
        """
        Get RL-learned weights for the current regime.
        
        Args:
            regime: Market regime
            
        Returns:
            RL-learned weights or None if no learner
        """
        if not self.rl_learner:
            return None
            
        try:
            weights = self.rl_learner.select_weights(regime)
            logger.debug(f"Got RL weights for {regime.to_key()}")
            return weights
        except Exception as e:
            logger.error(f"Failed to get RL weights: {e}")
            return None
            
    def blend_weights(
        self,
        expert_weights: Dict[str, float],
        rl_weights: Optional[Dict[str, float]],
        rl_blend_ratio: float = 0.7
    ) -> Dict[str, float]:
        """
        Blend expert and RL weights.
        
        Args:
            expert_weights: Expert-determined weights (base + regime)
            rl_weights: RL-learned weights
            rl_blend_ratio: How much to trust RL (0-1)
            
        Returns:
            Blended weights
        """
        if not rl_weights:
            return expert_weights
            
        blended = {}
        for agent in ALL_AGENTS:
            expert_w = expert_weights.get(agent, 0.0)
            rl_w = rl_weights.get(agent, expert_w)  # Fall back to expert if missing
            
            # Weighted combination
            blended[agent] = (rl_blend_ratio * rl_w) + ((1 - rl_blend_ratio) * expert_w)
            
        logger.info(f"Blended weights with RL ratio {rl_blend_ratio:.2f}")
        return blended
        
    def get_final_weights(
        self,
        state: DecisionState,
        sector: Optional[str] = None,
        use_rl: bool = True,
        rl_blend_ratio: float = 0.7,
        technical_indicators: Optional[Dict[str, float]] = None
    ) -> tuple[Dict[str, float], MarketRegime, Dict[str, WeightConfiguration]]:
        """
        Get final weights combining all sources.
        
        Args:
            state: Decision state
            sector: Optional sector
            use_rl: Whether to use RL weights
            rl_blend_ratio: RL blend ratio
            technical_indicators: Optional technical indicators
            
        Returns:
            Tuple of (final_weights, regime, weight_configs)
        """
        # Step 1: Get base weights
        base = self.get_base_weights()
        
        # Step 2: Detect regime
        regime = self.detect_regime(state, technical_indicators)
        
        # Step 3: Apply regime multipliers
        expert = self.apply_regime_multipliers(base, regime, sector)
        expert = normalize_weights(expert)
        
        # Step 4: Get RL weights if enabled
        rl_weights = None
        if use_rl:
            rl_weights = self.get_rl_weights(regime)
            
        # Step 5: Blend weights
        if rl_weights:
            final = self.blend_weights(expert, rl_weights, rl_blend_ratio)
        else:
            final = expert
            
        # Step 6: Normalize final weights
        final = normalize_weights(final)
        
        # Step 7: Create weight configurations for tracking
        configs = {}
        for agent in ALL_AGENTS:
            configs[agent] = WeightConfiguration(
                agent_name=agent,
                base_weight=base[agent],
                multiplier=expert[agent] / base[agent] if base[agent] > 0 else 1.0,
                rl_weight=rl_weights[agent] if rl_weights else expert[agent],
                final_weight=final[agent]
            )
            
        logger.info(
            f"Final weights computed for regime {regime.to_key()}, "
            f"RL={'enabled' if use_rl else 'disabled'}"
        )
        
        return final, regime, configs


if __name__ == "__main__":
    # Test weight manager
    logging.basicConfig(level=logging.INFO)
    
    from state import AgentOutput, DecisionState
    
    # Create test state
    test_outputs = {
        "inflation": AgentOutput(
            name="inflation",
            value="High inflation at 7%",
            confidence=0.9,
            sources=[]
        ),
        "interest_rates": AgentOutput(
            name="interest_rates",
            value="Rising rates, RBI hiked 50bps",
            confidence=0.95,
            sources=[]
        ),
        "current": AgentOutput(
            name="current",
            value="Weak quarterly results, bearish outlook",
            confidence=0.8,
            sources=[]
        ),
    }
    
    test_state = DecisionState(
        user_id="test",
        question="Test",
        symbol="TEST",
        sector="Banking",
        agent_outputs=test_outputs
    )
    
    manager = WeightManager()
    final, regime, configs = manager.get_final_weights(test_state, sector="banking", use_rl=False)
    
    print(f"Regime: {regime.to_key()}")
    print("\nTop weights:")
    sorted_weights = sorted(final.items(), key=lambda x: x[1], reverse=True)
    for agent, weight in sorted_weights[:10]:
        config = configs[agent]
        print(f"  {config.explain()}")
    print(f"\nTotal: {sum(final.values()):.6f}")
