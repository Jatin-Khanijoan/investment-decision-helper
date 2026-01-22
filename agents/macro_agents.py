import logging
from state import DecisionState
from providers import macro

logger = logging.getLogger(__name__)


async def inflation_agent(state: DecisionState) -> dict:
    logger.info("Triggering inflation agent for symbol: %s", state.get("symbol"))
    output = macro.inflation_in()
    logger.info(
        "Inflation agent response: value=%s, confidence=%.2f, sources=%d",
        output.value,
        output.confidence,
        len(output.sources),
    )
    return {"agent_outputs": {output.name: output}}


async def interest_rates_agent(state: DecisionState) -> dict:
    logger.info("Triggering interest rates agent for symbol: %s", state.get("symbol"))
    output = macro.repo_rate_in()
    logger.info(
        "Interest rates agent response: value=%s, confidence=%.2f, sources=%d",
        output.value,
        output.confidence,
        len(output.sources),
    )
    return {"agent_outputs": {output.name: output}}


async def gdp_growth_agent(state: DecisionState) -> dict:
    logger.info("Triggering GDP growth agent for symbol: %s", state.get("symbol"))
    output = macro.gdp_growth_in()
    logger.info(
        "GDP growth agent response: value=%s, confidence=%.2f, sources=%d",
        output.value,
        output.confidence,
        len(output.sources),
    )
    return {"agent_outputs": {output.name: output}}
