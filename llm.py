import os
import random

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

# Load multiple API keys
def load_api_keys(prefix):
    """Load multiple API keys from environment (e.g., GROQ_API_KEY_1, GROQ_API_KEY_2)"""
    keys = []
    i = 1
    while True:
        key = os.getenv(f"{prefix}_{i}")
        if key:
            keys.append(key)
            i += 1
        else:
            break
    
    # Fallback to single key if no numbered keys found
    if not keys:
        single_key = os.getenv(prefix)
        if single_key:
            keys.append(single_key)
    
    return keys

# Load Gemini clients
gemini_clients = []
if GEMINI_AVAILABLE:
    gemini_keys = load_api_keys("GEMINI_API_KEY")
    if gemini_keys:
        for key in gemini_keys:
            try:
                client = genai.Client(api_key=key)
                gemini_clients.append(client)
            except Exception as e:
                print(f"⚠️ Gemini key error: {e}")
        if gemini_clients:
            print(f"✅ Gemini configured with {len(gemini_clients)} key(s)")
    else:
        print("⚠️ GEMINI_API_KEY not found")

# Load Groq clients
groq_clients = []
if GROQ_AVAILABLE:
    groq_keys = load_api_keys("GROQ_API_KEY")
    if groq_keys:
        for key in groq_keys:
            try:
                client = Groq(api_key=key)
                groq_clients.append(client)
            except Exception as e:
                print(f"⚠️ Groq key error: {e}")
        if groq_clients:
            print(f"✅ Groq configured with {len(groq_clients)} key(s)")
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
    """Try all Gemini keys until one works"""
    if not gemini_clients:
        raise Exception("Gemini not configured")
    
    last_error = None
    for client in gemini_clients:
        try:
            response = client.models.generate_content(
                model=model,
                contents=message
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error
            if "429" in error_str or "quota" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str:
                last_error = e
                continue  # Try next key
            else:
                # Different error, raise immediately
                raise Exception(f"Gemini API Error: {error_str}")
    
    # All keys failed with rate limit
    raise Exception(f"All Gemini keys exhausted: {str(last_error)}")

def chat_with_groq(message: str, model: str = "llama-3.1-70b-versatile") -> str:
    """Try all Groq keys until one works"""
    if not groq_clients:
        raise Exception("Groq not configured")
    
    last_error = None
    for client in groq_clients:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": message}],
                temperature=0.7,
                max_tokens=2048
            )
            return completion.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error
            if "429" in error_str or "rate_limit" in error_str.lower():
                last_error = e
                continue  # Try next key
            else:
                # Different error, raise immediately
                raise Exception(f"Groq API Error: {error_str}")
    
    # All keys failed with rate limit
    raise Exception(f"All Groq keys exhausted: {str(last_error)}")

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
        if provider == "groq" and not groq_clients:
            continue
        if provider == "gemini" and not gemini_clients:
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