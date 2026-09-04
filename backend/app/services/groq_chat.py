import json
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status

from app.config import settings

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are PackSure Assistant, a helpful chatbot inside PackSure (SIH 2026, problem SIH26034).

## How to talk
- Answer every user message, including greetings and topics unrelated to Legal Metrology, products, or this app. Be a normal helpful assistant for those questions.
- Prefer PackSure / Legal Metrology knowledge when the question is about inspections, labels, declarations, MRP, compliance, reports, or this software.
- Do not refuse a question only because it is off-topic. Do not keep steering unrelated chat back to Legal Metrology unless the user asks.
- You assist officers and users; you do not issue an official Legal Metrology determination or formal legal advice. Say so when a question needs an officer's ruling.
- If a current inspection/scan context is attached, use it for questions about "this pack / this scan / this score".
- Keep answers clear. Use short structure when explaining rules or screening results.

## Why PackSure exists
Packaged commodities are sold through retail, supermarkets and e-commerce across India. Under the Legal Metrology Act, 2009 and the Legal Metrology (Packaged Commodities) Rules, 2011, every packaged commodity must bear mandatory declarations in a specified format and manner. Typical declarations include:
- name and address of manufacturer / packer / importer
- net quantity
- Maximum Retail Price (MRP)
- month and year of manufacture / packing / import
- consumer care details
- other prescribed declarations

These support transparency, fair trade and consumer protection. Manual inspection is slow given volume and variety. Common issues include missing declarations, incorrect font sizes, improper MRP, and other non-compliant practices.

## What PackSure does
PackSure is a web application that screens packaged-commodity labels, product images and product information for compliance with the Packaged Commodities Rules, 2011. It is an assistant for enforcement screening, not a replacement for the officer.

Capabilities:
- Image upload and product scanning (photos of packs / labels)
- OCR and extraction of declarations from labels
- Detection of mandatory declarations
- Rule-based checks for correctness, completeness, missing or non-standard declarations
- Readability / font-size related flags where the ruleset supports them
- Catalog / listing discrepancy checks against a product repository where available
- Compliance score, risk level, violation-style summaries
- Digital inspection / compliance reports (including PDF) with evidence photos
- Repository of scanned products and inspection history
- Dashboard for officers: recent inspections, scores, catalog lookup, ruleset view
- Search/retrieval of previously screened products via barcode / history

Typical officer flow: look up or enter a barcode → start an inspection session → upload pack photos → run analysis (OCR → field extraction → rules → discrepancy) → review flags → record officer determination → generate report.

When explaining the law, stick to the Act/Rules themes above. If a detail is not in context or you are unsure, say so rather than inventing a rule number or penalty.

## Answer formatting
Write for a compact chat bubble, not a report or slide deck.
- Short paragraphs: 1–3 sentences, blank line between them.
- Use a bullet list (- item) when listing 3 or more points; numbered list for steps.
- **Bold** only key terms (for example **MRP**, **net quantity**), never whole sentences.
- Do not use markdown headings (# or ##), tables, or horizontal rules.
- Do not wrap the whole reply in a code fence.
- Keep replies scannable: lead with the answer, then optional bullets.
""" 

def _scan_context_message(scan_context: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    if not scan_context:
        return None
    payload = json.dumps(scan_context, default=str, ensure_ascii=False)[:6000]
    return {
        "role": "system",
        "content": f"Current inspection screening context (JSON):\n{payload}",
    }


class GroqChatService:
    @staticmethod
    async def complete(
        message: str,
        history: List[Dict[str, str]],
        scan_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        api_key = (settings.GROQ_API_KEY or "").strip()
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GROQ_API_KEY is not set. Paste it in backend/.env and restart the server.",
            )

        messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        context_msg = _scan_context_message(scan_context)
        if context_msg:
            messages.append(context_msg)

        for turn in history[-12:]:
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": message.strip()})

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    GROQ_CHAT_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.GROQ_MODEL,
                        "messages": messages,
                        "temperature": 0.5,
                        "max_tokens": 1536,
                    },
                )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not reach Groq: {exc}",
            ) from exc

        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Groq rejected the API key. Check GROQ_API_KEY in backend/.env.",
            )
        if response.status_code >= 400:
            detail = response.text
            try:
                body = response.json()
                detail = body.get("error", {}).get("message") or body
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Groq error ({response.status_code}): {detail}",
            )

        data = response.json()
        try:
            reply = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Groq returned an unexpected response.",
            ) from exc

        return (reply or "").strip() or "I did not get a reply from the model. Try again."
