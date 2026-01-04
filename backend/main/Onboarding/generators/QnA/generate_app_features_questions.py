"""
App Features Questions Generator - Leveraging Chatbot's Question Generation
Uses chatbot's native QUESTION_GENERATION query type for intelligent MCQ creation
Focused on understanding application features for new users
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import importlib
import importlib.util

BACKEND_ROOT = Path(__file__).resolve().parents[4]  # backend/
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.repo_context import get_repo_context

load_dotenv()
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
                'category': 'Application Features'
            })

    return questions


def format_app_features_context(app_features_data: dict) -> str:
    """Format application features data into readable context for question generation"""
    context_parts = []

    # Add metadata
    metadata = app_features_data.get('metadata', {})
    repo_name = metadata.get('repository', 'Unknown')
    context_parts.append(f"Repository: {repo_name}")
    context_parts.append(f"Generated: {metadata.get('generated_at', 'Unknown')}\n")

    # Add features overview
    data = app_features_data.get('data', {})

    # Core Features
    core_features = data.get('core_features', {})
    if core_features:
        context_parts.append("## Core Features")
        if isinstance(core_features, dict) and 'answer' in core_features:
            context_parts.append(core_features['answer'])
        else:
            context_parts.append(str(core_features))
        context_parts.append("")

    # User Interface Features
    ui_features = data.get('user_interface_features', {})
    if ui_features:
        context_parts.append("## User Interface Features")
        if isinstance(ui_features, dict) and 'answer' in ui_features:
            context_parts.append(ui_features['answer'])
        else:
            context_parts.append(str(ui_features))
        context_parts.append("")

    # Data Management Features
    data_mgmt = data.get('data_management_features', {})
    if data_mgmt:
        context_parts.append("## Data Management Features")
        if isinstance(data_mgmt, dict) and 'answer' in data_mgmt:
            context_parts.append(data_mgmt['answer'])
        else:
            context_parts.append(str(data_mgmt))
        context_parts.append("")

    # Integration Features
    integration = data.get('integration_features', {})
    if integration:
        context_parts.append("## Integration Features")
        if isinstance(integration, dict) and 'answer' in integration:
            context_parts.append(integration['answer'])
        else:
            context_parts.append(str(integration))
        context_parts.append("")

    # Advanced Features
    advanced = data.get('advanced_features', {})
    if advanced:
        context_parts.append("## Advanced Features")
        if isinstance(advanced, dict) and 'answer' in advanced:
            context_parts.append(advanced['answer'])
        else:
            context_parts.append(str(advanced))
        context_parts.append("")

    # Customization Features
    customization = data.get('customization_features', {})
    if customization:
        context_parts.append("## Customization Features")
        if isinstance(customization, dict) and 'answer' in customization:
            context_parts.append(customization['answer'])
        else:
            context_parts.append(str(customization))
        context_parts.append("")

    # Performance Features
    performance = data.get('performance_features', {})
    if performance:
        context_parts.append("## Performance Features")
        if isinstance(performance, dict) and 'answer' in performance:
            context_parts.append(performance['answer'])
        else:
            context_parts.append(str(performance))
        context_parts.append("")

    # Security Features
    security = data.get('security_features', {})
    if security:
        context_parts.append("## Security Features")
        if isinstance(security, dict) and 'answer' in security:
            context_parts.append(security['answer'])
        else:
            context_parts.append(str(security))
        context_parts.append("")

    return "\n".join(context_parts)


def generate_app_features_questions(
        gmail_db_path: str = None,
        provider: str = 'openai',
        model: str = None,
        num_questions: int = 5,
        routing_method: str = 'llm'
) -> Path:
    """
    Generate MCQ application features questions for new user onboarding

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
    print("║" + " App Features MCQ Generator - User Onboarding ".center(78) + "║")
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

    # Load app features data
    app_features_file = ONBOARDING_ROOT / "reading" / "onboarding_app_features.json"

    if not app_features_file.exists():
        print(f"✗  App features file not found: {app_features_file}")
        return None

    print(f"\n📄 Loading application features data: {app_features_file.name}")
    with open(app_features_file, 'r', encoding='utf-8') as f:
        app_features_data = json.load(f)

    # Format app features context
    features_context = format_app_features_context(app_features_data)

    print(f"✓  Loaded application features information")
    print(f"   • Total characters: {len(features_context):,}")

    # Count categories
    data = app_features_data.get('data', {})
    categories = [k for k, v in data.items() if v]
    print(f"   • Feature categories: {len(categories)}")
    for cat in categories[:5]:
        print(f"     - {cat.replace('_', ' ').title()}")
    if len(categories) > 5:
        print(f"     ... and {len(categories) - 5} more")

    print("\n" + "═" * 80)
    print("Generating app features MCQ questions for new users...")
    print("═" * 80 + "\n")

    # App features specific prompt with EXAMPLE showing real options
    question_prompt = f"""Generate {num_questions} MCQ quiz questions about the application's features for new user onboarding.

APPLICATION FEATURES INFORMATION:
{features_context[:5000]}

CRITICAL REQUIREMENTS:
1. You MUST generate questions in MCQ format
2. Each question MUST have 4 REAL, SPECIFIC options based on the features information above
3. DO NOT use placeholder text like "Option A", "Option B" - use actual feature names, capabilities, or descriptions
4. Only ONE option should be correct
5. All 4 options must be plausible but only one is correct based on the features info above

EXAMPLE OF CORRECT FORMAT:
### Question 1 (MCQ - Easy)
What is the primary purpose of the task synchronization feature?
A. To backup tasks to cloud storage
B. To sync tasks across multiple devices using Taskwarrior server
C. To share tasks with other users via email
D. To export tasks to a calendar application

**Answer:** B - The task synchronization feature allows users to sync their tasks across multiple devices by connecting to a Taskwarrior server, ensuring data consistency across platforms.

REQUIREMENTS FOR YOUR QUESTIONS:
- Questions about: core features, UI capabilities, data management, integrations, customization options
- Help users understand WHAT the app can do and HOW to use features
- Provide 4 SPECIFIC options with real feature names or capabilities from the features info
- Include detailed explanations (3-5 sentences) referencing actual features
- Focus on practical usage and benefits for users

Generate {num_questions} MCQ questions with REAL feature-based options NOW."""

    print("📝 Sending app features MCQ generation request to chatbot...")
    print(f"   • MCQ questions requested: {num_questions}")
    print(f"   • Focus: Understanding application features for users\n")

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

        # Check if response is actually questions or just features description
        if '### Question' not in answer_text and (
                '## Core Features' in answer_text or '## User Interface' in answer_text):
            print("⚠  Chatbot returned features description instead of questions")
            print("    Retrying with more explicit prompt...\n")

            # Retry with even more explicit prompt
            retry_prompt = f"""GENERATE QUIZ QUESTIONS with REAL OPTIONS about app features, not describe the features.

Features info:
{features_context[:4000]}

Create {num_questions} MCQ questions with 4 REAL, SPECIFIC feature-based options each (not "Option A", "Option B").

MANDATORY FORMAT WITH REAL OPTIONS:
### Question 1 (MCQ - Easy)
Specific question about a feature capability?
A. Actual feature name or capability from features info
B. Another actual feature name or capability
C. Another actual feature name or capability  
D. Another actual feature name or capability

**Answer:** B - Detailed explanation about the feature.

GENERATE NOW."""

            response = chatbot.chat(retry_prompt)
            answer_text = response.get('answer', '') if isinstance(response, dict) else ''

            if not answer_text or '### Question' not in answer_text:
                print("✗  Still not receiving questions format after retry")
                print("    Raw response preview:")
                print(answer_text[:500] + "...\n")
                return None

        # Parse the structured response
        print("🔍 Parsing app features MCQ questions from response...")
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
            "repository": app_features_data.get("metadata", {}).get("repository", "unknown"),
            "provider": provider,
            "model": model or getattr(chatbot, 'model', 'unknown'),
            "total_questions_requested": num_questions,
            "total_questions_generated": len(valid_questions),
            "question_type": "MCQ Only",
            "generation_method": "chatbot_native_app_features_mcq_generation",
            "routing_method": routing_method,
            "focus": "Application Features Understanding for New Users",
            "feature_categories_covered": list(data.keys()),
            "quality_features": [
                "Native chatbot question generation",
                "MCQ format only (4 real options each)",
                "User-centric onboarding focus",
                "Application features focused",
                "Practical usage questions",
                "No placeholder options",
                "Understanding feature capabilities",
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

    json_file = output_dir / "onboarding_app_features_questions.json"

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
        print(f"\n{'GENERATED APP FEATURES MCQ QUESTIONS:'.upper()}")
        for i, q in enumerate(valid_questions, 1):
            difficulty = q.get('difficulty', 'Unknown')
            question_preview = q.get('question', 'N/A')[:75] + "..."
            print(f"   Q{i} [{difficulty}]: {question_preview}")

    if valid_questions:
        print(f"\n{'SAMPLE APP FEATURES MCQ QUESTION (DETAILED):'.upper()}")
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
    print(f"✓  App features MCQ questions saved to: {json_file.name}\n")

    return json_file


if __name__ == "__main__":
    # Configuration
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = "gpt-4o-mini"
    NUM_QUESTIONS = 5
    ROUTING_METHOD = "llm"


    result = generate_app_features_questions(
        gmail_db_path=GMAIL_DB_PATH,
        provider=PROVIDER,
        model=MODEL,
        num_questions=NUM_QUESTIONS,
        routing_method=ROUTING_METHOD
    )

    if result:
        print(f"✅ Success! App features MCQ questions available at: {result}")
    else:
        print("❌ App features question generation failed")
