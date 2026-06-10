import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv(override=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = "gemini-3.5-flash"

print(f"Key: {GOOGLE_API_KEY[:10]}...")

try:
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.4,
        max_retries=0, # fail fast!
        timeout=10,     # 5 seconds timeout
    )
    response = llm.invoke([HumanMessage(content="Hello")])
    print(response.content)
except Exception as e:
    import traceback
    traceback.print_exc()
