from fastapi import APIRouter

from app.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.groq_chat import GroqChatService

router = APIRouter(prefix="/chat", tags=["Assistant"])


@router.post("", response_model=ChatResponse, summary="PackSure assistant (Groq)")
async def chat(payload: ChatRequest) -> ChatResponse:
    history = [{"role": t.role, "content": t.content} for t in payload.history]
    reply = await GroqChatService.complete(
        message=payload.message,
        history=history,
        scan_context=payload.scan_context,
    )
    return ChatResponse(reply=reply, model=settings.GROQ_MODEL)
