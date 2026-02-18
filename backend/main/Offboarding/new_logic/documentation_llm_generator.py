# documentation_llm_generator.py

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


class DocumentationGenerator:

    def __init__(self):
        logger.info("Initializing DocumentationGenerator...")

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

        logger.info("Starting Documentation Generation...")
        start = time.time()

        serialized = json.dumps(domains, indent=2)

        prompt = f"""
Generate structured technical documentation for the following domains.

For EACH domain generate:

{{
  "domain": "...",
  "purpose": "...",
  "high_level_architecture": "...",
  "key_classes_and_modules": [...],
  "key_methods_and_flows": [...],
  "api_contracts": [...],
  "database_schema_notes": [...],
  "external_integrations": [...],
  "configuration_requirements": [...],
  "testing_strategy": [...],
  "operational_considerations": [...]
}}

Focus on clarity.
Avoid vague text.
Write as if publishing internal engineering docs.

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

        logger.info(f"Documentation generation completed in {round(time.time()-start,2)}s")
        return parsed
