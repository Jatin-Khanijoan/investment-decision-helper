import json
import re
from pathlib import Path
from state import AgentOutput
from providers.search_utils import search_web


def earnings_volatility(symbol: str) -> AgentOutput:
    try:
        # Get company name from symbol mapping
        from providers.utils import NIFTY50_SYMBOLS

        company_name = NIFTY50_SYMBOLS.get(symbol, symbol)

        query = (
            f"{company_name} {symbol} earnings volatility coefficient variation NSE BSE"
        )
        search_result = search_web(query, "company", max_results=4)

        if not search_result["results"]:
            return AgentOutput(
                name="earnings_volatility",
                value="insufficient",
                confidence=0.0,
                sources=[],
                notes=f"No earnings volatility data found for {symbol}",
            )

        # Extract volatility information
        volatility_info = []
        sources = []

        for result in search_result["results"]:
            content = result.get("content", "") + result.get("raw_content", "")
            # Look for volatility percentages or coefficients
            vol_matches = re.findall(
                r"(\d+\.?\d*)%\s*(?:volatility|variation)", content, re.IGNORECASE
            )
            if vol_matches:
                volatility_info.extend(
                    [float(match.replace("%", "")) for match in vol_matches]
                )
            sources.append(result["url"])

        if volatility_info:
            avg_volatility = (
                sum(volatility_info) / len(volatility_info) / 100
            )  # Convert to decimal
            confidence = min(0.8, len(volatility_info) * 0.2)
        else:
            avg_volatility = 0.15  # Default moderate volatility
            confidence = 0.3

        return AgentOutput(
            name="earnings_volatility",
            value=round(avg_volatility, 3),
            confidence=confidence,
            sources=sources,
            notes=f"Earnings volatility coefficient for {symbol}",
        )
    except Exception as e:
        return AgentOutput(
            name="earnings_volatility",
            value="insufficient",
            confidence=0.0,
            sources=[],
            notes=f"Search failed: {str(e)}",
        )


def agm(symbol: str) -> AgentOutput:
    try:
        from providers.utils import NIFTY50_SYMBOLS

        company_name = NIFTY50_SYMBOLS.get(symbol, symbol)

        query = (
            f"{company_name} {symbol} AGM annual general meeting date schedule NSE BSE"
        )
        search_result = search_web(query, "company", max_results=3)

        if not search_result["results"]:
            return AgentOutput(
                name="agm",
                value="",
                confidence=0.0,
                sources=[],
                notes=f"No AGM information found for {symbol}",
            )

        # Extract AGM information
        agm_info = []
        sources = []

        for result in search_result["results"]:
            content = result.get("content", "")
            title = result.get("title", "")

            # Look for AGM dates and information
            if "agm" in (content + title).lower():
                agm_info.append(f"{title}: {content[:150]}")
                sources.append(result["url"])

        combined_info = "; ".join(agm_info) if agm_info else "No recent AGM information"

        return AgentOutput(
            name="agm",
            value=combined_info,
            confidence=min(0.7, len(agm_info) * 0.25),
            sources=sources,
            notes=f"AGM information for {symbol}",
        )
    except Exception as e:
        return AgentOutput(
            name="agm",
            value="insufficient",
            confidence=0.0,
            sources=[],
            notes=f"Search failed: {str(e)}",
        )


