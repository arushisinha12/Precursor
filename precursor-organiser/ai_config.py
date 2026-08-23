# config.py
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Unlike the original version, we don't hard-fail when no key is set. The
# prototype should run out of the box; AI tagging just falls back to a
# lightweight keyword-based analyzer (see ai_core/observation_analyzer.py)
# when GEMINI_API_KEY isn't provided. Add a real key to backend/.env to
# switch to live Gemini analysis.
AI_ENABLED = bool(GEMINI_API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"
