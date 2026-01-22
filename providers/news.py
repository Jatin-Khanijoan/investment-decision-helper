from state import AgentOutput
from providers.search_utils import search_web


def policy_changes(sector: str | None) -> AgentOutput:
    try:
        if not sector:
            return AgentOutput(
                name="policy_changes",
                value="",
                confidence=0.0,
                sources=[],
                notes="No sector specified",
            )

        # Search for recent policy changes in the sector
        query = f"India government policy changes {sector} sector latest official"
        search_result = search_web(query, "news", max_results=5)

        if not search_result["results"]:
            return AgentOutput(
                name="policy_changes",
                value="",
                confidence=0.0,
                sources=[],
                notes=f"No recent policy changes found for {sector} sector",
            )

        # Extract policy information from results
        policy_info = []
        sources = []

        for result in search_result["results"][:3]:  # Top 3 results
            title = result.get("title", "")
            content = result.get("content", "")[:200]  # First 200 chars
            if title or content:
                policy_info.append(f"{title}: {content}")
                sources.append(result["url"])

        combined_info = (
            "; ".join(policy_info) if policy_info else "No significant policy changes"
        )

        # Determine confidence based on recency and number of sources
        confidence = min(0.8, len(search_result["results"]) * 0.2)

        return AgentOutput(
            name="policy_changes",
            value=combined_info,
            confidence=confidence,
            sources=sources,
            notes=f"Policy changes for {sector} sector from official/government sources",
        )
    except Exception as e:
        return AgentOutput(
            name="policy_changes",
            value="insufficient",
            confidence=0.0,
            sources=[],
            notes=f"Search failed: {str(e)}",
        )
