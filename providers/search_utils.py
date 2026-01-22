import os
from typing import Dict, Any
from tavily import TavilyClient


# Strict source validation rules
VALID_MACRO_SOURCES = {
    "rbi.org.in",
    "reservebankofindia.org.in",
    "rbidocs.rbi.org.in",
    "finmin.nic.in",
    "dea.gov.in",
    "mospi.gov.in",
    "statisticstimes.com",
    "tradingeconomics.com",
    "economictimes.indiatimes.com",
    "business-standard.com",
}

VALID_NEWS_SOURCES = {
    "pib.gov.in",
    "finmin.nic.in",
    "mospi.gov.in",
    "dea.gov.in",
    "sebi.gov.in",
    "nsdl.co.in",
    "cdslindia.com",
    "economictimes.indiatimes.com",
    "business-standard.com",
    "moneycontrol.com",
    "livemint.com",
    "thehindubusinessline.com",
}

VALID_COMPANY_SOURCES = {
    "nseindia.com",
    "bseindia.com",
    "moneycontrol.com",
    "bseindia.com",
    "nseindia.com",
    "bseindia.com",
    ".co.in",
    ".com",  # Company official websites
    "bloomberg.com",
    "reuters.com",
    "cnbc.com",
    "economictimes.indiatimes.com",
    "business-standard.com",
    "livemint.com",
    "thehindubusinessline.com",
}


def get_tavily_client():
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not set")
    return TavilyClient(api_key=api_key)


def validate_source(url: str, source_type: str) -> bool:
    """Validate if source URL is from trusted domains"""
    url_lower = url.lower()

    if source_type == "macro":
        return any(domain in url_lower for domain in VALID_MACRO_SOURCES)
    elif source_type == "news":
        return any(domain in url_lower for domain in VALID_NEWS_SOURCES)
    elif source_type == "company":
        return any(domain in url_lower for domain in VALID_COMPANY_SOURCES)
    return False


def search_web(query: str, source_type: str, max_results: int = 5) -> Dict[str, Any]:
    """Search web using Tavily with source validation"""
    try:
        client = get_tavily_client()

        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
            include_raw_content=True,
        )

        # Filter results by valid sources
        valid_results = []
        for result in response.get("results", []):
            if validate_source(result.get("url", ""), source_type):
                valid_results.append(result)

        return {
            "answer": response.get("answer", ""),
            "results": valid_results,
            "query": query,
        }
    except Exception as e:
        return {"answer": "", "results": [], "query": query, "error": str(e)}


def extract_value_from_content(content: str, query_type: str) -> Any:
    """Extract structured value from search content"""
    # This is a simple extraction - in production you'd use better parsing
    content_lower = content.lower()

    if query_type == "inflation":
        # Look for CPI, inflation rates
        if "cpi" in content_lower or "inflation" in content_lower:
            # Extract percentage values
            import re

            percentages = re.findall(r"(\d+\.?\d*)%", content)
            if percentages:
                return float(percentages[0])

    elif query_type == "interest_rates":
        # Look for repo rate, reverse repo rate
        if "repo" in content_lower:
            import re

            percentages = re.findall(r"(\d+\.?\d*)%", content)
            if percentages:
                return float(percentages[0])

    elif query_type == "gdp_growth":
        # Look for GDP growth rates
        if "gdp" in content_lower:
            import re

            percentages = re.findall(r"(\d+\.?\d*)%", content)
            if percentages:
                return float(percentages[0])

    # Default return the raw content
    return content[:500] if content else "No data found"
