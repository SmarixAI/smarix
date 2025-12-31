"""
Coding Question Generator - UI/Feature/Test-Case Based Questions
Generates 3 coding questions (UI, Features, Test Cases) and stores raw responses in JSON
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import importlib
import importlib.util

repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

load_dotenv()


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


def get_coding_question_prompt(category: str) -> str:
    """Return simple prompt for each category"""
    prompts = {
        "UI": "Generate a coding question based on a PR which involves UI related fix",
        "Feature": "Generate a coding question based on a PR which relates with main programming language of this application (example: Python, JavaScript, Dart, Java etc.)",
        "Test": "Generate a coding question based on a PR which involves test case related fix",
    }
    return prompts[category]


def generate_coding_questions(
    db_path: str,
    gmail_db_path: str = None,
    provider: str = "openai",
    model: str = None,
    use_multi_index: bool = True,
    routing_method: str = "llm",
) -> Path:
    """
    Generate 3 coding questions (UI, Feature, Test) and save raw responses to JSON
    """

    print("=" * 80)
    print("Coding Question Generator - Simple Raw JSON".center(80))
    print("UI | Features | Test Cases".center(80))
    print("=" * 80 + "\n")

    if model is None:
        model = "gpt-4o" if provider == "openai" else None

    print("Initializing chatbot...")
    try:
        chatbot = RAGChatbot(
            vector_db_path=db_path,
            gmail_db_path=gmail_db_path,
            provider=provider,
            model=model,
            temperature=0.7,
            verbose=True,
            routing_method=routing_method,
            enable_multi_query=False,
        )

        print("✅ Chatbot initialized successfully\n")

    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        return None

    categories = ["UI", "Feature", "Test"]
    all_questions = []

    print("=" * 80)
    print("Generating Coding Questions".center(80))
    print("=" * 80 + "\n")

    for idx, category in enumerate(categories, 1):
        print(f"\n{'='*80}")
        print(f"Question {idx}/3: {category} Category")
        print(f"{'='*80}\n")

        prompt = get_coding_question_prompt(category)
        print(f"Prompt: {prompt}\n")

        try:
            response = chatbot.chat(prompt)

            if not response or not isinstance(response, dict):
                print(f"❌ Invalid response for {category} question\n")
                continue

            answer_text = response.get("answer", "")

            if not answer_text:
                print(f"❌ Empty answer for {category} question\n")
                continue

            print(f"✅ Question Generated ({len(answer_text):,} characters)")
            print(f"\nPreview:\n{'-'*60}")
            print(answer_text[:300] + "..." if len(answer_text) > 300 else answer_text)
            print(f"{'-'*60}\n")

            all_questions.append(
                {
                    "question_number": idx,
                    "category": category,
                    "raw_response": answer_text,
                }
            )

        except Exception as e:
            print(f"❌ Error generating {category} question: {e}\n")
            continue

    data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator_version": "simple-raw-1.0",
            "provider": provider,
            "model": model,
            "total_questions_requested": 3,
            "total_questions_generated": len(all_questions),
            "categories": ["UI", "Feature", "Test"],
        },
        "questions": all_questions,
    }

    output_dir = repo_root / "data" / "Onboarding" / "onboarding_bugfix_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / "onboarding_coding_questions.json"
    
    # Ensure we're saving to the correct category folder (not parent folder)
    assert "onboarding_bugfix_data" in str(json_file), f"Error: File path should include 'onboarding_bugfix_data' but got: {json_file}"
    print(f"📁 Saving to: {json_file}")
    print(f"   Category folder: onboarding_bugfix_data")

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("GENERATION SUMMARY".center(80))
    print("=" * 80)
    print(f"Output: {json_file}")
    print(f"Questions Generated: {len(all_questions)}/3\n")
    print("=" * 80 + "\n")

    return json_file


if __name__ == "__main__":
    GITHUB_DB_PATH = "../../../../data/VectorDB/multi_index"
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = "gpt-4o-mini"
    USE_MULTI_INDEX = True
    ROUTING_METHOD = "llm"

    print("Configuration:")
    print(f"  Multi-index path: {GITHUB_DB_PATH}")
    print(f"  Gmail DB path: {GMAIL_DB_PATH}")
    print(f"  Provider: {PROVIDER}")
    print(f"  Model: {MODEL}")
    print(f"  Routing: {ROUTING_METHOD}")
    print(f"  Categories: UI, Features, Test Cases")
    print(f"  Questions: 3 Total")
    print(f"  Multi-index: {'Enabled' if USE_MULTI_INDEX else 'Disabled'}\n")

    result = generate_coding_questions(
        db_path=GITHUB_DB_PATH,
        gmail_db_path=GMAIL_DB_PATH,
        provider=PROVIDER,
        model=MODEL,
        use_multi_index=USE_MULTI_INDEX,
        routing_method=ROUTING_METHOD,
    )

    if result:
        print(f"✅ Success! Coding questions available at: {result}")
    else:
        print("❌ Coding question generation failed")
