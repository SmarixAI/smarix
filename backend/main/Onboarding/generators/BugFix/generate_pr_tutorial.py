"""
PR Tutorial Generator - Automated Tutorial Creation from Random PRs
Generates tutorials from 1 Easy, 1 Medium, and 1 Hard PR
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


def get_random_pr_prompt(difficulty: str) -> str:
    """Generate prompt to get a random PR based on difficulty"""

    prompt = f"Give me a random {difficulty} difficulty PR"

    return prompt


def get_tutorial_generation_prompt(pr_number: int) -> str:
    """Generate prompt to create tutorial for a specific PR"""

    prompt = f"Generate a tutorial for PR #{pr_number}"

    return prompt


def extract_pr_details(response_text: str) -> Optional[Dict]:
    """Extract PR details from the minimal 6-line response"""

    if not response_text or len(response_text.strip()) < 50:
        return None

    pr_details = {}

    # Extract PR Number
    pr_match = re.search(r'PR Number:\s*#?(\d+)', response_text, re.IGNORECASE)
    if pr_match:
        pr_details['pr_number'] = int(pr_match.group(1))
    else:
        return None  # PR number is mandatory

    # Extract PR Title
    title_match = re.search(r'PR Title:\s*(.+?)(?:\n|$)', response_text, re.IGNORECASE)
    if title_match:
        pr_details['pr_title'] = title_match.group(1).strip()

    # Extract Author
    author_match = re.search(r'Author:\s*(.+?)(?:\n|$)', response_text, re.IGNORECASE)
    if author_match:
        pr_details['author'] = author_match.group(1).strip()

    # Extract Difficulty
    difficulty_match = re.search(r'Difficulty:\s*(Easy|Medium|Hard)', response_text, re.IGNORECASE)
    if difficulty_match:
        pr_details['difficulty'] = difficulty_match.group(1).strip()

    # Extract Code Files Modified
    files_match = re.search(r'Code Files Modified:\s*(\d+)', response_text, re.IGNORECASE)
    if files_match:
        pr_details['code_files_modified'] = int(files_match.group(1))

    # Extract Brief Description
    desc_match = re.search(r'Brief Description:\s*(.+?)(?:\n|$)', response_text, re.IGNORECASE | re.DOTALL)
    if desc_match:
        pr_details['brief_description'] = desc_match.group(1).strip()

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
    db_path: str,
    gmail_db_path: str = None,
    provider: str = 'openai',
    model: str = None,
    use_multi_index: bool = True,
    routing_method: str = 'llm'
) -> Path:
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
            vector_db_path=db_path,
            gmail_db_path=gmail_db_path,
            provider=provider,
            model=model,
            temperature=0.5,
            verbose=True,
            routing_method=routing_method,
            enable_multi_query=False
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

        try:
            pr_response = chatbot.chat(random_pr_prompt)

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

        try:
            tutorial_response = chatbot.chat(tutorial_prompt)

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
    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    output_dir = repo_root / "data" / "Onboarding" / "onboarding_bugfix_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / "onboarding_pr_tutorials.json"
    
    # Ensure we're saving to the correct category folder (not parent folder)
    assert "onboarding_bugfix_data" in str(json_file), f"Error: File path should include 'onboarding_bugfix_data' but got: {json_file}"
    print(f"📁 Saving to: {json_file}")
    print(f"   Category folder: onboarding_bugfix_data")

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(tutorials_data, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 80)
    print("GENERATION SUMMARY".center(80))
    print("=" * 80)
    print(f"Output: {json_file.name}")
    print(f"Tutorials Generated: {len(all_tutorials)}/3")

    stats = tutorials_data['statistics']['by_difficulty']
    print(f"\nDIFFICULTY DISTRIBUTION:")
    print(f"  Easy: {stats['Easy']}")
    print(f"  Medium: {stats['Medium']}")
    print(f"  Hard: {stats['Hard']}")

    print(f"\nCODE STATISTICS:")
    print(f"  Total code blocks: {tutorials_data['statistics']['total_code_blocks']}")
    print(f"  Total code lines: {tutorials_data['statistics']['total_code_lines']}")
    print(f"  Total code files: {tutorials_data['statistics']['total_code_files_covered']}")
    print(f"  Average sections per tutorial: {tutorials_data['statistics']['average_sections_per_tutorial']}")

    if all_tutorials:
        print(f"\nGENERATED TUTORIALS:")
        for t in all_tutorials:
            num = t.get('tutorial_number', '?')
            diff = t.get('difficulty', 'Unknown')
            pr_num = t.get('pr_number', '?')
            title = t.get('pr_title', 'N/A')[:60]
            files = t.get('code_files_modified', 0)
            print(f"  Tutorial {num} ({diff})")
            print(f"     PR #{pr_num}: {title}...")
            print(f"     Files: {files}, Blocks: {t.get('code_blocks_count', 0)}\n")

    print("=" * 80 + "\n")
    print(f"✅ PR tutorials saved to: {json_file}\n")

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
    print(f"  Selection Method: Random PR Generator (with code-change filtering)")
    print(f"  Tutorials: 1 Easy, 1 Medium, 1 Hard = 3 Total")
    print(f"  Multi-index: {'Enabled' if USE_MULTI_INDEX else 'Disabled'}\n")

    result = generate_pr_tutorials(
        db_path=GITHUB_DB_PATH,
        gmail_db_path=GMAIL_DB_PATH,
        provider=PROVIDER,
        model=MODEL,
        use_multi_index=USE_MULTI_INDEX,
        routing_method=ROUTING_METHOD
    )

    if result:
        print(f"✅ Success! PR tutorials available at: {result}")
    else:
        print("❌ Tutorial generation failed")
