import json
import os
import re

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "deepseek/deepseek-chat-v3-0324"

SYSTEM_PROMPT = (
    "Ты мастер отмазок. Сначала генерируешь креативное объяснение для "
    "неловкой ситуации, затем выступаешь в роли независимого критика и "
    "даёшь ОБЪЕКТИВНУЮ оценку правдоподобности именно той отмазки, "
    "которую только что придумал.\n\n"
    "Оценивай беспристрастно, как сторонний наблюдатель: насколько "
    "легко эту отмазку проверить, есть ли в ней логические дыры, "
    "выглядит ли она естественно. Не защищай собственный текст — если "
    "отмазка слабая, ставь низкую оценку.\n\n"
    "Шкала rating (будь критичен, не завышай):\n"
    "- 1-30: явная ложь, легко проверяется, звучит абсурдно.\n"
    "- 31-60: натянуто, но в принципе возможно.\n"
    "- 61-85: правдоподобно, большинство поверит.\n"
    "- 86-100: почти неотличимо от правды, проверить невозможно.\n\n"
    "Варьируй оценки в зависимости от качества конкретной отмазки — "
    "низкие оценки это нормально. Не лепи всем подряд 85. Если "
    "отмазка дикая — ставь 10-20, если гениальная — 90+.\n\n"
    "Отвечай только валидным JSON без markdown-обёртки: "
    '{"excuse": string, "rating": number от 1 до 100}'
)

FALLBACK = {"excuse": "Мой кот съел мои оправдания", "rating": 42}


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def generate_excuse(situation: str) -> dict:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    user_prompt = (
        f"Ситуация: {situation}. Придумай убедительную отмазку на русском языке."
    )

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=1.2,
    )

    raw = completion.choices[0].message.content or ""
    try:
        data = json.loads(_strip_code_fence(raw))
        excuse = str(data["excuse"])
        rating = int(data["rating"])
        rating = max(1, min(100, rating))
        return {"excuse": excuse, "rating": rating}
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return FALLBACK


class GenerateRequest(BaseModel):
    situation: str


app = FastAPI(title="Генератор отмазок")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return FileResponse("static/index.html")


@app.post("/generate")
def generate(req: GenerateRequest):
    try:
        return generate_excuse(req.situation)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
