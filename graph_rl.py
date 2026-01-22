"""
RL-Enhanced Decision Graph with Thompson Sampling Weight Optimization.
Complete integration: Agents → RL Weighting → Regime Detection → Explainability → LLM Decision

Usage:
    from graph_rl import build_rl_graph
    graph = build_rl_graph()
    result = await graph.ainvoke(initial_state)
"""
import asyncio
import logging
from datetime import datetime
from langgraph.graph import StateGraph, END
from state import DecisionState, AgentOutput
from personal import personal_info
from llm import call_llm

# Import all 15 agents
from agents.macro_agents import inflation_agent, interest_rates_agent, gdp_growth_agent
from agents.news_policy_agents import policy_changes_agent
from agents.company_agents import (
    earnings_volatility_agent, agm_agent, governance_agent,
    sector_shocks_agent, valuation_shocks_agent, historical_agent,
    current_agent, financial_performance_agent,
)
from agents.data_quality_agents import (
    missing_financial_data_agent, missing_sentiment_agent, data_completeness_agent,
)

# Import RL components
from weight_manager import WeightManager
from rl_learner import ThompsonSamplingLearner
from database import DatabaseManager
from explainer import generate_weight_explanation
from data_accessor import NiftyDataAccessor
import numpy as np

logger = logging.getLogger(__name__)

# Initialize RL components globally
try:
    db_manager = DatabaseManager("kautilya_production.db")
    rl_learner = ThompsonSamplingLearner(db_manager)
    weight_manager = WeightManager(rl_learner=rl_learner)
    data_accessor = NiftyDataAccessor()
    RL_ENABLED = True
    logger.info("✅ RL components initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize RL components: {e}")
    RL_ENABLED = False
    db_manager = None
    rl_learner = None
    weight_manager = None
    data_accessor = None


def load_personal_context(state: DecisionState) -> dict:
    """Load user's personal investment profile."""
    user_id = state["user_id"]
    logger.info("Loading personal context for user: %s", user_id)
    personal_data = personal_info(user_id)

    if isinstance(personal_data, dict):
        context = f"User: {personal_data.get('name', 'Unknown')}, "
        context += f"Age: {personal_data.get('age', 'N/A')}, "
        context += f"Occupation: {personal_data.get('occupation', 'N/A')}, "
        context += f"Salary: {personal_data.get('salary', 'N/A')}"
    else:
        context = str(personal_data)

    logger.info("Personal context loaded: %s", context)
    return {"personal_context": context}


async def gather_signals(state: DecisionState) -> dict:
    """
    Run all 15 agents in parallel to gather comprehensive market signals.
    """
    logger.info("🔍 Gathering signals from 15 agents for symbol: %s", state.get("symbol"))

    agents = [
        inflation_agent, interest_rates_agent, gdp_growth_agent,
        policy_changes_agent, earnings_volatility_agent, agm_agent,
        governance_agent, sector_shocks_agent, valuation_shocks_agent,
        historical_agent, current_agent, financial_performance_agent,
        missing_financial_data_agent, missing_sentiment_agent, data_completeness_agent,
    ]

    logger.info("Executing %d agents in parallel...", len(agents))
    results = await asyncio.gather(*[agent(state) for agent in agents])

    merged_outputs = {}
    for result in results:
        if "agent_outputs" in result:
            merged_outputs.update(result["agent_outputs"])

    logger.info("✅ Collected outputs from %d agents", len(merged_outputs))
    return {"agent_outputs": merged_outputs}


