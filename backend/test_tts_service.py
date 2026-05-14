#!/usr/bin/env python3
"""
Quick test script for VoicevoxTTSService with real-time auto-play.

Run from project root: python backend/tts/test_tts_service.py

Tests:
1. Engine startup and polling mechanism
2. Audio synthesis
3. WAV metadata parsing
4. Auto-play functionality (if sounddevice available)
5. Audio stream to numpy conversion
"""

import sys
import os
import time

# Add parent directories to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(backend_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tts.voicevox_service import VoicevoxTTSService, SOUNDDEVICE_AVAILABLE
from core.logger import get_logger

logger = get_logger(__name__)


def test_engine_startup():
    """Test 1: Engine startup with polling mechanism."""
    print("\n" + "="*60)
    print("TEST 1: Engine Startup & Polling Mechanism")
    print("="*60)
    
    tts = VoicevoxTTSService(auto_play=False)
    
    print("Starting Voicevox engine...")
    start = time.time()
    
    success = tts.start_engine(timeout=15)
    elapsed = time.time() - start
    
    if success:
        print(f"✓ Engine started successfully in {elapsed:.2f}s")
        print(f"  - Engine ready: {tts.is_ready}")
        print(f"  - Health check passed")
        return tts
    else:
        print(f"✗ Engine failed to start after {elapsed:.2f}s")
        print(f"  - Verify Voicevox executable path exists")
        print(f"  - Check if port 50021 is available")
        return None


def test_audio_synthesis(tts):
    """Test 2: Audio synthesis."""
    print("\n" + "="*60)
    print("TEST 2: Audio Synthesis")
    print("="*60)
    
    test_texts = [
        ("こんにちは。", "Basic greeting"),
        ("今日の天気は晴れですね。", "Weather comment"),
        ("学校とは何ですか？", "Question"),
    ]
    
    for text, description in test_texts:
        print(f"\nSynthesizing: {description}")
        print(f"  Text: {text}")
        
        start = time.time()
        audio_output, error = tts.synthesize(text, speaker_id=1)
        elapsed = time.time() - start
        
        if error:
            print(f"  ✗ Error: {error}")
            continue
        
        print(f"  ✓ Synthesis successful in {elapsed*1000:.0f}ms")
        print(f"    - Duration: {audio_output.duration_ms:.0f}ms")
        print(f"    - Audio size: {len(audio_output.audio_data)} bytes")
        print(f"    - Sample rate: {audio_output.sample_rate}Hz")
        print(f"    - Channels: {audio_output.channels}")
        print(f"    - Format: {audio_output.audio_format}")
        
        return audio_output
    
    return None


def test_wav_metadata():
    """Test 3: WAV metadata parsing."""
    print("\n" + "="*60)
    print("TEST 3: WAV Metadata Parsing")
    print("="*60)
    
    # Create a minimal WAV sample
    tts = VoicevoxTTSService(auto_play=False)
    tts.start_engine(timeout=10)
    
    audio_output, _ = tts.synthesize("テスト")
    if not audio_output:
        print("✗ Could not generate test audio")
        return
    
    sample_rate, channels, duration = VoicevoxTTSService._parse_wav_metadata(
        audio_output.audio_data
    )
    
    print(f"✓ WAV metadata parsed")
    print(f"  - Sample rate: {sample_rate}Hz")
    print(f"  - Channels: {channels}")
    print(f"  - Duration: {duration:.0f}ms")
    print(f"  - Data integrity: {'✓ Valid' if sample_rate > 0 else '✗ Invalid'}")


def test_audio_playback(audio_output):
    """Test 4: Audio playback (if sounddevice available)."""
    print("\n" + "="*60)
    print("TEST 4: Audio Playback")
    print("="*60)
    
    if not SOUNDDEVICE_AVAILABLE:
        print("⚠ sounddevice not installed - skipping playback test")
        print("  Install with: pip install sounddevice numpy")
        return
    
    tts = VoicevoxTTSService(auto_play=True)
    
    if not audio_output:
        print("⚠ No audio to test - skipping")
        return
    
    print(f"Testing auto-play (async)...")
    success = tts.play_audio_async(audio_output)
    
    if success:
        print(f"✓ Audio playback started")
        print(f"  - Waiting for playback to complete...")
        
        completed = tts.wait_for_playback(timeout=15)
        if completed:
            print(f"✓ Playback completed")
        else:
            print(f"⚠ Playback timeout (audio may still be playing)")
    else:
        print(f"✗ Failed to start playback")


def test_numpy_conversion():
    """Test 5: WAV to numpy array conversion."""
    print("\n" + "="*60)
    print("TEST 5: WAV to Numpy Conversion")
    print("="*60)
    
    if not SOUNDDEVICE_AVAILABLE:
        print("⚠ sounddevice/numpy not available - skipping")
        return
    
    tts = VoicevoxTTSService(auto_play=False)
    tts.start_engine(timeout=10)
    
    audio_output, _ = tts.synthesize("テスト")
    if not audio_output:
        print("✗ Could not generate test audio")
        return
    
    audio_array = VoicevoxTTSService._wav_to_numpy_array(audio_output.audio_data)
    
    if audio_array is None:
        print("✗ Failed to convert WAV to numpy array")
        return
    
    print(f"✓ WAV converted to numpy array")
    print(f"  - Shape: {audio_array.shape}")
    print(f"  - Dtype: {audio_array.dtype}")
    print(f"  - Min value: {audio_array.min():.4f}")
    print(f"  - Max value: {audio_array.max():.4f}")
    print(f"  - Mean value: {audio_array.mean():.4f}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("VOICEVOX TTS SERVICE - TEST SUITE")
    print("="*60)
    print(f"sounddevice available: {SOUNDDEVICE_AVAILABLE}")
    
    # Test 1: Engine startup
    tts = test_engine_startup()
    if not tts:
        print("\n✗ Engine startup failed - cannot continue with tests")
        return 1
    
    # Test 2: Audio synthesis
    audio_output = test_audio_synthesis(tts)
    
    # Test 3: WAV metadata
    test_wav_metadata()
    
    # Test 4: Audio playback
    if audio_output:
        test_audio_playback(audio_output)
    
    # Test 5: Numpy conversion
    test_numpy_conversion()
    
    # Cleanup
    print("\n" + "="*60)
    print("Cleaning up...")
    tts.stop_engine()
    print("✓ Engine stopped")
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
