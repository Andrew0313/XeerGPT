# XeerGPT Configuration
import os
from datetime import timedelta

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'xeergpt-super-secret-key-2024'
    SESSION_COOKIE_NAME = 'xeergpt_session'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Chatbot Configuration
    CHATBOT_NAME = "XeerGPT"
    CHATBOT_VERSION = "1.0.0"
    MAX_MESSAGE_LENGTH = 1000
    MAX_HISTORY_LENGTH = 50
    
    # UI Configuration
    THEME_COLORS = {
        'primary': '#4F46E5',  # Indigo
        'secondary': '#10B981',  # Emerald
        'accent': '#8B5CF6',  # Violet
        'background': '#0F172A',  # Dark blue
        'text': '#F8FAFC'  # Light gray
    }
    
    # Features
    ENABLED_FEATURES = [
        'chat_history',
        'message_suggestions',
        'typing_indicators',
        'dark_mode',
        'export_chat',
        'voice_input_simulated'
    ]
    
    # Responses
    DEFAULT_RESPONSES = [
        "I'm processing your request...",
        "Let me think about that...",
        "That's an interesting question!",
        "I'm here to help with that!"
    ]
    
    # API Settings
    RATE_LIMIT = 100  # Requests per hour per user
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}