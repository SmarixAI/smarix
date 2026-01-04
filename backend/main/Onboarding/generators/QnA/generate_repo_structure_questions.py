"""
Repository Structure Questions Generator - Leveraging Chatbot's Question Generation
Uses chatbot's native QUESTION_GENERATION query type for intelligent MCQ creation
Focused on understanding repository organization for new developers
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import importlib
import importlib.util

BACKEND_ROOT = Path(__file__).resolve().parents[4]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.repo_context import get_repo_context
ctx = get_repo_context()

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


def parse_mcq_from_response(response_text: str) -> list:
    """
    Parse MCQ questions from chatbot's response with improved option extraction
    Format: ### Question N (MCQ - Difficulty) followed by options and **Answer:**
    """
    questions = []

    # Split by question headers
    question_pattern = r'###\s+Question\s+(\d+)\s+\(MCQ\s*-\s*(\w+)\)'
    question_splits = re.split(question_pattern, response_text)

    # Process splits (format: [text_before, num1, diff1, content1, num2, diff2, content2, ...])
    for i in range(1, len(question_splits), 3):
        if i + 2 > len(question_splits):
            break

        question_num = int(question_splits[i])
        difficulty = question_splits[i + 1].strip()
        content = question_splits[i + 2].strip()

        # Split content into question text and answer
        answer_split = re.split(r'\*\*Answer:\*\*', content, maxsplit=1)

        if len(answer_split) < 2:
            continue

        question_part = answer_split[0].strip()
        answer_part = answer_split[1].strip()

        # Extract question text and options with improved logic
        lines = question_part.split('\n')
        question_text = []
        options = {}
        in_options = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line is an option (A. B. C. D.)
            option_match = re.match(r'^([A-D])\.\s+(.+)$', line)
            if option_match:
                in_options = True
                option_letter = option_match.group(1)
                option_text = option_match.group(2).strip()
                options[option_letter] = option_text
            else:
                # It's part of the question text (only if we haven't started options yet)
                if not in_options:
                    question_text.append(line)

        # Extract correct answer and explanation
        correct_answer = None
        explanation = ""

        answer_match = re.match(r'^([A-D])\s*[-–—]\s*(.+)', answer_part, re.DOTALL)
        if answer_match:
            correct_answer = answer_match.group(1)
            explanation = answer_match.group(2).strip()
        else:
            # Try just letter
            letter_match = re.match(r'^([A-D])', answer_part)
            if letter_match:
                correct_answer = letter_match.group(1)
                explanation = answer_part[1:].strip()
                # Remove leading dashes or hyphens from explanation
                explanation = re.sub(r'^[-–—]\s*', '', explanation)

        # Validate this is a proper MCQ with real options (not just "Option A", "Option B")
        if len(options) == 4 and correct_answer and correct_answer in options:
            # Check if options are actual content, not placeholders
            has_placeholder = any(
                opt_text.lower().startswith('option ') and len(opt_text.split()) <= 2
                for opt_text in options.values()
            )

            if has_placeholder:
                # Skip this question as it has placeholder options
                continue

            questions.append({
                'question_number': question_num,
                'type': 'MCQ',
                'difficulty': difficulty,
                'question': ' '.join(question_text),
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation,
                'category': 'Repository Structure'
            })

    return questions


def format_repo_structure_context(repo_structure_data: dict) -> str:
    """Format repository structure data into readable context for question generation"""
    context_parts = []

    # Add metadata
    metadata = repo_structure_data.get('metadata', {})
    repo_name = metadata.get('repository', 'Unknown')
    context_parts.append(f"Repository: {repo_name}")
    context_parts.append(f"Generated: {metadata.get('generated_at', 'Unknown')}\n")

    # Add repository structure overview
    data = repo_structure_data.get('data', {})

    # Root Directory Overview
    root_overview = data.get('root_directory_overview', {})
    if root_overview:
        context_parts.append("## Root Directory Overview")
        if isinstance(root_overview, dict) and 'answer' in root_overview:
            context_parts.append(root_overview['answer'])
        else:
            context_parts.append(str(root_overview))
        context_parts.append("")

    # Source Code Organization
    source_org = data.get('source_code_organization', {})
    if source_org:
        context_parts.append("## Source Code Organization")
        if isinstance(source_org, dict) and 'answer' in source_org:
            context_parts.append(source_org['answer'])
        else:
            context_parts.append(str(source_org))
        context_parts.append("")

    # Configuration Files
    config_files = data.get('configuration_files', {})
    if config_files:
        context_parts.append("## Configuration Files")
        if isinstance(config_files, dict) and 'answer' in config_files:
            context_parts.append(config_files['answer'])
        else:
            context_parts.append(str(config_files))
        context_parts.append("")

    # Documentation Structure
    docs_structure = data.get('documentation_structure', {})
    if docs_structure:
        context_parts.append("## Documentation Structure")
        if isinstance(docs_structure, dict) and 'answer' in docs_structure:
            context_parts.append(docs_structure['answer'])
        else:
            context_parts.append(str(docs_structure))
        context_parts.append("")

    # Test Organization
    test_org = data.get('test_organization', {})
    if test_org:
        context_parts.append("## Test Organization")
        if isinstance(test_org, dict) and 'answer' in test_org:
            context_parts.append(test_org['answer'])
        else:
            context_parts.append(str(test_org))
        context_parts.append("")

    # Assets and Resources
    assets = data.get('assets_and_resources', {})
    if assets:
        context_parts.append("## Assets and Resources")
        if isinstance(assets, dict) and 'answer' in assets:
            context_parts.append(assets['answer'])
        else:
            context_parts.append(str(assets))
        context_parts.append("")

    # Build and Scripts
    build_scripts = data.get('build_and_scripts', {})
    if build_scripts:
        context_parts.append("## Build and Scripts")
        if isinstance(build_scripts, dict) and 'answer' in build_scripts:
            context_parts.append(build_scripts['answer'])
        else:
            context_parts.append(str(build_scripts))
        context_parts.append("")

    # Key Directories
    key_dirs = data.get('key_directories', {})
    if key_dirs:
        context_parts.append("## Key Directories")
        if isinstance(key_dirs, dict) and 'answer' in key_dirs:
            context_parts.append(key_dirs['answer'])
        else:
            context_parts.append(str(key_dirs))
        context_parts.append("")

    return "\n".join(context_parts)


def generate_repo_structure_questions(
    gmail_db_path: str = None,
    provider: str = 'openai',
    model: str = None,
    num_questions: int = 5,
    routing_method: str = 'llm'
) -> Path:
    """
    Generate MCQ repository structure questions for new developer onboarding

    Args:
        db_path: Path to vector database (multi-index directory)
        gmail_db_path: Optional path to Gmail database
        provider: LLM provider (openai/anthropic/ollama)
        model: Model name (optional, uses default for provider)
        num_questions: Number of MCQ questions to generate
        routing_method: Query routing method (llm/keyword/hybrid)

    Returns:
        Path to generated questions JSON file
    """

    print("╔" + "═" * 78 + "╗")
    print("║" + " Repository Structure MCQ Generator - Developer Onboarding ".center(78) + "║")
    print("╚" + "═" * 78 + "╝\n")

    if model is None:
        model = "gpt-4o-mini" if provider == 'openai' else None

    # Initialize chatbot
    print("⚙  Initializing chatbot with multi-index support...")
    try:
        chatbot = RAGChatbot(
            vector_db_path=VECTOR_DB_PATH,
            gmail_db_path=gmail_db_path,
            provider=provider,
            model=model,
            temperature=0.3,
            verbose=True,
            routing_method=routing_method,
            enable_multi_query=False
        )

        print("✓  Chatbot initialized successfully")

        if hasattr(chatbot, 'multi_index_store') and chatbot.multi_index_store:
            stats = chatbot.multi_index_store.get_statistics()
            print(f"   • Multi-index: {stats.get('total_indices', 0)} indices, {stats.get('total_vectors', 0)} vectors")
            print(f"   • Routing: {routing_method.upper()}")

    except Exception as e:
        print(f"✗  Failed to initialize chatbot: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Ensure multi-index is built: python build_indices.py")
        print("   2. Verify vector DB path points to multi-index directory")
        print("   3. Check all dependencies are installed")
        return None

    # Load repository structure data
    repo_structure_file = ONBOARDING_ROOT / "reading" / "onboarding_repo_structure.json"

    if not repo_structure_file.exists():
        print(f"✗  Repository structure file not found: {repo_structure_file}")
        return None

    print(f"\n📄 Loading repository structure data: {repo_structure_file.name}")
    with open(repo_structure_file, 'r', encoding='utf-8') as f:
        repo_structure_data = json.load(f)

    # Format repository structure context
    structure_context = format_repo_structure_context(repo_structure_data)

    print(f"✓  Loaded repository structure information")
    print(f"   • Total characters: {len(structure_context):,}")

    # Count categories
    data = repo_structure_data.get('data', {})
    categories = [k for k, v in data.items() if v]
    print(f"   • Categories: {len(categories)}")
    for cat in categories[:5]:
        print(f"     - {cat.replace('_', ' ').title()}")
    if len(categories) > 5:
        print(f"     ... and {len(categories) - 5} more")

    print("\n" + "═" * 80)
    print("Generating repository structure MCQ questions for new developers...")
    print("═" * 80 + "\n")

    # Repository structure specific prompt with EXAMPLE showing real options
    question_prompt = f"""Generate {num_questions} MCQ quiz questions about the repository structure and organization for new developer onboarding.

