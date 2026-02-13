from llm import llm_chat

def route_message(message: str, model: str = "openai/gpt-oss-120b"):
    return llm_chat(message, model=model)
