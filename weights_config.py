"""
Base weight configuration for 15 agents.
Defines expert-determined weight distributions.
"""
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Define all 15 agents
ALL_AGENTS = [
    # Macro agents (3)
    "inflation",
    "interest_rates",
    "gdp_growth",
    # Policy agents (1)
    "policy_changes",
    # Company agents (8)
    "earnings_volatility",
    "agm",
    "governance",
    "sector_shocks",
    "valuation_shocks",
    "historical",
    "current",
    "financial_performance",
    # Data quality agents (3)
    "missing_financial_data",
    "missing_sentiment",
    "data_completeness",
]

# Base weights - expert-determined distribution
# These sum to 1.0
BASE_WEIGHTS = {
    # Macro agents - Total: 0.25 (macro matters but not everything)
    "inflation": 0.10,
    "interest_rates": 0.10,
    "gdp_growth": 0.05,
    
    # Policy agents - Total: 0.05 (important but episodic)
    "policy_changes": 0.05,
    
    # Company agents - Total: 0.55 (most important for stock decisions)
    "earnings_volatility": 0.08,
    "agm": 0.03,
    "governance": 0.05,
    "sector_shocks": 0.07,
    "valuation_shocks": 0.08,
    "historical": 0.08,
    "current": 0.10,
    "financial_performance": 0.06,
    
    # Data quality agents - Total: 0.15 (meta-signals)
    "missing_financial_data": 0.05,
    "missing_sentiment": 0.05,
    "data_completeness": 0.05,
}

# Categorization for regime multipliers
AGENT_CATEGORIES = {
    "macro": ["inflation", "interest_rates", "gdp_growth"],
    "policy": ["policy_changes"],
    "company": [
        "earnings_volatility", "agm", "governance", "sector_shocks",
        "valuation_shocks", "historical", "current", "financial_performance"
    ],
    "data_quality": ["missing_financial_data", "missing_sentiment", "data_completeness"],
}

# Inverse mapping
AGENT_TO_CATEGORY = {}
for category, agents in AGENT_CATEGORIES.items():
    for agent in agents:
        AGENT_TO_CATEGORY[agent] = category


def get_base_weights() -> Dict[str, float]:
    """
    Get base weight distribution for all agents.
    
    Returns:
        Dictionary mapping agent names to base weights
    """
    return BASE_WEIGHTS.copy()


def validate_weights(weights: Dict[str, float]) -> bool:
    """
    Validate that weights sum to 1.0 and all agents are present.
    
    Args:
        weights: Dictionary of agent weights
        
    Returns:
        True if valid, False otherwise
    """
    # Check all agents are present
    if set(weights.keys()) != set(ALL_AGENTS):
        missing = set(ALL_AGENTS) - set(weights.keys())
        extra = set(weights.keys()) - set(ALL_AGENTS)
        logger.error(f"Weight validation failed: missing={missing}, extra={extra}")
        return False
        
    # Check weights sum to approximately 1.0
    total = sum(weights.values())
    if not (0.99 <= total <= 1.01):  # Allow small floating point error
        logger.error(f"Weights sum to {total}, not 1.0")
        return False
        
    # Check all weights are non-negative
    if any(w < 0 for w in weights.values()):
        logger.error("Some weights are negative")
        return False
        
    logger.info("Weight validation passed")
    return True


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize weights to sum to exactly 1.0.
    
    Args:
        weights: Dictionary of agent weights
        
    Returns:
        Normalized weights
    """
    total = sum(weights.values())
    if total == 0:
        logger.warning("All weights are zero, returning equal weights")
        return {agent: 1.0 / len(ALL_AGENTS) for agent in ALL_AGENTS}
        
    normalized = {agent: w / total for agent, w in weights.items()}
    logger.debug(f"Normalized weights from {total} to 1.0")
    return normalized


def get_rationale() -> Dict[str, str]:
    """
    Get rationale for each agent's base weight.
    
    Returns:
        Dictionary mapping agent names to rationale strings
    """
    return {
        "inflation": "Critical macro factor affecting valuations and sector rotation",
        "interest_rates": "Primary driver of discount rates and sector performance",
        "gdp_growth": "Broad economic context, less immediate for individual stocks",
        "policy_changes": "Episodic but high impact when they occur",
        "earnings_volatility": "Key company-specific risk factor",
        "agm": "Governance signals, lower weight as infrequent",
        "governance": "Important for risk assessment and ESG",
        "sector_shocks": "Critical for understanding relative performance",
        "valuation_shocks": "Important for entry/exit timing",
        "historical": "Context for current situation",
        "current": "Highest company weight - most relevant for NOW",
        "financial_performance": "Core fundamental analysis",
        "missing_financial_data": "Meta-signal about reliability",
        "missing_sentiment": "Meta-signal about information availability",
        "data_completeness": "Overall data quality indicator",
    }


if __name__ == "__main__":
    # Test weights configuration
    logging.basicConfig(level=logging.INFO)
    
    weights = get_base_weights()
    print("Base Weights:")
    for agent in ALL_AGENTS:
        category = AGENT_TO_CATEGORY[agent]
        print(f"  {agent:30s} ({category:15s}): {weights[agent]:.3f}")
    
    print(f"\nTotal: {sum(weights.values()):.6f}")
    print(f"Valid: {validate_weights(weights)}")
    
    print("\nCategory Totals:")
    for category, agents in AGENT_CATEGORIES.items():
        total = sum(weights[agent] for agent in agents)
        print(f"  {category:15s}: {total:.3f}")
