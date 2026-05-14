"""Pydantic models for strict data validation between backend and llm_core.

Ensures API-first design with clear data contracts.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class MessageInputSchema(BaseModel):
    """Validates incoming requests from backend.
    
    Maps backend ChatMessageRequest to llm_core input format.
    Performed early to fail fast with 422 errors.
    """

    session_id: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Unique identifier for the chat session"
    )
    user_text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User input text for the AI agent"
    )
    user_id: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Optional user identifier for personalization"
    )
    language: str = Field(
        default="en",
        description="Output language code: 'en' or 'vi'"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional context (mood, JLPT level, etc.)"
    )

    @field_validator("user_text")
    @classmethod
    def validate_user_text(cls, v: str) -> str:
        """Ensure user_text is non-empty after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("user_text must not be empty or whitespace-only")
        return stripped

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Restrict language to supported values."""
        if v not in ("en", "vi", "ja"):
            raise ValueError("language must be 'en', 'vi', or 'ja'")
        return v

    class Config:
        """Pydantic config for schema behavior."""
        json_schema_extra = {
            "example": {
                "session_id": "conv_12345",
                "user_text": "高校とは何ですか？",
                "user_id": "student_001",
                "language": "ja"
            }
        }


class ModelResponseSchema(BaseModel):
    """Standardized response structure with all LLM output tags.
    
    Includes display, HTML, voice, and intent tags from dual-track LLM output.
    Backend uses this for routing: display/HTML to frontend UI, voice to TTS engine.
    """

    session_id: str = Field(
        ...,
        description="Echo back session ID for request tracking"
    )
    assistant_text: str = Field(
        ...,
        description="Conversational text for UI display"
    )
    html_content: str = Field(
        default="",
        description="Detailed academic content with HTML5 formatting"
    )
    voice_text: str = Field(
        default="",
        description="Natural Japanese text for TTS synthesis"
    )
    intent_classification: str = Field(
        default="other",
        description="Query intent: 'other' or 'search'"
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Retrieved documents used in reasoning"
    )
    raw_output: str = Field(
        default="",
        description="Raw LLM output with XML tags (preserved for debugging and re-processing)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Latency (ms), token_usage, cache_hit flag, etc."
    )

    @field_validator("intent_classification")
    @classmethod
    def validate_intent(cls, v: str) -> str:
        """Validate intent is one of allowed values."""
        if v not in ("other", "search"):
            raise ValueError("intent_classification must be 'other' or 'search'")
        return v

    class Config:
        """Pydantic config for schema behavior."""
        json_schema_extra = {
            "example": {
                "session_id": "conv_12345",
                "assistant_text": "High school (高校) is the secondary education stage...",
                "html_content": "<p><b>Definition:</b> Grades 10-12 in Japanese education system</p>",
                "voice_text": "高校は日本の教育制度における中等教育段階です。",
                "intent_classification": "search",
                "sources": ["vocabulary_db:高校"],
                "metadata": {
                    "cache_hit": False,
                    "latency_ms": 3200,
                    "token_usage": 450
                }
            }
        }


class TTSVoiceExtractionSchema(BaseModel):
    """Schema for voice text extracted for TTS synthesis.
    
    Backend sends extracted voice text to TTS service via this schema.
    """

    session_id: str = Field(
        ...,
        description="Session ID for tracking"
    )
    voice_text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Japanese text for TTS synthesis (Hiragana, Katakana, Kanji)"
    )
    speaker_id: Optional[int] = Field(
        default=1,
        description="Voicevox speaker ID (default: 1 for female voice)"
    )

    class Config:
        """Pydantic config for schema behavior."""
        json_schema_extra = {
            "example": {
                "session_id": "conv_12345",
                "voice_text": "高校は日本の教育制度における中等教育段階です。",
                "speaker_id": 1
            }
        }


class FormattedLLMResponseSchema(BaseModel):
    """Complete formatted response from LLM with all tags validated.
    
    Output of output_formatter.py. Ready to route to frontend and TTS.
    """

    success: bool = Field(
        ...,
        description="Whether formatting was successful"
    )
    assistant_text: str = Field(
        ...,
        description="Assistant text for UI display"
    )
    html_content: str = Field(
        ...,
        description="HTML formatted content"
    )
    voice_text: str = Field(
        ...,
        description="Japanese text for TTS"
    )
    intent_classification: str = Field(
        ...,
        description="Intent: 'other' or 'search'"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Formatting metadata and statistics"
    )
    error_details: Optional[str] = Field(
        default=None,
        description="Error message if formatting failed"
    )

    class Config:
        """Pydantic config for schema behavior."""
        json_schema_extra = {
            "example": {
                "success": True,
                "assistant_text": "Here is the explanation...",
                "html_content": "<p>Detailed content</p>",
                "voice_text": "説明を提供します。",
                "intent_classification": "search",
                "metadata": {
                    "extraction_success": True,
                    "voice_text_length": 50
                }
            }
        }
