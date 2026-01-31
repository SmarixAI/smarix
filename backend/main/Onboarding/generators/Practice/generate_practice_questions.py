"""
Practice Questions Generator - Code-Level Tutorial Questions
Generates practice coding questions with step-by-step tutorials
1 Easy (5-6 steps), 2 Intermediate (7-8 steps), 1 Hard (9-10 steps)
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import importlib
import importlib.util
from typing import List, Dict, Optional

BACKEND_ROOT = Path(__file__).resolve().parents[4]  # backend/
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.repo_context import get_repo_context
from utils.s3 import s3_manager

ctx = get_repo_context()

REPO_OWNER = ctx["owner"]
REPO_NAME = ctx["repo"]


VECTOR_DB_PATH = ctx["vector_db"]
ONBOARDING_ROOT = ctx["onboarding"]



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

def can_generate_practice_tutorial(repo_chunks: list) -> bool:
    code_chunks = 0

    for c in repo_chunks:
        meta = c.get("metadata", {})

        # ✅ RAG-normalized fields
        content = c.get("text", "").strip()
        index_type = meta.get("index")  # "code", "file", etc.

        if index_type in {"code", "file"} and content:
            line_count = len(content.splitlines())
            if line_count >= 5:   # relaxed threshold is fine
                code_chunks += 1

    print(f"[DEBUG] Executable code chunks detected: {code_chunks}")
    return code_chunks >= 1

def load_practice_question_prompt() -> str:
    """Load the complete practice question generation prompt"""

    prompt_template = """CRITICAL INSTRUCTION: You MUST ONLY use information from the provided context (repository code, emails, documents). DO NOT generate any code, class names, function names, or examples that are not present in the context. If the context does not contain enough information for a particular functionality, skip it and choose a different functionality that exists in the context.

ABSOLUTELY FORBIDDEN: 
- NO Mermaid diagrams
- NO flowcharts
- NO visual diagrams of any kind
- NO architecture diagrams
- NO UML diagrams
- NO graphical representations
- NO markdown diagrams
- NO ASCII art diagrams

Generate ONE practice code-level tutorial question STRICTLY based on a functionality found in the provided context.

DIFFICULTY LEVEL: {difficulty}

- Easy question: EXACTLY 5-6 steps
- Intermediate question: EXACTLY 7-8 steps  
- Hard question: EXACTLY 9-10 steps

MANDATORY POINT: DO NOT provide the solution in just 1-2 steps. You MUST break down the question into the specified number of steps based on difficulty.

---

## Question Description

Create a clear, detailed code-level problem statement focusing on one major application flow that EXISTS IN THE CONTEXT (e.g., authentication, data processing, API integration, state management, error handling, database operations). 

Describe what the end result should accomplish. USE ONLY actual class names, function names, and structures from the provided context.

---

## Implementation Tutorial

YOU MUST break down the complete solution into the EXACT number of sequential steps specified for the difficulty level. EVERY SINGLE STEP MUST INCLUDE COMPLETE, WORKING CODE WITH NO PLACEHOLDERS OR COMMENTS LIKE "// logic will go here".

CRITICAL: Each step MUST contain AT LEAST 10-20 LINES OF CODE. Steps with fewer than 10 lines are FORBIDDEN.

IMPORTANT: Each step should implement ONLY ONE SMALL PART of the solution. Build the solution incrementally across all steps.

---

### For EACH Step, You MUST Provide ALL FOUR SECTIONS:

**Step X: [Step Title]**

**What to Do (MANDATORY - Write at least 5-6 sentences)**
- Explain in detail what needs to be implemented in this specific step ONLY
- Describe the purpose and how it connects to previous steps (if applicable)
- Explain the concepts, patterns, or techniques being used in THIS STEP
- Mention what files or components from the CONTEXT are being modified
- Describe the expected outcome after completing THIS SPECIFIC STEP
- Explain how this step contributes to the overall solution

**Code Snippet (MANDATORY - MUST BE 10-20 LINES PER STEP - COUNT THE LINES)**

