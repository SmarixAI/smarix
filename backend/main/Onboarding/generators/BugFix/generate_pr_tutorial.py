"""
PR Tutorial Generator v3.0 - Enhanced Distribution & Detail
Generates tutorials from 1 Easy, 1 Medium, and 1 Hard PR with comprehensive implementation steps
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

ctx = get_repo_context()
REPO_OWNER = ctx["owner"]
REPO_NAME = ctx["repo"]
ONBOARDING_ROOT = ctx["onboarding"]

PR_JSON_PATH = (
    BACKEND_ROOT /
    "data" /
    "DataProcessing" /
    REPO_OWNER /
    REPO_NAME /
    "chunks" /
    "pr_chunks.json"
)

def load_pr_chunks():
    if not PR_JSON_PATH.exists():
        raise FileNotFoundError(f"PR JSON not found at {PR_JSON_PATH}")
    with open(PR_JSON_PATH, "r") as f:
        return json.load(f)

def build_pr_map(pr_chunks):
    pr_map = {}
    for chunk in pr_chunks:
        pr_number = (
            chunk.get("entities", {}).get("pr_number")
            or chunk.get("metadata", {}).get("pr_number")
            or chunk.get("metadata", {}).get("number")
        )
        if pr_number:
            pr_number = int(pr_number)
            pr_map.setdefault(pr_number, []).append(chunk)
    return pr_map



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


def extract_patches_from_chunk(chunk: Dict) -> List[Dict]:
    """
    Extract all patches from a chunk with multiple fallback strategies.
    Returns list of dicts with 'filename' and 'patch' keys.
    """
    patches = []
    
    # Strategy 1: Check normalized 'file_changes' field
    if "file_changes" in chunk:
        for fc in chunk["file_changes"]:
            if fc.get("patch"):
                patches.append({
                    'filename': fc.get('filename', 'unknown'),
                    'patch': fc.get('patch')
                })
    
    # Strategy 2: Check 'raw_data' field (GitHub API format)
    raw = chunk.get("raw_data", {})
    if "changed_files" in raw:
        for fc in raw["changed_files"]:
            if fc.get("patch"):
                patches.append({
                    'filename': fc.get('filename', 'unknown'),
                    'patch': fc.get('patch')
                })
    
    # Strategy 3: Check 'files' field directly
    if "files" in raw:
        for fc in raw["files"]:
            if fc.get("patch"):
                patches.append({
                    'filename': fc.get('filename', 'unknown'),
                    'patch': fc.get('patch')
                })
    
    # Strategy 4: Check chunk content directly
    if "content" in chunk:
        content = chunk["content"]
        # Look for patch patterns in content
        if "diff --git" in content or "@@" in content:
            patches.append({
                'filename': chunk.get("metadata", {}).get("filename", "unknown"),
                'patch': content
            })
    
    # Strategy 5: Check text field
    if "text" in chunk:
        text = chunk["text"]
        if "diff --git" in text or "@@" in text:
            patches.append({
                'filename': chunk.get("metadata", {}).get("filename", "unknown"),
                'patch': text
            })
    
    return patches


def calculate_pr_metrics(chunks: List[Dict]) -> Dict[str, int]:
    """Calculate comprehensive metrics for a PR"""
    metrics = {
        'total_lines_changed': 0,
        'additions': 0,
        'deletions': 0,
        'file_count': 0,
        'unique_files': set()
    }
    
    for chunk in chunks:
        patches = extract_patches_from_chunk(chunk)
        for patch_info in patches:
            patch = patch_info['patch']
            filename = patch_info['filename']
            
            # Count lines
            lines = patch.split('\n')
            metrics['total_lines_changed'] += len(lines)
            
            # Count additions/deletions
            for line in lines:
                if line.startswith('+') and not line.startswith('+++'):
                    metrics['additions'] += 1
                elif line.startswith('-') and not line.startswith('---'):
                    metrics['deletions'] += 1
            
            metrics['unique_files'].add(filename)
    
    metrics['file_count'] = len(metrics['unique_files'])
    metrics['unique_files'] = list(metrics['unique_files'])  # Convert to list for JSON
    
    return metrics


def categorize_pr_difficulty_smart(chunks: List[Dict]) -> str:
    """
    Smart categorization with more nuanced difficulty levels based on:
    - Total lines changed
    - Number of files
    - Complexity indicators (control flow, error handling, etc.)
    """
    metrics = calculate_pr_metrics(chunks)
    
    total_lines = metrics['total_lines_changed']
    file_count = metrics['file_count']
    
    # Calculate complexity score
    complexity_score = 0
    
    for chunk in chunks:
        patches = extract_patches_from_chunk(chunk)
        for patch_info in patches:
            patch = patch_info['patch']
            
            # Check for complexity indicators
            if 'try' in patch.lower() or 'catch' in patch.lower():
                complexity_score += 2
            if 'async' in patch.lower() or 'await' in patch.lower():
                complexity_score += 2
            if 'class' in patch.lower():
                complexity_score += 3
            if 'interface' in patch.lower() or 'abstract' in patch.lower():
                complexity_score += 3
    
    # Decision logic with adjusted thresholds
    if total_lines <= 50 and file_count == 1 and complexity_score <= 3:
        return "Easy"
    elif total_lines <= 150 and file_count <= 3 and complexity_score <= 8:
        return "Medium"
    else:
        return "Hard"


def rebalance_difficulty_distribution(classified_prs: Dict[str, List[int]]) -> Dict[str, List[int]]:
    """
    Rebalance PR distribution to ensure each difficulty has candidates.
    Uses percentile-based reclassification if needed.
    """
    all_prs = [(pr, diff) for diff, prs in classified_prs.items() for pr in prs]
    
    if len(all_prs) < 3:
        return classified_prs
    
    # If any category is empty, redistribute
    if not classified_prs["Easy"] or not classified_prs["Medium"] or not classified_prs["Hard"]:
        print(f"⚙️ Rebalancing difficulty distribution...")
        
        # Sort all PRs and split into thirds
        total = len(all_prs)
        third = total // 3
        
        # Get random sample from each third
        random.shuffle(all_prs)
        
        rebalanced = {
            "Easy": [pr for pr, _ in all_prs[:third]],
            "Medium": [pr for pr, _ in all_prs[third:2*third]],
            "Hard": [pr for pr, _ in all_prs[2*third:]]
        }
        
        # Ensure each has at least one PR
        if not rebalanced["Easy"] and rebalanced["Medium"]:
            rebalanced["Easy"].append(rebalanced["Medium"].pop(0))
        if not rebalanced["Hard"] and rebalanced["Medium"]:
            rebalanced["Hard"].append(rebalanced["Medium"].pop())
        
        return rebalanced
    
    return classified_prs


def has_real_patches(chunks: List[Dict]) -> bool:
    """Check if any chunk contains real patches"""
    for chunk in chunks:
        patches = extract_patches_from_chunk(chunk)
        if patches:
            return True
    return False


def get_pr_metadata(chunks: List[Dict]) -> Dict:
    """Extract PR metadata from chunks"""
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        raw = chunk.get("raw_data", {})
        
        # Try to get PR title, description, etc.
        title = meta.get("title") or raw.get("title") or "Unknown PR"
        body = meta.get("body") or raw.get("body") or ""
        
        if title != "Unknown PR":
            return {
                "title": title,
                "body": body,
                "state": meta.get("state") or raw.get("state", "unknown"),
                "merged": meta.get("merged") or raw.get("merged", False)
            }
    
    return {"title": "Unknown PR", "body": "", "state": "unknown", "merged": False}


def generate_tutorial_content(chatbot, pr_number: int, chunks: List[Dict], difficulty: str) -> str:
    """
    Generates comprehensive tutorial content with detailed implementation steps.
    """
    # Extract PR metadata and metrics
    pr_meta = get_pr_metadata(chunks)
    metrics = calculate_pr_metrics(chunks)
    
    # Build Context from all patches
    unique_patches = {}  # filename -> patch
    
    for chunk in chunks:
        patches = extract_patches_from_chunk(chunk)
        for patch_info in patches:
            filename = patch_info['filename']
            patch = patch_info['patch']
            
            # Avoid duplicates
            if filename not in unique_patches:
                unique_patches[filename] = patch
    
    if not unique_patches:
        raise ValueError("No patches found in chunks - cannot generate tutorial")
    
    # Format patches for context
    context_parts = []
    for filename, patch in unique_patches.items():
        context_parts.append(
            f"═══════════════════════════════════════════════\n"
            f"📄 File: {filename}\n"
            f"═══════════════════════════════════════════════\n"
            f"{patch}\n"
        )
    
    full_context = "\n".join(context_parts)
    
    print(f"   📝 Extracted {len(unique_patches)} file(s) with patches")
    print(f"   📊 Metrics: {metrics['additions']}+ / {metrics['deletions']}- lines changed")
    
    system_prompt = """
