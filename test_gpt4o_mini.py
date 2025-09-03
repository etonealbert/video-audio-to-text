#!/usr/bin/env python3
"""Test script to check gpt-4o-mini-transcribe model availability and functionality."""

import os
import sys
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

def create_test_audio():
    """Create a small test audio file using ffmpeg."""
    test_file = Path("test_audio.mp3")
    
    if test_file.exists():
        return test_file
        
    try:
        # Create a 5-second test audio with a simple tone
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "sine=frequency=440:duration=5",
            "-c:a", "mp3", "-ar", "16000", "-ac", "1", str(test_file)
        ], check=True, capture_output=True)
        
        print(f"✅ Created test audio file: {test_file}")
        return test_file
        
    except subprocess.CalledProcessError:
        print("❌ Could not create test audio file with ffmpeg")
        return None
    except FileNotFoundError:
        print("❌ ffmpeg not found in PATH")
        return None

def test_model_availability():
    """Test if gpt-4o-mini-transcribe model is available and functional."""
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print("✅ OpenAI API key found")
    
    # Initialize client with timeout
    client = OpenAI(api_key=api_key, timeout=60.0)
    
    # Create a small test file or use existing one
    test_file = create_test_audio()
    if not test_file:
        # Fallback to using a small chunk of existing file
        existing_files = list(Path("inputs").glob("*.WAV"))
        if existing_files:
            test_file = existing_files[0]
            print(f"⚠️  Using existing large file for test: {test_file}")
        else:
            print("❌ No test file available")
            return False
    
    # Test gpt-4o-mini-transcribe model
    print("\n🔬 Testing gpt-4o-mini-transcribe model...")
    
    try:
        with open(test_file, "rb") as audio_file:
            start_time = time.time()
            
            # Test with text format
            print("  Testing with response_format='text'...")
            transcription_text = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                response_format="text"
            )
            
            elapsed = time.time() - start_time
            print(f"  ✅ Text response ({elapsed:.2f}s): {str(transcription_text)[:100]}...")
            
            # Reset file pointer
            audio_file.seek(0)
            
            # Test with json format
            print("  Testing with response_format='json'...")
            start_time = time.time()
            transcription_json = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
                response_format="json"
            )
            
            elapsed = time.time() - start_time
            print(f"  ✅ JSON response ({elapsed:.2f}s): {transcription_json.text[:100]}...")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Error testing gpt-4o-mini-transcribe: {e}")
        
        # Test fallback to whisper-1
        print("\n🔄 Testing fallback to whisper-1...")
        try:
            with open(test_file, "rb") as audio_file:
                start_time = time.time()
                transcription_fallback = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
                elapsed = time.time() - start_time
                print(f"  ✅ Whisper-1 fallback works ({elapsed:.2f}s): {str(transcription_fallback)[:100]}...")
                return False  # gpt-4o-mini-transcribe failed, but whisper-1 works
                
        except Exception as fallback_error:
            print(f"  ❌ Fallback to whisper-1 also failed: {fallback_error}")
            return False
            
    finally:
        # Clean up test file if we created one
        if test_file and test_file.name == "test_audio.mp3" and test_file.exists():
            test_file.unlink()
            print("🧹 Cleaned up test audio file")

def main():
    """Main test function."""
    print("🧪 Testing gpt-4o-mini-transcribe Model Integration")
    print("=" * 55)
    
    if test_model_availability():
        print("\n✅ gpt-4o-mini-transcribe model is available and working!")
        sys.exit(0)
    else:
        print("\n❌ gpt-4o-mini-transcribe model is not available or failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
