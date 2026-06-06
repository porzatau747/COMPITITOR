import json, logging
from pathlib import Path
import httpx
from openai import OpenAI
from app.config import get_settings
from app.services.scoring_service import detect_categories
logger=logging.getLogger(__name__)
PROMPT_PATH=Path(__file__).resolve().parents[1] / "prompts" / "analyze_post_prompt.txt"

REQUIRED_KEYS = {"hook", "hook_type", "content_type", "pain_point", "engagement_trigger", "why_it_worked", "risk", "detected_product_category"}

def mock_analyze_post(post, source_name: str) -> dict:
    cats=detect_categories(post.post_text)
    cat=cats[0] if cats else "IT"
    text=post.post_text or ""
    return {
      "hook": text[:80] or "ปัญหาไอทีที่ลูกค้าเจอบ่อย",
      "hook_type": ["Pain Hook", "Question Hook"],
      "content_type": "Problem/Solution Post",
      "pain_point": f"ลูกค้ากังวลว่า {cat} จะเลือกผิดหรือแก้ปัญหาไม่ตรงจุด",
      "engagement_trigger": ["คนอยากถามราคา", "คนเคยเจอปัญหาเดียวกัน", "คนอยากแชร์เก็บไว้"],
      "why_it_worked": "โพสต์แตะปัญหาใกล้ตัว ใช้ภาษาง่าย และเชื่อมกับการตัดสินใจซื้อหรือซ่อมได้ทันที",
      "risk": [] if cats else ["อาจขายของต่อได้ไม่ชัด ต้องปรับมุมให้ใกล้บริการร้าน"],
      "detected_product_category": cats or ["IT"],
      "_analysis_mode": "mock",
    }

def _prompt(post, source_name: str) -> str:
    tmpl=PROMPT_PATH.read_text(encoding="utf-8")
    values={
        "source_name": source_name,
        "post_text": post.post_text or "",
        "like_count": str(post.like_count or 0),
        "comment_count": str(post.comment_count or 0),
        "share_count": str(post.share_count or 0),
        "view_count": str(post.view_count or 0),
    }
    for key, value in values.items():
        tmpl = tmpl.replace("{" + key + "}", value)
    return tmpl

def _extract_json(text: str) -> dict:
    raw=(text or "").strip()
    if raw.startswith("```"):
        raw=raw.strip("`")
        if raw.lower().startswith("json"):
            raw=raw[4:].strip()
    data=json.loads(raw)
    missing=REQUIRED_KEYS-set(data.keys())
    if missing:
        raise ValueError(f"AI JSON missing keys: {sorted(missing)}")
    return data

def _is_gemini_base_url(base_url: str | None) -> bool:
    return bool(base_url and "generativelanguage.googleapis.com" in base_url)


def _gemini_endpoint(base_url: str, model: str) -> str:
    base=base_url.rstrip("/")
    if not base.endswith("/v1beta") and not base.endswith("/v1"):
        base=f"{base}/v1beta"
    model_name=model if model.startswith("models/") else f"models/{model}"
    return f"{base}/{model_name}:generateContent"


def _analyze_with_gemini(prompt: str, key: str, base_url: str, model: str) -> dict:
    url=_gemini_endpoint(base_url, model)
    payload={
        "contents":[{"role":"user", "parts":[{"text": prompt}]}],
        "generationConfig":{
            "temperature":0.2,
            "responseMimeType":"application/json",
        },
    }
    with httpx.Client(timeout=45) as client:
        resp=client.post(url, params={"key": key}, json=payload)
        if resp.status_code >= 400:
            detail=""
            try:
                detail=str(resp.json())[:500]
            except Exception:
                detail=resp.text[:500]
            raise RuntimeError(f"Gemini API error status={resp.status_code} body={detail}")
        data=resp.json()
    text=""
    candidates=data.get("candidates") or []
    if candidates:
        parts=((candidates[0].get("content") or {}).get("parts") or [])
        text="".join(part.get("text", "") for part in parts)
    if not text:
        raise ValueError("Gemini response did not contain text")
    return _extract_json(text)


def analyze_post_with_ai(post, source_name: str) -> dict:
    s=get_settings()
    key=s.openai_api_key or s.ai_api_key
    if not key or s.mock_mode:
        return mock_analyze_post(post, source_name)
    prompt=_prompt(post, source_name)
    last_error=None
    for attempt in range(3):
        try:
            if _is_gemini_base_url(s.ai_base_url):
                data=_analyze_with_gemini(prompt, key, s.ai_base_url or "https://generativelanguage.googleapis.com", s.ai_model)
                data["_analysis_mode"]="ai"
                return data
            client_kwargs={"api_key": key}
            if s.ai_base_url:
                client_kwargs["base_url"] = s.ai_base_url
            client=OpenAI(**client_kwargs)
            resp=client.chat.completions.create(
                model=s.ai_model,
                messages=[{"role":"user", "content": prompt}],
                temperature=0.2,
                response_format={"type":"json_object"},
            )
            data=_extract_json(resp.choices[0].message.content or "{}")
            data["_analysis_mode"]="ai"
            return data
        except Exception as exc:
            last_error=exc
            logger.warning("AI analyze failed attempt %s; falling back if retries exhausted: %s", attempt+1, exc)
    logger.error("AI analyze failed after retries; using mock analysis: %s", last_error)
    return mock_analyze_post(post, source_name)

def analyze_post(post, source_name: str) -> dict:
    return analyze_post_with_ai(post, source_name)