ABSOLUTE REQUIREMENTS FOR CODE:
1. REQUIRED: Code MUST be MINIMUM 10 lines, MAXIMUM 20 lines (count them!)
2. REQUIRED: Code MUST be complete and executable with NO placeholders
3. REQUIRED: Code MUST use actual class names, methods, and variables from the provided context
4. REQUIRED: Include all necessary imports, method signatures, and complete implementations FOR THIS STEP
5. REQUIRED: If a single function is too short, include related setup code, imports, class definitions, or helper methods to reach 10+ lines
6. REQUIRED: Add proper error handling, logging, or validation code to extend shorter implementations
7. FORBIDDEN: Code snippets with fewer than 10 lines
8. FORBIDDEN: Comments like "// logic will go here", "// add implementation", "// your code here"
9. FORBIDDEN: Placeholder text or incomplete code blocks
10. FORBIDDEN: Making up class names or methods not in the context
11. FORBIDDEN: Providing the complete solution in one step

**Tips (MANDATORY - Exactly 4-5 tips)**
1. [Specific actionable tip about best practices for THIS STEP based on the context]
2. [Tip about optimization, performance, or alternative approaches relevant to THIS STEP]
3. [Tip about edge cases or scenarios to handle specific to THIS STEP]
4. [Tip about testing or validating THIS STEP works correctly]
5. [Tip about debugging common issues in THIS STEP based on the codebase patterns]

**Common Mistakes to Avoid (MANDATORY - Exactly 2-3 mistakes)**
1. [Specific mistake developers make in THIS STEP with explanation of why it happens and its impact]
2. [Another common pitfall in THIS STEP with consequences and how to prevent it]
3. [Third mistake specific to THIS STEP with clear guidance on avoidance]

---

## ABSOLUTE REQUIREMENTS - FAILURE TO FOLLOW WILL RESULT IN INVALID OUTPUT:

### Output Format Requirements (CRITICAL):
1. FORBIDDEN: Mermaid diagrams, flowcharts, or any visual diagrams
2. FORBIDDEN: Architecture diagrams or system design illustrations
3. FORBIDDEN: UML diagrams or any graphical representations
4. REQUIRED: Only provide text-based tutorial with code snippets
5. REQUIRED: Focus on step-by-step code implementation only

