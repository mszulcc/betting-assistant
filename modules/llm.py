import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE, SYSTEM_PROMPT
from modules.rules_loader import get_rules

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

def get_llm():
    """Create and return a Gemini LLM instance via LangChain."""
    if not GOOGLE_API_KEY:
        return None

    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=LLM_TEMPERATURE,
        max_retries=0,  # fail fast!
    )


def build_system_prompt(kb_context: str = "", api_context: str = "") -> str:
    """Build the full system prompt with injected knowledge base, API context, and custom rules."""
    base = SYSTEM_PROMPT.format(
        kb_context=kb_context if kb_context else "No specific knowledge base data retrieved for this query.",
        api_context=api_context if api_context else "No live API data retrieved for this query.",
    )

    # Inject custom user rules from data/rules/*.md (if any files exist)
    rules = get_rules()
    if rules:
        rules_block = (
            "\n\n---\n"
            "CUSTOM USER BETTING RULES (highest priority — always follow these):\n"
            f"{rules}\n"
            "---"
        )
        return base + rules_block

    return base


def get_chat_stream(
        user_message: str,
        chat_history: list[dict],
        kb_context: str = "",
        api_context: str = "",
):
    """
    Get a response from the LLM with knowledge base and API context injected.
    Returns a generator yielding strings (text chunks).
    """
    llm = get_llm()
    if not llm:
        yield _fallback_response(kb_context, api_context)
        return

    # 1. Odkomentowano i zbudowano poprawny system prompt
    system_prompt = build_system_prompt(kb_context, api_context)
    messages = [SystemMessage(content=system_prompt)]

    # 2. Dodanie historii czatu (ostatnie 20 wiadomości)
    for msg in chat_history[-20:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    # 3. Dodanie aktualnej wiadomości użytkownika
    messages.append(HumanMessage(content=user_message))

    try:
        # Używamy streamowania dla lepszego UX w Streamlit
        for chunk in llm.stream(messages):
            if isinstance(chunk.content, str):
                yield chunk.content
            elif isinstance(chunk.content, list):
                # Płynne wyciąganie tekstu z porcji (chunków)
                text_parts = [
                    block.get("text", "")
                    for block in chunk.content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                yield "".join(text_parts)

    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "rate" in error_msg.lower():
            yield "⚠️ **API rate limit reached.** Please wait a moment and try again.\n\n" + _fallback_response(
                kb_context, api_context)
        else:
            yield f"⚠️ **Error communicating with the AI model:** {error_msg}\n\nHere's what I found in the knowledge base:\n\n{_fallback_response(kb_context, api_context)}"


def _fallback_response(kb_context: str, api_context: str) -> str:
    """Generate a basic response from KB/API data when LLM is unavailable."""
    parts = []

    if kb_context and kb_context != "No specific knowledge base data retrieved for this query.":
        parts.append("📚 **From Knowledge Base:**\n" + kb_context)

    if api_context and api_context != "No live API data retrieved for this query.":
        parts.append("⚽ **From Live Data:**\n" + api_context)

    if not parts:
        return "I'm currently unable to access the AI model. Please check your API key configuration in the sidebar."

    return "\n\n---\n\n".join(parts)


def is_llm_configured() -> bool:
    """Check if the Gemini API key is configured."""
    return bool(GOOGLE_API_KEY and GOOGLE_API_KEY != "your_gemini_api_key_here")