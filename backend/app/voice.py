import base64
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Optional

import whisper
from openai import OpenAI


class VoiceProcessor:
    """Speech helpers with graceful fallback when external APIs are unavailable."""

    STT_MODEL = "whisper-large-v3"
    TTS_MODEL = "canopylabs/orpheus-v1-english"
    TTS_VOICE = "troy"

    def __init__(self):
        current_dir = Path(__file__).resolve().parent
        backend_dir = current_dir.parent
        self.audio_dir = (backend_dir.parent / "frontend" / "public" / "audio").resolve()
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if self.groq_api_key:
            self.client = OpenAI(api_key=self.groq_api_key, base_url="https://api.groq.com/openai/v1")

        self.whisper_model = None
        try:
            self.whisper_model = whisper.load_model("tiny")
            print("🎤 Local whisper model loaded")
        except Exception as exc:
            print(f"⚠️ Whisper fallback unavailable: {exc}")

        print("🎤 VoiceProcessor initialized")
        print(f"   Audio directory: {self.audio_dir}")

    def speech_to_text(self, audio_base64: str) -> str:
        if not audio_base64:
            return "I didn't receive any audio."

        try:
            audio_bytes = base64.b64decode(audio_base64)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name

            if self.client:
                with open(tmp_path, "rb") as audio_file:
                    result = self.client.audio.transcriptions.create(file=audio_file, model=self.STT_MODEL, response_format="text")
                os.unlink(tmp_path)
                text = result.strip() if isinstance(result, str) else result.text.strip()
                if text:
                    print(f"🗣️ Transcribed: {text}")
                    return text

            if self.whisper_model is not None:
                try:
                    result = self.whisper_model.transcribe(tmp_path, language="en")
                    os.unlink(tmp_path)
                    text = (result.get("text") or "").strip()
                    if text:
                        print(f"🗣️ Transcribed locally: {text}")
                        return text
                except Exception as exc:
                    print(f"⚠️ Local whisper transcription failed: {exc}")

            os.unlink(tmp_path)
            return "I couldn't understand that audio. Please try typing instead."
        except Exception as exc:
            print(f"❌ STT Error: {exc}")
            return "I couldn't understand that audio. Please try typing instead."

    def text_to_speech(self, text: str) -> Optional[str]:
        if not text:
            return None

        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
        preferred_format = "wav" if self.client else "mp3"
        filename = f"response_{text_hash}.{preferred_format}"
        filepath = self.audio_dir / filename

        if filepath.exists():
            return f"/audio/{filename}"

        try:
            if self.client:
                response = self.client.audio.speech.create(
                    model=self.TTS_MODEL,
                    voice=self.TTS_VOICE,
                    input=text,
                    response_format="wav",
                )
                response.write_to_file(str(filepath))
                print(f"🔊 TTS generated: {filename}")
                return f"/audio/{filename}"
        except Exception as exc:
            print(f"❌ TTS Error: {exc}")

        fallback_filename = f"response_{text_hash}.mp3"
        fallback_path = self.audio_dir / fallback_filename
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(str(fallback_path))
            print(f"🔊 TTS generated with gTTS: {fallback_filename}")
            return f"/audio/{fallback_filename}"
        except Exception as fallback_error:
            print(f"❌ Fallback TTS also failed: {fallback_error}")
            return None