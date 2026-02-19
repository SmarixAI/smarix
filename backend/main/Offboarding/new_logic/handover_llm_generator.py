# handover_llm_generator.py

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

logger = logging.getLogger(__name__)

env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)
# Also attempt to load repo root .env (higher up) if present
repo_env_path = Path(__file__).resolve().parents[5] / ".env"
if repo_env_path.exists():
    load_dotenv(dotenv_path=repo_env_path)


class HandoverGenerator:

    def __init__(self):
        logger.info("Initializing HandoverGenerator...")

        api_key = os.getenv("OPENAI_API_KEY")
        if OpenAI is None:
            logger.warning("openai package not available; running HandoverGenerator in stub mode")
            self.client = None
            return

        if not api_key:
            logger.warning("OPENAI_API_KEY not found; running HandoverGenerator in stub mode")
            self.client = None
            return

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
            You are generating a precise engineering handover document.

            Your goal:
            Create a practical knowledge transfer checklist.
            No generic explanations.
            Only include sections relevant to the detected structural signals.

            For EACH domain return:

            {{
            "domain": "...",
            "risk_level": "...",

            "what_changed_summary": "...",

            "must_explain_live_in_kt": [
                "Specific component or flow that needs explanation"
            ],

            "production_risk_areas": [
                "Where this could break in prod"
            ],

            "consumer_or_dependency_impact": [
                "Which services, modules, APIs depend on this"
            ],

            "migration_or_rollback_strategy": [
                "How to rollback if this fails"
            ],

            "monitoring_and_alerting_to_verify": [
                "Logs / metrics / dashboards successor must check"
            ],

            "kt_session_mandatory_questions": [
                "Pinpoint technical questions successor must ask"
            ],

            "successor_first_30_day_checklist": [
                "Concrete tasks successor must complete"
            ]
            }}

            Rules:

            1. Only include DB migration section if db_schema_change present.
            2. Only include API impact section if api_contract_change present.
            3. Only include infra section if network_layer_change present.
            4. Only include rollback strategy if breaking_change or method_removed.
            5. If only class_added → keep it light.

            Be concise.
            No essays.
            No repetition.

            Return STRICT JSON only.

            Domains:
            {serialized}
            """



        # If no OpenAI client available, return stubbed handover documents
        if not self.client:
            logger.warning("No OpenAI client: returning stubbed Handover report.")
            stub = []
            for d in domains:
                stub.append({
                    "domain": d.get("domain"),
                    "risk_level": d.get("risk_level"),
                    "ownership_summary": "Auto-generated stub",
                    "architecture_to_explain": "",
                    "critical_dependencies": [],
                    "hidden_side_effects": [],
                    "infra_and_deployment_notes": [],
                    "db_migration_notes": [],
                    "monitoring_notes": [],
                    "known_pitfalls": [],
                    "kt_session_questions": [],
                    "first_30_day_successor_plan": []
                })
            logger.info(f"Handover generation completed in {round(time.time()-start,2)}s (stub)")
            return {"handovers": stub}

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
