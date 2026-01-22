import logging
import re
from state import DecisionState
from providers.search_utils import search_web

logger = logging.getLogger(__name__)


def extract_missing_data_from_llm_response(llm_response: dict) -> list[str]:
    """Extract what data the LLM identifies as missing"""
    missing_data = []

    # Check the 'why' field for mentions of missing data
    why_text = llm_response.get("why", "")
    if isinstance(why_text, str):
        why_lower = why_text.lower()

        # Look for common patterns indicating missing data
        missing_patterns = [
            r"insufficient.*data",
            r"lack.*data",
            r"missing.*data",
            r"no.*data",
            r"absence.*data",
            r"limited.*data",
            r"need.*more.*data",
            r"require.*additional.*data",
        ]

        for pattern in missing_patterns:
            if re.search(pattern, why_lower):
                # Extract specific types of missing data
                if (
                    "financial" in why_lower
                    or "earnings" in why_lower
                    or "performance" in why_lower
                ):
                    missing_data.append("financial_data")
                if "sentiment" in why_lower or "technical" in why_lower:
                    missing_data.append("market_sentiment")
                if "valuation" in why_lower or "p/e" in why_lower:
                    missing_data.append("valuation_metrics")
                if "historical" in why_lower:
                    missing_data.append("historical_performance")
                if "current" in why_lower or "price" in why_lower:
                    missing_data.append("current_price")
                if "governance" in why_lower:
                    missing_data.append("corporate_governance")
                if "sector" in why_lower:
                    missing_data.append("sector_analysis")
                if (
                    "macro" in why_lower
                    or "inflation" in why_lower
                    or "interest" in why_lower
                ):
                    missing_data.append("macroeconomic_data")
                break

    # Check key_factors for missing data mentions
    key_factors = llm_response.get("key_factors", [])
    for factor in key_factors:
        factor_lower = factor.lower()
        if any(
            term in factor_lower
            for term in ["missing", "lack", "absence", "insufficient", "no"]
        ):
            if "financial" in factor_lower or "performance" in factor_lower:
                missing_data.append("financial_data")
            if "sentiment" in factor_lower or "technical" in factor_lower:
                missing_data.append("market_sentiment")

    return list(set(missing_data))  # Remove duplicates


async def search_for_missing_data(
    missing_data_types: list[str], state: DecisionState
) -> dict:
    """Search for specific types of missing data"""
    symbol = state["symbol"]
    from providers.utils import NIFTY50_SYMBOLS

    company_name = NIFTY50_SYMBOLS.get(symbol, symbol)

    additional_outputs = {}

    for data_type in missing_data_types:
        logger.info(
            "Searching for missing data type: %s for symbol: %s", data_type, symbol
        )

        if data_type == "financial_data":
            query = f"{company_name} {symbol} financial results earnings revenue profit quarterly annual NSE BSE"
            search_result = search_web(query, "company", max_results=4)

            if search_result["results"]:
                # Extract financial information
                financial_info = []
                sources = []
                for result in search_result["results"][:2]:
                    content = result.get("content", "")
                    title = result.get("title", "")
                    financial_info.append(f"{title}: {content[:300]}")
                    sources.append(result["url"])

                from state import AgentOutput

                output = AgentOutput(
                    name="additional_financial_data",
                    value="; ".join(financial_info),
                    confidence=0.7,
                    sources=sources,
                    notes=f"Additional financial data found for {symbol}",
                )
                additional_outputs[output.name] = output

        elif data_type == "market_sentiment":
            query = f"{company_name} {symbol} market sentiment analyst rating technical analysis NSE BSE"
            search_result = search_web(query, "company", max_results=4)

            if search_result["results"]:
                sentiment_info = []
                sources = []
                for result in search_result["results"][:2]:
                    content = result.get("content", "")
                    title = result.get("title", "")
                    sentiment_info.append(f"{title}: {content[:300]}")
                    sources.append(result["url"])

                from state import AgentOutput

                output = AgentOutput(
                    name="additional_sentiment_data",
                    value="; ".join(sentiment_info),
                    confidence=0.6,
                    sources=sources,
                    notes=f"Additional market sentiment data found for {symbol}",
                )
                additional_outputs[output.name] = output

        elif data_type == "valuation_metrics":
            query = f"{company_name} {symbol} valuation P/E ratio P/B ratio EPS NSE BSE"
            search_result = search_web(query, "company", max_results=3)

            if search_result["results"]:
                valuation_info = []
                sources = []
                for result in search_result["results"][:2]:
                    content = result.get("content", "")
                    title = result.get("title", "")
                    valuation_info.append(f"{title}: {content[:250]}")
                    sources.append(result["url"])

                from state import AgentOutput

                output = AgentOutput(
                    name="additional_valuation_data",
                    value="; ".join(valuation_info),
                    confidence=0.7,
                    sources=sources,
                    notes=f"Additional valuation metrics found for {symbol}",
                )
                additional_outputs[output.name] = output

    return additional_outputs


async def missing_data_search_agent(state: DecisionState) -> dict:
    """Agent that searches for data identified as missing by the LLM"""
    logger.info("Analyzing LLM response for missing data requirements")

    decision_json = state.get("decision_json")
    if not decision_json:
        logger.warning("No decision_json found in state, skipping missing data search")
        return {}

    # Extract what data is missing from LLM response
    missing_data_types = extract_missing_data_from_llm_response(decision_json)

    if not missing_data_types:
        logger.info("LLM response indicates no additional data is missing")
        return {}

    logger.info(
        "Found %d types of missing data: %s",
        len(missing_data_types),
        missing_data_types,
    )

    # Search for the missing data
    additional_outputs = await search_for_missing_data(missing_data_types, state)

    if additional_outputs:
        logger.info("Found additional data for %d categories", len(additional_outputs))

        # Update the state with new agent outputs
        updated_outputs = state.get("agent_outputs", {}).copy()
        updated_outputs.update(additional_outputs)

        return {
            "agent_outputs": updated_outputs,
            "additional_data_found": True,
            "missing_data_types": missing_data_types,
        }
    else:
        logger.info("No additional data found for missing categories")
        return {"additional_data_found": False}
