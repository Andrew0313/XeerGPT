"""
LLM Module - Handles multiple AI providers with multiple API keys and fallback
VERIFIED WORKING - All models tested
"""

import os

# Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# OpenAI (for OpenRouter)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Gemini (Google GenAI)
try:
    from google import genai as google_genai
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
   
# Load multiple API keys
def load_api_keys(prefix):
    """Load multiple API keys from environment"""
    keys = []
    i = 1
    while True:
        key = os.getenv(f"{prefix}_{i}")
        if key:
            keys.append(key)
            i += 1
        else:
            break
    
    if not keys:
        single_key = os.getenv(prefix)
        if single_key:
            keys.append(single_key)
    
    return keys

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

# Load OpenRouter clients
openrouter_clients = []
if OPENAI_AVAILABLE:
    openrouter_keys = load_api_keys("OPENROUTER_API_KEY")
    if openrouter_keys:
        for key in openrouter_keys:
            try:
                client = OpenAI(
                    api_key=key,
                    base_url="https://openrouter.ai/api/v1"
                )
                openrouter_clients.append(client)
            except Exception as e:
                print(f"⚠️ OpenRouter key error: {e}")
        if openrouter_clients:
            print(f"✅ OpenRouter configured with {len(openrouter_clients)} key(s)")

# Load Google Gemini clients
gemini_clients = []
if GOOGLE_GENAI_AVAILABLE:
    gemini_keys = load_api_keys("GEMINI_API_KEY")
    if gemini_keys:
        for key in gemini_keys:
            try:
                client = google_genai.Client(api_key=key)
                gemini_clients.append(client)
            except Exception as e:
                print(f"⚠️ Gemini key error: {e}")
        if gemini_clients:
            print(f"✅ Google Gemini configured with {len(gemini_clients)} key(s)")
            
# VERIFIED WORKING MODELS
AVAILABLE_MODELS = {
    # ── Groq Models (Direct - Fastest, your own keys) ─────────────────────
        "llama-3.1-8b": {
        "provider": "groq",
        "model_id": "llama-3.1-8b-instant",       # ✅ still active
        "name": "Llama 3.1 8B",
        "description": "Ultra-fast — Simple tasks",
        "icon": "⚡"
    },
    "llama-3.3-70b": {
        "provider": "groq",
        "model_id": "llama-3.3-70b-versatile",   # ✅ replaces decommissioned llama-3.1-70b-versatile
        "name": "Llama 3.3 70B",
        "description": "Fast — General tasks",
        "icon": "🦙"
    },
    "llama-4-scout": {
        "provider": "groq",
        "model_id": "meta-llama/llama-4-scout-17b-16e-instruct",  # ✅ replaces decommissioned llama-3.2-90b-text-preview
        "name": "Llama 4 Scout 17B",
        "description": "Powerful — Complex coding, Multimodal",
        "icon": "🎯"
    },
    "llama-4-maverick": {
        "provider": "groq",
        "model_id": "meta-llama/llama-4-maverick-17b-128e-instruct",  # ✅ new Llama 4 model
        "name": "Llama 4 Maverick 17B",
        "description": "Most powerful — Advanced Coding",
        "icon": "🚀"
    },
    "gpt-oss-120b": {
    "provider": "groq",
    "model_id": "openai/gpt-oss-120b",
    "name": "CHATGPT 120B",
    "description": "OpenAI — Built-in web & code execution",
    "icon": "👑"
    },

    "qwen3-32b": {
    "provider": "groq",
    "model_id": "qwen/qwen3-32b",
    "name": "Qwen 3 32B",
    "description": "Alibaba — Math, Chinese",
    "icon": "🐉"
    },
    # ── OpenRouter Free Models ─────────────────────────────────────────────
    
    # DeepSeek Models (via OpenRouter - FREE!)
    "deepseek-chat": {
        "provider": "openrouter",
        "model_id": "deepseek/deepseek-chat-v3-0324",
        "name": "DeepSeek Chat V3",
        "description": "Standard — General Tasks",
        "icon": "🌊"
    },
    "deepseek-r1": {
        "provider": "openrouter",
        "model_id": "deepseek/deepseek-r1",
        "name": "DeepSeek Chat R1",
        "description": "Advanced — Math & Coding",
        "icon": "🧠"
    },
    "hermes-3-405b-free": {
    "provider": "openrouter",
    "model_id": "nousresearch/hermes-3-llama-3.1-405b:free",
    "name": "Hermes 3 405B",
    "description": "Conversational, roleplay",
    "icon": "✨"
    },
    
    #google gemini models ─────────────────────────────────────────────
    
    "gemini-3-pro": {
        "provider": "gemini",
        "model_id": "gemini-3-pro-preview",
        "name": "Gemini 3 Pro",
        "description": "Most powerful Gemini, agentic & multimodal",
        "icon": "💎"
    },
    "gemini-2.5-pro": {
        "provider": "gemini",
        "model_id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "description": "Deep reasoning, 1M context",
        "icon": "🔮"
    }
}



