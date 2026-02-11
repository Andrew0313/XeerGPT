"""
AI Providers Module
Supports multiple AI engines: Gemini, Groq, OpenAI, etc.
"""

import os
from typing import Optional

# Gemini
try:
    import google.genai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# OpenAI (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AIProvider:
    """Base class for AI providers"""
    
    def __init__(self):
        self.setup()
    
    def setup(self):
        """Setup the provider"""
        pass
    
    def chat(self, message: str, history: list = None) -> str:
        """Send a chat message and get response"""
        raise NotImplementedError


class GeminiProvider(AIProvider):
    """Google Gemini AI Provider"""
    
    MODELS = {
        "gemini-2.0-flash": {
            "name": "Gemini 2.0 Flash",
            "description": "Fast and efficient",
            "quota": "1,500 req/day"
        },
        "gemini-2.0-flash-lite": {
            "name": "Gemini 2.0 Flash Lite",
            "description": "Fastest & lightest",
            "quota": "1,500 req/day"
        },
        "gemini-2.5-flash": {
            "name": "Gemini 2.5 Flash",
            "description": "Best quality flash",
            "quota": "20 req/day"
        },
        "gemini-2.5-pro": {
            "name": "Gemini 2.5 Pro",
            "description": "Most powerful",
            "quota": "50 req/day"
        }
    }
    
    def setup(self):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai not installed. Run: pip install google-genai")
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
        
        genai.configure(api_key=api_key)
    
    def chat(self, message: str, model: str = "gemini-2.0-flash", history: list = None) -> str:
        try:
            model_instance = genai.GenerativeModel(model)
            response = model_instance.generate_content(message)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API Error: {str(e)}")


class GroqProvider(AIProvider):
    """Groq AI Provider - Fast inference with open-source models"""
    
    MODELS = {
        "llama-3.1-70b-versatile": {
            "name": "Llama 3.1 70B",
            "description": "Best quality, balanced speed",
            "quota": "14,400 req/day",
            "context": "128k tokens"
        },
        "llama-3.1-8b-instant": {
            "name": "Llama 3.1 8B",
            "description": "Ultra-fast responses",
            "quota": "14,400 req/day",
            "context": "128k tokens"
        },
        "llama-3.2-90b-text-preview": {
            "name": "Llama 3.2 90B",
            "description": "Latest, most powerful",
            "quota": "14,400 req/day",
            "context": "128k tokens"
        },
        "mixtral-8x7b-32768": {
            "name": "Mixtral 8x7B",
            "description": "Great for reasoning",
            "quota": "14,400 req/day",
            "context": "32k tokens"
        },
        "gemma2-9b-it": {
            "name": "Gemma 2 9B",
            "description": "Google's open model",
            "quota": "14,400 req/day",
            "context": "8k tokens"
        }
    }
    
    def setup(self):
        if not GROQ_AVAILABLE:
            raise ImportError("groq not installed. Run: pip install groq")
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment")
        
        self.client = Groq(api_key=api_key)
    
    def chat(self, message: str, model: str = "llama-3.1-70b-versatile", history: list = None) -> str:
        try:
            # Build messages array
            messages = []
            
            # Add conversation history if provided
            if history:
                for msg in history:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Call Groq API
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
                top_p=1,
                stream=False
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Groq API Error: {str(e)}")


class OpenAIProvider(AIProvider):
    """OpenAI Provider (optional - requires paid account after trial)"""
    
    MODELS = {
        "gpt-4o-mini": {
            "name": "GPT-4o Mini",
            "description": "Fast and affordable",
            "quota": "Paid after trial"
        },
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "description": "Classic, reliable",
            "quota": "Paid after trial"
        }
    }
    
    def setup(self):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai not installed. Run: pip install openai")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        
        self.client = OpenAI(api_key=api_key)
    
    def chat(self, message: str, model: str = "gpt-4o-mini", history: list = None) -> str:
        try:
            messages = []
            
            if history:
                for msg in history:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            messages.append({
                "role": "user",
                "content": message
            })
            
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API Error: {str(e)}")


# Provider registry
PROVIDERS = {
    "gemini": {
        "class": GeminiProvider if GEMINI_AVAILABLE else None,
        "available": GEMINI_AVAILABLE,
        "display_name": "Google Gemini",
        "icon": "🔮"
    },
    "groq": {
        "class": GroqProvider if GROQ_AVAILABLE else None,
        "available": GROQ_AVAILABLE,
        "display_name": "Groq (Llama)",
        "icon": "⚡"
    },
    "openai": {
        "class": OpenAIProvider if OPENAI_AVAILABLE else None,
        "available": OPENAI_AVAILABLE,
        "display_name": "OpenAI",
        "icon": "🤖"
    }
}


def get_provider(provider_name: str) -> AIProvider:
    """Get an AI provider instance"""
    if provider_name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    provider_info = PROVIDERS[provider_name]
    
    if not provider_info["available"]:
        raise ImportError(f"Provider {provider_name} is not available. Install required packages.")
    
    provider_class = provider_info["class"]
    return provider_class()


def get_available_providers() -> dict:
    """Get list of available providers"""
    return {
        name: info for name, info in PROVIDERS.items()
        if info["available"]
    }


def chat(message: str, provider: str = "gemini", model: str = None, history: list = None) -> str:
    """
    Universal chat function that works with any provider
    
    Args:
        message: User's message
        provider: AI provider name (gemini, groq, openai)
        model: Specific model to use (optional, uses default if not specified)
        history: Conversation history (optional)
    
    Returns:
        AI response text
    """
    provider_instance = get_provider(provider)
    
    if model:
        return provider_instance.chat(message, model=model, history=history)
    else:
        return provider_instance.chat(message, history=history)