def apply_rl_weighting(state: DecisionState) -> dict:
    """
    Apply RL-enhanced adaptive weighting to agent outputs.
    This is where Thompson Sampling magic happens!
    """
    logger.info("🤖 Applying RL-enhanced adaptive weighting...")
    
    if not RL_ENABLED or not weight_manager:
        logger.warning("⚠️  RL not available, using equal weights")
        # Fallback to equal weights
        agent_outputs = state.get("agent_outputs", {})
        num_agents = len(agent_outputs)
        equal_weights = {name: 1.0/num_agents for name in agent_outputs.keys()}
        return {"weights_used": equal_weights, "market_regime": "unknown", "weight_explanation": "RL not enabled"}
    
    try:
        # Calculate current market volatility for regime detection
        volatility = 0.15  # Default
        if data_accessor:
            try:
                recent_window = data_accessor.get_historical_window(
                    datetime.now(), days=20, include_end_date=True
                )
                if len(recent_window) > 10:
                    returns = recent_window['Close'].pct_change().dropna()
                    volatility = float(returns.std() * np.sqrt(252))
                    logger.info(f"📊 Calculated volatility: {volatility:.1%}")
            except Exception as e:
                logger.warning(f"Could not calculate volatility: {e}")
        
        # Get RL-optimized weights
        final_weights, regime, configs = weight_manager.get_final_weights(
            state,
            sector=state.get("sector"),
            use_rl=True,
            rl_blend_ratio=0.7,  # 70% RL, 30% expert
            technical_indicators={'volatility': volatility}
        )
        
        # Generate human-readable explanation
        weight_explanation = generate_weight_explanation(final_weights, regime, configs)
        
        # Log top weighted agents
        top_agents = sorted(final_weights.items(), key=lambda x: x[1], reverse=True)[:5]
        logger.info(f"✅ Regime detected: {regime.to_key()}")
        logger.info(f"🎯 Top 5 weighted agents: {[(name, f'{weight:.3f}') for name, weight in top_agents]}")
        
        return {
            "weights_used": final_weights,
            "market_regime": regime.to_key(),
            "weight_configs": configs,
            "volatility": volatility,
            "weight_explanation": weight_explanation
        }
        
    except Exception as e:
        logger.error(f"❌ RL weighting failed: {e}", exc_info=True)
        # Fallback to equal weights
        agent_outputs = state.get("agent_outputs", {})
        num_agents = len(agent_outputs)
        equal_weights = {name: 1.0/num_agents for name in agent_outputs.keys()}
        return {"weights_used": equal_weights, "market_regime": "error", "weight_explanation": f"Error: {str(e)}"}


def merge_context(state: DecisionState) -> dict:
    """
    Merge agent outputs with RL weights into prioritized context for LLM.
    HIGH priority agents get >10% weight, MEDIUM 5-10%, LOW <5%.
    """
    logger.info("📝 Merging agent outputs with RL-based prioritization...")
    
    agent_outputs = state.get("agent_outputs", {})
    weights = state.get("weights_used", {})
    all_citations = set()
    
    # Group agents by priority based on RL weights
    high_priority = []
    medium_priority = []
    low_priority = []
    
    for name, output in agent_outputs.items():
        if not isinstance(output, AgentOutput):
            continue
            
        weight = weights.get(name, 1.0/15)  # Default equal weight if not found
        
        # Format output with weight and confidence
        formatted = f"**{name.replace('_', ' ').title()}** (weight: {weight:.3f}, confidence: {output.confidence:.2f})\n"
        formatted += f"  {output.value}\n"
        if output.notes:
            formatted += f"  Notes: {output.notes}\n"
        
        # Collect citations
        if output.sources:
            all_citations.update(output.sources)
        
        # Categorize by weight
        if weight > 0.10:
            high_priority.append(formatted)
        elif weight > 0.05:
            medium_priority.append(formatted)
        else:
            low_priority.append(formatted)
    
    # Build prioritized context
    context_parts = []
    
    if high_priority:
        context_parts.append("=== 🔥 HIGH PRIORITY SIGNALS (weight > 0.10) ===")
        context_parts.append("These signals are MOST RELEVANT for current market conditions:\n")
        context_parts.extend(high_priority)
        context_parts.append("")
    
    if medium_priority:
        context_parts.append("=== 📊 MEDIUM PRIORITY SIGNALS (weight 0.05-0.10) ===")
        context_parts.extend(medium_priority)
        context_parts.append("")
    
    if low_priority:
        context_parts.append("=== 📋 SUPPORTING SIGNALS (weight < 0.05) ===")
        context_parts.extend(low_priority)
    
    full_context = "\n".join(context_parts)
    
    logger.info(f"✅ Context built: {len(high_priority)} high, {len(medium_priority)} medium, {len(low_priority)} low priority signals")
    
    return {"agent_summaries": full_context, "citations": list(all_citations)}


