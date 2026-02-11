from flask import Flask, request, jsonify, render_template
from router import route_message  # Your existing router
from llm import get_available_models  # NEW - for model list
from datetime import datetime
from models import db, Conversation, Message
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat")
def chat_page():
    return render_template("chat.html")

# NEW ENDPOINT - Get available AI models
@app.route("/api/models", methods=["GET"])
def get_models():
    """Return all available AI providers and models"""
    try:
        models = get_available_models()
        return jsonify({
            "success": True,
            "providers": models
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

# Get all conversations
@app.route("/api/conversations", methods=["GET"])
def get_conversations():
    conversations = Conversation.query.order_by(Conversation.updated_at.desc()).all()
    return jsonify({
        "conversations": [{
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
            "message_count": len(conv.messages)
        } for conv in conversations]
    })

# Get messages from a conversation
@app.route("/api/conversations/<int:conversation_id>/messages", methods=["GET"])
def get_messages(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
    
    return jsonify({
        "messages": [{
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        } for msg in messages]
    })

# Delete conversation
@app.route("/api/conversations/<int:conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    db.session.delete(conversation)
    db.session.commit()
    return jsonify({"success": True})

# Rename conversation
@app.route("/api/conversations/<int:conversation_id>/rename", methods=["PUT"])
def rename_conversation(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    data = request.get_json()
    new_title = data.get("title", "").strip()
    
    if not new_title:
        return jsonify({"success": False, "error": "Title cannot be empty"}), 400
    
    conversation.title = new_title
    db.session.commit()
    
    return jsonify({
        "success": True,
        "title": conversation.title
    })

# Clear all conversations
@app.route("/api/clear", methods=["POST"])
def clear_all():
    db.session.query(Message).delete()
    db.session.query(Conversation).delete()
    db.session.commit()
    return jsonify({"success": True})

# Chat endpoint - UPDATED with model support
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        message = data.get("message", "")
        conversation_id = data.get("conversation_id")
        model = data.get("model", "gemini-2.0-flash")  # NEW - get model from request
        
        print(f"📨 Message: '{message[:50]}...'")
        print(f"📋 Conversation ID: {conversation_id}")
        print(f"🤖 Model: {model}")

        # Only create NEW conversation if conversation_id is None
        if conversation_id is None:
            title = message[:50] + "..." if len(message) > 50 else message
            conversation = Conversation(title=title)
            db.session.add(conversation)
            db.session.commit()
            conversation_id = conversation.id
            print(f"✨ Created NEW conversation: {conversation_id}")
        else:
            conversation = Conversation.query.get(conversation_id)
            if not conversation:
                print(f"❌ Conversation {conversation_id} not found!")
                return jsonify({
                    "success": False,
                    "response": "Conversation not found"
                }), 404
            print(f"✅ Continuing conversation: {conversation_id}")

        # Save user message
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=message
        )
        db.session.add(user_message)
        db.session.commit()

        # Get AI response using selected model (via your existing router)
        try:
            ai_response = route_message(message, model=model)
        except Exception as e:
            error_str = str(e)
            print(f"AI Error: {e}")
            traceback.print_exc()
            db.session.rollback()

            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                return jsonify({
                    "success": False,
                    "response": f"⚠️ **{model}** has hit its rate limit. Please wait a moment or switch to a different model.",
                    "conversation_id": conversation_id
                }), 200

            return jsonify({
                "success": False,
                "response": f"❌ {error_str}",
                "conversation_id": conversation_id
            }), 200

        # Save AI message
        ai_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=ai_response
        )
        db.session.add(ai_message)

        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()

        db.session.commit()

        print(f"💾 Saved messages to conversation {conversation_id}")

        return jsonify({
            "success": True,
            "response": ai_response,
            "conversation_id": conversation_id,
            "model": model,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        print(f"ERROR in /api/chat: {str(e)}")
        traceback.print_exc()
        db.session.rollback()

        return jsonify({
            "success": False,
            "response": "I'm having trouble connecting right now. Please check your connection and try again."
        }), 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)