"""
LLM Module - Handles multiple AI providers
"""

import os

# Gemini - NEW API
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

gemini_client = None
if GEMINI_AVAILABLE:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        try:
            gemini_client = genai.Client(api_key=gemini_api_key)
            print("✅ Gemini configured")
        except Exception as e:
            print(f"⚠️ Gemini error: {e}")
    else:
        print("⚠️ GEMINI_API_KEY not found")

groq_client = None
if GROQ_AVAILABLE:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        try:
            groq_client = Groq(api_key=groq_api_key)
            print("✅ Groq configured")
        except Exception as e:
            print(f"⚠️ Groq error: {e}")
    else:
        print("⚠️ GROQ_API_KEY not found")

AVAILABLE_MODELS = {
    "llama-3.1-70b": {
        "provider": "groq",
        "model_id": "llama-3.1-70b-versatile",
        "name": "Llama 3.1 70B",
        "description": "Best quality",
        "icon": "⚡"
    },
    "llama-3.1-8b": {
        "provider": "groq",
        "model_id": "llama-3.1-8b-instant",
        "name": "Llama 3.1 8B",
        "description": "Ultra-fast",
        "icon": "⚡"
    },
    "gemini-1.5-flash": {
        "provider": "gemini",
        "model_id": "gemini-1.5-flash",
        "name": "Gemini 1.5 Flash",
        "description": "Fast & efficient",
        "icon": "🔮"
    },
    "gemini-1.5-pro": {
        "provider": "gemini",
        "model_id": "gemini-1.5-pro",
        "name": "Gemini 1.5 Pro",
        "description": "Most powerful",
        "icon": "🔮"
    }
}

def chat_with_gemini(message: str, model: str = "gemini-1.5-flash") -> str:
    if not gemini_client:
        raise Exception("Gemini not configured")
    try:
        response = gemini_client.models.generate_content(
            model=model,
            contents=message
        )
        return response.text
    except Exception as e:
        raise Exception(f"Gemini API Error: {str(e)}")

def chat_with_groq(message: str, model: str = "llama-3.1-70b-versatile") -> str:
    if not groq_client:
        raise Exception("Groq not configured")
    try:
        completion = groq_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message}],
            temperature=0.7,
            max_tokens=2048
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Groq API Error: {str(e)}")

def llm_chat(message: str, model: str = "gemini-1.5-flash") -> str:
    model_info = AVAILABLE_MODELS.get(model)
    if not model_info:
        print(f"⚠️ Unknown model '{model}', using gemini-1.5-flash")
        return chat_with_gemini(message, "gemini-1.5-flash")
    
    provider = model_info["provider"]
    model_id = model_info["model_id"]
    
    if provider == "groq":
        return chat_with_groq(message, model_id)
    elif provider == "gemini":
        return chat_with_gemini(message, model_id)
    else:
        raise Exception(f"Unknown provider: {provider}")

def get_available_models():
    providers = {}
    for model_key, model_info in AVAILABLE_MODELS.items():
        provider = model_info["provider"]
        if provider == "groq" and not groq_client:
            continue
        if provider == "gemini" and not gemini_client:
            continue
        
        if provider not in providers:
            providers[provider] = {
                "display_name": "Groq (Llama)" if provider == "groq" else "Google Gemini",
                "icon": model_info["icon"],
                "models": {}
            }
        providers[provider]["models"][model_key] = {
            "name": model_info["name"],
            "description": model_info["description"]
        }
    return providers