"""
Code Conventions Questions Generator - Leveraging Chatbot's Question Generation
Uses chatbot's native QUESTION_GENERATION query type for intelligent MCQ creation
Focused on helping new developers understand project coding standards
"""

import sys
import json
import re
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
                'category': 'Code Conventions'
            })

    return questions


def format_code_conventions_context(code_conventions_data: dict) -> str:
    """Format code conventions data into readable context for question generation"""
    context_parts = []

    # Add metadata
    metadata = code_conventions_data.get('metadata', {})
    repo_name = metadata.get('repository', 'Unknown')
    context_parts.append(f"Repository: {repo_name}")
    context_parts.append(f"Generated: {metadata.get('generated_at', 'Unknown')}\n")

    # Add code conventions overview
    data = code_conventions_data.get('data', {})

    # Naming Conventions
    naming = data.get('naming_conventions', {})
    if naming:
        context_parts.append("## Naming Conventions")
        if isinstance(naming, dict) and 'answer' in naming:
            context_parts.append(naming['answer'])
        else:
            context_parts.append(str(naming))
        context_parts.append("")

    # File Organization
    file_org = data.get('file_organization', {})
    if file_org:
        context_parts.append("## File Organization")
        if isinstance(file_org, dict) and 'answer' in file_org:
            context_parts.append(file_org['answer'])
        else:
            context_parts.append(str(file_org))
        context_parts.append("")

    # Code Style
    code_style = data.get('code_style', {})
    if code_style:
        context_parts.append("## Code Style")
        if isinstance(code_style, dict) and 'answer' in code_style:
            context_parts.append(code_style['answer'])
        else:
            context_parts.append(str(code_style))
        context_parts.append("")

    # Documentation Standards
    docs_standards = data.get('documentation_standards', {})
    if docs_standards:
        context_parts.append("## Documentation Standards")
        if isinstance(docs_standards, dict) and 'answer' in docs_standards:
            context_parts.append(docs_standards['answer'])
        else:
            context_parts.append(str(docs_standards))
        context_parts.append("")

    # Error Handling
    error_handling = data.get('error_handling', {})
    if error_handling:
        context_parts.append("## Error Handling")
        if isinstance(error_handling, dict) and 'answer' in error_handling:
            context_parts.append(error_handling['answer'])
        else:
            context_parts.append(str(error_handling))
        context_parts.append("")

    # Testing Standards
    testing = data.get('testing_standards', {})
    if testing:
        context_parts.append("## Testing Standards")
        if isinstance(testing, dict) and 'answer' in testing:
            context_parts.append(testing['answer'])
        else:
            context_parts.append(str(testing))
        context_parts.append("")

    # Version Control
    version_control = data.get('version_control', {})
    if version_control:
        context_parts.append("## Version Control")
        if isinstance(version_control, dict) and 'answer' in version_control:
            context_parts.append(version_control['answer'])
        else:
            context_parts.append(str(version_control))
        context_parts.append("")

    # Best Practices
    best_practices = data.get('best_practices', {})
    if best_practices:
        context_parts.append("## Best Practices")
        if isinstance(best_practices, dict) and 'answer' in best_practices:
            context_parts.append(best_practices['answer'])
        else:
            context_parts.append(str(best_practices))
        context_parts.append("")

    return "\n".join(context_parts)


def generate_code_conventions_questions(
        db_path: str,
        gmail_db_path: str = None,
        provider: str = 'openai',
        model: str = None,
        num_questions: int = 5,
        routing_method: str = 'llm'
) -> Path:
    """
    Generate MCQ code conventions questions for new developer onboarding

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
    print("║" + " Code Conventions MCQ Generator - Developer Onboarding ".center(78) + "║")
    print("╚" + "═" * 78 + "╝\n")

    if model is None:
        model = "gpt-4o-mini" if provider == 'openai' else None

    # Initialize chatbot
    print("⚙  Initializing chatbot with multi-index support...")
    try:
        chatbot = RAGChatbot(
            vector_db_path=db_path,
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

    # Load code conventions data
    code_conventions_file = repo_root / "data" / "Onboarding" / "onboarding_reading_data" / "onboarding_code_conventions.json"

    if not code_conventions_file.exists():
        print(f"✗  Code conventions file not found: {code_conventions_file}")
        return None

    print(f"\n📄 Loading code conventions data: {code_conventions_file.name}")
    with open(code_conventions_file, 'r', encoding='utf-8') as f:
        code_conventions_data = json.load(f)

    # Format code conventions context
    conventions_context = format_code_conventions_context(code_conventions_data)

    print(f"✓  Loaded code conventions information")
    print(f"   • Total characters: {len(conventions_context):,}")

    # Count categories
    data = code_conventions_data.get('data', {})
    categories = [k for k, v in data.items() if v]
    print(f"   • Convention categories: {len(categories)}")
    for cat in categories[:5]:
        print(f"     - {cat.replace('_', ' ').title()}")
    if len(categories) > 5:
        print(f"     ... and {len(categories) - 5} more")

    print("\n" + "═" * 80)
    print("Generating code conventions MCQ questions for new developers...")
    print("═" * 80 + "\n")

    # Code conventions specific prompt with EXAMPLE showing real options
    question_prompt = f"""Generate {num_questions} MCQ quiz questions about the project's code conventions and coding standards for new developer onboarding.

CODE CONVENTIONS INFORMATION:
{conventions_context[:5000]}

