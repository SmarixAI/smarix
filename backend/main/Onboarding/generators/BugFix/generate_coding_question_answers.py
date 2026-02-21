"""
Enhanced PR → Coding Question Generator (S3 Input + GitHub API Verification)

1. Reads PR chunks from S3.
2. Verifies 'Merged' status via GitHub API (Source of Truth).
3. Generates 3-4 diverse coding questions.
4. Uploads results to S3.
"""

import sys
import json
import time
import os
import requests
import boto3
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
from botocore.exceptions import ClientError

# ------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------

# Ensure backend path is correct
BACKEND_ROOT = Path(__file__).resolve().parents[4]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.repo_context import get_repo_context

load_dotenv()
client = OpenAI()
s3_client = boto3.client("s3")

# Context
ctx = get_repo_context()
REPO_OWNER = ctx["owner"]
REPO_NAME = ctx["repo"]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# S3 Paths
S3_BUCKET = "smarix-data-apsouth1"
S3_INPUT_KEY = f"DataProcessing/{REPO_OWNER}/{REPO_NAME}/chunks/pr_chunks.json"
S3_OUTPUT_KEY = (
    f"Onboarding/{REPO_OWNER}/{REPO_NAME}/bugfix/onboarding_coding_questions.json"
)


# ------------------------------------------------------------------
# GITHUB API VERIFICATION
# ------------------------------------------------------------------


def verify_pr_merged_via_api(pr_number: int) -> bool:
    """
    Checks if a PR is actually merged using the GitHub API.
    Returns True if merged, False otherwise.
    """
    if not GITHUB_TOKEN:
        print("   ⚠️ No GITHUB_TOKEN found. Skipping API verification (assuming False).")
        return False

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            is_merged = data.get("merged", False)
            state = data.get("state", "unknown")
            print(f"   🔍 API Check PR #{pr_number}: State={state}, Merged={is_merged}")
            return is_merged

        elif response.status_code == 404:
            print(f"   ❌ PR #{pr_number} not found on GitHub.")
            return False
        elif response.status_code == 403:
            print(f"   ⚠️ API Rate Limit exceeded.")
            return False

    except Exception as e:
        print(f"   ⚠️ API Request failed: {e}")

    return False


# ------------------------------------------------------------------
# S3 UTILS
# ------------------------------------------------------------------


def read_json_from_s3(bucket: str, key: str) -> List[dict]:
    print(f"   📥 Downloading from S3: s3://{bucket}/{key}")
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return [json.loads(line) for line in content.splitlines() if line.strip()]
    except Exception as e:
        print(f"   ❌ S3 Read Error: {e}")
        return []


def upload_json_to_s3(data: dict, bucket: str, key: str):
    print(f"   ☁️ Uploading to S3: s3://{bucket}/{key}")
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json",
        )
        print("   ✅ Upload successful!")
    except Exception as e:
        print(f"   ❌ S3 Upload Failed: {e}")


# ------------------------------------------------------------------
# CLASSIFICATION & GENERATION LOGIC
# ------------------------------------------------------------------


def classify_pr(pr: dict) -> Set[str]:
    categories = set()
    files = pr.get("file_changes", [])

    for f in files:
        name = f.get("filename", "").lower()
        patch = f.get("patch", "").lower()

        if any(k in name for k in ["view", "widget", "ui", "screen", "css", "html"]):
            categories.add("UI")
        if any(k in name for k in ["provider", "bloc", "state", "redux"]):
            categories.add("State Management")
        if any(k in name for k in ["api", "service", "http", "fetch"]):
            categories.add("API")
        if "test" in name or "spec" in name:
            categories.add("Testing")
        if any(k in patch for k in ["optimize", "async", "lazy"]):
            categories.add("Performance")

    if not categories:
        categories.add("Feature")
    return categories


def build_pr_context(pr: dict) -> str:
    pr_number = pr.get("entities", {}).get("pr_number") or pr.get(
        "pr_number", "Unknown"
    )
    lines = [f"PR #{pr_number}", "", "FILES CHANGED:"]

    for f in pr.get("file_changes", []):
        lines.append(f"\n{'='*60}\nFile: {f.get('filename', 'unknown')}")
        patch = f.get("patch", "")
        if patch:
            lines.append(f"\nDIFF:\n{patch[:4000]}")
            if len(patch) > 4000:
                lines.append("\n... (truncated)")

    return "\n".join(lines)


def extract_before_after(patch: str) -> tuple[str, str]:
    before, after = [], []
    for line in patch.splitlines():
        if line.startswith("-") and not line.startswith("---"):
            before.append(line[1:])
        elif line.startswith("+") and not line.startswith("+++"):
            after.append(line[1:])
        elif line.startswith(" "):
            before.append(line[1:])
            after.append(line[1:])
    return ("\n".join(before).strip(), "\n".join(after).strip())