def decide_with_llm(state: DecisionState) -> dict:
    """
    Make final investment decision using LLM with RL-weighted, prioritized context.
    """
    logger.info("🧠 Making final decision with LLM for: %s", state["question"][:50])

    system_prompt = """You are an expert investment advisor for India equities (NIFTY50) using an advanced RL-enhanced multi-agent system.

CRITICAL: The signals are prioritized using Thompson Sampling reinforcement learning that adapts to market conditions.
- HIGH PRIORITY signals have >10% weight - these are MOST IMPORTANT for current market regime
- MEDIUM PRIORITY signals provide supporting context
- LOW PRIORITY signals are included for completeness

INSTRUCTIONS:
- Base your decision PRIMARILY on HIGH PRIORITY signals
- Use medium/low priority as supporting evidence only
- Make a clear BUY/HOLD/SELL recommendation
- Provide specific, actionable reasoning citing the high-priority factors
- Output strict JSON only"""

    agent_summaries = state.get("agent_summaries", "")
    weight_explanation = state.get("weight_explanation", "")
    regime = state.get("market_regime", "unknown")
    
    user_prompt = f"""Investment Question: {state['question']}
Symbol: {state['symbol']}
Sector: {state.get('sector', 'Unknown')}
Personal Context: {state.get('personal_context', '')}

AGENT ANALYSIS (RL-Weighted by Market Regime):
{agent_summaries}

---
WEIGHT EXPLANATION (Why these priorities):
{weight_explanation}
---
Detected Market Regime: {regime}
---

Required JSON output:
{{
  "decision": "BUY | HOLD | SELL",
  "confidence": 0.0-1.0,
  "horizon": "short | medium | long",
  "why": "Detailed explanation focusing on HIGH PRIORITY signals and their implications",
  "key_factors": ["specific high-priority factors driving this decision"],
  "risks": ["specific risks from the analysis"],
  "personalization_considerations": ["how this fits user profile"],
  "used_agents": ["list key agents that influenced decision"],
  "citations": {state.get('citations', [])}
}}"""

    try:
        logger.info("Sending RL-weighted context to LLM (%d chars)", len(user_prompt))
        decision_json = call_llm(system_prompt, user_prompt)
        
        # Add RL metadata to output for transparency
        decision_json["weight_explanation"] = weight_explanation
        decision_json["regime_detected"] = regime
        decision_json["rl_enabled"] = RL_ENABLED
        decision_json["volatility"] = state.get("volatility", 0.15)
        
        logger.info(
            "✅ Decision: %s (confidence: %.2f, regime: %s)",
            decision_json.get("decision", "UNKNOWN"),
            decision_json.get("confidence", 0.0),
            regime
        )
        
        return {"decision_json": decision_json}
        
    except Exception as e:
        logger.error("❌ LLM decision failed: %s", str(e))
        # Conservative fallback
        return {
            "decision_json": {
                "decision": "HOLD",
                "confidence": 0.1,
                "horizon": "medium",
                "why": f"System error: {str(e)}. Recommending HOLD as conservative default.",
                "key_factors": ["System error occurred"],
                "risks": ["Unable to analyze data properly"],
                "personalization_considerations": ["Conservative approach recommended"],
                "used_agents": [],
                "citations": [],
                "weight_explanation": "Error in processing",
                "regime_detected": "unknown",
                "rl_enabled": False
            }
        }


def build_rl_graph() -> StateGraph:
    """
    Build the complete RL-enhanced decision graph.
    
    Flow: Personal Context → Gather 15 Agents → RL Weighting → Merge Context → LLM Decision
    """
    logger.info("🏗️  Building RL-enhanced decision graph...")
    
    workflow = StateGraph(DecisionState)
    
    # Add nodes
    workflow.add_node("load_personal", load_personal_context)
    workflow.add_node("gather_signals", gather_signals)
    workflow.add_node("apply_rl_weighting", apply_rl_weighting)
    workflow.add_node("merge_context", merge_context)
    workflow.add_node("decide", decide_with_llm)
    
    # Define flow
    workflow.set_entry_point("load_personal")
    workflow.add_edge("load_personal", "gather_signals")
    workflow.add_edge("gather_signals", "apply_rl_weighting")  # RL weighting happens here!
    workflow.add_edge("apply_rl_weighting", "merge_context")
    workflow.add_edge("merge_context", "decide")
    workflow.add_edge("decide", END)
    
    logger.info("✅ RL-enhanced graph built successfully")
    
    return workflow.compile()


if __name__ == "__main__":
    # Test the RL-enhanced graph
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*80)
    print("TESTING RL-ENHANCED DECISION GRAPH")
    print("="*80 + "\n")
    
    test_state = {
        "user_id": "test_user",
        "question": "Should I invest in HDFC Bank for the next 6 months?",
        "symbol": "HDFC Bank",
        "sector": "Banking",
        "agent_outputs": {},
        "citations": [],
        "errors": []
    }
    
    graph = build_rl_graph()
    
    print("Running complete pipeline with RL weighting...\n")
    
    result = asyncio.run(graph.ainvoke(test_state))
    
    print("\n" + "="*80)
    print("FINAL DECISION OUTPUT")
    print("="*80)
    
    decision = result.get("decision_json", {})
    print(f"\n📊 Decision: {decision.get('decision')}")
    print(f"🎯 Confidence: {decision.get('confidence'):.2%}")
    print(f"🌡️  Market Regime: {decision.get('regime_detected')}")
    print(f"🤖 RL Enabled: {decision.get('rl_enabled')}")
    print(f"📈 Volatility: {decision.get('volatility', 0):.1%}")
    print(f"\n💡 Why: {decision.get('why')}")
    print(f"\n🔑 Key Factors: {decision.get('key_factors')}")
    
    print("\n" + "="*80)
    print("✅ RL-Enhanced Pipeline Test Complete")
    print("="*80)