CRITICAL REQUIREMENTS:
1. You MUST generate questions in MCQ format
2. Each question MUST have 4 REAL, SPECIFIC options based on the conventions information above
3. DO NOT use placeholder text like "Option A", "Option B" - use actual naming patterns, style rules, or conventions
4. Only ONE option should be correct
5. All 4 options must be plausible but only one is correct based on the conventions info above

EXAMPLE OF CORRECT FORMAT:
### Question 1 (MCQ - Easy)
What naming convention should be used for class names in this project?
A. snake_case (e.g., user_profile)
B. camelCase (e.g., userProfile)
C. PascalCase (e.g., UserProfile)
D. kebab-case (e.g., user-profile)

**Answer:** C - According to the project's naming conventions, class names should use PascalCase (e.g., UserProfile), which capitalizes the first letter of each word without spaces or underscores, following Dart's standard conventions.

REQUIREMENTS FOR YOUR QUESTIONS:
- Questions about: naming conventions, file organization, code style, documentation, error handling, testing, version control, best practices
- Help developers understand HOW to write code that follows project standards
- Provide 4 SPECIFIC options with real convention examples from the conventions info
- Include detailed explanations (3-5 sentences) referencing actual standards
- Focus on practical coding scenarios and common mistakes to avoid

Generate {num_questions} MCQ questions with REAL convention-based options NOW."""

    print("📝 Sending code conventions MCQ generation request to chatbot...")
    print(f"   • MCQ questions requested: {num_questions}")
    print(f"   • Focus: Understanding project coding standards\n")

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

        # Check if response is actually questions or just conventions description
        if '### Question' not in answer_text and (
                '## Naming Conventions' in answer_text or '## Code Style' in answer_text):
            print("⚠  Chatbot returned conventions description instead of questions")
            print("    Retrying with more explicit prompt...\n")

            # Retry with even more explicit prompt
            retry_prompt = f"""GENERATE QUIZ QUESTIONS with REAL OPTIONS about code conventions, not describe the conventions.

Conventions info:
{conventions_context[:4000]}

Create {num_questions} MCQ questions with 4 REAL, SPECIFIC convention-based options each (not "Option A", "Option B").

MANDATORY FORMAT WITH REAL OPTIONS:
### Question 1 (MCQ - Easy)
Specific question about a coding standard or convention?
A. Actual naming pattern, style rule, or convention from conventions info
B. Another actual naming pattern, style rule, or convention
C. Another actual naming pattern, style rule, or convention  
D. Another actual naming pattern, style rule, or convention

**Answer:** B - Detailed explanation about the convention.

GENERATE NOW."""

            response = chatbot.chat(retry_prompt)
            answer_text = response.get('answer', '') if isinstance(response, dict) else ''

            if not answer_text or '### Question' not in answer_text:
                print("✗  Still not receiving questions format after retry")
                print("    Raw response preview:")
                print(answer_text[:500] + "...\n")
                return None

        # Parse the structured response
        print("🔍 Parsing code conventions MCQ questions from response...")
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
            "repository": code_conventions_data.get("metadata", {}).get("repository", "unknown"),
            "provider": provider,
            "model": model or getattr(chatbot, 'model', 'unknown'),
            "total_questions_requested": num_questions,
            "total_questions_generated": len(valid_questions),
            "question_type": "MCQ Only",
            "generation_method": "chatbot_native_code_conventions_mcq_generation",
            "routing_method": routing_method,
            "focus": "Code Conventions and Coding Standards for New Developers",
            "convention_categories_covered": list(data.keys()),
            "quality_features": [
                "Native chatbot question generation",
                "MCQ format only (4 real options each)",
                "Developer-centric onboarding focus",
                "Code conventions focused",
                "Practical coding standards questions",
                "No placeholder options",
                "Understanding project conventions",
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
    output_dir = repo_root / "data" / "Onboarding" / "onboarding_QnA_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / "onboarding_code_conventions_questions.json"

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
        print(f"\n{'GENERATED CODE CONVENTIONS MCQ QUESTIONS:'.upper()}")
        for i, q in enumerate(valid_questions, 1):
            difficulty = q.get('difficulty', 'Unknown')
            question_preview = q.get('question', 'N/A')[:75] + "..."
            print(f"   Q{i} [{difficulty}]: {question_preview}")

    if valid_questions:
        print(f"\n{'SAMPLE CODE CONVENTIONS MCQ QUESTION (DETAILED):'.upper()}")
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
    print(f"✓  Code conventions MCQ questions saved to: {json_file.name}\n")

    return json_file


if __name__ == "__main__":
    # Configuration
    GITHUB_DB_PATH = "../../../../data/VectorDB/multi_index"
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = "gpt-4o-mini"
    NUM_QUESTIONS = 5
    ROUTING_METHOD = "llm"

    print("Configuration:")
    print(f"  • Multi-index path: {GITHUB_DB_PATH}")
    print(f"  • Gmail DB path: {GMAIL_DB_PATH}")
    print(f"  • Provider: {PROVIDER}")
    print(f"  • Model: {MODEL}")
    print(f"  • Routing: {ROUTING_METHOD}")
    print(f"  • MCQ Questions: {NUM_QUESTIONS}")
    print(f"  • Focus: Code Conventions and Coding Standards\n")

    result = generate_code_conventions_questions(
        db_path=GITHUB_DB_PATH,
        gmail_db_path=GMAIL_DB_PATH,
        provider=PROVIDER,
        model=MODEL,
        num_questions=NUM_QUESTIONS,
        routing_method=ROUTING_METHOD
    )

    if result:
        print(f"✅ Success! Code conventions MCQ questions available at: {result}")
    else:
        print("❌ Code conventions question generation failed")
