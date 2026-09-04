from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: List[ChatTurn] = Field(default_factory=list)
    scan_context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    reply: str
    model: str
