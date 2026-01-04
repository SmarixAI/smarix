"""
Development Setup Questions Generator - Leveraging Chatbot's Question Generation
Uses chatbot's native QUESTION_GENERATION query type for intelligent MCQ creation
Focused on helping new developers set up their development environment
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import importlib
import importlib.util

BACKEND_ROOT = Path(__file__).resolve()
while BACKEND_ROOT.name != "backend":
    BACKEND_ROOT = BACKEND_ROOT.parent

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.repo_context import get_repo_context

load_dotenv()
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
                'category': 'Development Setup'
            })

    return questions


def format_dev_setup_context(dev_setup_data: dict) -> str:
    """Format development setup data into readable context for question generation"""
    context_parts = []

    # Add metadata
    metadata = dev_setup_data.get('metadata', {})
    repo_name = metadata.get('repository', 'Unknown')
    context_parts.append(f"Repository: {repo_name}")
    context_parts.append(f"Generated: {metadata.get('generated_at', 'Unknown')}\n")

    # Add development setup overview
    data = dev_setup_data.get('data', {})

    # Prerequisites
    prerequisites = data.get('prerequisites', {})
    if prerequisites:
        context_parts.append("## Prerequisites")
        if isinstance(prerequisites, dict) and 'answer' in prerequisites:
            context_parts.append(prerequisites['answer'])
        else:
            context_parts.append(str(prerequisites))
        context_parts.append("")

    # Installation Steps
    installation = data.get('installation_steps', {})
    if installation:
        context_parts.append("## Installation Steps")
        if isinstance(installation, dict) and 'answer' in installation:
            context_parts.append(installation['answer'])
        else:
            context_parts.append(str(installation))
        context_parts.append("")

    # Environment Configuration
    env_config = data.get('environment_configuration', {})
    if env_config:
        context_parts.append("## Environment Configuration")
        if isinstance(env_config, dict) and 'answer' in env_config:
            context_parts.append(env_config['answer'])
        else:
            context_parts.append(str(env_config))
        context_parts.append("")

    # Dependencies Setup
    dependencies = data.get('dependencies_setup', {})
    if dependencies:
        context_parts.append("## Dependencies Setup")
        if isinstance(dependencies, dict) and 'answer' in dependencies:
            context_parts.append(dependencies['answer'])
        else:
            context_parts.append(str(dependencies))
        context_parts.append("")

    # Build Instructions
    build = data.get('build_instructions', {})
    if build:
        context_parts.append("## Build Instructions")
        if isinstance(build, dict) and 'answer' in build:
            context_parts.append(build['answer'])
        else:
            context_parts.append(str(build))
        context_parts.append("")

    # Running the Application
    running = data.get('running_the_application', {})
    if running:
        context_parts.append("## Running the Application")
        if isinstance(running, dict) and 'answer' in running:
            context_parts.append(running['answer'])
        else:
            context_parts.append(str(running))
        context_parts.append("")

    # Testing Setup
    testing = data.get('testing_setup', {})
    if testing:
        context_parts.append("## Testing Setup")
        if isinstance(testing, dict) and 'answer' in testing:
            context_parts.append(testing['answer'])
        else:
            context_parts.append(str(testing))
        context_parts.append("")

    # Common Issues
    common_issues = data.get('common_issues', {})
    if common_issues:
        context_parts.append("## Common Issues and Solutions")
        if isinstance(common_issues, dict) and 'answer' in common_issues:
            context_parts.append(common_issues['answer'])
        else:
            context_parts.append(str(common_issues))
        context_parts.append("")

    # IDE Setup
    ide_setup = data.get('ide_setup', {})
    if ide_setup:
        context_parts.append("## IDE Setup")
        if isinstance(ide_setup, dict) and 'answer' in ide_setup:
            context_parts.append(ide_setup['answer'])
        else:
            context_parts.append(str(ide_setup))
        context_parts.append("")

    return "\n".join(context_parts)


def generate_dev_setup_questions(
        gmail_db_path: str = None,
        provider: str = 'openai',
        model: str = None,
        num_questions: int = 5,
        routing_method: str = 'llm'
) -> Path:
    """
    Generate MCQ development setup questions for new developer onboarding

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
    print("║" + " Development Setup MCQ Generator - Developer Onboarding ".center(78) + "║")
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

    # Load development setup data
    dev_setup_file = ONBOARDING_ROOT / "reading" / "onboarding_dev_setup.json"

    if not dev_setup_file.exists():
        print(f"✗  Development setup file not found: {dev_setup_file}")
        return None

    print(f"\n📄 Loading development setup data: {dev_setup_file.name}")
    with open(dev_setup_file, 'r', encoding='utf-8') as f:
        dev_setup_data = json.load(f)

    # Format development setup context
    setup_context = format_dev_setup_context(dev_setup_data)

    print(f"✓  Loaded development setup information")
    print(f"   • Total characters: {len(setup_context):,}")

    # Count categories
    data = dev_setup_data.get('data', {})
    categories = [k for k, v in data.items() if v]
    print(f"   • Setup categories: {len(categories)}")
    for cat in categories[:5]:
        print(f"     - {cat.replace('_', ' ').title()}")
    if len(categories) > 5:
        print(f"     ... and {len(categories) - 5} more")

    print("\n" + "═" * 80)
    print("Generating development setup MCQ questions for new developers...")
    print("═" * 80 + "\n")

    # Development setup specific prompt with EXAMPLE showing real options
    question_prompt = f"""Generate {num_questions} MCQ quiz questions about the development environment setup for new developer onboarding.

DEVELOPMENT SETUP INFORMATION:
{setup_context[:5000]}

CRITICAL REQUIREMENTS:
1. You MUST generate questions in MCQ format
2. Each question MUST have 4 REAL, SPECIFIC options based on the setup information above
3. DO NOT use placeholder text like "Option A", "Option B" - use actual tools, commands, steps, or requirements
4. Only ONE option should be correct
5. All 4 options must be plausible but only one is correct based on the setup info above

EXAMPLE OF CORRECT FORMAT:
### Question 1 (MCQ - Easy)
What is the first step to set up the development environment for this project?
A. Install Flutter SDK version 3.0 or higher
B. Clone the repository using git
C. Install Android Studio
D. Configure the Taskwarrior server

**Answer:** A - The first prerequisite for setting up the development environment is installing Flutter SDK version 3.0 or higher, as this is the primary framework used by the application.

REQUIREMENTS FOR YOUR QUESTIONS:
- Questions about: prerequisites, installation steps, configuration, dependencies, build process, running the app, testing
- Help developers understand HOW to set up their environment correctly
- Provide 4 SPECIFIC options with real tools, commands, or steps from the setup info
- Include detailed explanations (3-5 sentences) referencing actual setup procedures
- Focus on practical setup tasks and troubleshooting

Generate {num_questions} MCQ questions with REAL setup-based options NOW."""

    print("📝 Sending development setup MCQ generation request to chatbot...")
    print(f"   • MCQ questions requested: {num_questions}")
    print(f"   • Focus: Development environment setup procedures\n")

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

        # Check if response is actually questions or just setup description
        if '### Question' not in answer_text and (
                '## Prerequisites' in answer_text or '## Installation' in answer_text):
            print("⚠  Chatbot returned setup description instead of questions")
            print("    Retrying with more explicit prompt...\n")

            # Retry with even more explicit prompt
            retry_prompt = f"""GENERATE QUIZ QUESTIONS with REAL OPTIONS about dev setup, not describe the setup process.

Setup info:
{setup_context[:4000]}

Create {num_questions} MCQ questions with 4 REAL, SPECIFIC setup-based options each (not "Option A", "Option B").

MANDATORY FORMAT WITH REAL OPTIONS:
### Question 1 (MCQ - Easy)
Specific question about setup step or requirement?
A. Actual tool name, command, or setup step from setup info
B. Another actual tool name, command, or setup step
C. Another actual tool name, command, or setup step  
D. Another actual tool name, command, or setup step

**Answer:** B - Detailed explanation about the setup procedure.

GENERATE NOW."""

            response = chatbot.chat(retry_prompt)
            answer_text = response.get('answer', '') if isinstance(response, dict) else ''

            if not answer_text or '### Question' not in answer_text:
                print("✗  Still not receiving questions format after retry")
                print("    Raw response preview:")
                print(answer_text[:500] + "...\n")
                return None

        # Parse the structured response
        print("🔍 Parsing development setup MCQ questions from response...")
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
            "repository": dev_setup_data.get("metadata", {}).get("repository", "unknown"),
            "provider": provider,
            "model": model or getattr(chatbot, 'model', 'unknown'),
            "total_questions_requested": num_questions,
            "total_questions_generated": len(valid_questions),
            "question_type": "MCQ Only",
            "generation_method": "chatbot_native_dev_setup_mcq_generation",
            "routing_method": routing_method,
            "focus": "Development Environment Setup for New Developers",
            "setup_categories_covered": list(data.keys()),
            "quality_features": [
                "Native chatbot question generation",
                "MCQ format only (4 real options each)",
                "Developer-centric onboarding focus",
                "Development setup focused",
                "Practical setup questions",
                "No placeholder options",
                "Understanding setup procedures",
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

    json_file = output_dir / "onboarding_dev_setup_questions.json"

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
        print(f"\n{'GENERATED DEVELOPMENT SETUP MCQ QUESTIONS:'.upper()}")
        for i, q in enumerate(valid_questions, 1):
            difficulty = q.get('difficulty', 'Unknown')
            question_preview = q.get('question', 'N/A')[:75] + "..."
            print(f"   Q{i} [{difficulty}]: {question_preview}")

    if valid_questions:
        print(f"\n{'SAMPLE DEVELOPMENT SETUP MCQ QUESTION (DETAILED):'.upper()}")
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
    print(f"✓  Development setup MCQ questions saved to: {json_file.name}\n")

    return json_file


if __name__ == "__main__":
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = "gpt-4o-mini"
    NUM_QUESTIONS = 5
    ROUTING_METHOD = "llm"



    result = generate_dev_setup_questions(
        gmail_db_path=GMAIL_DB_PATH,
        provider=PROVIDER,
        model=MODEL,
        num_questions=NUM_QUESTIONS,
        routing_method=ROUTING_METHOD
    )

    if result:
        print(f"✅ Success! Development setup MCQ questions available at: {result}")
    else:
        print("❌ Development setup question generation failed")
