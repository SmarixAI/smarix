"""
Tech Stack Questions Generator - Leveraging Chatbot's Question Generation
Uses chatbot's native QUESTION_GENERATION query type for intelligent MCQ creation
Focused on technology stack understanding for new developers
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
    Parse MCQ questions from chatbot's response
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

        # Extract question text (before options)
        lines = question_part.split('\n')
        question_text = []
        options = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line is an option (A. B. C. D.)
            option_match = re.match(r'^([A-D])\.\s+(.+)$', line)
            if option_match:
                option_letter = option_match.group(1)
                option_text = option_match.group(2).strip()
                options[option_letter] = option_text
            else:
                # It's part of the question text
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

        # Validate this is a proper MCQ
        if len(options) == 4 and correct_answer and correct_answer in options:
            questions.append({
                'question_number': question_num,
                'type': 'MCQ',
                'difficulty': difficulty,
                'question': ' '.join(question_text),
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation,
                'category': 'Technology Stack'
            })

    return questions


def format_tech_stack_context(tech_stack_data: dict) -> str:
    """Format tech stack data into readable context for question generation"""
    context_parts = []

    # Add metadata
    metadata = tech_stack_data.get('metadata', {})
    repo_name = metadata.get('repository', 'Unknown')
    context_parts.append(f"Repository: {repo_name}")
    context_parts.append(f"Generated: {metadata.get('generated_at', 'Unknown')}\n")

    # Add tech stack overview
    data = tech_stack_data.get('data', {})

    # Programming Languages
    languages = data.get('programming_languages', {})
    if languages:
        context_parts.append("## Programming Languages")
        if isinstance(languages, dict) and 'answer' in languages:
            context_parts.append(languages['answer'])
        else:
            context_parts.append(str(languages))
        context_parts.append("")

    # Frameworks and Libraries
    frameworks = data.get('frameworks_and_libraries', {})
    if frameworks:
        context_parts.append("## Frameworks and Libraries")
        if isinstance(frameworks, dict) and 'answer' in frameworks:
            context_parts.append(frameworks['answer'])
        else:
            context_parts.append(str(frameworks))
        context_parts.append("")

    # Development Tools
    tools = data.get('development_tools', {})
    if tools:
        context_parts.append("## Development Tools")
        if isinstance(tools, dict) and 'answer' in tools:
            context_parts.append(tools['answer'])
        else:
            context_parts.append(str(tools))
        context_parts.append("")

    # Build and Deployment
    build_deploy = data.get('build_and_deployment', {})
    if build_deploy:
        context_parts.append("## Build and Deployment")
        if isinstance(build_deploy, dict) and 'answer' in build_deploy:
            context_parts.append(build_deploy['answer'])
        else:
            context_parts.append(str(build_deploy))
        context_parts.append("")

    # Database and Storage
    database = data.get('database_and_storage', {})
    if database:
        context_parts.append("## Database and Storage")
        if isinstance(database, dict) and 'answer' in database:
            context_parts.append(database['answer'])
        else:
            context_parts.append(str(database))
        context_parts.append("")

    # API and Integration
    api = data.get('api_and_integration', {})
    if api:
        context_parts.append("## API and Integration")
        if isinstance(api, dict) and 'answer' in api:
            context_parts.append(api['answer'])
        else:
            context_parts.append(str(api))
        context_parts.append("")

    # Testing
    testing = data.get('testing', {})
    if testing:
        context_parts.append("## Testing")
        if isinstance(testing, dict) and 'answer' in testing:
            context_parts.append(testing['answer'])
        else:
            context_parts.append(str(testing))
        context_parts.append("")

    return "\n".join(context_parts)


def generate_tech_stack_questions(
    db_path: str,
    gmail_db_path: str = None,
    provider: str = 'openai',
    model: str = None,
    num_questions: int = 5,
    routing_method: str = 'llm'
) -> Path:
    """
    Generate MCQ tech stack questions for new developer onboarding

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
    print("║" + " Tech Stack MCQ Questions Generator - Developer Onboarding ".center(78) + "║")
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

    # Load tech stack data
    tech_stack_file = repo_root / "data" / "Onboarding" / "onboarding_reading_data" / "onboarding_tech_stack.json"

    if not tech_stack_file.exists():
        print(f"✗  Tech stack file not found: {tech_stack_file}")
        return None

    print(f"\n📄 Loading tech stack data: {tech_stack_file.name}")
    with open(tech_stack_file, 'r', encoding='utf-8') as f:
        tech_stack_data = json.load(f)

    # Format tech stack context
    tech_context = format_tech_stack_context(tech_stack_data)

    print(f"✓  Loaded tech stack information")
    print(f"   • Total characters: {len(tech_context):,}")

    # Count categories
    data = tech_stack_data.get('data', {})
    categories = [k for k, v in data.items() if v]
    print(f"   • Categories: {len(categories)}")
    for cat in categories[:5]:
        print(f"     - {cat.replace('_', ' ').title()}")
    if len(categories) > 5:
        print(f"     ... and {len(categories) - 5} more")

    print("\n" + "═" * 80)
    print("Generating tech stack MCQ questions for new developers...")
    print("═" * 80 + "\n")

    # Tech stack specific prompt - EXPLICITLY request question generation format
    question_prompt = f"""Generate {num_questions} MCQ quiz questions about the technology stack for new developer onboarding.

TECHNOLOGY STACK INFORMATION:
{tech_context[:5000]}

CRITICAL: You MUST generate questions in MCQ format, not a tech stack overview.

REQUIREMENTS:
- Generate ONLY multiple-choice questions (MCQ format)
- Each question must have exactly 4 options (A, B, C, D)
- Only ONE option should be correct
- Questions about: programming languages, frameworks, libraries, tools, build systems, testing
- Help developers understand WHAT technologies are used and WHY
- AVOID: Version numbers, deprecated technologies, overly specific details
- Provide detailed explanations (3-5 sentences)

FORMAT (MANDATORY):
### Question 1 (MCQ - Easy)
What is the primary programming language used in this repository?
A. Option A
B. Option B
C. Option C
D. Option D

**Answer:** B - Detailed explanation referencing the tech stack information above.

Generate {num_questions} MCQ questions NOW."""

    print("📝 Sending tech stack MCQ generation request to chatbot...")
    print(f"   • MCQ questions requested: {num_questions}")
    print(f"   • Focus: Technology stack understanding for new developers\n")

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

        # Check if response is actually questions or just tech stack info
        if '### Question' not in answer_text and '## Programming Languages' in answer_text:
            print("⚠  Chatbot returned tech stack overview instead of questions")
            print("    Retrying with more explicit prompt...\n")

            # Retry with even more explicit prompt
            retry_prompt = f"""I need you to GENERATE QUIZ QUESTIONS, not explain the tech stack.

Based on this tech stack information:
{tech_context[:4000]}

Create {num_questions} multiple-choice quiz questions to test a new developer's understanding.

USE THIS EXACT FORMAT:
### Question 1 (MCQ - Easy)
Question text here?
A. First option
B. Second option  
C. Third option
D. Fourth option

**Answer:** B - Explanation here.

### Question 2 (MCQ - Medium)
Question text here?
A. First option
B. Second option
C. Third option
D. Fourth option

**Answer:** C - Explanation here.

GENERATE THE QUESTIONS NOW."""

            response = chatbot.chat(retry_prompt)
            answer_text = response.get('answer', '') if isinstance(response, dict) else ''

            if not answer_text or '### Question' not in answer_text:
                print("✗  Still not receiving questions format after retry")
                print("    Raw response preview:")
                print(answer_text[:500] + "...\n")
                return None

        # Parse the structured response
        print("🔍 Parsing tech stack MCQ questions from response...")
        parsed_questions = parse_mcq_from_response(answer_text)

        print(f"   • Valid MCQ questions parsed: {len(parsed_questions)}\n")

        if not parsed_questions:
            print("✗  No valid MCQ questions found in response")
            print("Raw response preview:")
            print(answer_text[:500] + "...\n")
            return None

        valid_questions = [q for q in parsed_questions if q.get('options') and len(q['options']) == 4]

        print(f"✓  Successfully parsed: {len(valid_questions)} complete MCQ questions")

    except Exception as e:
        print(f"✗  Error during question generation: {e}")
        import traceback
        traceback.print_exc()
        # Re-raise connection errors so they're properly handled upstream
        if "Connection error" in str(e) or "APIConnectionError" in str(type(e).__name__):
            raise
        return None

    # Prepare output data with improved structure
    questions_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": tech_stack_data.get("metadata", {}).get("repository", "unknown"),
            "provider": provider,
            "model": model or getattr(chatbot, 'model', 'unknown'),
            "total_questions_requested": num_questions,
            "total_questions_generated": len(valid_questions),
            "question_type": "MCQ Only",
            "generation_method": "chatbot_native_tech_stack_mcq_generation",
            "routing_method": routing_method,
            "focus": "Technology Stack Understanding for New Developers",
            "tech_categories_covered": list(data.keys()),
            "quality_features": [
                "Native chatbot question generation",
                "MCQ format only (4 options each)",
                "Developer-centric onboarding focus",
                "Technology stack focused",
                "Practical and relevant questions",
                "Understanding technology choices",
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

    json_file = output_dir / "onboarding_tech_stack_questions.json"

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
        print(f"\n{'GENERATED TECH STACK MCQ QUESTIONS:'.upper()}")
        for i, q in enumerate(valid_questions, 1):
            difficulty = q.get('difficulty', 'Unknown')
            question_preview = q.get('question', 'N/A')[:75] + "..."
            print(f"   Q{i} [{difficulty}]: {question_preview}")

    if valid_questions:
        print(f"\n{'SAMPLE TECH STACK MCQ QUESTION (DETAILED):'.upper()}")
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
    print(f"✓  Tech stack MCQ questions saved to: {json_file.name}\n")

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
    print(f"  • Focus: Technology Stack for Developer Onboarding\n")

    result = generate_tech_stack_questions(
        db_path=GITHUB_DB_PATH,
        gmail_db_path=GMAIL_DB_PATH,
        provider=PROVIDER,
        model=MODEL,
        num_questions=NUM_QUESTIONS,
        routing_method=ROUTING_METHOD
    )

    if result:
        print(f"✅ Success! Tech stack MCQ questions available at: {result}")
    else:
        print("❌ Tech stack question generation failed")