def governance(symbol: str) -> AgentOutput:
    try:
        from providers.utils import NIFTY50_SYMBOLS

        company_name = NIFTY50_SYMBOLS.get(symbol, symbol)

        query = f"{company_name} {symbol} corporate governance issues controversies SEBI NSE BSE"
        search_result = search_web(query, "company", max_results=4)

        if not search_result["results"]:
            return AgentOutput(
                name="governance",
                value="",
                confidence=0.0,
                sources=[],
                notes=f"No governance issues found for {symbol}",
            )

        # Extract governance information
        governance_issues = []
        sources = []

        for result in search_result["results"]:
            content = result.get("content", "")
            title = result.get("title", "")

            # Look for governance-related keywords
            gov_keywords = [
                "governance",
                "board",
                "compliance",
                "regulatory",
                "sebi",
                "investigation",
            ]
            if any(keyword in (content + title).lower() for keyword in gov_keywords):
                governance_issues.append(f"{title}: {content[:200]}")
                sources.append(result["url"])

        combined_info = (
            "; ".join(governance_issues)
            if governance_issues
            else "No significant governance issues"
        )

        return AgentOutput(
            name="governance",
            value=combined_info,
            confidence=min(0.8, len(governance_issues) * 0.2),
            sources=sources,
            notes=f"Corporate governance information for {symbol}",
        )
    except Exception as e:
        return AgentOutput(
            name="governance",
            value="insufficient",
            confidence=0.0,
            sources=[],
            notes=f"Search failed: {str(e)}",
        )


def sector_shocks(symbol: str, sector: str | None) -> AgentOutput:
    try:
        if not sector:
            return AgentOutput(
                name="sector_shocks",
                value="",
                confidence=0.0,
                sources=[],
                notes="No sector specified",
            )

        from providers.utils import NIFTY50_SYMBOLS

        company_name = NIFTY50_SYMBOLS.get(symbol, symbol)

        query = (
            f"{sector} sector shocks news impact {company_name} {symbol} India latest"
        )
        search_result = search_web(query, "company", max_results=5)

        if not search_result["results"]:
            return AgentOutput(
                name="sector_shocks",
                value="",
                confidence=0.0,
                sources=[],
                notes=f"No sector shocks found for {sector}",
            )

        # Extract sector shock information
        shock_info = []
        sources = []

        for result in search_result["results"]:
            content = result.get("content", "")
            title = result.get("title", "")

            # Look for shock-related keywords
            shock_keywords = [
                "shock",
                "crisis",
                "impact",
                "disruption",
                "challenge",
                "issue",
            ]
            if any(keyword in (content + title).lower() for keyword in shock_keywords):
                shock_info.append(f"{title}: {content[:200]}")
                sources.append(result["url"])

        combined_info = (
            "; ".join(shock_info) if shock_info else "No significant sector shocks"
        )

        return AgentOutput(
            name="sector_shocks",
            value=combined_info,
            confidence=min(0.9, len(shock_info) * 0.2),
            sources=sources,
            notes=f"Sector shocks for {sector} affecting {symbol}",
        )
    except Exception as e:
        return AgentOutput(
            name="sector_shocks",
            value="insufficient",
            confidence=0.0,
            sources=[],
            notes=f"Search failed: {str(e)}",
        )


def valuation_shocks(symbol: str) -> AgentOutput:
    try:
        from providers.utils import NIFTY50_SYMBOLS

        company_name = NIFTY50_SYMBOLS.get(symbol, symbol)

        query = f"{company_name} {symbol} valuation shock discount premium P/E ratio NSE BSE"
        search_result = search_web(query, "company", max_results=4)

        if not search_result["results"]:
            return AgentOutput(
                name="valuation_shocks",
                value="",
                confidence=0.0,
                sources=[],
                notes=f"No valuation data found for {symbol}",
            )

        # Extract valuation information
        valuation_info = []
        sources = []

        for result in search_result["results"]:
            content = result.get("content", "")
            title = result.get("title", "")

            # Look for valuation metrics
            if any(
                term in (content + title).lower()
                for term in ["p/e", "valuation", "premium", "discount", "ratio"]
            ):
                valuation_info.append(f"{title}: {content[:200]}")
                sources.append(result["url"])

        combined_info = (
            "; ".join(valuation_info)
            if valuation_info
            else "No significant valuation shocks"
        )

        return AgentOutput(
            name="valuation_shocks",
            value=combined_info,
            confidence=min(0.7, len(valuation_info) * 0.2),
            sources=sources,
            notes=f"Valuation analysis for {symbol}",
        )
    except Exception as e:
        return AgentOutput(
            name="valuation_shocks",
            value="insufficient",
            confidence=0.0,
            sources=[],
            notes=f"Search failed: {str(e)}",
        )


