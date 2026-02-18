# handover_llm_generator.py

import os
import json
import re
import logging
import time
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)


class HandoverGenerator:

    def __init__(self):
        logger.info("Initializing HandoverGenerator...")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")

        self.client = OpenAI(api_key=api_key)

    def _clean(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*", "", text)
            text = text.replace("```", "")
        return text.strip()

    def generate(self, domains: List[Dict[str, Any]]) -> Dict[str, Any]:

        logger.info("Starting Handover Generation...")
        start = time.time()

        serialized = json.dumps(domains, indent=2)

        prompt = f"""
You are generating a production-grade engineering handover document.

For EACH domain generate:

{{
  "domain": "...",
  "risk_level": "...",
  "ownership_summary": "...",
  "architecture_to_explain": "...",
  "critical_dependencies": [...],
  "hidden_side_effects": [...],
  "infra_and_deployment_notes": [...],
  "db_migration_notes": [...],
  "monitoring_notes": [...],
  "known_pitfalls": [...],
  "kt_session_questions": [...],
  "first_30_day_successor_plan": [...]
}}

Use structural signals:
- db_schema_change → ask about migrations & rollback
- api_contract_change → ask about consumers
- lifecycle_change → ask about race conditions
- sql_logic_change → ask about query performance
- network_layer_change → ask about retry/timeout
- method_removed → what broke?
- class_removed → replacement strategy?

Return STRICT JSON only.

Domains:
{serialized}
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = self._clean(response.choices[0].message.content)

        parsed = json.loads(content)

        logger.info(f"Handover generation completed in {round(time.time()-start,2)}s")
        return parsed
