import json
import os
import re
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

from .config import config
from .models import VoiceChatRequest, VoiceChatResponse
from .rag import RAGSystem
from .state_machine import LOCATIONS, StateMachine
from .tools import ToolRegistry
from .voice import VoiceProcessor

load_dotenv()

app = FastAPI(title="Great Barrier Reef Voice Guide")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)

audio_dir = Path(os.path.join(project_root, "frontend", "public", "audio"))
audio_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")

# Initialize
config.validate()
rag = RAGSystem()
voice = VoiceProcessor()

client = None
if config.GROQ_API_KEY:
    client = OpenAI(api_key=config.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

# Tools
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "look_up_artifact",
            "description": "Search the knowledge base for information about marine life, equipment, safety, weather, or any topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {"type": "string", "description": "Topic to search"}
                },
                "required": ["item"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "change_location",
            "description": "Move to a different dive location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_room": {
                        "type": "string",
                        "enum": ["dive_boat", "reef_flats", "reef_wall"]
                    }
                },
                "required": ["target_room"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_dive_limit",
            "description": "Calculate safe dive time based on depth and tank pressure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "depth_m": {"type": "number", "description": "Depth in meters"},
                    "tank_pressure_bar": {"type": "integer", "description": "Tank pressure in bar"}
                },
                "required": ["depth_m", "tank_pressure_bar"]
            }
        }
    }
]

# Sessions
sessions = {}

def get_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = {
            "current_location": "dive_boat",
            "inventory": [],
            "discovered_clues": []
        }
    return sessions[session_id]

def clean_text(text: str) -> str:
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F700-\U0001F77F"
        u"\U0001F780-\U0001F7FF"
        u"\U0001F800-\U0001F8FF"
        u"\U0001F900-\U0001F9FF"
        u"\U0001FA00-\U0001FA6F"
        u"\U0001FA70-\U0001FAFF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text).strip()


def generate_local_response(user_text: str, session: dict, tools: ToolRegistry) -> str:
    text = user_text.lower().strip()

    if not text or text in {"hello", "hi", "hey"}:
        return "Welcome aboard! You can ask about marine life, move to a reef location, or check your dive limit."

    if "gear locker" in text or "locker" in text:
        return tools.look_up_artifact("gear locker")

    if "reef flats" in text or "move to" in text and "flats" in text:
        return tools.change_location("reef_flats")

    if "reef wall" in text or "deep wall" in text:
        return tools.change_location("reef_wall")

    if "dive boat" in text:
        return tools.change_location("dive_boat")

    if "dive limit" in text or "bottom time" in text or "safe time" in text:
        depth = 20
        pressure = 200
        if "depth" in text:
            try:
                depth = float(re.search(r"(\d+)", text).group(1))
            except Exception:
                depth = 20
        if "pressure" in text:
            try:
                pressure = int(re.search(r"(\d+)", text).group(1))
            except Exception:
                pressure = 200
        return tools.calculate_dive_limit(depth, pressure)

    if "weather" in text:
        return "The weather is calm and visibility is good for a reef excursion today."

    if "clownfish" in text:
        return tools.look_up_artifact("clownfish")

    if "shark" in text or "sharks" in text:
        return tools.look_up_artifact("sharks")

    if "safety" in text or "danger" in text:
        return tools.look_up_artifact("safety")

    result = tools.look_up_artifact(text)
    if result and result != f"I don't have specific information about '{text}' at the {session.get('current_location', 'dive_boat')}.":
        return result

    return "I can help with reef facts, location changes, and dive time calculations. Try asking about marine life or the gear locker."
@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "🌊 Great Barrier Reef Voice Guide", "status": "running"}

@app.post("/voice-chat")
async def voice_chat(request: VoiceChatRequest, session_id: str = None, text: str = None):
    try:
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session = get_session(session_id)
        
        # Get user text
        user_text = text if text and text != "" else "Hello"
        
        if request.audio_data and request.audio_data != "":
            try:
                user_text = voice.speech_to_text(request.audio_data)
                if user_text.startswith("I couldn't understand"):
                    user_text = "Hello"
            except Exception as e:
                print(f"STT Error: {e}")
                user_text = "Hello"
        
        print(f"User: {user_text}")
        
        state_machine = StateMachine(session)
        tools = ToolRegistry(session, rag)
        
        current_location = session.get("current_location", "dive_boat")
        inventory = session.get("inventory", [])
        
        if client:
            try:
                system_prompt = f"""You are a Great Barrier Reef dive guide assistant.

Current location: {current_location}
Inventory: {inventory}

Use tools:
1. look_up_artifact(item) - Search knowledge base for ANY information
2. change_location(target) - Move to a different location
3. calculate_dive_limit(depth, pressure) - Calculate safe dive time

Rules:
- For information questions → use look_up_artifact()
- For location changes → use change_location()
- For dive time → use calculate_dive_limit()
- For greetings → respond directly
"""

                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": clean_text(user_text)}
                    ],
                    tools=TOOLS,
                    tool_choice="auto"
                )

                tool_calls = response.choices[0].message.tool_calls
                response_text = ""

                if tool_calls:
                    for tool_call in tool_calls:
                        tool_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)

                        print(f"Tool: {tool_name} -> {args}")

                        if tool_name == "look_up_artifact":
                            response_text = tools.look_up_artifact(args.get("item", user_text))
                        elif tool_name == "change_location":
                            target = args.get("target_room")
                            if current_location == target:
                                response_text = f"You are already at {LOCATIONS[target]['name']}."
                            else:
                                response_text = tools.change_location(target)
                                session["current_location"] = target
                        elif tool_name == "calculate_dive_limit":
                            response_text = tools.calculate_dive_limit(
                                args.get("depth_m", 20),
                                args.get("tank_pressure_bar", 200)
                            )
                else:
                    response_text = response.choices[0].message.content
                    print(f"LLM Direct: {response_text[:50]}...")
            except Exception as exc:
                print(f"LLM Error: {exc}")
                response_text = None
        else:
            response_text = None

        if not response_text:
            response_text = generate_local_response(clean_text(user_text), session, tools)
        
        # TTS
        audio_url = None
        try:
            audio_url = voice.text_to_speech(response_text)
        except Exception as e:
            print(f"TTS Error: {e}")
        
        chips = state_machine.get_context_chips()
        
        return VoiceChatResponse(
            text=response_text,
            current_room=session["current_location"],
            audio_url=audio_url,
            context_chips=chips,
            inventory=session.get("inventory", [])
        )
        
    except Exception as e:
        print(f"Error: {e}")
        return VoiceChatResponse(
            text=f"Error: {str(e)}",
            current_room="dive_boat",
            audio_url=None,
            context_chips=[],
            inventory=[]
        )

@app.get("/session/{session_id}")
async def get_session_state(session_id: str):
    session = get_session(session_id)
    return {
        "current_room": session["current_location"],
        "inventory": session.get("inventory", []),
        "discovered_clues": session.get("discovered_clues", [])
    }