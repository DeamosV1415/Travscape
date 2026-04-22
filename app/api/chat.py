"""
Travscape Chat API Router.

Handles the streaming chat endpoint that connects the frontend
to the TravelAssistant agent.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from main import TravelAssistant


router = APIRouter(prefix="/api", tags=["chat"])


# ==================== MODELS ====================

class ChatRequest(BaseModel):
    message: str
    user_id: str


class ChatResponse(BaseModel):
    response: str
    thread_id: str


# ==================== ASSISTANT INSTANCE ====================

print("Creating TravelAssistant instance...")
assistant = TravelAssistant()
print("TravelAssistant ready!")


# ==================== ENDPOINTS ====================

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat responses token-by-token via Server-Sent Events (SSE).

    The frontend connects to this endpoint and receives tokens in real-time,
    creating a typewriter effect in the chat UI.

    Request body:
        - message: The user's message text
        - user_id: Firebase UID of the authenticated user

    SSE data format:
        - { "content": "token text", "done": false }  — streaming token
        - { "content": "", "done": true }              — stream complete
        - { "error": "message", "done": true }         — error occurred
    """
    async def generate():
        try:
            token_count = 0
            async for token in assistant.chat(request.message, request.user_id):
                token_count += 1
                yield f"data: {json.dumps({'content': token, 'done': False})}\n\n"

            # Send completion signal
            print(f"Streamed {token_count} tokens to user {request.user_id}")
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

        except Exception as e:
            print(f"Streaming error for user {request.user_id}: {e}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
