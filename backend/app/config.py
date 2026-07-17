import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration with safe defaults for local demo usage."""

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

    PORT = int(os.getenv("PORT", 8000))
    HOST = os.getenv("HOST", "0.0.0.0")

    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./backend/data/chromadb")
    AUDIO_OUTPUT_DIR = os.getenv("AUDIO_OUTPUT_DIR", "./frontend/public/audio")

    STT_MODEL = os.getenv("STT_MODEL", "whisper-large-v3")
    TTS_MODEL = os.getenv("TTS_MODEL", "canopylabs/orpheus-v1-english")
    TTS_VOICE = os.getenv("TTS_VOICE", "troy")

    @classmethod
    def validate(cls):
        """Report missing optional API keys without blocking local usage."""
        warnings = []

        if not cls.GROQ_API_KEY:
            warnings.append("GROQ_API_KEY not set; voice features will fall back to local behavior")
        if not cls.GOOGLE_API_KEY:
            warnings.append("GOOGLE_API_KEY not set; RAG will use bundled local documents")

        if warnings:
            print("⚠️ Configuration warnings:")
            for warning in warnings:
                print(f"   - {warning}")
            return False

        print("✅ Configuration ready")
        return True


config = Config()