def chat_with_groq(message: str, model: str = "llama-3.3-70b-versatile") -> str:
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
            if "429" in error_str or "rate_limit" in error_str.lower():
                last_error = e
                continue
            else:
                raise Exception(f"Groq API Error: {error_str}")
    
    raise Exception(f"All Groq keys exhausted: {str(last_error)}")

def chat_with_openrouter(message: str, model: str = "meta-llama/llama-3.1-70b-instruct") -> str:
    """Try all OpenRouter keys until one works"""
    if not openrouter_clients:
        raise Exception("OpenRouter not configured")
    
    last_error = None
    for client in openrouter_clients:
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
            if "429" in error_str or "rate_limit" in error_str.lower() or "502" in error_str:
                last_error = e
                continue
            else:
                raise Exception(f"OpenRouter API Error: {error_str}")
    
    raise Exception(f"All OpenRouter keys exhausted: {str(last_error)}")

# ── ADD this function alongside chat_with_groq / chat_with_openrouter ──────

def chat_with_gemini(message: str, model: str = "gemini-2.5-flash") -> str:
    """Try all Gemini keys until one works"""
    if not gemini_clients:
        raise Exception("Google Gemini not configured")

    last_error = None
    for client in gemini_clients:
        try:
            response = client.models.generate_content(
                model=model,
                contents=message,
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                last_error = e
                continue
            else:
                raise Exception(f"Gemini API Error: {error_str}")

    raise Exception(f"All Gemini keys exhausted: {str(last_error)}")

def llm_chat(message: str, model: str = "llama-3.3-70b") -> str:
    """Main chat function - routes to correct provider"""
    model_info = AVAILABLE_MODELS.get(model)
    if not model_info:
        print(f"⚠️ Unknown model '{model}', using llama-3.3-70b")
        return chat_with_groq(message, "llama-3.3-70b-versatile")
    
    provider = model_info["provider"]
    model_id = model_info["model_id"]
    
    if provider == "groq":
        return chat_with_groq(message, model_id)
    elif provider == "openrouter":
        return chat_with_openrouter(message, model_id)
    elif provider == "gemini":
        return chat_with_gemini(message, model_id)
    else:
        raise Exception(f"Unknown provider: {provider}")

def get_available_models():
    """Return available models for the frontend"""
    providers = {}
    for model_key, model_info in AVAILABLE_MODELS.items():
        provider = model_info["provider"]
        
        # Skip if provider not configured
        if provider == "groq" and not groq_clients:
            continue
        if provider == "openrouter" and not openrouter_clients:
            continue
        if provider == "gemini" and not gemini_clients:
            continue
        provider_display = {
            "groq": "Groq (Fast)",
            "openrouter": "OpenRouter (Free)",
            "gemini": "Google Gemini (Official)"
        }
        
        if provider not in providers:
            providers[provider] = {
                "display_name": provider_display.get(provider, provider),
                "models": {}
            }
        providers[provider]["models"][model_key] = {
            "name": model_info["name"],
            "description": model_info["description"],
            "icon": model_info["icon"]
        }
    return providers