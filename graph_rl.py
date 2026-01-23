"""
RL-Enhanced Decision Graph with Thompson Sampling Weight Optimization.
Complete integration: Agents → RL Weighting → Regime Detection → Explainability → LLM Decision

Usage:
    from graph_rl import build_rl_graph
    graph = build_rl_graph()
    result = await graph.ainvoke(initial_state)
"""
import asyncio
import json
import logging
from datetime import datetime
from langgraph.graph import StateGraph, END
from state import DecisionState, AgentOutput
from personal import personal_info, get_investment_persona
from llm import call_llm
from config import USER_PROFILE_FILE, PRODUCTION_DB

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
    db_manager = DatabaseManager(str(PRODUCTION_DB))
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
    """Load user's personal investment profile with comprehensive details."""
    user_id = state["user_id"]
    logger.info("Loading personal context for user: %s", user_id)
    personal_data = personal_info(user_id)
    
    # FALLBACK: Check if we got default profile, if so try loading JSON directly
    # This addresses issues where personal.py might be cached or path resolution fails
    try:
        if personal_data.get("name") in ["Guest User", "Unknown"] or not personal_data.get("profile_complete"):
            profile_file = USER_PROFILE_FILE

            if profile_file.exists():
                logger.info("⚠️ Falling back to direct JSON loading from %s", profile_file)
                with open(profile_file, 'r') as f:
                    profile_json = json.load(f)
                    # We need to reconstruct the personal_data structure manually since personal_info did it
                    # This is a simplified version of what personal_info does, focusing on what LLM needs
                    personal_data = {
                        "name": profile_json.get("name", "User"),
                        "age": profile_json.get("age", 30),
                        "risk_profile": {
                            "risk_label": profile_json.get("risk_label", "Moderate"),
                            "risk_tolerance_score": profile_json.get("risk_tolerance", 5),
                            "notes": profile_json.get("market_drop_reaction", "")
                        },
                        "investment_goals": {
                            "primary_goal": profile_json.get("primary_goal", "Wealth Creation"),
                            "time_horizon": profile_json.get("investment_horizon", "5-10 years")
                        },
                        "portfolio_summary": {
                            "total_value": profile_json.get("portfolio_value", 0),
                            "holdings": profile_json.get("holdings", []),
                            "allocation": {
                                "equities": profile_json.get("equity_allocation", 0) / 100,
                                "mutual_funds": profile_json.get("mutual_fund_allocation", 0) / 100,
                                "bonds_fixed_deposits": profile_json.get("bonds_fd_allocation", 0) / 100,
                                "cash": profile_json.get("cash_allocation", 0) / 100,
                                "gold_etf": profile_json.get("gold_allocation", 0) / 100
                            }
                        },
                        "profile_complete": True
                    }
                    logger.info("✅ Successfully loaded profile directly from JSON. Holdings: %d", 
                               len(personal_data["portfolio_summary"]["holdings"]))
    except Exception as e:
        logger.error("❌ Direct JSON load failed: %s", e)

    # Get comprehensive investment persona for decision-making
    persona = get_investment_persona(user_id)

    # Build detailed context for LLM
    if isinstance(personal_data, dict):
        # Basic info
        context = f"User: {personal_data.get('name', 'Unknown')}\n"
        context += f"Age: {personal_data.get('age', 'N/A')}\n"
        context += f"Occupation: {personal_data.get('occupation', 'N/A')}\n"

        # Financial status
        salary = personal_data.get('salary', 0)
        if salary > 0:
            context += f"Annual Salary: ₹{salary:,}\n"

        # Risk profile
        risk_profile = personal_data.get('risk_profile', {})
        context += f"Risk Tolerance: {risk_profile.get('risk_label', 'Moderate')} ({risk_profile.get('risk_tolerance_score', 5)}/10)\n"
        context += f"Investment Experience: {risk_profile.get('investment_experience', 'Beginner')}\n"

        # Investment goals
        goals = personal_data.get('investment_goals', {})
        context += f"Primary Goal: {goals.get('primary_goal', 'Wealth Creation')}\n"
        context += f"Time Horizon: {goals.get('time_horizon', '5-10 years')}\n"

        # Portfolio info
        portfolio = personal_data.get('portfolio_summary', {})
        if portfolio.get('total_value', 0) > 0:
            context += f"Current Portfolio: ₹{portfolio['total_value']:,}\n"

        # Market preferences
        prefs = personal_data.get('market_preferences', {})
        if prefs.get('preferred_sectors'):
            context += f"Preferred Sectors: {', '.join(prefs['preferred_sectors'])}\n"
        if prefs.get('avoid_sectors'):
            context += f"Sectors to Avoid: {', '.join(prefs['avoid_sectors'])}\n"

        # Profile completeness warning
        if not personal_data.get('profile_complete', False):
            context += "\n⚠️ User profile incomplete - using conservative defaults.\n"
    else:
        context = str(personal_data)

    logger.info("Personal context loaded for: %s", personal_data.get('name', 'Unknown'))
    return {"personal_context": context, "personal_data": personal_data}


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
    Merge agent outputs with RL weights into compact prioritized context for LLM.
    Only HIGH priority signals get full details; others are summarized.
    """
    logger.info("📝 Merging agent outputs with RL-based prioritization...")

    agent_outputs = state.get("agent_outputs", {})
    weights = state.get("weights_used", {})
    all_citations = set()

    # Group agents by priority based on RL weights
    high_priority = []
    other_signals = []
    agent_names_used = []

    for name, output in agent_outputs.items():
        if not isinstance(output, AgentOutput):
            continue

        weight = weights.get(name, 1.0/15)
        agent_names_used.append(name.replace('_', ' ').title())

        # Collect citations
        if output.sources:
            all_citations.update(output.sources)

        # Only HIGH priority (>10% weight) gets full details
        if weight > 0.10:
            formatted = f"• {name.replace('_', ' ').title()} [w:{weight:.2f}]: {output.value}"
            if output.notes:
                formatted += f" ({output.notes})"
            high_priority.append(formatted)
        else:
            # Compact format for others: just name and signal direction
            value_str = str(output.value)
            signal = value_str[:50] + "..." if len(value_str) > 50 else value_str
            other_signals.append(f"{name.replace('_', ' ').title()}: {signal}")

    # Build compact context
    context_parts = []

    if high_priority:
        context_parts.append("KEY SIGNALS:")
        context_parts.extend(high_priority)

    if other_signals:
        context_parts.append("\nOTHER SIGNALS: " + " | ".join(other_signals))

    full_context = "\n".join(context_parts)

    logger.info(f"✅ Context built: {len(high_priority)} key signals, {len(other_signals)} supporting")

    return {
        "agent_summaries": full_context,
        "citations": list(all_citations),
        "agents_used": agent_names_used
    }


def _get_compact_portfolio(personal_data: dict) -> str:
    """Generate compact portfolio summary for LLM prompt."""
    portfolio = personal_data.get("portfolio_summary", {})
    if not portfolio:
        return "No portfolio data available"

    total = portfolio.get("total_value", 0)
    holdings = portfolio.get("holdings", [])
    allocation = portfolio.get("allocation", {})
    
    # Build portfolio context even if no specific holdings
    parts = [f"Total Portfolio Value: ₹{total:,}"]
    
    # Add allocation breakdown
    if allocation:
        alloc_parts = []
        if allocation.get("equities", 0) > 0:
            alloc_parts.append(f"Equities: {allocation['equities']*100:.0f}%")
        if allocation.get("mutual_funds", 0) > 0:
            alloc_parts.append(f"MFs: {allocation['mutual_funds']*100:.0f}%")
        if allocation.get("bonds_fixed_deposits", 0) > 0:
            alloc_parts.append(f"Bonds/FD: {allocation['bonds_fixed_deposits']*100:.0f}%")
        if allocation.get("cash", 0) > 0:
            alloc_parts.append(f"Cash: {allocation['cash']*100:.0f}%")
        if allocation.get("gold_etf", 0) > 0:
            alloc_parts.append(f"Gold: {allocation['gold_etf']*100:.0f}%")
        if alloc_parts:
            parts.append("Allocation: " + ", ".join(alloc_parts))

    # Add specific holdings if available
    if holdings:
        # Separate gainers and losers
        losers = [h for h in holdings if h.get("gain_loss_pct", 0) < 0]
        gainers = [h for h in holdings if h.get("gain_loss_pct", 0) >= 0]

        if losers:
            loss_summary = ", ".join([
                f"{h['ticker']}({h.get('gain_loss_pct', 0):+.1f}%)"
                for h in sorted(losers, key=lambda x: x.get("gain_loss_pct", 0))[:3]
            ])
            parts.append(f"📉 Losing Positions: {loss_summary}")

        if gainers:
            gain_summary = ", ".join([
                f"{h['ticker']}({h.get('gain_loss_pct', 0):+.1f}%)"
                for h in sorted(gainers, key=lambda x: x.get("gain_loss_pct", 0), reverse=True)[:3]
            ])
            parts.append(f"📈 Winning Positions: {gain_summary}")

        # Sector concentration
        sectors = {}
        for h in holdings:
            sec = h.get("sector", "Other")
            sectors[sec] = sectors.get(sec, 0) + h.get("value_inr", 0)
        if sectors and total > 0:
            top_sector = max(sectors.items(), key=lambda x: x[1])
            if top_sector[1] / total > 0.3:
                parts.append(f"⚠️ Sector Concentration: {top_sector[0]} ({top_sector[1]/total*100:.0f}%)")
    else:
        parts.append("No specific stock holdings tracked")

    return "\n".join(parts)


def decide_with_llm(state: DecisionState) -> dict:
    """
    Make final investment decision using LLM with RL-weighted, prioritized context.
    """
    logger.info("🧠 Making final decision with LLM for: %s", state["question"][:50])

    # Get personal data for personalization
    personal_data = state.get("personal_data", {})
    
    # Log personal data structure for debugging
    logger.info("📋 Personal data keys: %s", list(personal_data.keys()))
    portfolio_summary = personal_data.get("portfolio_summary", {})
    logger.info("📊 Portfolio summary keys: %s", list(portfolio_summary.keys()))
    logger.info("📈 Holdings count: %d", len(portfolio_summary.get("holdings", [])))
    logger.info("💼 Mutual funds count: %d", len(portfolio_summary.get("mutual_funds", [])))
    logger.info("💰 Portfolio total value: ₹%d", portfolio_summary.get("total_value", 0))
    
    # Log actual holdings data
    holdings = portfolio_summary.get("holdings", [])
    if holdings:
        logger.info("📌 Holdings details:")
        for h in holdings[:3]:  # Show first 3
            logger.info("   - %s (%s): ₹%d, P/L: %.1f%%", 
                       h.get("name", "?"), h.get("ticker", "?"), 
                       h.get("value_inr", 0), h.get("gain_loss_pct", 0))
    
    # Get formatted portfolio and log it
    portfolio_context = _get_compact_portfolio(personal_data)
    logger.info("📝 Formatted portfolio context:\n%s", portfolio_context)

    system_prompt = """You are an India equities (NIFTY50) investment advisor using RL-weighted multi-agent analysis.

