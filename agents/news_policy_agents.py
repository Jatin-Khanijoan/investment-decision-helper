import logging
from state import DecisionState
from providers import news

logger = logging.getLogger(__name__)


async def policy_changes_agent(state: DecisionState) -> dict:
    sector = state.get("sector")
    logger.info(
        "Triggering policy changes agent for symbol: %s, sector: %s",
        state.get("symbol"),
        sector,
    )
    output = news.policy_changes(sector)
    logger.info(
        "Policy changes agent response: value='%s...', confidence=%.2f, sources=%d",
        output.value[:100],
        output.confidence,
        len(output.sources),
    )
    return {"agent_outputs": {output.name: output}}
