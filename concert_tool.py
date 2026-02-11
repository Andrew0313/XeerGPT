from concert_scraper import MalaysiaConcertScraper
from llm import llm_chat

scraper = MalaysiaConcertScraper()

def concert_tool(message):
    extraction_prompt = f"""
Extract artist, date, and location from this message.
Return JSON.

Message: "{message}"
"""

    info = llm_chat(extraction_prompt)

    # parse JSON (simple version for now)
    events = scraper.search_concerts()

    return f"I found {len(events)} concerts matching your request."
