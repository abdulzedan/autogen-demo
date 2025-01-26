from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from ..services.manager import MultiAgentManager, PipelineStep

router = APIRouter()
manager = MultiAgentManager()

class StepsResponse(BaseModel):
    steps: List[PipelineStep]

class ChatRequest(BaseModel):
    message: str

@router.post("", response_model=StepsResponse)
async def chat_with_agents(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    result = manager.process_user_message(req.message)
    # The shape is: { "steps": [ {role, color, content}... ] }
    return result
