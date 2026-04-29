from typing import List, Optional
from pydantic import BaseModel, Field


class MessageInputSchema(BaseModel):
    """Schema for chat requests received by the backend from the frontend."""

    session_id: str = Field(..., description="Unique identifier for the chat session")
    user_text: str = Field(..., description="User input text for the AI agent")
    metadata: Optional[dict] = Field(default_factory=dict, description="Optional session metadata")


class ModelResponseSchema(BaseModel):
    """Schema for structured assistant responses returned to the backend."""

    session_id: str = Field(..., description="ID of the chat session")
    assistant_text: str = Field(..., description="Generated text from the AI agent")
    sources: List[str] = Field(default_factory=list, description="Optional source documents or retrieval hints")
