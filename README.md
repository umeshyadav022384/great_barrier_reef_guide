# Great Barrier Reef Guide

A voice-enabled, interactive reef guide demo built with a Python backend and a lightweight frontend. The app lets users explore reef locations, ask about marine life, and use context chips for guided interactions.

## What the app does

- Provides a conversational dive guide experience for the Great Barrier Reef.
- Uses a retrieval-augmented generation (RAG) flow over local reef documents.
- Supports voice input and text-to-speech output.
- Tracks a simple session state with current location, inventory, and navigable reef zones.

## Project structure

- backend/ - FastAPI backend, state machine, RAG logic, and voice integration
- frontend/ - Static web UI for chat, chips, and background visuals
- data/documents/ - Source documents used for the knowledge base
- data/chromadb/ - Local Chroma vector database for retrieval

## Tech stack

- Backend: FastAPI, Python, Chroma, OpenAI-compatible chat client
- Frontend: plain HTML/CSS/JavaScript
- Voice: speech-to-text and text-to-speech integration
- Model defaults:
  - LLM provider: Groq by default
  - LLM model: llama-3.3-70b-versatile
  - Speech-to-text model: whisper-large-v3
  - Text-to-speech model: canopylabs/orpheus-v1-english
  - TTS voice: troy

## Code flow

1. The browser sends a request from the frontend chat UI to the FastAPI backend.
2. The backend route in backend/app/main.py receives the message or audio input.
3. The request is processed by the state machine in backend/app/state_machine.py to manage location and inventory state.
4. The RAG layer in backend/app/rag.py and the tool layer in backend/app/tools.py retrieve reef knowledge and perform actions such as moving locations or unlocking the deep reef wall.
5. The response is returned to the frontend with text, audio, updated chips, and inventory state.

## Local development setup

### 1. Create a virtual environment

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start the backend

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Open the frontend

You can open frontend/src/index.html directly in a browser, or serve the frontend from a static server. The frontend expects the API at http://127.0.0.1:8000 by default.

## Docker run

The repository includes a docker-compose.yml file for running both services together.

```powershell
docker-compose up --build
```

## Configuration

Configuration is loaded from backend/app/config.py and can be overridden with environment variables.

Common variables:

- GROQ_API_KEY - API key for the Groq-based LLM provider
- LLM_PROVIDER - Select the provider (default: groq)
- LLM_MODEL - Override the default LLM model
- STT_MODEL - Speech-to-text model
- TTS_MODEL - Text-to-speech model
- TTS_VOICE - Voice name for TTS

## Data sources

- Reef knowledge comes from documents stored in data/documents/
- The local vector database is stored in data/chromadb/
- If API keys are not provided, the app can still run in a local/demo mode using the bundled documents.

## Useful commands

- Start backend: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
- Rebuild containers: docker-compose build
- Run containers: docker-compose up

## License

This project is intended as an educational demo. Add a license file if you plan to publish it.


