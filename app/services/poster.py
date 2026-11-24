"""Poster reader: the only place the model key is used."""
import base64
import datetime
import json
import os
import re

import httpx

PROMPT = ('Read this event poster. Answer ONLY with JSON: {"title": string, "venue": string, '
          '"date": ISO 8601 date-time, "price": number in euros}. Use null for anything you cannot read.')
NO_KEY = "Poster reading is off (no model key). Please type the details in."
NOT_READ = "I could not read the poster. Please type the details in."


def ask_model(image: bytes, mime: str) -> str:
    model = os.getenv("MODEL_NAME", "gemini-2.5-flash")
    body = {"contents": [{"parts": [{"text": PROMPT},
                                    {"inline_data": {"mime_type": mime, "data": base64.b64encode(image).decode()}}]}]}
    res = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                     headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, json=body, timeout=30)
    res.raise_for_status()
    return res.json()["candidates"][0]["content"]["parts"][0]["text"]


def _date(value):
    try:
        when = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return ""
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    return when.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _text(value):
    return value.strip() if isinstance(value, str) else ""


def read_poster(image: bytes, mime: str) -> dict:
    empty = {"title": "", "venue": "", "date": "", "price": None, "note": ""}
    if not os.getenv("GEMINI_API_KEY"):
        return {**empty, "note": NO_KEY}
    try:
        answer = ask_model(image, mime)
        match = re.search(r"\{.*\}", answer, re.S)
        data = json.loads(match.group(0))
    except Exception:  # fallback: model down, bad key, or an answer that is not JSON: never block the form
        return {**empty, "note": NOT_READ}
    price = data.get("price")
    ok_price = isinstance(price, (int, float)) and not isinstance(price, bool) and price >= 0
    return {"title": _text(data.get("title")), "venue": _text(data.get("venue")),
            "date": _date(data.get("date")) if data.get("date") else "",
            "price": float(price) if ok_price else None, "note": ""}
