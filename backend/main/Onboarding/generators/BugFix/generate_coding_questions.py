"""
Coding Question Generator - UI/Feature/Test-Case Based Questions
Generates 3 coding questions (UI, Features, Test Cases) linked to specific PRs
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
from typing import List, Dict, Optional, Tuple

# ------------------------------------------------------------------
# Ensure backend/ is on PYTHONPATH
# ------------------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parents[4]  # backend/
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.repo_context import get_repo_context
from utils.s3 import s3_manager
from core.ChatBot.query_type import QueryType

load_dotenv()

ctx = get_repo_context()
REPO_OWNER = ctx["owner"]
REPO_NAME = ctx["repo"]
VECTOR_DB_PATH = ctx["vector_db"]


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


def get_category_search_query(category: str) -> str:
    """Returns keywords to find PRs relevant to the category."""
    queries = {
        "UI": "pull request frontend UI css react widget view fix style",
        "Feature": "pull request backend api database controller service logic feature",
        "Test": "pull request tests coverage unit testing integration assert",
    }
    return queries.get(category, "pull request code change")


def find_best_pr_for_category(chatbot, category: str) -> Optional[int]:
    """
    Searches the DB for PR chunks matching the category keywords
    and returns the most relevant PR number.
    """
    search_query = get_category_search_query(category)
    print(f"   🔍 Searching for PRs related to: '{category}'...")

    query_embedding = chatbot.get_query_embedding(search_query)
    
    chunks = []
    # Broad search to find candidate PRs
    if hasattr(chatbot.vector_db, 'search'):
        chunks = chatbot.vector_db.search(query_embedding, top_k=30) # Increased top_k
    
    # Fallback to specific indices
    if not chunks and hasattr(chatbot.vector_db, 'indices'):
        for idx_name in ['pr', 'github', 'code']:
            if idx_name in chatbot.vector_db.indices:
                res = chatbot.vector_db.indices[idx_name].search(query_embedding, top_k=30)
                if isinstance(res, list): chunks.extend(res)

    # Flatten if dict
    if isinstance(chunks, dict):
        flat = []
        for v in chunks.values():
            if isinstance(v, list): flat.extend(v)
        chunks = flat

    # Extract valid PR numbers
    candidate_prs = []
    for c in chunks:
        meta = c.get("metadata", {})
        # Look for pr_number in metadata
        pr_num = meta.get("pr_number") or meta.get("number")
        
        # Also check content/text for "PR #123" pattern if metadata fails
        if not pr_num:
            text = c.get("content") or c.get("text", "")
            match = re.search(r'PR\s*#?(\d+)', text, re.IGNORECASE)
            if match:
                pr_num = int(match.group(1))

        if pr_num and str(pr_num).isdigit():
            candidate_prs.append(int(pr_num))

    if not candidate_prs:
        return None

    # Return the most frequent or simply the first found (most relevant)
    seen = set()
    unique_candidates = [x for x in candidate_prs if not (x in seen or seen.add(x))]
    
    print(f"   ✅ Found candidate PRs: {unique_candidates}")
    return unique_candidates[0]


def fetch_pr_context(chatbot, pr_number: int) -> str:
    """Fetches all chunks specific to a PR number to build context."""
    print(f"   📥 Fetching context for PR #{pr_number}...")
    
    chunks = []
    
    # --- FIX: Use Direct Metadata Lookup (.find) instead of Semantic Search (.search) ---
    if hasattr(chatbot.vector_db, 'find'):
        # Try finding by pr_number integer
        chunks = chatbot.vector_db.find(where={"pr_number": int(pr_number)}, top_k=50)
        
        # If no result, try string (sometimes metadata types vary)
        if not chunks:
            chunks = chatbot.vector_db.find(where={"pr_number": str(pr_number)}, top_k=50)
            
    # Fallback: If .find() didn't work, use semantic search with HIGH top_k
    if not chunks:
        print(f"   ⚠️ Direct lookup failed, falling back to vector search...")
        query_text = f"PR #{pr_number} code changes files"
        query_embedding = chatbot.get_query_embedding(query_text)
        if hasattr(chatbot.vector_db, 'search'):
            chunks = chatbot.vector_db.search(query_embedding, top_k=100) # Get A LOT to ensure we hit the right PR

    # Filter strictly for this PR
    relevant_content = []
    for c in chunks:
        meta = c.get("metadata", {})
        meta_pr = meta.get("pr_number") or meta.get("number")
        text = c.get("content") or c.get("text", "")
        
        # Check metadata match
        if meta_pr and int(meta_pr) == pr_number:
            path = meta.get("file_path", "unknown")
            relevant_content.append(f"File: {path}\n```\n{text[:2000]}\n```")
        # Check text content match (fallback)
        elif str(pr_number) in text:
             path = meta.get("file_path", "unknown")
             relevant_content.append(f"File: {path}\n```\n{text[:2000]}\n```")

    return "\n\n".join(relevant_content)


def generate_coding_questions(
    gmail_db_path: str = None,
    provider: str = "openai",
    model: str = None,
    use_multi_index: bool = True,
    routing_method: str = "llm",
) -> str:

    print("=" * 80)
    print("Coding Question Generator (PR-Based)".center(80))
    print("=" * 80 + "\n")

    if model is None:
        model = "gpt-4o" if provider == "openai" else None

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
        print("✅ Chatbot initialized successfully\n")
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        return None

    categories = ["UI", "Feature", "Test"]
    all_questions = []

    for idx, category in enumerate(categories, 1):
        print(f"\n[{idx}/3] {category} question")

        # STEP 1: Find a relevant PR
        pr_number = find_best_pr_for_category(chatbot, category)
        
        if not pr_number:
            print(f"   ⚠️ No suitable PR found for {category}. Skipping.")
            continue

        # STEP 2: Get Context for that PR
        context = fetch_pr_context(chatbot, pr_number)
        
        if not context:
            print(f"   ⚠️ No context found for PR #{pr_number}. Skipping.")
            continue
        else:
            print(f"   ✅ Context found: {len(context)} chars")

        # STEP 3: Generate Question
        system_prompt = (
            "You are an expert technical interviewer. "
            "Your task is to generate a realistic coding interview question based on the provided PR code changes."
        )
        
        user_prompt = f"""
        CONTEXT:
        The following code changes come from PR #{pr_number}.
        {context[:15000]}

        TASK:
        Generate a {category}-focused coding interview question based on this PR.
        
        CRITICAL REQUIREMENT:
        You MUST include the text "PR #{pr_number}" inside your response, or the system will fail.

        OUTPUT FORMAT:
        Return ONLY a JSON object (no markdown):
        {{
            "title": "Question Title",
            "problem": "Description of the problem (Make sure to mention PR #{pr_number} here)...",
            "code_snippet": "Relevant code snippet...",
            "solution": "Brief solution..."
        }}
        """

        try:
            print(f"   🤖 Generating question for PR #{pr_number}...")
            raw_response = chatbot.call_llm(system_prompt, user_prompt)
            
            clean_response = raw_response.replace("```json", "").replace("```", "").strip()
            
            # Fallback: If LLM forgot to put PR # in the JSON body, force it into the raw text
            if f"PR #{pr_number}" not in clean_response and f"PR {pr_number}" not in clean_response:
                print("   ⚠️  Injecting missing PR number into response...")
                try:
                    data = json.loads(clean_response)
                    data['problem'] = f"Referencing PR #{pr_number}: " + data.get('problem', '')
                    clean_response = json.dumps(data)
                except:
                    # If not valid JSON, just append it
                    clean_response += f"\n\n(Reference: PR #{pr_number})"

            all_questions.append({
                "question_number": idx,
                "category": category,
                "raw_response": clean_response,
            })
            print("   ✅ Question generated.")
            
        except Exception as e:
            print(f"   ❌ LLM Generation failed: {e}")
            continue

    # Prepare Final Data
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

    # Upload to S3
    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/bugfix/onboarding_coding_questions.json"

    try:
        s3_manager.upload_json(data, s3_key)
        print(f"\n✅ Coding questions uploaded to S3:")
        print(f"   s3://{s3_manager.bucket}/{s3_key}\n")
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")
        raise

    return s3_key


if __name__ == "__main__":
    generate_coding_questions(
        provider="openai",
        model="gpt-4o-mini",
        routing_method="llm",
    )