REQUIREMENTS:
1. Reference user's age, risk profile, and specific holdings by name
2. Focus on KEY SIGNALS (highest RL weights) for current market regime
3. Mention relevant portfolio positions (especially losses or sector overlap)
4. Output strict JSON only
5. Use granular confidence scores (e.g., 0.65, 0.78, 0.82) based on signal strength and data completeness. Avoid default 0.5/0.6."""

    agent_summaries = state.get("agent_summaries", "")
    weight_explanation = state.get("weight_explanation", "")
    regime = state.get("market_regime", "unknown")
    agents_used = state.get("agents_used", [])
    citations = state.get("citations", [])

    user_prompt = f"""Q: {state['question']}
Symbol: {state['symbol']} | Sector: {state.get('sector', 'Unknown')} | Regime: {regime}

USER: {personal_data.get('name', 'User')}, Age {personal_data.get('age', 30)}, Risk: {personal_data.get('risk_profile', {}).get('risk_label', 'Moderate')}
Goal: {personal_data.get('investment_goals', {}).get('primary_goal', 'Wealth creation')} | Horizon: {personal_data.get('investment_goals', {}).get('time_horizon', 'Long-term')}

PORTFOLIO SUMMARY:
{_get_compact_portfolio(personal_data)}

{agent_summaries}

Regime Context: {weight_explanation}

Return JSON:
{{"decision":"BUY|HOLD|SELL","confidence":0.0-1.0,"horizon":"short|medium|long","why":"explanation referencing user profile","key_factors":["factors"],"risks":["risks"],"personalization_considerations":["3-5 user-specific points"],"used_agents":{json.dumps(agents_used)},"citations":{json.dumps(citations)}}}"""

    try:
        logger.info("Sending RL-weighted context to LLM (%d chars)", len(user_prompt))
        
        # Log complete payload being sent to Gemini
        logger.info("="*80)
        logger.info("📤 LLM PAYLOAD - SYSTEM PROMPT:")
        logger.info("="*80)
        logger.info(system_prompt)
        logger.info("="*80)
        logger.info("📤 LLM PAYLOAD - USER PROMPT:")
        logger.info("="*80)
        logger.info(user_prompt)
        logger.info("="*80)
        
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
