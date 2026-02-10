from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict

PlatformType = Literal["whatsapp", "instagram", "email", "generic"]

class IncomingMessage(BaseModel):
    platform_unique_id: str
    query: str
    conversation_id: Optional[str] = None
    platform: PlatformType = "generic"
    
    # --- TAMBAHAN BARU ---
    type: str = "text"  # Default 'text', bisa 'image', 'file', dll.
    # ---------------------
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

class ChatbotResponse(BaseModel):
    success: bool
    answer: Optional[str] = None
    conversation_id: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None

class OutgoingMessage(BaseModel):
    recipient_id: str
    message: str
    subject: Optional[str] = None
    conversation_id: Optional[str] = None
    thread_key: Optional[str] = None
    platform: Optional[PlatformType] = None

class OutboundMessageRequest(BaseModel):
    recipient_id: str
    message: str
    platform: str