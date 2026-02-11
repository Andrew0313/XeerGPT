"""
Database Migration Script
Adds UsageTracking table to existing database without losing data
Run this ONCE after deploying the new code
"""

from flask import Flask
from models import db, UsageTracking, Conversation, Message
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def migrate():
    """Add UsageTracking table to database"""
    with app.app_context():
        print("🔄 Starting migration...")
        
        # Create all tables (this will add UsageTracking if it doesn't exist)
        db.create_all()
        
        print("✅ Migration complete!")
        print("📊 Database tables:")
        print("  - conversations")
        print("  - messages")
        print("  - usage_tracking (NEW)")
        
        # Verify existing data
        conv_count = Conversation.query.count()
        msg_count = Message.query.count()
        usage_count = UsageTracking.query.count()
        
        print(f"\n📈 Current data:")
        print(f"  - Conversations: {conv_count}")
        print(f"  - Messages: {msg_count}")
        print(f"  - Usage records: {usage_count}")
        
        if conv_count > 0:
            print("\n✅ Your existing conversations are safe!")
        
        print("\n🎉 You can now restart your server with the new code.")

if __name__ == "__main__":
    migrate()