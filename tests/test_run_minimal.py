import pytest
from graph import build_graph
from state import DecisionState


@pytest.mark.asyncio
async def test_graph_runs_with_stubs():
    """Test graph executes with stub providers"""
    initial_state: DecisionState = {
        "user_id": "test_user",
        "question": "Should I buy RELIANCE?",
        "symbol": "RELIANCE",
        "sector": "Energy",
        "agent_outputs": {},
        "citations": [],
        "errors": [],
    }

    graph = build_graph()
    result = await graph.ainvoke(initial_state)

    assert "decision_json" in result
    assert "personal_context" in result
    assert "agent_outputs" in result
