# backend/app/models.py

from pydantic import BaseModel
from typing import List, Optional

class VoiceChatRequest(BaseModel):
    """Request model for voice chat endpoint"""
    audio_data: str  # base64 encoded audio

class VoiceChatResponse(BaseModel):
    """Response model for voice chat endpoint"""
    text: str  # The response text
    current_room: str  # Current location
    audio_url: Optional[str] = None  # URL to audio file
    context_chips: List[str] = []  # Action buttons
    inventory: List[str] = []  # User's items

class SessionState(BaseModel):
    """Session state model"""
    current_location: str = "dive_boat"
    inventory: List[str] = []
    discovered_clues: List[str] = []