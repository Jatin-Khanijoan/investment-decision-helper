import pytest
from state import DecisionOutput, AgentOutput


def test_decision_output_schema():
    """Test JSON schema validation"""
    valid_output = {
        "decision": "HOLD",
        "confidence": 0.7,
        "horizon": "medium",
        "why": "Test reasoning",
        "key_factors": ["inflation", "rates"],
        "risks": ["volatility"],
        "personalization_considerations": ["risk_tolerance"],
        "used_agents": ["inflation", "interest_rates"],
        "citations": ["RBI"],
    }

    decision = DecisionOutput(**valid_output)
    assert decision.decision == "HOLD"
    assert decision.confidence == 0.7

    # Test invalid schema
    with pytest.raises(ValueError):
        DecisionOutput(decision="INVALID", confidence=2.0)


def test_agent_output_schema():
    """Test agent output schema"""
    output = AgentOutput(
        name="test", value=123, confidence=0.5, sources=["source1"], notes="test note"
    )

    assert output.name == "test"
    assert output.confidence == 0.5
