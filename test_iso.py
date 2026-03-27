import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash", generation_config={"temperature": 0.9})

prompt = """You are a local Sri Lankan cultural guide.
Provide brief, highly accurate cultural norms and rules for visiting: 'Sigiriya'

Return ONLY a valid JSON object (no markdown, no extra text) with EXACTLY these string keys:
{
  "dress_code": "Brief advice on what to wear here",
  "behavior_rules": "1-2 sentences on how to behave, taboos, local rules, and a description of the local people/community around it",
  "best_season": "The best months to visit this specific area and why",
  "historical_context": "1-2 sentences of interesting background or fun fact"
}
"""

try:
    response = model.generate_content(prompt)
    print("==== SUCCESS ====")
    print(response.text)
except Exception as e:
    print("==== EXCEPTION ====")
    import traceback
    traceback.print_exc()
