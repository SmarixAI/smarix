# finalcall_llm_generator.py

import os
import json
import re
import logging
import time
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Use global logging config (defined in main runner)
logger = logging.getLogger(__name__)

# -----------------------------------------
# Load Environment
# -----------------------------------------

env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)


class FinalCallGenerator:

    def __init__(self):

        logger.info("Initializing FinalCallGenerator...")

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment")
            raise ValueError("OPENAI_API_KEY not found")

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
