# finalcall_llm_generator.py

import os
import json
import re
import logging
import time
from typing import List, Dict, Any
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

from dotenv import load_dotenv
from pathlib import Path

# Use global logging config (defined in main runner)
logger = logging.getLogger(__name__)

# -----------------------------------------
# Load Environment
# -----------------------------------------

env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)
# Also attempt to load repo root .env (higher up) if present
repo_env_path = Path(__file__).resolve().parents[5] / ".env"
if repo_env_path.exists():
    load_dotenv(dotenv_path=repo_env_path)


class FinalCallGenerator:

    def __init__(self):

        logger.info("Initializing FinalCallGenerator...")

        api_key = os.getenv("OPENAI_API_KEY")

        if OpenAI is None:
            logger.warning("openai package not available; running in offline stub mode")
            self.client = None
            return

        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment; running in offline stub mode")
            self.client = None
            return

        self.client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully.")

    # -----------------------------------------
    # Clean LLM Response
    # -----------------------------------------
    def _clean(self, text: str) -> str:

        text = text.strip()

        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*", "", text)
            text = text.replace("```", "")

        return text.strip()

    # -----------------------------------------
    # Generate Final Call Analysis
    # -----------------------------------------
    def generate(self, domains: List[Dict[str, Any]]) -> Dict[str, Any]:

        logger.info("--------------------------------------------------")
        logger.info("Starting Final Call LLM generation...")

        start_time = time.time()

        logger.info(f"Number of domains received: {len(domains)}")

        serialized_domains = json.dumps(domains, indent=2)

        logger.info(
            f"Serialized domain payload size: {len(serialized_domains)} characters"
        )

        # Safety truncation
        if len(serialized_domains) > 120000:
            logger.warning("Payload too large. Truncating to 120000 characters.")
            serialized_domains = serialized_domains[:120000]

        prompt = f"""
You are a senior engineering manager.

Below are structured knowledge domains with deterministic risk scoring.

For EACH domain:
- Explain why risky
- Identify fragile areas
- Generate handover questions
- Generate regression focus

Return strict JSON only.

Domains:
{serialized_domains}
"""

        logger.info("Calling OpenAI API...")
        # If no OpenAI client available, return a deterministic stubbed response
        if not self.client:
            logger.warning("No OpenAI client: returning stubbed FinalCall report.")
            stub = []
            for d in domains:
                stub.append({
                    "domain": d.get("domain"),
                    "risk_score": d.get("risk_score"),
                    "risk_level": d.get("risk_level"),
                    "why_risky": f"Auto-generated stub: risk level {d.get('risk_level')}",
                    "fragile_areas": [],
                    "handover_questions": [],
                    "regression_focus": []
                })
            return {"final_calls": stub}

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

        except Exception as e:
            logger.exception("OpenAI API call failed.")
            return {
                "error": "OpenAI API call failed",
                "details": str(e)
            }

        logger.info("OpenAI response received.")

        content = response.choices[0].message.content
        cleaned_content = self._clean(content)

        logger.info("Cleaning and parsing LLM response...")

        try:
            parsed = json.loads(cleaned_content)
            logger.info("LLM JSON parsing successful.")

        except json.JSONDecodeError:
            logger.error("LLM JSON parsing failed.")
            logger.error(f"Raw LLM response: {cleaned_content}")

            return {
                "error": "LLM parse failed",
                "raw": cleaned_content
            }

        duration = round(time.time() - start_time, 2)

        logger.info(
            f"Final Call generation completed in {duration} seconds."
        )
        logger.info("--------------------------------------------------\n")

        return parsed
