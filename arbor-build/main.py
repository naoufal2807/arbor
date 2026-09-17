from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI()

class ChatRequest(BaseModel):
    messages: list
    model: str = "auto"
    max_tokens: int = 100
    
@app.post("/v1/chat/completions")
async def chat(request: ChatRequest):
    # ollama first pluging
    async with httpx.AsyncClient() as client:
        response = await  client.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "gemma3:270m",
                "messages": request.messages,
                "stream": False
            }
        )
        ollama_response = response.json()
    
    # Return in OpenAI format
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": ollama_response.get("message", {}).get("content", "")
                }
            }
        ],
        "x_gateway":{
            "backend":"ollama",
            "cost": 0.0,
            "ttft_ms": 0
        }    }