"""
Coding Question Generator - UI/Feature/Test-Case Based Questions
Generates 3 coding questions (UI, Features, Test Cases)
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import importlib
import importlib.util

# --- Ensure backend/ is on PYTHONPATH ---
BACKEND_ROOT = Path(__file__).resolve().parents[4]  # backend/
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.repo_context import get_repo_context

load_dotenv()

# --- Repo context ---
ctx = get_repo_context()

REPO_OWNER = ctx["owner"]
REPO_NAME = ctx["repo"]
VECTOR_DB_PATH = ctx["vector_db"]
ONBOARDING_ROOT = ctx["onboarding"]


def _load_rag_chatbot_class():
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

    for path in BACKEND_ROOT.rglob("chatbot.py"):
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


def get_coding_question_prompt(category: str) -> str:
    prompts = {
        "UI": "Generate a coding question based on a PR which involves UI related fix",
        "Feature": "Generate a coding question based on a PR related to the core language/framework of this repository",
        "Test": "Generate a coding question based on a PR which involves test case related fix",
    }
    return prompts[category]


def generate_coding_questions(
    gmail_db_path: str = None,
    provider: str = "openai",
    model: str = None,
    use_multi_index: bool = True,
    routing_method: str = "llm",
) -> Path:

    if model is None:
        model = "gpt-4o" if provider == "openai" else None

    chatbot = RAGChatbot(
        vector_db_path=VECTOR_DB_PATH,
        gmail_db_path=gmail_db_path,
        provider=provider,
        model=model,
        temperature=0.7,
        verbose=True,
        routing_method=routing_method,
        enable_multi_query=False,
    )

    categories = ["UI", "Feature", "Test"]
    all_questions = []

    for idx, category in enumerate(categories, 1):
        print(f"\n[{idx}/3] {category} question")

        response = chatbot.chat(get_coding_question_prompt(category))
        answer = response.get("answer") if isinstance(response, dict) else None

        if not answer:
            continue

        all_questions.append({
            "question_number": idx,
            "category": category,
            "raw_response": answer,
        })

    data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repo": f"{REPO_OWNER}/{REPO_NAME}",
            "generator": "coding_questions",
            "provider": provider,
            "model": model,
            "total_questions": len(all_questions),
        },
        "questions": all_questions,
    }

    output_dir = ONBOARDING_ROOT / "bugfix"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / "onboarding_coding_questions.json"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Coding questions saved to: {json_file}\n")
    return json_file


if __name__ == "__main__":
    generate_coding_questions(
        provider="openai",
        model="gpt-4o-mini",
        routing_method="llm",
    )
