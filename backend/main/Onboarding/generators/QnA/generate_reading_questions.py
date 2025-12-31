"""
Overview Questions Generator - Leveraging Chatbot's Question Generation
Uses chatbot's native QUESTION_GENERATION query type for intelligent MCQ creation
Optimized for meaningful onboarding questions for new users
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
    Parse MCQ questions from chatbot's response in the actual format received
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
        # Format: "B - explanation text" or just "B"
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
                'category': 'Application Overview'
            })

    return questions


def generate_overview_questions(
    db_path: str,
    gmail_db_path: str = None,
    provider: str = 'openai',
    model: str = None,
    num_questions: int = 5,
    routing_method: str = 'llm'
) -> Path:
    """
    Generate MCQ overview questions for new user onboarding

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
    print("║" + " MCQ Overview Questions Generator - New User Onboarding ".center(78) + "║")
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

    # Load project overview
    overview_file = repo_root / "data" / "Onboarding" / "onboarding_reading_data" / "onboarding_project_overview.json"

    if not overview_file.exists():
        print(f"✗  Project overview file not found: {overview_file}")
        return None

    print(f"\n📄 Loading project overview: {overview_file.name}")
    with open(overview_file, 'r', encoding='utf-8') as f:
        overview_data = json.load(f)

    # Extract project context
    project_sections = []
    for key, value in overview_data.get("data", {}).items():
        if isinstance(value, dict) and "answer" in value:
            answer = value.get("answer", "")
            if answer and not str(answer).startswith("Error:") and not str(answer).startswith("No implementation"):
                project_sections.append(f"**{key}**:\n{answer}")

    context_summary = "\n\n".join(project_sections[:6])

    print(f"✓  Loaded {len(project_sections)} sections")
    print(f"   • Total characters: {sum(len(s) for s in project_sections):,}")

    print("\n" + "═" * 80)
    print("Generating meaningful MCQ questions for new user onboarding...")
    print("═" * 80 + "\n")

    # Improved MCQ-only prompt focused on meaningful onboarding questions
    question_prompt = f"""Generate {num_questions} multiple-choice questions (MCQ) about this application specifically designed for new user onboarding based on the repository documentation.

APPLICATION DOCUMENTATION:
{context_summary[:4500]}

CRITICAL REQUIREMENTS:
- Generate ONLY multiple-choice questions (MCQ format)
- Each question must have exactly 4 options (A, B, C, D)
- Only ONE option should be correct
- Questions must be MEANINGFUL and USEFUL for new users learning about the app
- Focus on: app purpose, key features, user benefits, getting started, main workflows
- AVOID: Internal issue numbers, PR numbers, technical implementation details, code structure
- AVOID: Questions that require prior knowledge or aren't helpful for onboarding
- Questions should help users understand WHAT the app does and HOW to use it
- Provide detailed explanations (3-5 sentences) that help users learn

IMPORTANT: Make questions practical and relevant to actual app usage, not development details.

Generate {num_questions} meaningful MCQ questions now."""

    print("📝 Sending MCQ generation request to chatbot...")
    print(f"   • MCQ questions requested: {num_questions}")
    print(f"   • Focus: Meaningful onboarding questions for new users")
    print(f"   • Avoiding: Technical details, issue numbers, code structure\n")

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

        # Parse the structured response using improved parser
        print("🔍 Parsing MCQ questions from response...")
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
            "repository": overview_data.get("metadata", {}).get("repository", "unknown"),
            "provider": provider,
            "model": model or getattr(chatbot, 'model', 'unknown'),
            "total_questions_requested": num_questions,
            "total_questions_generated": len(valid_questions),
            "question_type": "MCQ Only",
            "generation_method": "chatbot_native_mcq_generation_v2",
            "routing_method": routing_method,
            "focus": "Meaningful Onboarding Questions for New Users",
            "quality_features": [
                "Native chatbot question generation",
                "MCQ format only (4 options each)",
                "User-centric onboarding focus",
                "Practical and relevant questions",
                "Avoids technical implementation details",
                "Context-aware from repository documentation",
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

    json_file = output_dir / "onboarding_overview_questions.json"

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
        print(f"\n{'GENERATED MCQ QUESTIONS:'.upper()}")
        for i, q in enumerate(valid_questions, 1):
            difficulty = q.get('difficulty', 'Unknown')
            question_preview = q.get('question', 'N/A')[:75] + "..."
            print(f"   Q{i} [{difficulty}]: {question_preview}")

    if valid_questions:
        print(f"\n{'SAMPLE MCQ QUESTION (DETAILED):'.upper()}")
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
    print(f"✓  MCQ questions saved to: {json_file.name}\n")

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
    print(f"  • Question Type: MCQ ONLY (New User Onboarding)\n")

    result = generate_overview_questions(
        db_path=GITHUB_DB_PATH,
        gmail_db_path=GMAIL_DB_PATH,
        provider=PROVIDER,
        model=MODEL,
        num_questions=NUM_QUESTIONS,
        routing_method=ROUTING_METHOD
    )

    if result:
        print(f"✅ Success! MCQ questions available at: {result}")
    else:
        print("❌ Question generation failed")
