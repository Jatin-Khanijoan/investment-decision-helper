from typing import TypedDict, Any
from pydantic import BaseModel


class AgentOutput(BaseModel):
    name: str
    value: Any
    confidence: float
    sources: list[str]
    notes: str | None = None


class DecisionState(TypedDict, total=False):
    user_id: str
    question: str
    symbol: str
    sector: str | None
    personal_context: str
    agent_outputs: dict[str, AgentOutput]
    citations: list[str]
    errors: list[str]
    decision_json: dict | None


class DecisionOutput(BaseModel):
    decision: str  # "BUY", "HOLD", or "SELL"
    confidence: float  # 0.0 to 1.0
    horizon: str  # "short", "medium", or "long"
    why: str  # 3-6 bullet points explaining decision
    key_factors: list[str]
    risks: list[str]
    personalization_considerations: list[str]
    used_agents: list[str]
    citations: list[str]
