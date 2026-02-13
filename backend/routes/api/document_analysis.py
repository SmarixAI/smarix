from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from openai import OpenAI
import json

router = APIRouter()

client = OpenAI()


@router.post("/analyze-document")
async def analyze_document(
    employeeId: str = Form(...),
    documentId: str = Form(...),
    file: UploadFile = File(...)
):
    # 1️⃣ Validate file type
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files allowed")

    try:
        # 2️⃣ Read file content
        content = await file.read()
        text = content.decode("utf-8")

        if not text.strip():
            raise HTTPException(status_code=400, detail="File is empty")

        # 3️⃣ Call OpenAI with strict JSON enforcement
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": """
You are a documentation compliance auditor.

You MUST return strictly valid JSON in this format:

{
  "score": number (0-100),
  "improvements": [
    "string",
    "string",
    "string"
  ]
}

Rules:
- Return JSON only
- Do NOT wrap in markdown
- Do NOT add explanation
- Do NOT add extra text
"""
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        raw_content = response.choices[0].message.content.strip()

        # 4️⃣ Safe JSON parsing
        try:
            parsed = json.loads(raw_content)
        except Exception:
            return {
                "error": "AI returned invalid JSON",
                "raw_response": raw_content
            }

        # 5️⃣ Validate required fields
        if "score" not in parsed or "improvements" not in parsed:
            return {
                "error": "AI response missing required fields",
                "raw_response": raw_content
            }

        # 6️⃣ (Optional future) Update S3 here

        return parsed

    except HTTPException:
        raise

    except Exception as e:
        return {
            "error": "Internal analysis error",
            "details": str(e)
        }
