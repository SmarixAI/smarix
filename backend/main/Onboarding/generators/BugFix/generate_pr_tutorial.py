"""
PR Tutorial Generator - Automated Tutorial Creation from Random PRs
Generates tutorials from 1 Easy, 1 Medium, and 1 Hard PR
"""

import sys
import json
import re
import random
from pathlib import Path
from datetime import datetime
import importlib
import importlib.util
from typing import List, Dict, Optional, Any

# --- Ensure backend/ is on PYTHONPATH ---
BACKEND_ROOT = Path(__file__).resolve().parents[4]  # backend/
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

repo_root = BACKEND_ROOT

from utils.repo_context import get_repo_context
from utils.s3 import s3_manager
from core.ChatBot.query_type import QueryType

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


def fetch_candidate_prs(chatbot, limit: int = 50) -> Dict[int, List[Dict]]:
    """
    Directly searches the Vector DB for PR chunks to build a candidate pool.
    Returns a dictionary mapping PR Numbers to their chunks.
    """
    print(f"   🔍 Scanning Vector DB for PR candidates...")
    
    # Generic keywords to cast a wide net for PRs
    search_queries = ["pull request merge", "fix bug", "feature implementation", "refactor code"]
    candidates = {}

    for q in search_queries:
        try:
            # 1. Get embedding
            query_embedding = chatbot.get_query_embedding(q)
            
            # 2. Raw Search (Bypassing RAG filters)
            chunks = []
            if hasattr(chatbot.vector_db, 'search'):
                chunks = chatbot.vector_db.search(query_embedding, top_k=limit)
            
            # Fallback to specific indices if main search fails or returns mixed results
            if hasattr(chatbot.vector_db, 'indices'):
                # Check 'pr' or 'github' indices if they exist
                for idx_name in ['pr', 'github', 'code']:
                    if idx_name in chatbot.vector_db.indices:
                        results = chatbot.vector_db.indices[idx_name].search(query_embedding, top_k=limit)
                        if isinstance(results, list):
                            chunks.extend(results)
            
            # 3. Process & Group chunks
            for c in chunks:
                meta = c.get("metadata", {})
                
                # Check if it's actually a PR chunk
                # (Some systems label 'type': 'pr', others might infer from fields like 'pr_number')
                chunk_type = meta.get("type", "unknown")
                pr_number = meta.get("pr_number") or meta.get("number")
                
                # If explicitly a PR or has a PR number, add it
                if pr_number and (chunk_type == 'pr' or str(pr_number).isdigit()):
                    pr_id = int(pr_number)
                    if pr_id not in candidates:
                        candidates[pr_id] = []
                    candidates[pr_id].append(c)
                    
        except Exception as e:
            print(f"   ⚠️ Search error for query '{q}': {e}")
            continue

    print(f"   ✅ Found {len(candidates)} unique PR candidates.")
    return candidates


def categorize_pr_difficulty(chunks: List[Dict]) -> str:
    """
    Estimates difficulty based on content length and complexity.
    """
    total_len = sum(len(c.get("content", "") or c.get("text", "")) for c in chunks)
    
    # Heuristics for difficulty
    if total_len < 1000:
        return "Easy"
    elif total_len < 4000:
        return "Medium"
    else:
        return "Hard"


def generate_tutorial_content(chatbot, pr_number: int, chunks: List[Dict], difficulty: str) -> str:
    """
    Generates the tutorial content using the LLM directly.
    """
    # Build Context
    context_parts = []
    for c in chunks:
        content = c.get("content") or c.get("text", "")
        meta = c.get("metadata", {})
        path = meta.get("file_path") or c.get("file_path", "unknown")
        context_parts.append(f"File: {path}\nContent:\n{content[:2000]}") # Truncate large chunks
    
    full_context = "\n\n".join(context_parts)
    
    system_prompt = (
        "You are an expert technical educator. "
        "Your task is to create a comprehensive, step-by-step tutorial based on the provided Pull Request code."
    )
    
    user_prompt = f"""
    TASK: Generate a {difficulty} level tutorial for PR #{pr_number}.

    PR CONTEXT:
    {full_context[:25000]}  # Context limit

    TUTORIAL STRUCTURE:
    ### 1. Overview
    - What was changed and why? (2-3 sentences)
    
    ### 2. Problem Context
    - What issue does this fix?
    
    ### 3. Step-by-Step Implementation
    - Walk through the code changes logically.
    - Explain *why* specific lines were changed.
    
    ### 4. Testing
    - How would you test these changes?
    
    ### 5. Key Takeaways
    - What can we learn from this PR?

    Use markdown formatting. Be educational and clear.
    """
    
    return chatbot.call_llm(system_prompt, user_prompt)