REPOSITORY STRUCTURE INFORMATION:
{structure_context[:5000]}

CRITICAL REQUIREMENTS:
1. You MUST generate questions in MCQ format
2. Each question MUST have 4 REAL, SPECIFIC options based on the structure information above
3. DO NOT use placeholder text like "Option A", "Option B" - use actual directory names, file locations, or descriptions
4. Only ONE option should be correct
5. All 4 options must be plausible but only one is correct based on the structure info above

EXAMPLE OF CORRECT FORMAT:
### Question 1 (MCQ - Easy)
Where is the main source code located in this repository?
A. In the /src directory
B. In the /lib directory
C. In the /code directory
D. In the /app directory

**Answer:** B - The main source code is located in the /lib directory, which contains all the core Dart files for the application logic and UI components.

REQUIREMENTS FOR YOUR QUESTIONS:
- Questions about: directory locations, file organization, project structure, finding resources
- Help developers understand WHERE things are located
- Provide 4 SPECIFIC options with real directory names or descriptions from the structure info
- Include detailed explanations (3-5 sentences) referencing actual directories

Generate {num_questions} MCQ questions with REAL options NOW."""

    print("📝 Sending repository structure MCQ generation request to chatbot...")
    print(f"   • MCQ questions requested: {num_questions}")
    print(f"   • Emphasis: Real options, not placeholders\n")

    try:
        # Call chatbot with question generation prompt
        response = chatbot.chat(question_prompt)

        if not response or not isinstance(response, dict):
            print("✗  Invalid response from chatbot")
            return None

        answer_text = response.get('answer', '')

        if not answer_text:
            print("✗  Empty response from chatbot")
            return None

        print("✓  Received response from chatbot")
        print(f"   • Response length: {len(answer_text):,} characters\n")

        # Check if response is actually questions or just structure description
        if '### Question' not in answer_text and ('## Root Directory' in answer_text or '## Source Code' in answer_text):
            print("⚠  Chatbot returned structure description instead of questions")
            print("    Retrying with more explicit prompt...\n")

            # Retry with even more explicit prompt
            retry_prompt = f"""GENERATE QUIZ QUESTIONS with REAL OPTIONS, not describe the structure.

