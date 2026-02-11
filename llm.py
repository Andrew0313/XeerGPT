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

# OpenAI (for DeepSeek and OpenRouter)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

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

# Load DeepSeek clients
deepseek_clients = []
if OPENAI_AVAILABLE:
    deepseek_keys = load_api_keys("DEEPSEEK_API_KEY")
    if deepseek_keys:
        for key in deepseek_keys:
            try:
                client = OpenAI(
                    api_key=key,
                    base_url="https://api.deepseek.com"
                )
                deepseek_clients.append(client)
            except Exception as e:
                print(f"⚠️ DeepSeek key error: {e}")
        if deepseek_clients:
            print(f"✅ DeepSeek configured with {len(deepseek_clients)} key(s)")
    else:
        print("⚠️ DEEPSEEK_API_KEY not found")

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
    else:
        print("⚠️ OPENROUTER_API_KEY not found")

AVAILABLE_MODELS = {
    # Groq Models
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
    
    # Gemini Models
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
    },
    
    # DeepSeek Models
    "deepseek-chat": {
        "provider": "deepseek",
        "model_id": "deepseek-chat",
        "name": "DeepSeek Chat",
        "description": "Almost unlimited free",
        "icon": "🌊"
    },
    "deepseek-reasoner": {
        "provider": "deepseek",
        "model_id": "deepseek-reasoner",
        "name": "DeepSeek R1",
        "description": "Advanced reasoning",
        "icon": "🌊"
    },
    
    # OpenRouter Models (Free ones)
    "llama-3.1-8b-free": {
        "provider": "openrouter",
        "model_id": "meta-llama/llama-3.1-8b-instruct:free",
        "name": "Llama 3.1 8B (Free)",
        "description": "Free via OpenRouter",
        "icon": "🔀"
    },
    "gemini-flash-free": {
        "provider": "openrouter",
        "model_id": "google/gemini-flash-1.5:free",
        "name": "Gemini Flash (Free)",
        "description": "Free via OpenRouter",
        "icon": "🔀"
    },
    "mistral-7b-free": {
        "provider": "openrouter",
        "model_id": "mistralai/mistral-7b-instruct:free",
        "name": "Mistral 7B (Free)",
        "description": "Free via OpenRouter",
        "icon": "🔀"
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
            if "429" in error_str or "quota" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str:
                last_error = e
                continue
            else:
                raise Exception(f"Gemini API Error: {error_str}")
    
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
            if "429" in error_str or "rate_limit" in error_str.lower():
                last_error = e
                continue
            else:
                raise Exception(f"Groq API Error: {error_str}")
    
    raise Exception(f"All Groq keys exhausted: {str(last_error)}")

def chat_with_deepseek(message: str, model: str = "deepseek-chat") -> str:
    """Try all DeepSeek keys until one works"""
    if not deepseek_clients:
        raise Exception("DeepSeek not configured")
    
    last_error = None
    for client in deepseek_clients:
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
                raise Exception(f"DeepSeek API Error: {error_str}")
    
    raise Exception(f"All DeepSeek keys exhausted: {str(last_error)}")

def chat_with_openrouter(message: str, model: str = "meta-llama/llama-3.1-8b-instruct:free") -> str:
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
            if "429" in error_str or "rate_limit" in error_str.lower():
                last_error = e
                continue
            else:
                raise Exception(f"OpenRouter API Error: {error_str}")
    
    raise Exception(f"All OpenRouter keys exhausted: {str(last_error)}")

def llm_chat(message: str, model: str = "deepseek-chat") -> str:
    model_info = AVAILABLE_MODELS.get(model)
    if not model_info:
        print(f"⚠️ Unknown model '{model}', using deepseek-chat")
        return chat_with_deepseek(message, "deepseek-chat")
    
    provider = model_info["provider"]
    model_id = model_info["model_id"]
    
    if provider == "groq":
        return chat_with_groq(message, model_id)
    elif provider == "gemini":
        return chat_with_gemini(message, model_id)
    elif provider == "deepseek":
        return chat_with_deepseek(message, model_id)
    elif provider == "openrouter":
        return chat_with_openrouter(message, model_id)
    else:
        raise Exception(f"Unknown provider: {provider}")

def get_available_models():
    providers = {}
    for model_key, model_info in AVAILABLE_MODELS.items():
        provider = model_info["provider"]
        
        # Check if provider is available
        if provider == "groq" and not groq_clients:
            continue
        if provider == "gemini" and not gemini_clients:
            continue
        if provider == "deepseek" and not deepseek_clients:
            continue
        if provider == "openrouter" and not openrouter_clients:
            continue
        
        # Map provider names to display names
        provider_display = {
            "groq": "Groq (Llama)",
            "gemini": "Google Gemini",
            "deepseek": "DeepSeek",
            "openrouter": "OpenRouter"
        }
        
        if provider not in providers:
            providers[provider] = {
                "display_name": provider_display.get(provider, provider),
                "icon": model_info["icon"],
                "models": {}
            }
        providers[provider]["models"][model_key] = {
            "name": model_info["name"],
            "description": model_info["description"]
        }
    return providers