Generate the practice question now."""

    return prompt_template


def parse_practice_question(response_text: str, difficulty: str, question_number: int) -> Optional[Dict]:
    """Parse a practice question from chatbot response"""

    if not response_text or len(response_text.strip()) < 100:
        return None

    parsed_question = {
        'question_number': question_number,
        'difficulty': difficulty,
        'type': 'Practice Code Tutorial',
        'raw_response': response_text,
        'steps': []
    }

    desc_match = re.search(r'##\s*Question Description\s*\n+(.*?)(?=##\s*Implementation Tutorial|$)',
                          response_text, re.DOTALL | re.IGNORECASE)
    if desc_match and desc_match.groups():
        parsed_question['question_description'] = desc_match.group(1).strip()

    step_pattern = r'\*\*Step\s+(\d+):\s*([^\*]+?)\*\*\s*\n+(.*?)(?=\*\*Step\s+\d+:|$)'
    steps_iter = re.finditer(step_pattern, response_text, re.DOTALL)

    for step_match in steps_iter:
        if not step_match.groups() or len(step_match.groups()) < 3:
            continue
        try:
            step_num = int(step_match.group(1))
            step_title = step_match.group(2).strip() if step_match.group(2) else ""
            step_content = step_match.group(3).strip() if step_match.group(3) else ""
        except (IndexError, ValueError, AttributeError) as e:
            print(f"⚠ Warning: Error parsing step match: {e}")
            continue

        # What to Do: capture until Code Snippet or Tips or Common Mistakes or next Step
        what_to_do = ""
        try:
            what_to_do_match = re.search(
                r'\*\*What to Do[:\s]*\*\*\s*\n+(.*?)(?=\*\*Code Snippet|\*\*Tips|\*\*Common Mistakes|\*\*Step|\Z)',
                step_content,
                re.DOTALL | re.IGNORECASE
            )
            if what_to_do_match and what_to_do_match.groups():
                what_to_do = what_to_do_match.group(1).strip()
        except (IndexError, AttributeError):
            pass

        # Code snippet between triple backticks (handles optional language after backticks)
        code_snippet = ""
        try:
            code_match = re.search(r'```(?:[\w+-]*)\s*\n(.*?)\n```', step_content, re.DOTALL)
            if code_match and code_match.groups():
                code_snippet = code_match.group(1).strip()
        except (IndexError, AttributeError):
            pass

        # Tips: numbered list (captures multiple numbered items)
        tips = []
        try:
            tips_match = re.search(
                r'\*\*Tips[:\s]*\*\*\s*\n+(.*?)(?=\*\*Common Mistakes|\*\*Step|\Z)',
                step_content,
                re.DOTALL | re.IGNORECASE
            )
            if tips_match and tips_match.groups():
                tips_text = tips_match.group(1).strip()
                tips = [t.strip() for t in re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n\Z)', tips_text, re.DOTALL) if t.strip()]
        except (IndexError, AttributeError):
            pass

        # Common mistakes: numbered list
        mistakes = []
        try:
            mistakes_match = re.search(
                r'\*\*Common Mistakes(?: to Avoid)?[:\s]*\*\*\s*\n+(.*?)(?=\*\*Step|\Z)',
                step_content,
                re.DOTALL | re.IGNORECASE
            )
            if mistakes_match and mistakes_match.groups():
                mistakes_text = mistakes_match.group(1).strip()
                mistakes = [m.strip() for m in re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\Z)', mistakes_text, re.DOTALL) if m.strip()]
        except (IndexError, AttributeError):
            pass

        parsed_question['steps'].append({
            'step_number': step_num,
            'step_title': step_title,
            'what_to_do': what_to_do,
            'code_snippet': code_snippet,
            'code_line_count': len(code_snippet.split('\n')) if code_snippet else 0,
            'tips': tips,
            'common_mistakes': mistakes
        })

    if not parsed_question['steps']:
        return None

    return parsed_question


def generate_practice_questions(
    gmail_db_path: str = None,
    provider: str = 'openai',
    model: str = None,
    use_multi_index: bool = True,
    routing_method: str = 'llm'
) -> str:
    """
    Generate practice code tutorial questions
    1 Easy, 2 Intermediate, 1 Hard = 4 total questions
    """

    print("=" * 80)
    print("Practice Code Tutorial Questions Generator".center(80))
    print("1 Easy | 2 Intermediate | 1 Hard".center(80))
    print("=" * 80 + "\n")

    if model is None:
        model = "gpt-4o" if provider == 'openai' else None

    print("Initializing chatbot with multi-index support...")
    try:
        chatbot = RAGChatbot(
            vector_db_path=VECTOR_DB_PATH,
            gmail_db_path=gmail_db_path,
            provider=provider,
            model=model,
            temperature=0.4,
            verbose=True,
            routing_method=routing_method,
            enable_multi_query=False,
            disable_conversation_storage=True  # Skip conversation storage for generators
        )

        print("Chatbot initialized successfully")

        if use_multi_index and hasattr(chatbot, 'multi_index_store') and chatbot.multi_index_store:
            stats = chatbot.multi_index_store.get_statistics()
            print(f"Multi-index: {stats.get('total_indices', 0)} indices, {stats.get('total_vectors', 0)} vectors")
            print(f"Routing: {routing_method.upper()}")

    except Exception as e:
        print(f"Failed to initialize chatbot: {e}")
        return None

    prompt_template = load_practice_question_prompt()

    questions_config = [
        {"difficulty": "Easy", "steps": "5-6"},
        {"difficulty": "Intermediate", "steps": "7-8"},
        {"difficulty": "Intermediate", "steps": "7-8"},
        {"difficulty": "Hard", "steps": "9-10"}
    ]

    # 🔍 Pull executable repo context ONLY for feasibility check
    repo_chunks = []

    # Pull from CODE index
    # ✅ CORRECT: use RAG abstraction, not vector store internals
    # 🔍 Pull executable repo context ONLY for feasibility check
    # 🔍 Pull executable repo context ONLY for feasibility check
    repo_chunks = []

    store = getattr(chatbot, "multi_index_store", None)

    if store:
        # Deterministic lookup — no embeddings, no routing
        repo_chunks.extend(
            store.find(
                where={"language": "dart"},
                index="file",
                top_k=20
            )
        )

        repo_chunks.extend(
            store.find(
                where={"language": "dart"},
                index="code",
                top_k=20
            )
        )

    print(f"[DEBUG] Feasibility chunks pulled: {len(repo_chunks)}")


    for c in repo_chunks[:5]:
        meta = c.get("metadata", {})
        print({
            "index": meta.get("index"),
            "file": meta.get("file_path"),
            "lines": len(c.get("text", "").splitlines())
        })

    repo_chunks = repo_chunks or []

    all_questions = []

    print("\n" + "=" * 80)
    print("Generating Practice Code Tutorial Questions")
    print("=" * 80 + "\n")

    can_generate = can_generate_practice_tutorial(repo_chunks)

    for idx, config in enumerate(questions_config, 1):
        difficulty = config["difficulty"]
        steps = config["steps"]

        if not can_generate:
            print(
                f"⚠️  Skipping Question {idx} ({difficulty}) — "
                "not enough executable repo code"
            )
            continue

        print(f"Question {idx}/4: {difficulty} Level ({steps} steps)")
        print(f"Sending request to chatbot...\n")

        question_prompt = prompt_template.format(difficulty=difficulty)

        schema_name = f"{REPO_OWNER}_{REPO_NAME}".replace("-", "_")
        try:
            response = chatbot.chat(question_prompt, schema_name=schema_name)

            if not response or not isinstance(response, dict):
                print(f"Invalid response for Question {idx}\n")
                continue

            answer_text = response.get('answer', '')

            if not answer_text:
                print(f"Empty response for Question {idx}\n")
                continue

            print(f"Received response ({len(answer_text):,} characters)")

            try:
                parsed = parse_practice_question(answer_text, difficulty, idx)

                if parsed and parsed.get('steps'):
                    step_count = len(parsed['steps'])
                    print(f"Parsed successfully: {step_count} steps found")

                    valid_steps = [s for s in parsed['steps'] if s.get('code_line_count', 0) >= 10]
                    print(f"Steps with 10+ lines of code: {len(valid_steps)}/{step_count}")

                    all_questions.append(parsed)
                    print(f"Question {idx} added to output\n")
                else:
                    print(f"Failed to parse Question {idx} - no steps found")
                    print(f"Response preview (first 500 chars): {answer_text[:500]}...\n")
            except (IndexError, AttributeError, ValueError) as parse_error:
                print(f"⚠️  Error parsing Question {idx}: {parse_error}")
                print(f"   This usually means the LLM response format doesn't match expected pattern")
                print(f"   Response preview (first 500 chars): {answer_text[:500]}...\n")
                continue

        except Exception as e:
            print(f"Error generating Question {idx}: {e}\n")
            import traceback
            traceback.print_exc()
            continue

    
    questions_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "provider": provider,
            "model": model or getattr(chatbot, 'model', 'unknown'),
            "total_questions_requested": 4,
            "total_questions_generated": len(all_questions),
            "question_breakdown": "1 Easy, 2 Intermediate, 1 Hard",
            "question_type": "Practice Code Tutorial with Step-by-Step Implementation",
            "multi_index_enabled": use_multi_index,
            "routing_method": routing_method,
            "features": [
                "Step-by-step code tutorials",
                "10-20 lines of code per step",
                "Tips and common mistakes for each step",
                "Context-aware from repository",
                "No hallucinated code",
                "Complete executable code only"
            ]
        },
        "questions": all_questions,
        "statistics": {
            "total_questions": len(all_questions),
            "by_difficulty": {
                "Easy": len([q for q in all_questions if q.get('difficulty') == 'Easy']),
                "Intermediate": len([q for q in all_questions if q.get('difficulty') == 'Intermediate']),
                "Hard": len([q for q in all_questions if q.get('difficulty') == 'Hard'])
            },
            "total_steps": sum(len(q.get('steps', [])) for q in all_questions),
            "average_steps_per_question": round(sum(len(q.get('steps', [])) for q in all_questions) / len(all_questions), 1) if all_questions else 0
        }
    }

    # Upload to S3
    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/practice/onboarding_practice_questions.json"

    try:
        s3_manager.upload_json(questions_data, s3_key)
        print(f"✅ Practice questions uploaded to S3:")
        print(f"   s3://{s3_manager.bucket}/{s3_key}\n")
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")
        raise

    return s3_key


if __name__ == "__main__":
    gmail_db_path: str = None,
    PROVIDER = "openai"
    MODEL = "gpt-4o-mini"
    USE_MULTI_INDEX = True
    ROUTING_METHOD = "llm"

    result = generate_practice_questions(
        provider="openai",
        model="gpt-4o-mini",
        use_multi_index=True,
        routing_method="llm"
    )

