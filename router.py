from llm import llm_chat

def route_message(message: str, model: str = "gemini-2.0-flash"):
    return llm_chat(message, model=model)