Structure info:
{structure_context[:4000]}

Create {num_questions} MCQ questions with 4 REAL, SPECIFIC options each (not "Option A", "Option B").

MANDATORY FORMAT WITH REAL OPTIONS:
### Question 1 (MCQ - Easy)
Specific question about location?
A. Actual directory or file name from structure
B. Another actual directory or file name
C. Another actual directory or file name  
D. Another actual directory or file name

**Answer:** B - Detailed explanation.

GENERATE NOW."""

            response = chatbot.chat(retry_prompt)
            answer_text = response.get('answer', '') if isinstance(response, dict) else ''

            if not answer_text or '### Question' not in answer_text:
                print("✗  Still not receiving questions format after retry")
                print("    Raw response preview:")
                print(answer_text[:500] + "...\n")
                return None

        # Parse the structured response
        print("🔍 Parsing repository structure MCQ questions from response...")
        parsed_questions = parse_mcq_from_response(answer_text)

        print(f"   • Valid MCQ questions parsed: {len(parsed_questions)}\n")

        if not parsed_questions:
            print("✗  No valid MCQ questions found in response")
            print("    (Questions with placeholder options like 'Option A' are filtered out)")
            print("Raw response preview:")
            print(answer_text[:800] + "...\n")
            return None

        valid_questions = [q for q in parsed_questions if q.get('options') and len(q['options']) == 4]

        print(f"✓  Successfully parsed: {len(valid_questions)} complete MCQ questions with real options")

    except Exception as e:
        print(f"✗  Error during question generation: {e}")
        import traceback
        traceback.print_exc()
        # Re-raise connection errors so they're properly handled upstream
        if "Connection error" in str(e) or "APIConnectionError" in str(type(e).__name__):
            raise
        return None

    # Prepare output data
    questions_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": repo_structure_data.get("metadata", {}).get("repository", "unknown"),
            "provider": provider,
            "model": model or getattr(chatbot, 'model', 'unknown'),
            "total_questions_requested": num_questions,
            "total_questions_generated": len(valid_questions),
            "question_type": "MCQ Only",
            "generation_method": "chatbot_native_repo_structure_mcq_generation",
            "routing_method": routing_method,
            "focus": "Repository Structure and Organization for New Developers",
            "structure_categories_covered": list(data.keys()),
            "quality_features": [
                "Native chatbot question generation",
                "MCQ format only (4 real options each)",
                "Developer-centric onboarding focus",
                "Repository navigation focused",
                "Practical location-based questions",
                "No placeholder options",
                "Understanding project organization",
                "Comprehensive explanations",
                "Multi-index retrieval"
            ]
        },
        "questions": valid_questions,
        "statistics": {
            "total_questions": len(valid_questions),
            "by_difficulty": {
                "Easy": len([q for q in valid_questions if q.get('difficulty', '').lower() == 'easy']),
                "Medium": len([q for q in valid_questions if q.get('difficulty', '').lower() == 'medium']),
                "Hard": len([q for q in valid_questions if q.get('difficulty', '').lower() == 'hard'])
            }
        }
    }

    # Save to file
    output_dir = ONBOARDING_ROOT / "qna"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / "onboarding_repo_structure_questions.json"

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(questions_data, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "═" * 80)
    print("GENERATION SUMMARY".center(80))
    print("═" * 80)
    print(f"📁 Output: {json_file}")
    print(f"✓  MCQ Questions: {len(valid_questions)}/{num_questions}")

    stats = questions_data['statistics']['by_difficulty']
    print(f"\n{'DIFFICULTY DISTRIBUTION:'.upper()}")
    print(f"   • Easy: {stats['Easy']}")
    print(f"   • Medium: {stats['Medium']}")
    print(f"   • Hard: {stats['Hard']}")

    if valid_questions:
        print(f"\n{'GENERATED REPOSITORY STRUCTURE MCQ QUESTIONS:'.upper()}")
        for i, q in enumerate(valid_questions, 1):
            difficulty = q.get('difficulty', 'Unknown')
            question_preview = q.get('question', 'N/A')[:75] + "..."
            print(f"   Q{i} [{difficulty}]: {question_preview}")

    if valid_questions:
        print(f"\n{'SAMPLE REPOSITORY STRUCTURE MCQ QUESTION (DETAILED):'.upper()}")
        sample = valid_questions[0]
        print(f"   Question {sample.get('question_number', 1)} - Difficulty: {sample.get('difficulty', 'N/A')}")
        print(f"   Q: {sample.get('question', 'N/A')}")
        print(f"\n   Options:")
        if sample.get('options'):
            for opt_key in ['A', 'B', 'C', 'D']:
                if opt_key in sample['options']:
                    opt_val = sample['options'][opt_key]
                    marker = "✓" if opt_key == sample.get('correct_answer') else " "
                    print(f"      {marker} {opt_key}. {opt_val}")
        print(f"\n   Correct Answer: {sample.get('correct_answer', 'N/A')}")
        print(f"   Explanation: {sample.get('explanation', 'N/A')}")

    print(f"\n{'═' * 80}\n")
    print(f"✓  Repository structure MCQ questions saved to: {json_file.name}\n")

    return json_file


if __name__ == "__main__":
    # Configuration
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = "gpt-4o-mini"
    NUM_QUESTIONS = 5
    ROUTING_METHOD = "llm"


    result = generate_repo_structure_questions(
        gmail_db_path=GMAIL_DB_PATH,
        provider=PROVIDER,
        model=MODEL,
        num_questions=NUM_QUESTIONS,
        routing_method=ROUTING_METHOD
    )

    if result:
        print(f"✅ Success! Repository structure MCQ questions available at: {result}")
    else:
        print("❌ Repository structure question generation failed")
