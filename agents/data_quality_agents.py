import logging
from state import DecisionState
from providers.search_utils import search_web

logger = logging.getLogger(__name__)


async def missing_financial_data_agent(state: DecisionState) -> dict:
    """Agent that identifies absence of financial data for the symbol"""
    symbol = state["symbol"]

    logger.info("Assessing financial data availability for symbol: %s", symbol)

    # Check what financial data we have
    agent_outputs = state.get("agent_outputs", {})

    missing_data_points = []

    # Check for key financial metrics
    if (
        "earnings_volatility" not in agent_outputs
        or agent_outputs["earnings_volatility"].value == "insufficient"
    ):
        missing_data_points.append("earnings data and volatility metrics")

    if (
        "valuation_shocks" not in agent_outputs
        or agent_outputs["valuation_shocks"].value == "insufficient"
    ):
        missing_data_points.append("valuation metrics (P/E, P/B ratios)")

    if (
        "historical" not in agent_outputs
        or agent_outputs["historical"].value == "insufficient"
    ):
        missing_data_points.append("historical performance data")

    if (
        "current" not in agent_outputs
        or agent_outputs["current"].value == "insufficient"
    ):
        missing_data_points.append("current price and market data")

    from providers.utils import NIFTY50_SYMBOLS

    company_name = NIFTY50_SYMBOLS.get(symbol, symbol)

    # Search for any available financial data
    query = f"{company_name} {symbol} financial data earnings revenue growth NSE BSE"
    search_result = search_web(query, "company", max_results=3)

    data_available = []
    sources = []

    if search_result["results"]:
        for result in search_result["results"]:
            content = result.get("content", "")
            if any(
                term in content.lower()
                for term in ["earnings", "revenue", "profit", "growth", "quarterly"]
            ):
                data_available.append("Some financial data found")
                sources.append(result["url"])
                break

    if not data_available:
        data_available.append("No specific financial data located")

    assessment = f"Absence of {symbol}-specific financial data"
    if missing_data_points:
        assessment += f" including: {', '.join(missing_data_points)}"

    from state import AgentOutput

    output = AgentOutput(
        name="missing_financial_data",
        value=assessment,
        confidence=0.9 if not data_available[0].startswith("No") else 0.3,
        sources=sources,
        notes=f"Financial data assessment for {symbol}",
    )

    logger.info(
        "Missing financial data assessment: %s (confidence: %.2f)",
        assessment,
        output.confidence,
    )
    return {"agent_outputs": {output.name: output}}


async def missing_sentiment_agent(state: DecisionState) -> dict:
    """Agent that identifies lack of market sentiment and technical indicators"""
    symbol = state["symbol"]

    logger.info("Assessing market sentiment availability for symbol: %s", symbol)

    # We don't have dedicated sentiment agents, so most sentiment data will be missing
    missing_sentiment_points = []

    # We don't have dedicated sentiment agents, so most sentiment data will be missing
    missing_sentiment_points.extend(
        [
            "market sentiment indicators",
            "technical analysis signals",
            "analyst recommendations",
            "news sentiment analysis",
        ]
    )

    from providers.utils import NIFTY50_SYMBOLS

    company_name = NIFTY50_SYMBOLS.get(symbol, symbol)

    # Search for sentiment indicators
    query = f"{company_name} {symbol} market sentiment technical analysis analyst rating NSE BSE"
    search_result = search_web(query, "company", max_results=3)

    sentiment_available = []
    sources = []

    if search_result["results"]:
        for result in search_result["results"]:
            content = result.get("content", "")
            if any(
                term in content.lower()
                for term in [
                    "sentiment",
                    "technical",
                    "analyst",
                    "rating",
                    "bullish",
                    "bearish",
                ]
            ):
                sentiment_available.append("Some sentiment data found")
                sources.append(result["url"])
                break

    if not sentiment_available:
        sentiment_available.append("No market sentiment indicators located")

    assessment = f"Lack of market sentiment or technical indicators for {symbol}"
    if missing_sentiment_points:
        assessment += f" - missing: {', '.join(missing_sentiment_points)}"

    from state import AgentOutput

    output = AgentOutput(
        name="missing_sentiment",
        value=assessment,
        confidence=0.9,  # We know sentiment data is generally missing
        sources=sources,
        notes=f"Market sentiment assessment for {symbol}",
    )

    logger.info(
        "Missing sentiment assessment: %s (confidence: %.2f)",
        assessment,
        output.confidence,
    )
    return {"agent_outputs": {output.name: output}}


async def data_completeness_agent(state: DecisionState) -> dict:
    """Agent that assesses the necessity for comprehensive data"""
    symbol = state["symbol"]

    logger.info("Assessing data completeness requirements for symbol: %s", symbol)

    agent_outputs = state.get("agent_outputs", {})
    total_agents = 15  # Total number of agents we run
    successful_agents = sum(
        1
        for output in agent_outputs.values()
        if hasattr(output, "value") and output.value != "insufficient"
    )

    completeness_ratio = successful_agents / total_agents if total_agents > 0 else 0

    assessment = f"The necessity for comprehensive data to make informed investment decisions for {symbol}"

    if completeness_ratio < 0.5:
        assessment += ". Current data completeness is low, requiring additional research before confident decisions."
    elif completeness_ratio < 0.8:
        assessment += (
            ". Moderate data availability suggests need for supplementary analysis."
        )
    else:
        assessment += ". Good data coverage available for analysis."

    from state import AgentOutput

    output = AgentOutput(
        name="data_completeness",
        value=assessment,
        confidence=completeness_ratio,
        sources=[],  # This is a meta-assessment
        notes=f"Data completeness assessment: {successful_agents}/{total_agents} agents successful",
    )

    logger.info(
        "Data completeness assessment: %.1f%% complete (confidence: %.2f)",
        completeness_ratio * 100,
        output.confidence,
    )
    return {"agent_outputs": {output.name: output}}