def build_solution(pr: dict) -> dict:
    files = []
    for f in pr.get("file_changes", []):
        patch = f.get("patch", "")
        before, after = extract_before_after(patch)
        files.append(
            {
                "filename": f.get("filename", "unknown"),
                "before_code": before,
                "after_code": after,
                "diff": patch,
            }
        )
    return {"files": files}


# ------------------------------------------------------------------
# LLM
# ------------------------------------------------------------------

SYSTEM_PROMPT = """
You are a Technical Interviewer. Generate a coding question based on the provided PR.
Focus on: Problem ID, Solution Analysis, and Best Practices.
Output strictly in JSON.
"""


def user_prompt(category: str, context: str, pr_number: int, difficulty: str) -> str:
    return f"""
PR CONTEXT:
{context}

TASK: Generate a {difficulty}-level {category} question for PR #{pr_number}.

OUTPUT JSON format:
{{
  "title": "Title",
  "difficulty": "{difficulty}",
  "category": "{category}",
  "scenario": {{ "context": "...", "problem_statement": "..." }},
  "questions": ["Q1...", "Q2..."],
  "model_answer": {{ "problem_analysis": "...", "solution_explanation": "..." }},
  "key_concepts": ["Concept1"]
}}
"""


def generate_question(pr: dict, category: str, difficulty: str) -> Optional[dict]:
    pr_number = pr.get("entities", {}).get("pr_number") or pr.get("pr_number")
    context = build_pr_context(pr)

    for _ in range(3):
        try:
            res = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.3,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": user_prompt(
                            category, context, pr_number, difficulty
                        ),
                    },
                ],
            )
            raw = res.choices[0].message.content.strip()
            if "```" in raw:
                raw = (
                    raw.split("```json")[1].split("```")[0].strip()
                    if "json" in raw
                    else raw.split("```")[1].strip()
                )
            return json.loads(raw)
        except Exception:
            time.sleep(1)
    return None


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------


def generate_coding_question_answers(
    gmail_db_path=None,
    provider="openai",
    model=None,
    db_path=None
):
    print(f"🚀 Generator (API Verify Mode) starting for {REPO_OWNER}/{REPO_NAME}")

    pr_chunks = read_json_from_s3(S3_BUCKET, S3_INPUT_KEY)
    if not pr_chunks:
        return

    # --- SELECTION STRATEGY ---
    selected_prs = {}
    used_ids = set()
    targets = ["UI", "Feature", "Testing", "State Management"]

    print("\n🔍 Finding valid MERGED PRs...")

    # Iterate until we have enough PRs or run out of chunks
    for pr in pr_chunks:
        # Check if we have enough
        if len(used_ids) >= 4:
            break

        pid = pr.get("entities", {}).get("pr_number") or pr.get("pr_number")
        if not pid or pid in used_ids:
            continue

        # 1. Classify first (Don't waste API calls on irrelevant PRs)
        cats = classify_pr(pr)
        matched = cats.intersection(targets)
        primary_cat = list(matched)[0] if matched else "Feature"

        # Skip if we already have a PR for this category
        if len(selected_prs.get(primary_cat, [])) >= 1:
            continue

        # 2. VERIFY VIA API
        is_merged = verify_pr_merged_via_api(pid)

        if is_merged:
            selected_prs.setdefault(primary_cat, []).append(pr)
            used_ids.add(pid)
            print(f"   ✅ Accepted PR #{pid} for {primary_cat}")
        else:
            print(f"   ⏭️  Skipping PR #{pid} (Not Merged)")

        time.sleep(0.5)  # Be nice to GitHub API

    # Fill gaps if needed (optional logic here)
    if len(used_ids) < 3:
        print("⚠️ Warning: Could not find 3 unique merged PRs across categories.")

    # --- GENERATION ---
    questions = []
    count = 1
    diffs = ["Junior", "Mid", "Mid", "Junior"]

    for idx, (cat, prs) in enumerate(selected_prs.items()):
        for pr in prs:
            pid = pr.get("entities", {}).get("pr_number") or pr.get("pr_number")
            diff = diffs[idx % 4]
            print(f"\n[{count}] Generating {cat} ({diff}) for PR #{pid}...")

            q_data = generate_question(pr, cat, diff)

            if q_data:
                questions.append(
                    {
                        "question_number": count,
                        "pr_number": pid,
                        "category": cat,
                        "difficulty": diff,
                        "title": q_data.get("title", f"{cat} Challenge"),
                        "raw_response": json.dumps(q_data),
                        "question_data": q_data,
                        "solution": build_solution(pr),
                        "pr_metadata": {
                            "files": [
                                f.get("filename") for f in pr.get("file_changes", [])
                            ]
                        },
                    }
                )
                print("   ✅ Generated")
                count += 1
            else:
                print("   ❌ Generation Failed")

    # --- UPLOAD ---
    if questions:
        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total": len(questions),
            },
            "questions": questions,
        }
        upload_json_to_s3(output_data, S3_BUCKET, S3_OUTPUT_KEY)
    else:
        print("❌ No questions generated.")


if __name__ == "__main__":
    generate_coding_question_answers()