You are an expert software engineering instructor who specializes in creating comprehensive, in-depth technical tutorials.

Your tutorials are known for:
- Exceptional depth and detail in implementation explanations
- Line-by-line code analysis with reasoning
- Thorough exploration of alternative approaches
- Clear architectural context and design decisions
- Extensive testing and validation guidance

You NEVER write summaries. You write complete, tutorial-style technical documentation that teaches developers not just WHAT changed, but WHY and HOW to think about similar problems.
"""

    user_prompt = f"""
Create a **comprehensive, deeply educational Pull Request tutorial** for developers learning this codebase.

This tutorial will be used for onboarding and should serve as a complete learning resource.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ PR INFORMATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PR NUMBER: #{pr_number}
TITLE: {pr_meta['title']}
DIFFICULTY LEVEL: {difficulty}

FILES MODIFIED: {metrics['file_count']}
TOTAL CHANGES: +{metrics['additions']} / -{metrics['deletions']} lines
FILES: {', '.join(metrics['unique_files'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ QUALITY REQUIREMENTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MINIMUM LENGTH: 1500-2000 words (this is NON-NEGOTIABLE)

SECTION 3 (Step-by-Step Implementation) MUST BE THE LONGEST SECTION:
- Minimum 800-1000 words for this section alone
- One detailed subsection per file
- Line-by-line explanation of key changes
- Analysis of old vs new approaches
- Discussion of alternative solutions considered
- Code snippets with inline explanations

CRITICAL RULES:
✓ Write in complete paragraphs with natural flow
✓ Explain your reasoning at each step
✓ Include specific code references from the patches
✓ Discuss WHY decisions were made, not just WHAT changed
✓ Use technical terminology but explain complex concepts
✓ Include realistic examples and scenarios
✓ Quote actual code lines from patches when explaining changes
✗ Do NOT write bullet points or lists (use prose)
✗ Do NOT compress explanations to save space
✗ Do NOT skip over "obvious" parts
✗ Do NOT use generic placeholders

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ MANDATORY STRUCTURE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. Overview and Context (200-300 words)

Write a comprehensive introduction that covers:
- The purpose and scope of this PR
- The high-level problem being solved
- The impact on the codebase and users
- How this PR fits into the larger project architecture

Start with context about the project and what this component does. Then explain what motivated this change. Discuss who benefits from this change and how.

## 2. Problem Analysis (300-400 words)

Provide deep analysis of the problem:
- Detailed description of the bug/limitation being addressed
- How the old code behaved and why it was problematic
- Realistic scenarios where the issue would manifest
- Edge cases and failure modes
- Why this problem is important to fix

Include specific examples of how a user or developer would encounter this issue. Explain the technical root cause. Discuss what makes this problem challenging to solve.

## 3. Step-by-Step Implementation (800-1000 words)

THIS IS THE MOST IMPORTANT SECTION. It must be exceptionally detailed.

For EACH file that was modified, create a subsection like this:

### 3.1 Changes to [filename]

Begin by explaining:
- What role this file plays in the codebase
- What functionality it provides
- Why it needed to be modified for this PR

Then provide a detailed walkthrough:

**Old Implementation:**
Explain how the previous code worked. Quote specific lines from the deletion (- lines) in the patch. Explain the logic flow. Point out the specific weaknesses or bugs.

**New Implementation:**
Explain the new approach in detail. Quote specific lines from the additions (+ lines) in the patch. Walk through the logic step by step. Explain why each change was made.

**Key Changes:**
For each significant modification, explain:
1. What the specific change is (quote the exact code)
2. Why this change was necessary
3. How it solves the problem
4. What alternative approaches might have been considered
5. Why this approach is better than alternatives

**Technical Deep Dive:**
Discuss any complex algorithms, data structures, or patterns used. Explain control flow changes. Analyze error handling improvements. Discuss performance implications.

Repeat this pattern for EVERY file. If there are multiple files, ensure each gets thorough coverage.

## 4. Testing and Validation (200-300 words)

Explain how to verify this change works correctly:

- What manual testing steps should be performed
- What automated tests would be appropriate
- Edge cases that need special testing
- Potential regression risks to watch for
- How to validate the fix actually solves the original problem

Provide specific test scenarios with expected outcomes. Explain what could still break and how to detect it.

## 5. Architectural Insights and Best Practices (200-300 words)

Discuss broader lessons:
- Design patterns or principles demonstrated
- How this change improves code quality
- Architectural decisions and trade-offs
- Best practices illustrated by this PR
- How similar issues can be prevented
- What developers can learn and apply elsewhere

Connect this specific change to general software engineering principles.

## 6. Key Takeaways (100-200 words)

Summarize the most important lessons from this PR. What should developers remember? What patterns or techniques are worth internalizing?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ THE ACTUAL CODE CHANGES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{full_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ REMINDERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Reference the actual file names shown above
- Quote actual lines from the patches
- Count the files correctly (you have {metrics['file_count']} files to discuss)
- Section 3 must have {metrics['file_count']} subsections (one per file)
- Make Section 3 at least 800-1000 words
- Total tutorial must be 1500-2000 words minimum
- Write in flowing prose, not bullet points
- Be thorough, detailed, and educational

BEGIN YOUR TUTORIAL NOW:
"""
    
    return chatbot.call_llm(system_prompt, user_prompt)


def parse_tutorial(response_text: str, pr_number: int, difficulty: str) -> Optional[Dict]:
    """Parse tutorial response from chatbot with enhanced validation"""
    if not response_text or len(response_text.strip()) < 500:
        print(f"   ⚠️ Tutorial too short: {len(response_text)} chars")
        return None
    
    # Basic parsing logic
    sections = {}
    current_section = None
    current_lines = []
    
    for line in response_text.split('\n'):
        # Check for section headers
        if line.strip().startswith('## '):
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_lines).strip()
            
            # Start new section
            header = line.strip('# ').strip()
            # Normalize section names
            if '1' in header or 'overview' in header.lower():
                current_section = 'overview'
            elif '2' in header or 'problem' in header.lower():
                current_section = 'problem_context'
            elif '3' in header or 'implementation' in header.lower() or 'step' in header.lower():
                current_section = 'implementation_steps'
            elif '4' in header or 'test' in header.lower():
                current_section = 'testing'
            elif '5' in header or 'architectural' in header.lower() or 'insight' in header.lower():
                current_section = 'architectural_insights'
            elif '6' in header or 'takeaway' in header.lower() or 'key' in header.lower():
                current_section = 'key_takeaways'
            else:
                current_section = header.lower().replace(' ', '_')
            
            current_lines = []
        else:
            current_lines.append(line)
    
    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_lines).strip()
    
    # Count various metrics
    code_blocks = re.findall(r'```', response_text)
    total_words = len(response_text.split())
    total_lines = len(response_text.split('\n'))
    
    # Check implementation section quality
    impl_section = sections.get('implementation_steps', '')
    impl_words = len(impl_section.split())
    
    return {
        'tutorial_number': pr_number,
        'pr_number': pr_number,
        'difficulty': difficulty,
        'type': 'PR Tutorial',
        'raw_response': response_text,
        'sections': sections,
        'code_blocks_count': len(code_blocks) // 2,
        'total_lines': total_lines,
        'total_words': total_words,
        'implementation_words': impl_words,
        'quality_score': min(100, (total_words / 15))  # Target 1500+ words
    }


def generate_pr_tutorials(
    provider: str = "openai",
    model: str = None
) -> str:
    """
    Generate PR tutorials: 1 Easy, 1 Medium, 1 Hard with comprehensive implementation steps
    """
    print("=" * 80)
    print("PR Tutorial Generator v3.0 (Enhanced Detail & Distribution)".center(80))
    print("=" * 80 + "\n")
    
    if model is None:
        model = "gpt-4o" if provider == 'openai' else None
    
    # Initialize Chatbot
    try:
        chatbot = RAGChatbot(
            vector_db_path=ctx["vector_db"],
            gmail_db_path=None,
            provider=provider,
            model=model,
            temperature=0.7,
            verbose=False,
            disable_conversation_storage=True
        )

        print("✅ Chatbot initialized successfully\n")
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        return None
    
    # STEP 1: Fetch and Classify Candidates

    # STEP 1: Load PR chunks directly from JSON
    print("📂 Loading PR chunks from local JSON...")

    all_chunks = load_pr_chunks()
    candidates = build_pr_map(all_chunks)

    # 🔥 ADD THESE TWO LINES RIGHT HERE
    print(f"📄 Using PR JSON: {PR_JSON_PATH}")
    print(f"📦 Total PRs found: {len(candidates)}")

    if not candidates:
        print("❌ No PR candidates found in pr_chunks.json.")
        return None


    
    # Classify PRs by difficulty with smart categorization
    classified_prs = {"Easy": [], "Medium": [], "Hard": []}
    
    for pr_num, chunks in candidates.items():
        # Only classify if it has patches
        if has_real_patches(chunks):
            diff = categorize_pr_difficulty_smart(chunks)
            classified_prs[diff].append(pr_num)
    
    # Rebalance if needed
    classified_prs = rebalance_difficulty_distribution(classified_prs)
    
    print(f"📊 Final Distribution (with patches):")
    print(f"   Easy: {len(classified_prs['Easy'])} PRs")
    print(f"   Medium: {len(classified_prs['Medium'])} PRs")
    print(f"   Hard: {len(classified_prs['Hard'])} PRs\n")
    
    all_tutorials = []
    difficulties = ["Easy", "Medium", "Hard"]
    
    for idx, difficulty in enumerate(difficulties, 1):
        print(f"\n{'='*80}")
        print(f"Tutorial {idx}/3: {difficulty} Difficulty")
        print(f"{'='*80}\n")
        
        # Select Random PR from this difficulty
        pool = classified_prs[difficulty]
        
        if not pool:
            print(f"❌ No {difficulty} PRs available after distribution.")
            continue
        
        # Randomly select
        random.shuffle(pool)
        selected_pr = pool[0]
        pr_chunks = candidates[selected_pr]
        
        print(f"✅ Selected PR #{selected_pr} ({len(pr_chunks)} chunks)")
        
        # STEP 2: Generate Tutorial
        print(f"🤖 Generating comprehensive tutorial via LLM...")
        
        try:
            tutorial_text = generate_tutorial_content(chatbot, selected_pr, pr_chunks, difficulty)
            parsed = parse_tutorial(tutorial_text, selected_pr, difficulty)
            
            if parsed:
                all_tutorials.append(parsed)
                print(f"✅ Tutorial generated:")
                print(f"   📏 Total: {parsed['total_words']} words, {parsed['total_lines']} lines")
                print(f"   🔧 Implementation section: {parsed['implementation_words']} words")
                print(f"   📊 Quality score: {parsed['quality_score']:.1f}%")
                print(f"   💻 Code blocks: {parsed['code_blocks_count']}")
            else:
                print(f"⚠️ Failed to parse generated tutorial.")
        
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Create output structure
    tutorials_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator_version": "3.0 (Enhanced Detail & Distribution)",
            "provider": provider,
            "model": model,
            "total_tutorials_generated": len(all_tutorials),
            "average_words": sum(t['total_words'] for t in all_tutorials) / max(len(all_tutorials), 1),
            "average_quality_score": sum(t['quality_score'] for t in all_tutorials) / max(len(all_tutorials), 1)
        },
        "tutorials": all_tutorials,
        "statistics": {
            "total_tutorials": len(all_tutorials),
            "by_difficulty": {d: len([t for t in all_tutorials if t['difficulty'] == d]) 
                            for d in difficulties},
            "quality_metrics": {
                "min_words": min((t['total_words'] for t in all_tutorials), default=0),
                "max_words": max((t['total_words'] for t in all_tutorials), default=0),
                "avg_implementation_words": sum(t['implementation_words'] for t in all_tutorials) / max(len(all_tutorials), 1)
            }
        }
    }
    
    # Upload to S3
    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/bugfix/onboarding_pr_tutorials.json"
    
    try:
        s3_manager.upload_json(tutorials_data, s3_key)
        print("\n" + "=" * 80)
        print(f"✅ PR tutorials uploaded to S3:")
        print(f"   s3://{s3_manager.bucket}/{s3_key}")
        print(f"\n📊 Final Statistics:")
        print(f"   Generated: {len(all_tutorials)} tutorial(s)")
        print(f"   Avg Length: {tutorials_data['metadata']['average_words']:.0f} words")
        print(f"   Avg Quality: {tutorials_data['metadata']['average_quality_score']:.1f}%")
        print()
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")
        raise
    
    return s3_key


if __name__ == "__main__":
    generate_pr_tutorials(
        provider="openai",
        model="gpt-4o"
    )
