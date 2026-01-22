import logging
from state import DecisionState
from providers import company

logger = logging.getLogger(__name__)


async def earnings_volatility_agent(state: DecisionState) -> dict:
    symbol = state["symbol"]
    logger.info("Triggering earnings volatility agent for symbol: %s", symbol)
    output = company.earnings_volatility(symbol)
    logger.info(
        "Earnings volatility agent response: value=%s, confidence=%.2f, sources=%d",
        output.value,
        output.confidence,
        len(output.sources),
    )
    return {"agent_outputs": {output.name: output}}


async def agm_agent(state: DecisionState) -> dict:
    symbol = state["symbol"]
    logger.info("Triggering AGM agent for symbol: %s", symbol)
    output = company.agm(symbol)
    logger.info(
        "AGM agent response: value='%s...', confidence=%.2f, sources=%d",
        output.value[:50],
        output.confidence,
        len(output.sources),
    )
    return {"agent_outputs": {output.name: output}}


async def governance_agent(state: DecisionState) -> dict:
    symbol = state["symbol"]
    logger.info("Triggering governance agent for symbol: %s", symbol)
    output = company.governance(symbol)
    logger.info(
        "Governance agent response: value='%s...', confidence=%.2f, sources=%d",
        output.value[:50],
        output.confidence,
        len(output.sources),
    )
    return {"agent_outputs": {output.name: output}}


async def sector_shocks_agent(state: DecisionState) -> dict:
    symbol = state["symbol"]
    sector = state.get("sector")
    logger.info(
        "Triggering sector shocks agent for symbol: %s, sector: %s", symbol, sector
    )
    output = company.sector_shocks(symbol, sector)
    logger.info(
        "Sector shocks agent response: value='%s...', confidence=%.2f, sources=%d",
        output.value[:50],
        output.confidence,
        len(output.sources),
    )
    return {"agent_outputs": {output.name: output}}


async def valuation_shocks_agent(state: DecisionState) -> dict:
    symbol = state["symbol"]
    logger.info("Triggering valuation shocks agent for symbol: %s", symbol)
    output = company.valuation_shocks(symbol)
    logger.info(
        "Valuation shocks agent response: value='%s...', confidence=%.2f, sources=%d",
        output.value[:50],
        output.confidence,
        len(output.sources),
    )
    return {"agent_outputs": {output.name: output}}


async def historical_agent(state: DecisionState) -> dict:
    symbol = state["symbol"]
    logger.info("Triggering historical agent for symbol: %s", symbol)
    output = company.historical(symbol)
    logger.info(
        "Historical agent response: value='%s...', confidence=%.2f, sources=%d",
        output.value[:50],
        output.confidence,
        len(output.sources),
    )
    return {"agent_outputs": {output.name: output}}


async def current_agent(state: DecisionState) -> dict:
    symbol = state["symbol"]
    logger.info("Triggering current price agent for symbol: %s", symbol)
    output = company.current(symbol)
    price_info = "N/A"
    if isinstance(output.value, dict) and "price" in output.value:
        price_info = f"₹{output.value['price']}"
    logger.info(
        "Current price agent response: value=%s, confidence=%.2f, sources=%d",
        price_info,
        output.confidence,
        len(output.sources),
    )
    return {"agent_outputs": {output.name: output}}


async def financial_performance_agent(state: DecisionState) -> dict:
    """Agent that gathers comprehensive financial performance data"""
    symbol = state["symbol"]

    logger.info("Triggering financial performance agent for symbol: %s", symbol)

    from providers.utils import NIFTY50_SYMBOLS

    company_name = NIFTY50_SYMBOLS.get(symbol, symbol)

    query = f"{company_name} {symbol} financial performance revenue growth profit margins EBITDA ROE ROA quarterly annual NSE BSE"
    search_result = company.search_web(query, "company", max_results=5)

    if not search_result["results"]:
        from state import AgentOutput

        output = AgentOutput(
            name="financial_performance",
            value="insufficient",
            confidence=0.0,
            sources=[],
            notes=f"No financial performance data found for {symbol}",
        )
        logger.info(
            "Financial performance agent response: value=%s, confidence=%.2f, sources=%d",
            output.value,
            output.confidence,
            len(output.sources),
        )
        return {"agent_outputs": {output.name: output}}

    # Extract financial performance information
    performance_data = []
    sources = []

    for result in search_result["results"]:
        content = result.get("content", "")
        title = result.get("title", "")

        # Look for financial metrics
        financial_keywords = [
            "revenue",
            "profit",
            "margin",
            "EBITDA",
            "ROE",
            "ROA",
            "growth",
            "earnings",
        ]
        if any(keyword in (content + title).lower() for keyword in financial_keywords):
            performance_data.append(f"{title}: {content[:250]}")
            sources.append(result["url"])

    combined_performance = (
        "; ".join(performance_data)
        if performance_data
        else "No financial performance data available"
    )

    from state import AgentOutput

    confidence = min(0.8, len(performance_data) * 0.2) if performance_data else 0.0

    output = AgentOutput(
        name="financial_performance",
        value=combined_performance,
        confidence=confidence,
        sources=sources,
        notes=f"Financial performance data for {symbol}",
    )

    logger.info(
        "Financial performance agent response: value='%s...', confidence=%.2f, sources=%d",
        output.value[:50],
        output.confidence,
        len(output.sources),
    )
    return {"agent_outputs": {output.name: output}}
