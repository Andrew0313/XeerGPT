from llm import llm_chat

def route_message(message: str, model: str = "gemini-flash-1.5"):
    return llm_chat(message, model=model)
