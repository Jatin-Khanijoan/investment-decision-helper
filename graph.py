import asyncio
import logging
from langgraph.graph import StateGraph, END
from state import DecisionState, AgentOutput
from personal import personal_info
from llm import call_llm
from agents.macro_agents import inflation_agent, interest_rates_agent, gdp_growth_agent
from agents.news_policy_agents import policy_changes_agent
from agents.company_agents import (
    earnings_volatility_agent,
    agm_agent,
    governance_agent,
    sector_shocks_agent,
    valuation_shocks_agent,
    historical_agent,
    current_agent,
    financial_performance_agent,
)
from agents.data_quality_agents import (
    missing_financial_data_agent,
    missing_sentiment_agent,
    data_completeness_agent,
)
from agents.missing_data_search_agent import missing_data_search_agent

logger = logging.getLogger(__name__)


def load_personal_context(state: DecisionState) -> dict:
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
    logger.info(
        "Starting parallel execution of 15 agents for symbol: %s", state.get("symbol")
    )

    agents = [
        inflation_agent,
        interest_rates_agent,
        gdp_growth_agent,
        policy_changes_agent,
        earnings_volatility_agent,
        agm_agent,
        governance_agent,
        sector_shocks_agent,
        valuation_shocks_agent,
        historical_agent,
        current_agent,
        financial_performance_agent,
        missing_financial_data_agent,
        missing_sentiment_agent,
        data_completeness_agent,
    ]

    logger.info("Executing %d agents in parallel", len(agents))
    results = await asyncio.gather(*[agent(state) for agent in agents])

    merged_outputs = {}
    for result in results:
        if "agent_outputs" in result:
            merged_outputs.update(result["agent_outputs"])

    logger.info("All agents completed. Collected %d agent outputs", len(merged_outputs))
    return {"agent_outputs": merged_outputs}


def merge_context(state: DecisionState) -> dict:
    logger.info("Merging agent outputs into context")
    outputs = state.get("agent_outputs", {})

    citations = set()

    # Group agents by category for better LLM understanding
    macro_data = []
    company_data = []
    policy_data = []
    quality_data = []

    for name, output in outputs.items():
        if isinstance(output, AgentOutput):
            # Format each agent output clearly
            if output.value != "insufficient":
                formatted_output = f"• {name.replace('_', ' ').title()}: {output.value} (confidence: {output.confidence:.2f})"
                if output.notes:
                    formatted_output += f" - {output.notes}"
            else:
                formatted_output = f"• {name.replace('_', ' ').title()}: No data available (confidence: {output.confidence:.2f})"
                if output.notes:
                    formatted_output += f" - {output.notes}"

            if output.sources:
                citations.update(output.sources)

            # Categorize the data
            if name in ["inflation", "interest_rates", "gdp_growth"]:
                macro_data.append(formatted_output)
            elif name in ["policy_changes"]:
                policy_data.append(formatted_output)
            elif name in [
                "missing_financial_data",
                "missing_sentiment",
                "data_completeness",
            ]:
                quality_data.append(formatted_output)
            else:
                company_data.append(formatted_output)

    # Build structured context
    context_parts = []

    if macro_data:
        context_parts.append("=== MACROECONOMIC DATA ===")
        context_parts.extend(macro_data)
        context_parts.append("")

    if policy_data:
        context_parts.append("=== POLICY & REGULATORY DATA ===")
        context_parts.extend(policy_data)
        context_parts.append("")

    if company_data:
        context_parts.append("=== COMPANY-SPECIFIC DATA ===")
        context_parts.extend(company_data)
        context_parts.append("")

    if quality_data:
        context_parts.append("=== DATA QUALITY ASSESSMENT ===")
        context_parts.extend(quality_data)
        context_parts.append("")

    full_context = "\n".join(context_parts)
    logger.info(
        "Created structured context with %d agent outputs and %d citations",
        len(outputs),
        len(citations),
    )
    return {"agent_summaries": full_context, "citations": list(citations)}


def decide_with_llm(state: DecisionState) -> dict:
    logger.info(
        "Making final decision with LLM for question: %s", state["question"][:50]
    )

    system_prompt = """You are a disciplined investment reasoning model for India equities (NIFTY50). Use only provided context. Do not invent numbers. Make the best possible decision even with partial data. If confidence is low due to missing data, reflect that in the confidence score and explain in the 'why' field. Never use INSUFFICIENT_DATA as a decision - always choose BUY, HOLD, or SELL based on available information. Output strict JSON only."""

    agent_summaries = state.get("agent_summaries", "")

    user_prompt = f"""Question: {state['question']}
Symbol: {state['symbol']}
Personal Context: {state.get('personal_context', '')}

Below is comprehensive research data collected from multiple specialized agents:

{agent_summaries}

INSTRUCTIONS:
- Analyze ALL the data provided above across macroeconomic, company-specific, policy, and quality assessment categories
- Make a clear BUY/HOLD/SELL recommendation based on the available data
- Consider confidence levels and data completeness when assessing reliability
- If data is insufficient for a strong recommendation, use HOLD with low confidence
- Provide 3-6 specific bullet points explaining your reasoning
- Highlight key factors, risks, and how this relates to the user's profile

Required JSON structure:
{{
  "decision": "BUY | HOLD | SELL",
  "confidence": 0.0-1.0,
  "horizon": "short | medium | long",
  "why": "3-6 bullet points explaining the decision and noting any data limitations",
  "key_factors": ["specific factors from the data above"],
  "risks": ["specific risks identified from the data"],
  "personalization_considerations": ["how this relates to user profile"],
  "used_agents": ["list key data sources used"],
  "citations": {state.get('citations', [])}
}}"""

    try:
        logger.info("Sending context to LLM (%d chars)", len(user_prompt))
        decision_json = call_llm(system_prompt, user_prompt)
        logger.info(
            "LLM decision: %s (confidence: %.2f)",
            decision_json.get("decision", "UNKNOWN"),
            decision_json.get("confidence", 0.0),
        )
        return {"decision_json": decision_json}
    except Exception as e:
        logger.error("LLM decision failed: %s", str(e))
        # Provide a conservative HOLD decision when LLM fails
        return {
            "decision_json": {
                "decision": "HOLD",
                "confidence": 0.1,
                "horizon": "medium",
                "why": f"Decision system error: {str(e)}. Recommending HOLD as conservative default.",
                "key_factors": ["System error occurred"],
                "risks": ["Unable to analyze data properly"],
                "personalization_considerations": ["Conservative approach recommended"],
                "used_agents": [],
                "citations": [],
            }
        }