def parse_tutorial(response_text: str, pr_number: int, difficulty: str) -> Optional[Dict]:
    """Parse tutorial response from chatbot"""
    if not response_text or len(response_text.strip()) < 200:
        return None

    # Basic parsing logic (can be expanded)
    sections = {}
    current_section = None
    
    for line in response_text.split('\n'):
        if line.strip().startswith('###'):
            current_section = line.strip('# ').lower().split('.')[0] # Get header
            # Normalize keys
            if 'overview' in current_section: current_section = 'overview'
            elif 'problem' in current_section: current_section = 'problem_context'
            elif 'step' in current_section: current_section = 'implementation_steps'
            elif 'test' in current_section: current_section = 'testing'
            elif 'takeaway' in current_section: current_section = 'key_takeaways'
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)

    # Join lists back to strings
    for k in sections:
        sections[k] = '\n'.join(sections[k]).strip()

    code_blocks = re.findall(r'```', response_text)
    
    return {
        'tutorial_number': pr_number,
        'pr_number': pr_number,
        'difficulty': difficulty,
        'type': 'PR Tutorial',
        'raw_response': response_text,
        'sections': sections,
        'code_blocks_count': len(code_blocks) // 2,
        'total_code_lines': len(response_text.split('\n'))
    }


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
    print("PR Tutorial Generator v2.0 (Direct DB Access)".center(80))
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
            temperature=0.5,
            verbose=True,
            routing_method=routing_method,
            enable_multi_query=False,
            disable_conversation_storage=True
        )
        print("✅ Chatbot initialized successfully\n")
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        return None

    # STEP 1: Fetch and Classify Candidates
    candidates = fetch_candidate_prs(chatbot)
    if not candidates:
        print("❌ No PR candidates found in Vector DB.")
        return None

    classified_prs = {"Easy": [], "Medium": [], "Hard": []}
    for pr_num, chunks in candidates.items():
        diff = categorize_pr_difficulty(chunks)
        classified_prs[diff].append(pr_num)

    print(f"   📊 Candidate Pool: Easy={len(classified_prs['Easy'])}, Medium={len(classified_prs['Medium'])}, Hard={len(classified_prs['Hard'])}\n")

    all_tutorials = []
    difficulties = ["Easy", "Medium", "Hard"]

    for idx, difficulty in enumerate(difficulties, 1):
        print(f"\n{'='*80}")
        print(f"Tutorial {idx}/3: {difficulty} Difficulty")
        print(f"{'='*80}\n")

        # Select Random PR
        pool = classified_prs[difficulty]
        if not pool:
            # Fallback to any pool if specific difficulty missing
            print(f"   ⚠️ No {difficulty} PRs found. Trying fallback...")
            pool = [p for sublist in classified_prs.values() for p in sublist]
            if not pool:
                print("   ❌ No PRs available at all.")
                continue
        
        selected_pr = random.choice(pool)
        pr_chunks = candidates[selected_pr]
        
        print(f"   ✅ Selected PR #{selected_pr} ({len(pr_chunks)} chunks)")

        # STEP 2: Generate Tutorial
        print(f"   🤖 Generating content via LLM...")
        try:
            tutorial_text = generate_tutorial_content(chatbot, selected_pr, pr_chunks, difficulty)
            
            parsed = parse_tutorial(tutorial_text, selected_pr, difficulty)
            if parsed:
                all_tutorials.append(parsed)
                print(f"   ✅ Tutorial generated and parsed successfully.")
            else:
                print(f"   ⚠️ Failed to parse generated tutorial.")

        except Exception as e:
            print(f"   ❌ Generation failed: {e}")
            continue

    # Create output structure
    tutorials_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator_version": "2.0 (Direct DB Access)",
            "provider": provider,
            "model": model,
            "total_tutorials_generated": len(all_tutorials),
        },
        "tutorials": all_tutorials,
        "statistics": {
            "total_tutorials": len(all_tutorials),
            "by_difficulty": {d: len([t for t in all_tutorials if t['difficulty'] == d]) for d in difficulties}
        }
    }

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


if __name__ == "__main__":
    generate_pr_tutorials(
        gmail_db_path=None,
        provider="openai",
        model="gpt-4o-mini",
        use_multi_index=True,
        routing_method="llm"
    )