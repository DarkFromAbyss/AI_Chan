"""Integration example for VoicevoxTTSService with real-time auto-play.

Quick reference for using the rebuilt TTS module in your application.
"""

from backend.tts.voicevox_service import VoicevoxTTSService

# ============================================================================
# EXAMPLE 1: Basic Usage with Auto-Play (Recommended)
# ============================================================================

def example_basic_auto_play():
    """Auto-play audio as Japanese text is synthesized."""
    
    # Initialize service with auto-play enabled (requires sounddevice)
    tts = VoicevoxTTSService(auto_play=True)
    
    # Start engine (polls http://127.0.0.1:50021/version until ready)
    if not tts.start_engine():
        print("Failed to start Voicevox engine")
        return
    
    # Synthesize and auto-play (no UI interaction needed)
    japanese_text = "こんにちは。今日の天気は晴れですね。"
    
    audio_output, error = tts.synthesize(japanese_text, speaker_id=1)
    
    if error:
        print(f"TTS Error: {error}")
    else:
        print(f"Audio playing... Duration: {audio_output.duration_ms:.0f}ms")
        # Audio is playing in background thread (in-memory)
        # No temporary .wav files created
        
        # Optionally wait for playback to finish
        tts.wait_for_playback(timeout=10)
        print("Playback complete")


# ============================================================================
# EXAMPLE 2: Synchronous Playback (Block Until Complete)
# ============================================================================

def example_sync_playback():
    """Wait for audio to finish playing."""
    
    tts = VoicevoxTTSService(auto_play=False)  # Manual playback control
    tts.start_engine()
    
    japanese_text = "学校とは何ですか？"
    
    audio_output, error = tts.synthesize(japanese_text)
    
    if not error:
        # Play synchronously and wait for completion
        success = tts.play_audio_sync(audio_output, timeout=30)
        if success:
            print("Synchronous playback completed")


# ============================================================================
# EXAMPLE 3: Get Audio Data Without Playing (for streaming to frontend)
# ============================================================================

def example_get_audio_only():
    """Synthesize audio and return as bytes (no auto-play)."""
    
    tts = VoicevoxTTSService(auto_play=False)
    tts.start_engine()
    
    japanese_text = "これはテストです。"
    
    audio_output, error = tts.synthesize(japanese_text)
    
    if not error:
        # Return audio bytes to frontend for playback
        audio_bytes = audio_output.audio_data  # WAV format in-memory
        sample_rate = audio_output.sample_rate  # e.g., 44100
        duration_ms = audio_output.duration_ms
        
        # Can be used with FastAPI StreamingResponse or sent to client
        print(f"Audio data: {len(audio_bytes)} bytes")
        print(f"Sample rate: {sample_rate}Hz")
        print(f"Duration: {duration_ms:.0f}ms")


# ============================================================================
# EXAMPLE 4: Integration with FastAPI Router
# ============================================================================

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

# Global TTS service (initialize in main.py)
tts_service = VoicevoxTTSService(auto_play=False)
tts_service.start_engine()

router = APIRouter(prefix="/api/tts", tags=["tts"])


@router.post("/synthesize-stream")
async def synthesize_and_stream(text: str, speaker_id: int = 1):
    """
    Synthesize text and stream audio directly to client.
    
    Client receives WAV stream for real-time playback.
    """
    audio_output, error = tts_service.synthesize(text, speaker_id)
    
    if error:
        return {"error": error}
    
    # Stream WAV data to browser for auto-play
    return StreamingResponse(
        iter([audio_output.audio_data]),
        media_type="audio/wav",
        headers={
            "Content-Length": len(audio_output.audio_data),
            "Content-Disposition": "inline"
        }
    )


@router.post("/synthesize-with-autoplay")
async def synthesize_with_autoplay(text: str, speaker_id: int = 1):
    """
    Synthesize and auto-play on backend server audio device.
    
    Useful for server-side scenarios or testing.
    """
    audio_output, error = tts_service.synthesize(
        text, 
        speaker_id,
        auto_play_override=True  # Force auto-play
    )
    
    if error:
        return {"error": error}
    
    return {
        "status": "ok",
        "duration_ms": audio_output.duration_ms,
        "synthesis_time_ms": audio_output.synthesis_time_ms
    }


# ============================================================================
# EXAMPLE 5: Error Handling and Retry Logic
# ============================================================================

def example_robust_usage():
    """Handle common error scenarios."""
    
    tts = VoicevoxTTSService(auto_play=True)
    
    # Ensure engine is started
    for attempt in range(3):
        if tts.start_engine(timeout=15):
            break
        if attempt < 2:
            print(f"Engine start attempt {attempt+1} failed, retrying...")
            continue
        else:
            print("Failed to start engine after 3 attempts")
            return
    
    texts = [
        "最初の文です。",
        "二番目の文です。",
        "最後の文です。"
    ]
    
    for i, text in enumerate(texts):
        print(f"Processing text {i+1}...")
        
        audio_output, error = tts.synthesize(text)
        
        if error:
            print(f"  Error: {error}")
            continue
        
        print(f"  Synthesized: {audio_output.duration_ms:.0f}ms")
        
        # Wait for current playback before next synthesis
        tts.wait_for_playback(timeout=10)


# ============================================================================
# INSTALLATION REQUIREMENTS
# ============================================================================
INSTALLATION_INFO = """
Required packages:
    pip install sounddevice numpy requests

Optional packages for enhanced audio:
    pip install pygame
    pip install pyaudio

Voicevox Engine:
    - Download from: https://voicevox.hiroshimacity.jp/
    - Extract to: voicevox/windows-directml/ folder
    - Verify: run.exe exists in that directory
"""


if __name__ == "__main__":
    # Run examples
    print("Example 1: Basic Auto-Play")
    print("=" * 50)
    example_basic_auto_play()
    
    print("\n\nExample 2: Get Audio Only (no playback)")
    print("=" * 50)
    example_get_audio_only()
