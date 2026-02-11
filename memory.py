chat_history = []

def save_memory(user, bot):
    chat_history.append({"role": "user", "content": user})
    chat_history.append({"role": "assistant", "content": bot})

    if len(chat_history) > 10:
        chat_history.pop(0)
        chat_history.pop(0)

def get_memory():
    return chat_history