def historical(symbol: str) -> AgentOutput:
    try:
        from providers.utils import NIFTY50_SYMBOLS

        company_name = NIFTY50_SYMBOLS.get(symbol, symbol)

        query = f"{company_name} {symbol} historical performance 5 year returns NSE BSE"
        search_result = search_web(query, "company", max_results=3)

        if not search_result["results"]:
            return AgentOutput(
                name="historical",
                value="",
                confidence=0.0,
                sources=[],
                notes=f"No historical data found for {symbol}",
            )

        # Extract historical performance information
        historical_info = []
        sources = []

        for result in search_result["results"]:
            content = result.get("content", "")
            title = result.get("title", "")

            # Look for historical performance data
            if any(
                term in (content + title).lower()
                for term in ["historical", "performance", "returns", "5 year", "past"]
            ):
                historical_info.append(f"{title}: {content[:250]}")
                sources.append(result["url"])

        combined_info = (
            "; ".join(historical_info)
            if historical_info
            else "No historical performance data"
        )

        return AgentOutput(
            name="historical",
            value=combined_info,
            confidence=min(0.8, len(historical_info) * 0.25),
            sources=sources,
            notes=f"Historical performance data for {symbol}",
        )
    except Exception as e:
        return AgentOutput(
            name="historical",
            value="insufficient",
            confidence=0.0,
            sources=[],
            notes=f"Search failed: {str(e)}",
        )


def current(symbol: str) -> AgentOutput:
    try:
        from providers.utils import NIFTY50_SYMBOLS

        company_name = NIFTY50_SYMBOLS.get(symbol, symbol)

        query = f"{company_name} {symbol} current stock price NSE BSE live"
        search_result = search_web(query, "company", max_results=2)

        # Try to read from stocks.json first as fallback
        price_data = None
        if Path("stocks.json").exists():
            try:
                with open("stocks.json") as f:
                    data = json.load(f)
                    # If stocks.json has price data, use it
                    if isinstance(data, dict) and symbol in data:
                        price_data = data[symbol]
            except (json.JSONDecodeError, IOError):
                pass

        if not search_result["results"] and not price_data:
            return AgentOutput(
                name="current",
                value="insufficient",
                confidence=0.0,
                sources=[],
                notes=f"No current price data found for {symbol}",
            )

        # Extract price from search results
        price_info = {}
        sources = []

        if search_result["results"]:
            for result in search_result["results"]:
                content = result.get("content", "")
                # Look for price patterns
                price_matches = re.findall(r"₹\s*(\d+(?:,\d+)*(?:\.\d+)?)", content)
                if price_matches:
                    # Take the first price found
                    price_str = price_matches[0].replace(",", "")
                    try:
                        price_info["price"] = float(price_str)
                        price_info["symbol"] = symbol
                        sources.append(result["url"])
                        break
                    except ValueError:
                        continue

        # Fallback to stocks.json if search didn't find price
        if not price_info and price_data:
            price_info = {"price": price_data.get("price", 0), "symbol": symbol}
            sources = ["stocks.json"]

        if price_info:
            return AgentOutput(
                name="current",
                value=price_info,
                confidence=0.8 if sources and "stocks.json" not in sources else 0.5,
                sources=sources,
                notes=f"Current price information for {symbol}",
            )
        else:
            return AgentOutput(
                name="current",
                value="insufficient",
                confidence=0.0,
                sources=[],
                notes=f"Could not extract price data for {symbol}",
            )

    except Exception as e:
        return AgentOutput(
            name="current",
            value="insufficient",
            confidence=0.0,
            sources=[],
            notes=f"Search failed: {str(e)}",
        )
