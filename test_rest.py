import os
from dotenv import load_dotenv
import requests

load_dotenv(override=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
payload = {
    "contents": [{"parts": [{"text": "Hello"}]}]
}
print("Making REST request...")
try:
    response = requests.post(url, json=payload, timeout=5)
    print(f"Status: {response.status_code}")
    print(response.text)
except Exception as e:
    print(f"Exception: {e}")
