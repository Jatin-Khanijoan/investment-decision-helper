"""
Market regime detection from agent outputs.
Classifies market conditions to apply appropriate weight multipliers.
"""
from rl_models import MarketRegime
from state import AgentOutput, DecisionState
from typing import Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Detects market regime from agent outputs.
    """
    
    @staticmethod
    def extract_inflation_level(inflation_output: AgentOutput) -> str:
        """
        Extract inflation level from inflation agent output.
        
        Returns: "low", "medium", or "high"
        """
        if inflation_output.value == "insufficient":
            return "medium"  # Default to medium if no data
            
        value_str = str(inflation_output.value).lower()
        
        # Look for keywords or percentages
        if "low" in value_str or "deflation" in value_str:
            return "low"
        elif "high" in value_str or "elevated" in value_str or "rising" in value_str:
            return "high"
        else:
            # Try to extract percentage
            match = re.search(r'(\d+\.?\d*)%', value_str)
            if match:
                pct = float(match.group(1))
                if pct < 4.0:
                    return "low"
                elif pct > 6.0:
                    return "high"
                else:
                    return "medium"
            return "medium"
    
    @staticmethod
    def extract_rate_trend(rates_output: AgentOutput) -> str:
        """
        Extract interest rate trend from interest rates agent output.
        
        Returns: "falling", "stable", or "rising"
        """
        if rates_output.value == "insufficient":
            return "stable"
            
        value_str = str(rates_output.value).lower()
        
        # Look for trend keywords
        if any(word in value_str for word in ["rising", "increasing", "hike", "raised", "up"]):
            return "rising"
        elif any(word in value_str for word in ["falling", "decreasing", "cut", "lowered", "down"]):
            return "falling"
        else:
            return "stable"
    
    @staticmethod
    def extract_sentiment(agent_outputs: Dict[str, AgentOutput]) -> str:
        """
        Extract market sentiment from company and sentiment agents.
        
        Returns: "bearish", "neutral", or "bullish"
        """
        # Look at relevant sentiment signals
        sentiment_keywords = {
            "bullish": ["buy", "bullish", "positive", "strong", "growth", "outperform"],
            "bearish": ["sell", "bearish", "negative", "weak", "decline", "underperform"],
        }
        
        bullish_count = 0
        bearish_count = 0
        
        # Check company-specific agents
        company_agents = ["current", "historical", "financial_performance", "earnings_volatility"]
        
        for agent_name in company_agents:
            if agent_name in agent_outputs:
                output = agent_outputs[agent_name]
                if output.value == "insufficient":
                    continue
                    
                value_str = str(output.value).lower()
                notes_str = str(output.notes).lower() if output.notes else ""
                combined = value_str + " " + notes_str
                
                # Count sentiment keywords
                for keyword in sentiment_keywords["bullish"]:
                    if keyword in combined:
                        bullish_count += 1
                        
                for keyword in sentiment_keywords["bearish"]:
                    if keyword in combined:
                        bearish_count += 1
        
        # Determine overall sentiment
        if bullish_count > bearish_count + 1:
            return "bullish"
        elif bearish_count > bullish_count + 1:
            return "bearish"
        else:
            return "neutral"
    
    @staticmethod
    def calculate_volatility(technical_indicators: Dict[str, float] = None) -> float:
        """
        Calculate or extract volatility measure.
        
        For now, returns a default value. In production, would use
        historical volatility from NIFTY data.
        
        Returns: Annualized volatility (0.0 to 1.0+)
        """
        # Default to moderate volatility
        # In production, this would come from technical_indicators.py
        if technical_indicators and "volatility" in technical_indicators:
            return technical_indicators["volatility"]
        return 0.15  # Default 15% annualized volatility
    
    @classmethod
    def detect_regime(
        cls, 
        state: DecisionState,
        technical_indicators: Dict[str, float] = None
    ) -> MarketRegime:
        """
        Detect market regime from state.
        
        Args:
            state: Current decision state with agent outputs
            technical_indicators: Optional technical indicators
            
        Returns:
            MarketRegime object
        """
        agent_outputs = state.get("agent_outputs", {})
        
        # Extract components
        inflation = cls.extract_inflation_level(
            agent_outputs.get("inflation", AgentOutput(
                name="inflation", 
                value="insufficient", 
                confidence=0.0, 
                sources=[]
            ))
        )
        
        rate_trend = cls.extract_rate_trend(
            agent_outputs.get("interest_rates", AgentOutput(
                name="interest_rates",
                value="insufficient",
                confidence=0.0,
                sources=[]
            ))
        )
        
        sentiment = cls.extract_sentiment(agent_outputs)
        volatility = cls.calculate_volatility(technical_indicators)
        
        regime = MarketRegime(
            inflation=inflation,
            rate_trend=rate_trend,
            sentiment=sentiment,
            volatility=volatility
        )
        
        logger.info(f"Detected regime: {regime.to_key()}, volatility={volatility:.3f}")
        return regime


if __name__ == "__main__":
    # Test regime detection
    logging.basicConfig(level=logging.INFO)
    
    # Create mock agent outputs
    from state import AgentOutput, DecisionState
    
    test_outputs = {
        "inflation": AgentOutput(
            name="inflation",
            value="High inflation at 6.5%",
            confidence=0.9,
            sources=[]
        ),
        "interest_rates": AgentOutput(
            name="interest_rates",
            value="RBI has raised rates by 25bps",
            confidence=0.95,
            sources=[]
        ),
        "current": AgentOutput(
            name="current",
            value="Strong quarterly results, bullish outlook",
            confidence=0.8,
            sources=[]
        ),
    }
    
    test_state = DecisionState(
        user_id="test",
        question="Test",
        symbol="TEST",
        agent_outputs=test_outputs
    )
    
    regime = RegimeDetector.detect_regime(test_state)
    print(f"Regime: {regime}")
    print(f"Key: {regime.to_key()}")
    print(f"Vector: {regime.to_vector()}")
