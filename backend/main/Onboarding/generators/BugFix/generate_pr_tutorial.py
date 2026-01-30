"""
PR Tutorial Generator - Automated Tutorial Creation from Random PRs
Generates tutorials from 1 Easy, 1 Medium, and 1 Hard PR
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
import importlib
import importlib.util
from typing import List, Dict, Optional

# --- Ensure backend/ is on PYTHONPATH ---
BACKEND_ROOT = Path(__file__).resolve().parents[4]  # backend/
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

repo_root = BACKEND_ROOT

from utils.repo_context import get_repo_context
from utils.s3 import s3_manager

ctx = get_repo_context()

REPO_OWNER = ctx["owner"]
REPO_NAME = ctx["repo"]
VECTOR_DB_PATH = ctx["vector_db"]
ONBOARDING_ROOT = ctx["onboarding"]


def _load_rag_chatbot_class():
    """Dynamically load RAGChatbot class from various possible locations"""
    candidates = [
        "core.chatbot",
        "core.ChatBot.chatbot",
        "ChatBot.core.chatbot",
        "ChatBot.chatbot",
    ]

    for cand in candidates:
        try:
            mod = importlib.import_module(cand)
            if hasattr(mod, "RAGChatbot"):
                return mod.RAGChatbot
        except Exception:
            pass

    for path in repo_root.rglob("chatbot.py"):
        try:
            spec = importlib.util.spec_from_file_location("rag_chatbot_dynamic", str(path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "RAGChatbot"):
                return getattr(mod, "RAGChatbot")
        except Exception:
            pass

    raise ImportError("Could not import RAGChatbot class")


RAGChatbot = _load_rag_chatbot_class()


def get_random_pr_prompt(difficulty: str) -> str:
    """Generate prompt to get a random PR based on difficulty"""

    prompt = f"Give me a random {difficulty} difficulty PR"

    return prompt


def get_tutorial_generation_prompt(pr_number: int) -> str:
    """Generate prompt to create tutorial for a specific PR"""

    prompt = f"Generate a tutorial for PR #{pr_number}"

    return prompt


def extract_pr_details(response_text: str) -> Optional[Dict]:
    if not response_text or len(response_text.strip()) < 50:
        return None

    pr_details = {}

    # --- PR Number ---
    pr_match = re.search(
        r'PR\s*Number:\s*\*{0,2}#?(\d+)\*{0,2}',
        response_text,
        re.IGNORECASE
    )
    if not pr_match:
        pr_match = re.search(
            r'Pull\s*Request.*?#(\d+)',
            response_text,
            re.IGNORECASE
        )

    if not pr_match:
        return None

    pr_details["pr_number"] = int(pr_match.group(1))

    # --- Title ---
    title_match = re.search(
        r'Pull\s*Request:\s*(.+)',
        response_text,
        re.IGNORECASE
    )
    if title_match:
        pr_details["pr_title"] = title_match.group(1).strip()

    # --- Author ---
    author_match = re.search(
        r'Author:\s*\*{0,2}(.+?)\*{0,2}',
        response_text,
        re.IGNORECASE
    )
    if author_match:
        pr_details["author"] = author_match.group(1).strip()

    # --- Code files modified ---
    files_match = re.search(
        r'Files\s*Modified.*?\n.*?`.*?`',
        response_text,
        re.IGNORECASE | re.DOTALL
    )
    pr_details["code_files_modified"] = (
        len(re.findall(r'`[^`]+`', files_match.group(0)))
        if files_match else 0
    )

    # --- Difficulty (fallback inference) ---
    pr_details["difficulty"] = "Unknown"

    # --- Brief description ---
    summary_match = re.search(
        r'Summary of Changes\s*\n(.+?)(?:\n\n|$)',
        response_text,
        re.IGNORECASE | re.DOTALL
    )
    if summary_match:
        pr_details["brief_description"] = summary_match.group(1).strip()

    return pr_details



def parse_tutorial(response_text: str, pr_details: Dict, tutorial_number: int) -> Optional[Dict]:
    """Parse tutorial response from chatbot"""

    if not response_text or len(response_text.strip()) < 200:
        return None

    parsed_tutorial = {
        'tutorial_number': tutorial_number,
        'pr_number': pr_details.get('pr_number'),
        'pr_title': pr_details.get('pr_title', 'N/A'),
        'author': pr_details.get('author', 'Unknown'),
        'difficulty': pr_details.get('difficulty', 'Unknown'),
        'code_files_modified': pr_details.get('code_files_modified', 0),
        'brief_description': pr_details.get('brief_description', 'N/A'),
        'type': 'PR Tutorial',
        'raw_response': response_text,
        'sections': {}
    }

    # Extract Overview section
    overview_match = re.search(
        r'###\s*1\.?\s*.*?Overview.*?\s*\n+(.*?)(?=###\s*2\.?|$)',
        response_text,
        re.DOTALL | re.IGNORECASE
    )
    if overview_match:
        parsed_tutorial['sections']['overview'] = overview_match.group(1).strip()

    # Extract Problem Context
    problem_match = re.search(
        r'###\s*2\.?\s*.*?Problem.*?\s*\n+(.*?)(?=###\s*3\.?|$)',
        response_text,
        re.DOTALL | re.IGNORECASE
    )
    if problem_match:
        parsed_tutorial['sections']['problem_context'] = problem_match.group(1).strip()

    # Extract Step-by-Step Implementation
    steps_match = re.search(
        r'###\s*3\.?\s*.*?Step.*?\s*\n+(.*?)(?=###\s*4\.?|$)',
        response_text,
        re.DOTALL | re.IGNORECASE
    )
    if steps_match:
        parsed_tutorial['sections']['implementation_steps'] = steps_match.group(1).strip()

    # Extract Testing section
    testing_match = re.search(
        r'###\s*(?:4|5)\.?\s*.*?Testing.*?\s*\n+(.*?)(?=###|$)',
        response_text,
        re.DOTALL | re.IGNORECASE
    )
    if testing_match:
        parsed_tutorial['sections']['testing'] = testing_match.group(1).strip()

    # Extract Key Takeaways/Summary
    takeaways_match = re.search(
        r'###\s*(?:5|6)\.?\s*.*?(?:Takeaways?|Summary).*?\s*\n+(.*?)(?=###|$)',
        response_text,
        re.DOTALL | re.IGNORECASE
    )
    if takeaways_match:
        parsed_tutorial['sections']['key_takeaways'] = takeaways_match.group(1).strip()

    # Count code blocks
    code_blocks = re.findall(r'``````', response_text)
    parsed_tutorial['code_blocks_count'] = len(code_blocks)
    parsed_tutorial['total_code_lines'] = sum(len(block.split('\n')) for block in code_blocks)

    return parsed_tutorial


def generate_pr_tutorials(
    gmail_db_path: str = None,
    provider: str = 'openai',
    model: str = None,
    use_multi_index: bool = True,
    routing_method: str = 'llm'
) -> str:
    """
    Generate PR tutorials: 1 Easy, 1 Medium, 1 Hard using Random PR Generator
    """

    print("=" * 80)
    print("PR Tutorial Generator v2.0 (Random PR Generator)".center(80))
    print("1 Easy | 1 Medium | 1 Hard".center(80))
    print("=" * 80 + "\n")

    if model is None:
        model = "gpt-4o" if provider == 'openai' else None

    print("Initializing chatbot...")
    try:
        chatbot = RAGChatbot(
            vector_db_path=VECTOR_DB_PATH,
            gmail_db_path=gmail_db_path,
            provider=provider,
            model=model,
            temperature=0.5,
            verbose=True,
            routing_method=routing_method,
            enable_multi_query=False,
            disable_conversation_storage=True  # Skip conversation storage for generators
        )

        print("✅ Chatbot initialized successfully\n")

        if use_multi_index and hasattr(chatbot, 'multi_index_store') and chatbot.multi_index_store:
            stats = chatbot.multi_index_store.get_statistics()
            print(f"Multi-index: {stats.get('total_indices', 0)} indices, {stats.get('total_vectors', 0)} vectors")
            print(f"Routing: {routing_method.upper()}\n")

    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        return None

    difficulties = ["Easy", "Medium", "Hard"]
    all_tutorials = []

    print("=" * 80)
    print("Generating PR Tutorials")
    print("=" * 80 + "\n")

    for idx, difficulty in enumerate(difficulties, 1):
        print(f"\n{'='*80}")
        print(f"Tutorial {idx}/3: {difficulty} Difficulty")
        print(f"{'='*80}\n")

        # STEP 1: Get Random PR using Random PR Generator
        print(f"STEP 1: Getting random {difficulty} PR...")
        random_pr_prompt = get_random_pr_prompt(difficulty)

        schema_name = f"{REPO_OWNER}_{REPO_NAME}".replace("-", "_")
        try:
            pr_response = chatbot.chat(random_pr_prompt, schema_name=schema_name)

            if not pr_response or not isinstance(pr_response, dict):
                print(f"❌ Invalid response from Random PR Generator\n")
                continue

            pr_response_text = pr_response.get('answer', '')

            if not pr_response_text:
                print(f"❌ Empty response from Random PR Generator\n")
                continue

            print(f"✅ Random PR Response received ({len(pr_response_text)} characters)")
            print(f"\nPR Details:\n{'-'*60}")
            print(pr_response_text)
            print(f"{'-'*60}\n")

            # Extract PR details from the 6-line response
            pr_details = extract_pr_details(pr_response_text)

            if not pr_details or 'pr_number' not in pr_details:
                print(f"❌ Could not extract PR details from response\n")
                continue

            pr_number = pr_details['pr_number']
            print(f"✅ Selected PR #{pr_number}: {pr_details.get('pr_title', 'N/A')}")
            print(f"   Author: {pr_details.get('author', 'Unknown')}")
            print(f"   Difficulty: {pr_details.get('difficulty', 'Unknown')}")
            print(f"   Code Files: {pr_details.get('code_files_modified', 0)}\n")

        except Exception as e:
            print(f"❌ Error getting random PR: {e}\n")
            continue

        # STEP 2: Generate tutorial for the selected PR
        print(f"STEP 2: Generating tutorial for PR #{pr_number}...")
        tutorial_prompt = get_tutorial_generation_prompt(pr_number)

        schema_name = f"{REPO_OWNER}_{REPO_NAME}".replace("-", "_")
        try:
            tutorial_response = chatbot.chat(tutorial_prompt, schema_name=schema_name)

            if not tutorial_response or not isinstance(tutorial_response, dict):
                print(f"❌ Invalid tutorial response\n")
                continue

            tutorial_text = tutorial_response.get('answer', '')

            if not tutorial_text:
                print(f"❌ Empty tutorial response\n")
                continue

            print(f"✅ Tutorial Generated ({len(tutorial_text):,} characters)")

            # Parse tutorial
            parsed = parse_tutorial(tutorial_text, pr_details, idx)

            if parsed:
                print(f"✅ Tutorial parsed successfully")
                print(f"   - Sections: {len(parsed.get('sections', {}))}")
                print(f"   - Code Blocks: {parsed.get('code_blocks_count', 0)}")
                print(f"   - Total Code Lines: {parsed.get('total_code_lines', 0)}")

                # Add selection response
                parsed['pr_selection_response'] = pr_response_text

                all_tutorials.append(parsed)
                print(f"✅ Tutorial {idx} completed successfully\n")
            else:
                print(f"❌ Failed to parse tutorial {idx}\n")

        except Exception as e:
            print(f"❌ Error generating tutorial: {e}\n")
            continue

    # Create output structure
    tutorials_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator_version": "2.0 (Random PR Generator)",
            "provider": provider,
            "model": model or getattr(chatbot, 'model', 'unknown'),
            "total_tutorials_requested": 3,
            "total_tutorials_generated": len(all_tutorials),
            "tutorial_breakdown": "1 Easy, 1 Medium, 1 Hard",
            "tutorial_type": "PR-Based Step-by-Step Implementation Tutorial",
            "selection_method": "Random PR Generator with code-change filtering",
            "multi_index_enabled": use_multi_index,
            "routing_method": routing_method,
            "features": [
                "Random PR selection with difficulty-based filtering",
                "Automatic code-change validation (excludes docs/configs/tests)",
                "Comprehensive step-by-step tutorials",
                "Real code from actual merged PRs",
                "Problem context and solutions",
                "Testing and practice exercises",
                "Context-aware from repository"
            ]
        },
        "tutorials": all_tutorials,
        "statistics": {
            "total_tutorials": len(all_tutorials),
            "by_difficulty": {
                "Easy": len([t for t in all_tutorials if t.get('difficulty') == 'Easy']),
                "Medium": len([t for t in all_tutorials if t.get('difficulty') == 'Medium']),
                "Hard": len([t for t in all_tutorials if t.get('difficulty') == 'Hard'])
            },
            "total_code_blocks": sum(t.get('code_blocks_count', 0) for t in all_tutorials),
            "total_code_lines": sum(t.get('total_code_lines', 0) for t in all_tutorials),
            "total_code_files_covered": sum(t.get('code_files_modified', 0) for t in all_tutorials),
            "average_sections_per_tutorial": round(
                sum(len(t.get('sections', {})) for t in all_tutorials) / len(all_tutorials), 1
            ) if all_tutorials else 0
        }
    }

    # Save to JSON
    # Upload to S3
    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/bugfix/onboarding_pr_tutorials.json"

    try:
        s3_manager.upload_json(tutorials_data, s3_key)
        print("=" * 80 + "\n")
        print(f"✅ PR tutorials uploaded to S3:")
        print(f"   s3://{s3_manager.bucket}/{s3_key}\n")
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")
        raise

    return s3_key


    print("=" * 80 + "\n")
    print(f"✅ PR tutorials saved to: {json_file}\n")

    return json_file


if __name__ == "__main__":
    result = generate_pr_tutorials(
        gmail_db_path=None,
        provider="openai",
        model="gpt-4o-mini",
        use_multi_index=True,
        routing_method="llm"
    )


