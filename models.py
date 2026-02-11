from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Conversation(db.Model):
    """Conversation/Chat Session"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship to messages
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.title}>'


class Message(db.Model):
    """Individual Message in a Conversation"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<Message {self.id}: {self.role}>'


class UsageTracking(db.Model):
    """
    API Usage Tracking - Persistent across server restarts
    Stores daily usage counts per provider
    """
    __tablename__ = 'usage_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False, unique=True, index=True)  # 'groq', 'openrouter', etc.
    date = db.Column(db.Date, nullable=False)  # Current date (UTC)
    count = db.Column(db.Integer, default=0, nullable=False)  # Number of requests today
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<UsageTracking {self.provider}: {self.count} on {self.date}>'