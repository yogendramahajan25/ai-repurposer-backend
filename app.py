# import os
# import json
# import re
# import requests
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()
# GROQ_API_URL = os.getenv("GROQ_API_URL")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# app = FastAPI()

# # Allow frontend to access backend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class RepurposeRequest(BaseModel):
#     text: str
#     actions: list  # ["summary","flashcards","quiz","linkedin","translate:hi"]

# # def call_groq(prompt: str, max_tokens=800):
# #     headers = {
# #         "Authorization": f"Bearer {GROQ_API_KEY}",
# #         "Content-Type": "application/json",
# #     }
# #     payload = {
# #         "model": "mixtral-8x7b-32768",  # Example Groq model
# #         "messages": [{"role": "user", "content": prompt}],
# #         "temperature": 0.3,
# #         "max_tokens": max_tokens,
# #     }
# #     resp = requests.post(GROQ_API_URL, headers=headers, json=payload)
# #     resp.raise_for_status()
# #     data = resp.json()
# #     return data["choices"][0]["message"]["content"]


# def call_groq(prompt: str, max_tokens=512, temperature=0.2):
#     headers = {
#         "Authorization": f"Bearer {GROQ_API_KEY}",
#         "Content-Type": "application/json",
#     }

#     payload = {
#         "model": "llama-3.1-8b-instant",  # or llama-3.1-70b-versatile, mixtral-8x7b-32768
#         "messages": [
#             {"role": "system", "content": "You are a helpful AI assistant."},
#             {"role": "user", "content": prompt}
#         ],
#         "max_tokens": max_tokens,
#         "temperature": temperature
#     }

#     resp = requests.post(
#         "https://api.groq.com/openai/v1/chat/completions",
#         headers=headers,
#         json=payload,
#         timeout=60
#     )
#     resp.raise_for_status()
#     data = resp.json()
#     return data["choices"][0]["message"]["content"]





# @app.post("/repurpose")
# def repurpose(req: RepurposeRequest):
#     text = req.text
#     actions = req.actions
#     response = {}

#     # Summary + Flashcards + Quiz
#     if any(a in ["summary","flashcards","quiz"] for a in actions):
#         prompt = f"""
# You are a content repurposing assistant.
# Input:
# \"\"\"{text}\"\"\"

# Return JSON with keys you were asked for:
# - summary (3 sentences)
# - flashcards (list of Q/A pairs, max 5)
# - quiz (list of multiple-choice Qs with options and correct answer)

# Only include requested keys: {actions}
# """
#         raw = call_groq(prompt)
#         try:
#             parsed = json.loads(raw)
#         except:
#             match = re.search(r'(\{.*\})', raw, re.S)
#             parsed = json.loads(match.group(1)) if match else {"raw": raw}
#         response.update(parsed)

#     # LinkedIn post
#     if "linkedin" in actions:
#         prompt = f"""
# Convert this content into a LinkedIn post under 200 words.
# Input:
# \"\"\"{text}\"\"\"
# Return JSON: {{"post":"<linkedin text>"}}
# """
#         raw = call_groq(prompt, max_tokens=400)
#         try:
#             response["linkedin"] = json.loads(raw)["post"]
#         except:
#             response["linkedin"] = raw

#     # Translations
#     for act in actions:
#         if act.startswith("translate:"):
#             lang = act.split(":")[1]
#             prompt = f"""
# Translate the following into {lang}.
# Input:
# \"\"\"{text}\"\"\"
# Return JSON: {{"language":"{lang}","translated":"<text>"}}
# """
#             raw = call_groq(prompt, max_tokens=600)
#             try:
#                 response.setdefault("translations", {})[lang] = json.loads(raw)["translated"]
#             except:
#                 response.setdefault("translations", {})[lang] = raw

#     return response



import os
import json
import re
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RepurposeRequest(BaseModel):
    text: str
    actions: list  # ["summary","flashcards","quiz","linkedin","translate:hi"]

def call_groq(prompt: str, max_tokens=512, temperature=0.2):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def safe_parse_json(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Match the first {...} block (non-greedy)
        match = re.search(r'\{.*?\}', raw, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        # fallback
        return {"raw": raw}


@app.post("/repurpose")
def repurpose(req: RepurposeRequest):
    text = req.text
    actions = req.actions
    response = {}

    # Summary + Flashcards + Quiz
    if any(a in ["summary","flashcards","quiz"] for a in actions):
        prompt = f"""
You are a content repurposing assistant.
Input:
\"\"\"{text}\"\"\"

Return JSON with keys you were asked for:
- summary (3 sentences)
- flashcards (list of Q/A pairs, max 5)
- quiz (list of multiple-choice Qs with options and correct answer)

Only include requested keys: {actions}
"""
        raw = call_groq(prompt)
        parsed = safe_parse_json(raw)
        response.update(parsed)

    # LinkedIn post
    if "linkedin" in actions:
        prompt = f"""
Convert this content into a LinkedIn post under 200 words.
Input:
\"\"\"{text}\"\"\"
Return JSON: {{"post":"<linkedin text>"}}
"""
        raw = call_groq(prompt, max_tokens=400)
        linkedin_parsed = safe_parse_json(raw)
        response["linkedin"] = linkedin_parsed.get("post", raw)

    # Translations
    for act in actions:
        if act.startswith("translate:"):
            lang = act.split(":")[1]
            prompt = f"""
Translate the following into {lang}.
Input:
\"\"\"{text}\"\"\"
Return JSON: {{"language":"{lang}","translated":"<text>"}}
"""
            raw = call_groq(prompt, max_tokens=600)
            trans_parsed = safe_parse_json(raw)
            response.setdefault("translations", {})[lang] = trans_parsed.get("translated", raw)

    return response
