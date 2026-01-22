from state import AgentOutput
from providers.search_utils import search_web, extract_value_from_content


def inflation_in() -> AgentOutput:
    try:
        query = "India CPI inflation rate latest RBI official"
        search_result = search_web(query, "macro", max_results=3)

        if not search_result["results"]:
            return AgentOutput(
                name="inflation",
                value="insufficient",
                confidence=0.0,
                sources=[],
                notes="No valid sources found",
            )

        # Extract inflation value from search results
        best_result = search_result["results"][0]
        content = best_result.get("content", "") + best_result.get("raw_content", "")
        value = extract_value_from_content(content, "inflation")

        sources = [r["url"] for r in search_result["results"]]

        return AgentOutput(
            name="inflation",
            value=value,
            confidence=0.8 if isinstance(value, (int, float)) else 0.3,
            sources=sources,
            notes="CPI YoY from RBI/official sources",
        )
    except Exception as e:
        return AgentOutput(
            name="inflation",
            value="insufficient",
            confidence=0.0,
            sources=[],
            notes=f"Search failed: {str(e)}",
        )


def repo_rate_in() -> AgentOutput:
    try:
        query = "India RBI repo rate current official"
        search_result = search_web(query, "macro", max_results=3)

        if not search_result["results"]:
            return AgentOutput(
                name="interest_rates",
                value="insufficient",
                confidence=0.0,
                sources=[],
                notes="No valid sources found",
            )

        # Extract repo rate from search results
        best_result = search_result["results"][0]
        content = best_result.get("content", "") + best_result.get("raw_content", "")
        value = extract_value_from_content(content, "interest_rates")

        sources = [r["url"] for r in search_result["results"]]

        return AgentOutput(
            name="interest_rates",
            value=value,
            confidence=0.9 if isinstance(value, (int, float)) else 0.4,
            sources=sources,
            notes="RBI repo rate official",
        )
    except Exception as e:
        return AgentOutput(
            name="interest_rates",
            value="insufficient",
            confidence=0.0,
            sources=[],
            notes=f"Search failed: {str(e)}",
        )


def gdp_growth_in() -> AgentOutput:
    try:
        query = "India GDP growth rate latest MOSPI official"
        search_result = search_web(query, "macro", max_results=3)

        if not search_result["results"]:
            return AgentOutput(
                name="gdp_growth",
                value="insufficient",
                confidence=0.0,
                sources=[],
                notes="No valid sources found",
            )

        # Extract GDP growth from search results
        best_result = search_result["results"][0]
        content = best_result.get("content", "") + best_result.get("raw_content", "")
        value = extract_value_from_content(content, "gdp_growth")

        sources = [r["url"] for r in search_result["results"]]

        return AgentOutput(
            name="gdp_growth",
            value=value,
            confidence=0.7 if isinstance(value, (int, float)) else 0.3,
            sources=sources,
            notes="GDP growth YoY from MOSPI/official sources",
        )
    except Exception as e:
        return AgentOutput(
            name="gdp_growth",
            value="insufficient",
            confidence=0.0,
            sources=[],
            notes=f"Search failed: {str(e)}",
        )
