"""
Explainability module for RL-based investment decisions.
Generates human-readable explanations of weights, regimes, and RL learning.
"""
import logging
from typing import Dict, List, Optional, Tuple
from rl_models import MarketRegime, WeightConfiguration
from rl_learner import ThompsonSamplingLearner
from database import DatabaseManager

logger = logging.getLogger(__name__)


def generate_regime_description(regime: MarketRegime) -> str:
    """
    Generate plain-language description of market regime.
    
    Args:
        regime: MarketRegime object
        
    Returns:
        Human-readable description
    """
    # Inflation description
    inflation_desc = {
        "low": "low inflation (< 4%)",
        "medium": "moderate inflation (4-6%)",
        "high": "high inflation (> 6%)"
    }.get(regime.inflation, "unknown inflation")
    
    # Rate trend description
    rate_desc = {
        "falling": "falling interest rates",
        "stable": "stable interest rates",
        "rising": "rising interest rates"
    }.get(regime.rate_trend, "unknown rate trend")
    
    # Sentiment description
    sentiment_desc = {
        "bearish": "bearish market sentiment",
        "neutral": "neutral market sentiment",
        "bullish": "bullish market sentiment"
    }.get(regime.sentiment, "unknown sentiment")
    
    # Volatility description
    vol = regime.volatility
    if vol > 0.25:
        vol_desc = "very high volatility"
    elif vol > 0.20:
        vol_desc = "high volatility"
    elif vol > 0.15:
        vol_desc = "moderate volatility"
    else:
        vol_desc = "low volatility"
        
    description = (
        f"Market regime: {inflation_desc}, {rate_desc}, {sentiment_desc}, "
        f"with {vol_desc} ({vol:.1%} annualized)"
    )
    
    return description


def explain_agent_weight(
    agent_name: str,
    config: WeightConfiguration,
    regime: MarketRegime
) -> str:
    """
    Explain why an agent has its current weight.
    
    Args:
        agent_name: Name of the agent
        config: Weight configuration for the agent
        regime: Current market regime
        
    Returns:
        Explanation string
    """
    # Agent role descriptions
    agent_roles = {
        "inflation": "Monitors inflation trends and purchasing power impact",
        "interest_rates": "Tracks RBI rate changes and monetary policy",
        "gdp_growth": "Analyzes economic growth and sector performance",
        "policy_changes": "Identifies regulatory and policy shifts",
        "earnings_volatility": "Assesses earnings stability and surprises",
        "agm": "Reviews shareholder meeting outcomes and governance signals",
        "governance": "Evaluates board quality and corporate governance",
        "sector_shocks": "Detects industry-specific disruptions",
        "valuation_shocks": "Monitors sudden valuation changes",
        "historical": "Analyzes long-term performance patterns",
        "current": "Examines recent company performance",
        "financial_performance": "Reviews financial statements and ratios",
        "missing_financial_data": "Flags data gaps in financial reporting",
        "missing_sentiment": "Identifies missing sentiment signals",
        "data_completeness": "Assesses overall data quality"
    }
    
    role = agent_roles.get(agent_name, "Analyzes market signals")
    
    # Explain multiplier
    if config.multiplier > 1.2:
        regime_impact = "boosted significantly"
    elif config.multiplier > 1.05:
        regime_impact = "moderately increased"
    elif config.multiplier < 0.85:
        regime_impact = "significantly reduced"
    elif config.multiplier < 0.95:
        regime_impact = "moderately reduced"
    else:
        regime_impact = "kept stable"
        
    explanation = (
        f"{agent_name.replace('_', ' ').title()}: {role}. "
        f"Weight {regime_impact} for current regime (base={config.base_weight:.3f}, "
        f"×{config.multiplier:.2f} = {config.final_weight:.3f})"
    )
    
    return explanation


def generate_weight_explanation(
    weights: Dict[str, float],
    regime: MarketRegime,
    configs: Dict[str, WeightConfiguration],
    rl_stats: Optional[Dict] = None
) -> str:
    """
    Generate comprehensive weight explanation.
    
    Args:
        weights: Final agent weights
        regime: Detected market regime
        configs: Weight configurations for all agents
        rl_stats: Optional RL learning statistics
        
    Returns:
        Formatted explanation string
    """
    lines = []
    
    # Regime description
    lines.append("📊 MARKET REGIME")
    lines.append(generate_regime_description(regime))
    lines.append("")
    
    # Top weighted agents
    lines.append("🎯 TOP WEIGHTED AGENTS")
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    
    for i, (agent, weight) in enumerate(sorted_weights[:5], 1):
        config = configs.get(agent)
        if config:
            lines.append(f"{i}. {explain_agent_weight(agent, config, regime)}")
    
    lines.append("")
    
    # RL learning status
    if rl_stats:
        lines.append("🤖 RL LEARNING STATUS")
        lines.append(f"Decisions learned from: {rl_stats.get('total_decisions', 0)}")
        lines.append(f"Regime familiarity: {rl_stats.get('decisions_in_regime', 0)} decisions in this regime")
        
        if 'top_reliable_agents' in rl_stats:
            lines.append(f"Most reliable agents: {', '.join(rl_stats['top_reliable_agents'][:3])}")
    
    return "\n".join(lines)