def search_missing_data(state: DecisionState) -> dict:
    """Node wrapper for missing data search agent"""
    import asyncio

    logger.info("Starting missing data search")
    result = asyncio.run(missing_data_search_agent(state))
    logger.info(
        "Missing data search completed, result keys: %s",
        list(result.keys()) if result else "None",
    )
    logger.info(
        "additional_data_found in result: %s",
        result.get("additional_data_found") if result else "N/A",
    )
    return result


def should_re_decide(state: DecisionState) -> str:
    """Conditional check if we should re-decide with additional data"""
    logger.info("Full state keys for conditional check: %s", list(state.keys()))
    additional_data_found = state.get("additional_data_found", False)
    logger.info("Checking if additional data was found: %s", additional_data_found)
    logger.info(
        "State additional_data_found value: %s", state.get("additional_data_found")
    )

    if additional_data_found:
        logger.info("Additional data found, re-deciding with updated information")
        return "re_decide"
    else:
        logger.info("No additional data found, proceeding with initial decision")
        return END


def re_decide_with_llm(state: DecisionState) -> dict:
    """Re-run LLM decision with additional data"""
    logger.info("Re-deciding with additional data found")

    # Update the agent summaries with new data
    outputs = state.get("agent_outputs", {})
    citations = set(state.get("citations", []))

    agent_summaries = []
    for name, output in outputs.items():
        if isinstance(output, AgentOutput):
            line = (
                f"[{output.name}] value={output.value} (conf={output.confidence:.2f})"
            )
            if output.sources:
                line += f" | sources={len(output.sources)}"
                citations.update(output.sources)
            agent_summaries.append(line)

    # Update state with new context
    state_copy = state.copy()
    state_copy["agent_summaries"] = "\n".join(agent_summaries)
    state_copy["citations"] = list(citations)

    # Re-run the decision
    system_prompt = """You are a disciplined investment reasoning model for India equities (NIFTY50). Use only provided context. Make the best possible decision even with partial data. This is an updated decision with additional research data. Output strict JSON only."""

    user_prompt = f"""Question: {state_copy['question']}
Symbol: {state_copy['symbol']}
Personal Context: {state_copy.get('personal_context', '')}

UPDATED Agent Data (includes additional research):
{state_copy["agent_summaries"]}

This decision incorporates additional data that was identified as missing in the initial analysis.

Constraints: JSON only, concise why

Required JSON structure:
{{
  "decision": "BUY | HOLD | SELL",
  "confidence": 0.0-1.0,
  "horizon": "short | medium | long",
  "why": "3-6 bullet points explaining the updated decision with additional data",
  "key_factors": ["..."],
  "risks": ["..."],
  "personalization_considerations": ["..."],
  "used_agents": ["..."],
  "citations": {state_copy.get('citations', [])}
}}"""

    try:
        logger.info(
            "Re-sending context to LLM with additional data (%d chars)",
            len(user_prompt),
        )
        decision_json = call_llm(system_prompt, user_prompt)
        logger.info(
            "Re-decision completed: %s (confidence: %.2f)",
            decision_json.get("decision", "UNKNOWN"),
            decision_json.get("confidence", 0.0),
        )
        return {"decision_json": decision_json}
    except Exception as e:
        logger.error("Re-decision LLM failed: %s", str(e))
        # Return the original decision if re-decision fails
        return {}


def build_graph() -> StateGraph:
    workflow = StateGraph(DecisionState)

    workflow.add_node("load_personal", load_personal_context)
    workflow.add_node("gather_signals", gather_signals)
    workflow.add_node("merge_context", merge_context)
    workflow.add_node("decide", decide_with_llm)
    workflow.add_node("search_missing", search_missing_data)
    workflow.add_node("re_decide", re_decide_with_llm)

    workflow.set_entry_point("load_personal")
    workflow.add_edge("load_personal", "gather_signals")
    workflow.add_edge("gather_signals", "merge_context")
    workflow.add_edge("merge_context", "decide")
    workflow.add_edge("decide", "search_missing")
    workflow.add_conditional_edges(
        "search_missing", should_re_decide, {"re_decide": "re_decide", END: END}
    )
    workflow.add_edge("re_decide", END)

    return workflow.compile()
