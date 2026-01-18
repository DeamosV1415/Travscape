from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from main import TravelAssistant
import uvicorn
import json
from typing import Optional

app = FastAPI(
    title="Trav Travel Assistant API",
    description="AI-powered travel planning assistant",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create assistant instance
print("Creating TravelAssistant instance...")
assistant = TravelAssistant()
print("Assistant ready!")

# ==================== MODELS ====================

class ChatRequest(BaseModel):
    message: str
    user_id: str

class ChatResponse(BaseModel):
    response: str
    thread_id: str

# ==================== STREAMING ENDPOINT ====================

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat responses token-by-token (typewriter effect).
    """
    async def generate():
        try:
            token_count = 0
            async for token in assistant.chat(request.message, request.user_id):
                token_count += 1
                # Send each token as SSE
                yield f"data: {json.dumps({'content': token, 'done': False})}\n\n"
            
            # Send done signal
            print(f"Streamed {token_count} tokens to user {request.user_id}")
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
        
        except Exception as e:
            print(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )