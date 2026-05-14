"""Text-to-Speech (TTS) service package using Voicevox engine.

Provides real-time audio synthesis for Japanese text with streaming support.
Manages subprocess lifecycle and error handling per rules.md standards.
"""

from .voicevox_service import VoicevoxTTSService, TTSAudioOutput

__all__ = [
    "VoicevoxTTSService",
    "TTSAudioOutput",
]
