"""
Simple Onboarding Data Generator
Single command to extract all onboarding info from existing RAG chatbot
"""

import sys
import os
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
from utils.s3 import s3_manager

load_dotenv()
ctx = get_repo_context()

REPO_OWNER = ctx["owner"]
REPO_NAME = ctx["repo"]
VECTOR_DB_PATH = ctx["vector_db"]
ONBOARDING_ROOT = ctx["onboarding"]

REPO_FULL_NAME = f"{REPO_OWNER}/{REPO_NAME}"


def _load_rag_chatbot_class():
    """Try several import paths and finally attempt to load chatbot.py by path."""
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
            # ignore and try next candidate
            pass

    # Fallback: search the repo for a file named chatbot.py and load it dynamically
    for path in BACKEND_ROOT.rglob("chatbot.py"):
        try:
            spec = importlib.util.spec_from_file_location("rag_chatbot_dynamic", str(path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            if hasattr(mod, "RAGChatbot"):
                return getattr(mod, "RAGChatbot")
        except Exception:
            # try next match
            pass

    # If we reach here, nothing worked
    raise ImportError(
        "Could not import RAGChatbot. Tried import paths: "
        + ", ".join(candidates)
        + ". Also searched repository for chatbot.py. "
        "Make sure project is on PYTHONPATH and package markers (__init__.py) exist where needed."
    )


# get the class (raises informative ImportError if not found)
RAGChatbot = _load_rag_chatbot_class()


def parse_single_mcq_from_response(response_text: str) -> dict:
    """
    Parse a single MCQ question from chatbot's response
    Returns a dict with question, options, correct_answer, and explanation
    """
    # Try to find the first MCQ in the response
    question_pattern = r'###\s+Question\s+(\d+)\s+\(MCQ\s*-\s*(\w+)\)'
    match = re.search(question_pattern, response_text)
    
    if not match:
        # Try alternative format without header
        # Look for question text followed by options A-D
        lines = response_text.split('\n')
        question_text = []
        options = {}
        correct_answer = None
        explanation = ""
        
        answer_section = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for answer markers
            if '**Answer:**' in line or 'Answer:' in line:
                answer_section = True
                answer_line = line.split(':', 1)[-1].strip() if ':' in line else line.replace('**Answer:**', '').strip()
                if answer_line:
                    answer_match = re.match(r'^([A-D])\s*[-–—]\s*(.+)', answer_line, re.DOTALL)
                    if answer_match:
                        correct_answer = answer_match.group(1)
                        explanation = answer_match.group(2).strip()
                    else:
                        letter_match = re.match(r'^([A-D])', answer_line)
                        if letter_match:
                            correct_answer = letter_match.group(1)
                            explanation = answer_line[1:].strip()
                continue
            
            if answer_section:
                explanation += " " + line if explanation else line
                continue
            
            # Check if line is an option
            option_match = re.match(r'^([A-D])\.\s+(.+)$', line)
            if option_match:
                option_letter = option_match.group(1)
                option_text = option_match.group(2).strip()
                options[option_letter] = option_text
            else:
                # It's part of the question text
                question_text.append(line)
        
        if len(options) == 4 and correct_answer and correct_answer in options:
            return {
                'question': ' '.join(question_text),
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation.strip()
            }
        return None
    
    # Extract content after the header
    start_idx = match.end()
    content = response_text[start_idx:].strip()
    
    # Split content into question text and answer
    answer_split = re.split(r'\*\*Answer:\*\*', content, maxsplit=1)
    
    if len(answer_split) < 2:
        return None
    
    question_part = answer_split[0].strip()
    answer_part = answer_split[1].strip()
    
    # Extract question text and options
    lines = question_part.split('\n')
    question_text = []
    options = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line is an option
        option_match = re.match(r'^([A-D])\.\s+(.+)$', line)
        if option_match:
            option_letter = option_match.group(1)
            option_text = option_match.group(2).strip()
            options[option_letter] = option_text
        else:
            question_text.append(line)
    
    # Extract correct answer and explanation
    correct_answer = None
    explanation = ""
    
    answer_match = re.match(r'^([A-D])\s*[-–—]\s*(.+)', answer_part, re.DOTALL)
    if answer_match:
        correct_answer = answer_match.group(1)
        explanation = answer_match.group(2).strip()
    else:
        letter_match = re.match(r'^([A-D])', answer_part)
        if letter_match:
            correct_answer = letter_match.group(1)
            explanation = answer_part[1:].strip()
    
    # Validate this is a proper MCQ
    if len(options) == 4 and correct_answer and correct_answer in options:
        return {
            'question': ' '.join(question_text),
            'options': options,
            'correct_answer': correct_answer,
            'explanation': explanation
        }
    
    return None


def generate_data_qna(reading_overview_data, chatbot, gmail_db_path=None, provider='openai', model=None):
    """
    Generate MCQ questions for teaching_content items in reading overview
    Adds a 'qna' array to the data section
    """
    print("\n" + "=" * 80)
    print("GENERATING MCQ QUESTIONS FOR READING OVERVIEW")
    print("=" * 80 + "\n")
    
    # Get the data section with teaching_content
    sections = reading_overview_data.get("sections", {})
    data_section = sections.get("data", {})
    teaching_content = data_section.get("teaching_content", [])
    
    if not teaching_content:
        print("  ⚠ No teaching_content items found, skipping...\n")
        return reading_overview_data
    
    qna_list = []
    
    for idx, item_data in enumerate(teaching_content, 1):
        if not isinstance(item_data, dict) or "topic" not in item_data or "content" not in item_data:
            continue
        
        topic_text = item_data.get("topic", "")
        content_text = item_data.get("content", "")
        title = item_data.get("title", f"Item {idx}")
        
        if not topic_text or not content_text or str(content_text).startswith("Error:"):
            print(f"  [{idx}/{len(teaching_content)}] ⚠ Skipping '{title}' (invalid data)")
            continue
        
        print(f"  [{idx}/{len(teaching_content)}] Generating MCQ for '{title}'...")
        
        # Create prompt for generating MCQ
        mcq_prompt = f"""Based on the following topic information, generate ONE multiple-choice question (MCQ) for new employee onboarding.

TOPIC: {title}

INFORMATION ABOUT THIS TOPIC:
{content_text[:2000]}

CRITICAL REQUIREMENTS:
- Generate EXACTLY ONE multiple-choice question (MCQ format)
- The question must have exactly 4 options (A, B, C, D)
- Only ONE option should be correct
- The question should test understanding of the key concepts from the topic
- Focus on important, practical knowledge that helps new employees understand the project overview
- Provide a clear explanation (3-5 sentences) that helps users learn
- Format the response as:
  ### Question 1 (MCQ - Medium)
  [Your question text here]
  A. [Option A]
  B. [Option B]
  C. [Option C]
  D. [Option D]
  **Answer:** [Correct letter] - [Detailed explanation]

Generate the MCQ question now."""

        schema_name = f"{REPO_OWNER}_{REPO_NAME}".replace("-", "_")
        try:
            response = chatbot.chat(mcq_prompt, schema_name=schema_name)
            answer = response.get('answer', '') if isinstance(response, dict) else getattr(response, 'answer', str(response))
            
            if answer:
                mcq = parse_single_mcq_from_response(answer)
                if mcq:
                    # Use title as subsection if available
                    if title:
                        mcq['subsection'] = title
                    qna_list.append(mcq)
                    print(f"    ✓ Generated MCQ successfully")
                else:
                    print(f"    ✗ Failed to parse MCQ from response")
            else:
                print(f"    ✗ Empty response from chatbot")
                
        except Exception as e:
            print(f"    ✗ Error: {e}")
            continue
    
    # Add qna list to data section
    if qna_list:
        if "data" not in sections:
            sections["data"] = {}
        sections["data"]["qna"] = qna_list
        reading_overview_data["sections"] = sections
        print(f"\n✓ Added {len(qna_list)} MCQ questions to reading overview\n")
    else:
        print(f"\n⚠ No MCQ questions generated\n")
    
    print(f"✓ Total MCQ questions generated: {len(qna_list)}")
    print("=" * 80 + "\n")
    
    return reading_overview_data


def generate_reading_overview( gmail_db_path=None, provider='openai', model=None):
    """Generate complete reading overview data with a single function call"""

    print("Starting Reading Overview Data Generation...\n")

    # Initialize chatbot
    print("Loading chatbot...")
    chatbot = RAGChatbot(
        vector_db_path=VECTOR_DB_PATH,
        gmail_db_path=gmail_db_path,
        provider=provider,
        model=model,
        verbose=False,
        disable_conversation_storage=True  # Skip conversation storage for generators
    )

    # Define all questions
    questions = [
        ("Welcome: What Does This Application Do?",
         "As a new team member, start here: What is this application? What problem does it solve for users, "
         "and why was it built? Help me understand the business domain, target users, and the core value proposition "
         "based on what's implemented in the codebase. **Focus on concepts, not code snippets.**"),

        ("What Can Users Do? Main Features & Capabilities",
         "Walk me through all the features users can access in this application. For each feature, explain "
         "what it does, why it matters, and point me to the code that implements it so I know where to look when working on enhancements. "
         "**Describe functionality conceptually and provide file/module references rather than code examples.**"),

        ("How Do Users Interact? UI/UX Overview",
         "Analyze the UI components, screen files, routes, and navigation code to describe: What screens or views exist? "
         "What buttons, forms, or interactive elements are present? How do users navigate between different parts of the application? "
         "**Infer the user journey from component names, route definitions, and UI code structure - no code snippets needed, just describe what you observe.**"),

        ("Who Can Access What? Authentication & Authorization",
         "Explain how authentication works in this app. Are there different user roles (admin, regular user, etc.)? "
         "What permissions does each role have? Walk me through the login flow and any security measures implemented. "
         "**Conceptual explanation only - mention relevant modules but don't include code.**"),

        ("Day-to-Day User Journeys: Core Workflows",
         "What are the most common things users do in this application? Walk me through 2-3 typical user journeys "
         "step-by-step, showing how the features connect and referencing the code modules involved in each workflow. "
         "**Explain workflows conceptually with module references, no code snippets.**"),

        ("How Is Data Handled? Storage & Management",
         "Help me understand the data layer: What data models exist? How is data stored and retrieved? "
         "Are there any caching, synchronization, or backup mechanisms? Point me to the relevant database schemas or data classes. "
         "**Provide architecture explanation and file references; include schema definitions if helpful but avoid application code.**"),

        ("How Is the Code Organized? Architecture & Patterns",
         "Give me the architectural overview: What design patterns are used (MVC, microservices, layered, etc.)? "
         "How are the major components organized? How do frontend and backend communicate? This will help me understand where to add new code. "
         "**High-level architecture explanation only - no code examples needed.**"),

        ("System Flow Diagram: How Everything Connects",
         "Provide a visual system flow diagram (mermaid or similar) showing the complete request/response cycle. "
         "Include all major components (UI, API, database, external services) and how data flows through the system from user action to response. "
         "**Diagram required - no code snippets.**"),

        ("What Works Well? Strengths & Best Practices",
         "Analyze the codebase structure, patterns, and implementation quality to identify: What architectural decisions are sound? "
         "What coding patterns are consistently used? Which modules demonstrate good separation of concerns, error handling, or testability? "
         "**Infer best practices from code organization, naming conventions, and design patterns you observe - point to example files/modules but don't paste code.**"),

        ("What Needs Attention? Known Issues & Roadmap",
         "What should I be aware of? Are there known bugs, technical debt, or incomplete features? "
         "Check for TODO/FIXME comments, open issues, or planned improvements so I understand areas that might need refactoring. "
         "**Summarize issues conceptually - no code needed.**"),

        ("Who Uses This & Why? Use Cases & Scenarios",
         "Based on the features, data models, and workflows implemented in the codebase, infer: Who would use this application? "
         "What problems are they solving? Derive 3-4 realistic use cases by analyzing what actions users can perform, "
         "what data they manage, and what outcomes the application enables. "
         "**Infer user personas and scenarios from the implemented functionality - narrative explanation only, no code examples.**"),

        ("What Are We Built With? Complete Tech Stack",
         "List the complete technology stack: frontend frameworks, backend technologies, databases, third-party libraries, "
         "build tools, and deployment platforms. Explain why each technology was chosen and what role it plays. "
         "**Technology overview only - configuration examples acceptable if needed, but no application code.**"),

        ("Languages in Use: Breakdown & Purpose",
         "What programming languages are used in this project and where? Provide a breakdown (e.g., Java 70%, JavaScript 20%, SQL 10%) "
         "and explain what each language is used for so I know what skills I'll be working with most. "
         "**Statistical breakdown and explanation - no code snippets.**"),

        ("Frontend & Backend Frameworks: Configuration & Usage",
         "Detail the frameworks: What frontend framework handles the UI? What backend framework processes requests? "
         "How are they configured? Where are the configuration files? This helps me understand the development workflow. "
         "**Explain framework usage and reference config files; brief config snippets acceptable if needed.**"),

        ("Database Deep Dive: Schema & Relationships",
         "Explain the database setup: What type of database is used? Show me the schema, main tables, and their relationships. "
         "How are migrations managed? Point me to sample queries or ORM models so I understand the data structure. "
         "**Schema definitions and relationship diagrams are helpful; include SQL/ORM schema but avoid application code.**"),

        ("Where Does Everything Go? Project Structure",
         "Give me a directory-by-directory breakdown of the project structure. Where should I put new controllers, models, tests, or utilities? "
         "Understanding the organization conventions will help me contribute code that fits the existing structure. "
         "**Directory tree and explanations only - no code examples.**"),

        ("How Big Is This Project? Codebase Metrics",
         "Provide statistics: How many files and lines of code? How many modules or services? What's the test coverage? "
         "These metrics help me gauge the project scope and complexity. "
         "**Numbers and metrics only - no code needed.**"),

        ("How Do We Test? Testing Strategy & Coverage",
         "Explain the testing approach: What testing frameworks are used? Where are the test files? What types of tests exist "
         "(unit, integration, e2e)? What's currently covered and what areas need more tests? How do I run the test suite? "
         "**Testing strategy explanation; brief test command examples acceptable but avoid detailed test code.**"),

        ("External Connections: APIs & Third-Party Integrations",
         "Does this app connect to external services or APIs? List all integrations (payment gateways, email services, cloud storage, etc.), "
         "explain their purposes, and show me where API keys are configured and how authentication with external services works. "
         "**Conceptual overview with configuration references; API endpoint lists acceptable, but no implementation code.**"),
    ]

    # Collect responses
    reading_overview_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": getattr(chatbot, "repo_info", {}).get('name', 'unknown'),
            "provider": provider,
            "model": getattr(chatbot, "model", None)
        },
        "sections": {
            "data": {
                "teaching_content": []
            }
        }
    }

    total = len(questions)
    print(f"Asking {total} questions...\n")

    for idx, (key, question) in enumerate(questions, 1):
        print(f"[{idx}/{total}] {key}...")

        schema_name = f"{REPO_OWNER}_{REPO_NAME}".replace("-", "_")

        try:
            response = chatbot.chat(question, schema_name=schema_name)
            # The exact response shape may differ by your chatbot implementation;
            # adapt the keys ('answer', 'context_quality') if needed.
            answer = response.get('answer') if isinstance(response, dict) else getattr(response, 'answer', str(response))
            quality = response.get('context_quality', 1.0) if isinstance(response, dict) else getattr(response, 'context_quality', 1.0)
            reading_overview_data["sections"]["data"]["teaching_content"].append({
                "title": key,
                "topic": question,
                "content": answer,
                "quality": quality
            })
        except Exception as e:
            print(f"Error: {e}")
            reading_overview_data["sections"]["data"]["teaching_content"].append({
                "title": key,
                "topic": question,
                "content": f"Error: {str(e)}",
                "quality": 0.0
            })

    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_project_overview.json"
    
    try:
        s3_manager.upload_json(reading_overview_data, s3_key)
        print(f"\n✓ Uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"\n❌ Failed to upload to S3: {e}")
        raise

    successful_count = len([d for d in reading_overview_data['sections']['data']['teaching_content'] if not str(d.get('content')).startswith('Error:')])
    print(f"Answered {successful_count}/{total} questions successfully")

    # Generate MCQ questions for data items
    print("\n" + "=" * 80)
    print("Starting MCQ QNA Generation...")
    print("=" * 80)
    reading_overview_data = generate_data_qna(reading_overview_data, chatbot, gmail_db_path, provider, model)
    
    # Upload updated version with QNA to S3
    try:
        s3_manager.upload_json(reading_overview_data, s3_key)
        print(f"✓ Updated file with QNA uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"❌ Failed to upload updated file: {e}")
        raise

    return s3_key


def add_qna_to_existing_reading_overview(
    json_file_path: str = None,
    gmail_db_path: str = None,
    provider: str = 'openai',
    model: str = None
) -> Path:
    """
    Add MCQ QNA questions to an existing reading overview JSON file
    
    Args:
        json_file_path: Path to existing reading overview JSON file (if None, uses default path)
        gmail_db_path: Optional path to Gmail database
        provider: LLM provider (openai/anthropic/ollama)
        model: Model name (optional, uses default for provider)
    
    Returns:
        Path to updated JSON file
    """
    print("╔" + "═" * 78 + "╗")
    print("║" + " ADD QNA TO EXISTING READING OVERVIEW ".center(78) + "║")
    print("╚" + "═" * 78 + "╝\n")
    
    # Determine file path
    if json_file_path is None:
        json_file_path = str(ONBOARDING_ROOT / "reading" / "onboarding_project_overview.json")
    
    json_file = Path(json_file_path)
    
    if not json_file.exists():
        print(f"✗  File not found: {json_file}")
        return None
    
    print(f"📄 Loading existing reading overview: {json_file.name}")
    
    # Load existing data
    with open(json_file, 'r', encoding='utf-8') as f:
        reading_overview_data = json.load(f)
    
    # Initialize chatbot
    print("⚙  Initializing chatbot...")
    try:
        chatbot = RAGChatbot(
            vector_db_path=VECTOR_DB_PATH,
            gmail_db_path=gmail_db_path,
            provider=provider,
            model=model,
            verbose=False,
            disable_conversation_storage=True  # Skip conversation storage for generators
        )
        print("✓  Chatbot initialized successfully\n")
    except Exception as e:
        print(f"✗  Failed to initialize chatbot: {e}")
        return None
    
    # Generate QNA
    reading_overview_data = generate_data_qna(reading_overview_data, chatbot, gmail_db_path, provider, model)
    
    # Save updated file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(reading_overview_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓  Updated file saved: {json_file}\n")
    
    return json_file


if __name__ == "__main__":
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = None

    # Uncomment to just add QNA to existing file:
    # add_qna_to_existing_reading_overview(gmail_db_path=GMAIL_DB_PATH, provider=PROVIDER, model=MODEL)
    
    # Generate complete reading overview with QNA:
    generate_reading_overview(GMAIL_DB_PATH, PROVIDER, MODEL)