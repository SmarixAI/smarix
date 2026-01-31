"""
Practice Questions Generator - Code-Level Tutorial Questions
Generates practice coding questions with step-by-step tutorials
1 Easy (5-6 steps), 2 Intermediate (7-8 steps), 1 Hard (9-10 steps)
"""

import sys
import json
import re
import random
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
    """Dynamically load RAGChatbot class"""
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


def get_random_code_context(chatbot, limit: int = 10) -> str:
    """
    Fetches random but relevant code chunks from the DB to serve as context
    for the practice question.
    """
    # Keywords to find meaty code logic (not just configs)
    keywords = [
        "service implementation", "controller logic", "api handler", 
        "data processing", "authentication logic", "utility functions",
        "business logic", "database model", "helper class"
    ]
    
    selected_keyword = random.choice(keywords)
    print(f"   🔍 Searching for code context using: '{selected_keyword}'...")
    
    query_embedding = chatbot.get_query_embedding(selected_keyword)
    
    chunks = []
    if hasattr(chatbot.vector_db, 'search'):
        chunks = chatbot.vector_db.search(query_embedding, top_k=limit)
    
    # Fallback to specific indices
    if not chunks and hasattr(chatbot.vector_db, 'indices'):
        for idx in ['code', 'github']:
            if idx in chatbot.vector_db.indices:
                res = chatbot.vector_db.indices[idx].search(query_embedding, top_k=limit)
                if isinstance(res, list): chunks.extend(res)
                
    # Flatten if needed
    if isinstance(chunks, dict):
        flat = []
        for v in chunks.values():
            if isinstance(v, list): flat.extend(v)
        chunks = flat

    # Filter for good code chunks (not too short)
    valid_chunks = []
    for c in chunks:
        text = c.get("content") or c.get("text", "")
        if len(text.splitlines()) > 10:
            path = c.get("metadata", {}).get("file_path", "unknown")
            valid_chunks.append(f"File: {path}\n```\n{text[:2000]}\n```")
    
    if not valid_chunks:
        return ""
        
    # Return a random selection of 3-5 chunks to form a context
    selected_chunks = random.sample(valid_chunks, min(len(valid_chunks), 5))
    return "\n\n".join(selected_chunks)