def generate_rl_proof(
    regime: MarketRegime,
    rl_learner: ThompsonSamplingLearner,
    db: DatabaseManager
) -> Dict:
    """
    Generate RL proof statistics showing learning effectiveness.
    
    Args:
        regime: Current market regime
        rl_learner: RL learner instance
        db: Database manager
        
    Returns:
        Dictionary with RL proof statistics
    """
    regime_key = regime.to_key()
    
    # Get RL statistics
    rl_stats = rl_learner.get_statistics(regime)
    
    # Query decision history for this regime
    decisions_in_regime = db.get_decisions_by_regime(regime_key)
    
    # Calculate metrics
    total_decisions = len(decisions_in_regime)
    
    if total_decisions > 0:
        # Evaluate decisions
        evaluated = [d for d in decisions_in_regime if d.get('evaluated')]
        correct = 0
        total_reward = 0.0
        
        for d in evaluated:
            if d.get('reward'):
                total_reward += d['reward']
                # Check if correct
                decision = d.get('decision')
                outcome = d.get('outcome_7d', 0)
                if decision == 'BUY' and outcome > 1.0:
                    correct += 1
                elif decision == 'SELL' and outcome < -1.0:
                    correct += 1
                elif decision == 'HOLD' and abs(outcome) < 2.0:
                    correct += 1
        
        accuracy = (correct / len(evaluated) * 100) if evaluated else 0
        avg_reward = (total_reward / len(evaluated)) if evaluated else 0
    else:
        accuracy = 0
        avg_reward = 0
        
    # Find most reliable agents
    sorted_by_reliability = sorted(
        rl_stats.items(),
        key=lambda x: x[1]['reliability'],
        reverse=True
    )
    top_reliable = [agent for agent, stats in sorted_by_reliability[:5]]
    
    # Weight evolution (compare to initial uniform)
    weight_changes = {}
    for agent, stats in rl_stats.items():
        initial_weight = 1.0 / 15  # Uniform prior
        current_weight = stats['mean_weight']
        change = current_weight - initial_weight
        weight_changes[agent] = change
        
    # Find agents with biggest weight changes
    top_gainers = sorted(weight_changes.items(), key=lambda x: x[1], reverse=True)[:3]
    top_losers = sorted(weight_changes.items(), key=lambda x: x[1])[:3]
    
    proof = {
        'regime': regime_key,
        'total_decisions': total_decisions,
        'decisions_evaluated': len([d for d in decisions_in_regime if d.get('evaluated')]),
        'accuracy_in_regime': accuracy,
        'avg_reward': avg_reward,
        'top_reliable_agents': top_reliable,
        'weight_gainers': [(agent, f"+{change:.3f}") for agent, change in top_gainers],
        'weight_losers': [(agent, f"{change:.3f}") for agent, change in top_losers],
        'total_observations': sum(s['total_observations'] for s in rl_stats.values())
    }
    
    return proof


def format_rl_proof_for_display(proof: Dict) -> str:
    """
    Format RL proof statistics for display.
    
    Args:
        proof: RL proof dictionary
        
    Returns:
        Formatted string
    """
    lines = []
    
    lines.append("🔬 RL LEARNING PROOF")
    lines.append(f"Regime: {proof['regime']}")
    lines.append(f"Total decisions in this regime: {proof['total_decisions']}")
    lines.append(f"Accuracy: {proof['accuracy_in_regime']:.1f}%")
    lines.append(f"Average reward: {proof['avg_reward']:.3f}")
    lines.append("")
    
    if proof['weight_gainers']:
        lines.append("📈 Agents gaining weight through learning:")
        for agent, change in proof['weight_gainers']:
            lines.append(f"  • {agent.replace('_', ' ').title()}: {change}")
    
    lines.append("")
    
    if proof['weight_losers']:
        lines.append("📉 Agents losing weight through learning:")
        for agent, change in proof['weight_losers'][:3]:
            lines.append(f"  • {agent.replace('_', ' ').title()}: {change}")
    
    lines.append("")
    lines.append(f"Total RL observations: {proof['total_observations']}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Test explainer
    logging.basicConfig(level=logging.INFO)
    
    from weight_manager import WeightManager
    from state import AgentOutput, DecisionState
    
    # Create test scenario
    test_regime = MarketRegime(
        inflation="high",
        rate_trend="rising",
        sentiment="bearish",
        volatility=0.22
    )
    
    print("Regime Description:")
    print(generate_regime_description(test_regime))
    print()
    
    # Test with weight manager
    weight_manager = WeightManager()
    test_state = DecisionState(
        user_id="test",
        question="Test",
        symbol="TEST",
        agent_outputs={}
    )
    
    weights, regime, configs = weight_manager.get_final_weights(
        test_state,
        sector="banking",
        use_rl=False,
        technical_indicators={'volatility': 0.22}
    )
    
    print("Weight Explanation:")
    explanation = generate_weight_explanation(weights, test_regime, configs)
    print(explanation)
