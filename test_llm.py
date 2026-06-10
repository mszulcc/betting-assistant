import os
import time
from dotenv import load_dotenv

load_dotenv(override=True)
from modules.llm import get_llm, build_system_prompt
from langchain_core.messages import HumanMessage, SystemMessage

print("Test bezpośredni (bez strumieniowania)...")
llm = get_llm()

if llm:
    start_time = time.time()
    try:
        # Wysyłamy proste, bezpośrednie zapytanie bez historii czatu
        res = llm.invoke([HumanMessage(content="Hi, respond with one word: Hello")])
        print(f"Odpowiedź po {time.time() - start_time:.2f} sekundach:")
        print(res.content)
    except Exception as e:
        print("Błąd podczas invoke:", e)
else:
    print("Brak klucza API!")