def load_practice_question_prompt(difficulty: str, steps: str) -> str:
    """Load the complete practice question generation prompt"""

    return f"""
    ROLE: Expert Coding Instructor.
    
    TASK: Generate ONE practice code-level tutorial question based on the provided repository code.
    
    DIFFICULTY: {difficulty}
    REQUIRED STEPS: {steps}
    
    CRITICAL CONSTRAINT: 
    - You MUST use the provided "REPO CONTEXT" code. 
    - Do NOT invent classes or functions that don't exist in the context.
    - If the context is about Authentication, write an Auth question. If it's about Data, write a Data question.

    OUTPUT FORMAT:
    ## Question Description
    Create a clear problem statement based on the code provided. Example: "Implement the error handling logic for the UserService."

    ## Implementation Tutorial
    Break the solution down into exactly {steps} steps.

    **Step 1: [Title]**
    **What to Do**: Explain the task (5-6 sentences).
    **Code Snippet**:
    ```python
    # 10-20 lines of COMPLETE, EXECUTABLE code based on the context.
    # No placeholders like "// logic here".
    ```
    **Tips**: 
    1. Tip 1
    2. Tip 2
    3. Tip 3
    4. Tip 4
    5. Tip 5
    **Common Mistakes**:
    1. Mistake 1
    2. Mistake 2

    (Repeat for all {steps} steps)
    """


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
    if desc_match:
        parsed_question['question_description'] = desc_match.group(1).strip()

    # Improved regex to capture steps robustly
    step_pattern = r'\*\*Step\s+(\d+):\s*([^\*]+?)\*\*(.*?)(?=\*\*Step\s+\d+:|$)'
    steps_iter = re.finditer(step_pattern, response_text, re.DOTALL)

    for step_match in steps_iter:
        if not step_match.groups():
            continue
            
        step_num = int(step_match.group(1))
        step_title = step_match.group(2).strip()
        step_content = step_match.group(3).strip()

        # Extract subsections
        what_to_do = ""
        wtd_match = re.search(r'\*\*What to Do.*?\*\*\s*(.*?)(?=\*\*Code Snippet)', step_content, re.DOTALL | re.IGNORECASE)
        if wtd_match: what_to_do = wtd_match.group(1).strip()

        code_snippet = ""
        code_match = re.search(r'```(?:[\w+-]*)\s*\n(.*?)\n```', step_content, re.DOTALL)
        if code_match: code_snippet = code_match.group(1).strip()

        tips = []
        tips_match = re.search(r'\*\*Tips.*?\*\*\s*(.*?)(?=\*\*Common Mistakes)', step_content, re.DOTALL | re.IGNORECASE)
        if tips_match:
            tips = [t.strip() for t in re.findall(r'\d+\.\s*(.+)', tips_match.group(1))]

        mistakes = []
        mistakes_match = re.search(r'\*\*Common Mistakes.*?\*\*\s*(.*?)(?=$)', step_content, re.DOTALL | re.IGNORECASE)
        if mistakes_match:
            mistakes = [m.strip() for m in re.findall(r'\d+\.\s*(.+)', mistakes_match.group(1))]

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

    print("=" * 80)
    print("Practice Code Tutorial Questions Generator".center(80))
    print("=" * 80 + "\n")

    if model is None:
        model = "gpt-4o" if provider == 'openai' else None

    # Initialize Chatbot
    try:
        chatbot = RAGChatbot(
            vector_db_path=VECTOR_DB_PATH,
            gmail_db_path=gmail_db_path,
            provider=provider,
            model=model,
            temperature=0.7,
            verbose=True,
            routing_method=routing_method,
            enable_multi_query=False,
            disable_conversation_storage=True
        )
        print("✅ Chatbot initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        return None

    questions_config = [
        {"difficulty": "Easy", "steps": "5-6"},
        {"difficulty": "Intermediate", "steps": "7-8"},
        {"difficulty": "Intermediate", "steps": "7-8"},
        {"difficulty": "Hard", "steps": "9-10"}
    ]

    all_questions = []

    for idx, config in enumerate(questions_config, 1):
        difficulty = config["difficulty"]
        steps = config["steps"]

        print(f"\nQuestion {idx}/4: {difficulty} Level ({steps} steps)")

        # STEP 1: Fetch Real Code Context
        context = get_random_code_context(chatbot)
        
        if not context:
            print(f"   ⚠️ Not enough code context found. Skipping.")
            continue
            
        print(f"   ✅ Context found: {len(context)} chars")

        # STEP 2: Generate Question via LLM
        system_prompt = load_practice_question_prompt(difficulty, steps)
        user_prompt = f"REPO CONTEXT:\n{context[:20000]}" # Limit context

        try:
            print(f"   🤖 Generating question via LLM...")
            raw_response = chatbot.call_llm(system_prompt, user_prompt)
            
            # STEP 3: Parse
            parsed = parse_practice_question(raw_response, difficulty, idx)

            if parsed and parsed.get('steps'):
                all_questions.append(parsed)
                print(f"   ✅ Question generated and parsed ({len(parsed['steps'])} steps).")
            else:
                print(f"   ⚠️ Failed to parse generated question.")

        except Exception as e:
            print(f"   ❌ Error generating question: {e}")
            continue

    # Prepare Output
    questions_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "total_questions_generated": len(all_questions),
        },
        "questions": all_questions,
        "statistics": {
            "total_questions": len(all_questions),
            "by_difficulty": {
                "Easy": len([q for q in all_questions if q.get('difficulty') == 'Easy']),
                "Intermediate": len([q for q in all_questions if q.get('difficulty') == 'Intermediate']),
                "Hard": len([q for q in all_questions if q.get('difficulty') == 'Hard'])
            }
        }
    }

    # Upload to S3
    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/practice/onboarding_practice_questions.json"

    try:
        s3_manager.upload_json(questions_data, s3_key)
        print(f"\n✅ Practice questions uploaded to S3:")
        print(f"   s3://{s3_manager.bucket}/{s3_key}\n")
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")
        raise

    return s3_key


if __name__ == "__main__":
    generate_practice_questions(
        provider="openai",
        model="gpt-4o-mini",
        use_multi_index=True,
        routing_method="llm"
    )