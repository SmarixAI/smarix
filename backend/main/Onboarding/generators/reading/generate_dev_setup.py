"""
Dev Setup Data Generator
Extracts comprehensive development setup, installation, and configuration information
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
            pass

    # Fallback: search the repo for a file named chatbot.py and load it dynamically
    for path in BACKEND_ROOT.rglob("chatbot.py"):
        try:
            spec = importlib.util.spec_from_file_location("rag_chatbot_dynamic", str(path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "RAGChatbot"):
                return getattr(mod, "RAGChatbot")
        except Exception:
            pass

    raise ImportError(
        "Could not import RAGChatbot. Tried import paths: "
        + ", ".join(candidates)
        + ". Also searched repository for chatbot.py. "
        "Make sure project is on PYTHONPATH and package markers (__init__.py) exist where needed."
    )


def get_rag_chatbot_class():
    """Get RAGChatbot class, loading it if not already loaded."""
    global RAGChatbot
    if RAGChatbot is None:
        RAGChatbot = _load_rag_chatbot_class()
    return RAGChatbot

# Initialize as None, will be loaded on first use
RAGChatbot = None


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


def generate_section_qna(dev_setup_data, chatbot, gmail_db_path=None, provider='openai', model=None):
    """
    Generate MCQ questions for each section based on teaching_content
    Adds a 'qna' array to each section
    """
    print("\n" + "=" * 80)
    print("GENERATING MCQ QUESTIONS FOR EACH SECTION")
    print("=" * 80 + "\n")
    
    sections = dev_setup_data.get("sections", {})
    total_qnas = 0
    
    for section_name, section_content in sections.items():
        if not isinstance(section_content, dict):
            continue
            
        print(f"Processing section: {section_name}")
        
        # Get teaching_content array from section
        teaching_content = section_content.get("teaching_content", [])
        
        if not teaching_content:
            print(f"  ⚠ No teaching_content found, skipping...\n")
            continue
        
        qna_list = []
        
        for idx, item_data in enumerate(teaching_content, 1):
            if not isinstance(item_data, dict):
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
- Focus on important, practical knowledge that helps new employees understand the development setup
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

            try:
                response = chatbot.chat(mcq_prompt)
                answer = response.get('answer', '') if isinstance(response, dict) else getattr(response, 'answer', str(response))
                
                if answer:
                    mcq = parse_single_mcq_from_response(answer)
                    if mcq:
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
        
        # Add qna list to section
        if qna_list:
            sections[section_name]["qna"] = qna_list
            total_qnas += len(qna_list)
            print(f"  ✓ Added {len(qna_list)} MCQ questions to section '{section_name}'\n")
        else:
            print(f"  ⚠ No MCQ questions generated for section '{section_name}'\n")
    
    print(f"✓ Total MCQ questions generated: {total_qnas}")
    print("=" * 80 + "\n")
    
    return dev_setup_data


def generate_dev_setup_data(gmail_db_path=None, provider='openai', model=None):
    """Generate comprehensive development setup analysis data"""

    print("Starting Dev Setup Data Generation...\n")

    # Initialize chatbot
    print("Loading chatbot...")
    RAGChatbotClass = get_rag_chatbot_class()
    chatbot = RAGChatbotClass(
        vector_db_path=VECTOR_DB_PATH,
        gmail_db_path=gmail_db_path,
        provider=provider,
        model=model,
        verbose=False
    )

    # Define dev setup specific questions
    questions = [
        # 1. Pre-requisites
        ("Required Software and Tools",
         "What are all the prerequisites needed before setting up this project? List required software, tools, versions, "
         "and system requirements. Include: programming languages and their versions, frameworks, build tools, "
         "package managers, databases, development tools (IDEs, editors), and any other dependencies. "
         "**Comprehensive list of prerequisites with version requirements.**"),

        ("System Requirements",
         "What are the system requirements for development? Include: operating system versions (Windows, macOS, Linux), "
         "minimum RAM, disk space, processor requirements, and any platform-specific requirements. "
         "**List system requirements for each supported platform.**"),

        ("Development Environment Prerequisites",
         "What development environment setup is required? Include: IDE or editor recommendations, required extensions "
         "or plugins, development server requirements, and any environment-specific configurations. "
         "**List development environment prerequisites.**"),

        ("External Service Prerequisites",
         "What external services or accounts are needed? Include: cloud services, API keys, database instances, "
         "authentication providers, and any third-party services that must be configured before development. "
         "**List external service prerequisites and setup requirements.**"),

        # 2. Installation Steps
        ("Repository Cloning and Initial Setup",
         "Provide step-by-step installation instructions from cloning the repository to running the application locally. "
         "Start with: how to clone the repository, which branch to use, and initial repository setup steps. "
         "**Step-by-step cloning and initial setup instructions.**"),

        ("Dependency Installation",
         "How are dependencies installed? Provide detailed steps for: installing package dependencies, setting up "
         "virtual environments (if applicable), installing global tools, and configuring package managers. "
         "Include all commands needed. **Step-by-step dependency installation instructions with commands.**"),

        ("Configuration Setup",
         "What configuration is needed? Describe: environment variable setup, configuration file creation, "
         "API key configuration, database connection setup, and any other configuration steps. Include where to find "
         "example configuration files. **Step-by-step configuration instructions.**"),

        ("Database Setup and Migration",
         "How is the database set up? Provide steps for: database installation, schema creation, running migrations, "
         "seeding initial data, and database connection configuration. **Step-by-step database setup instructions.**"),

        ("Build and Compilation",
         "How is the application built? Provide steps for: compiling the code, building assets, running build scripts, "
         "and preparing the application for execution. Include build commands and expected outputs. "
         "**Step-by-step build instructions with commands.**"),

        ("Running the Application",
         "How do you run the application locally? Provide steps for: starting development servers, running the "
         "application, accessing the application, and verifying it's working correctly. Include all necessary commands. "
         "**Step-by-step instructions for running the application.**"),

        # 3. FAQs
        ("Common Setup Issues and Solutions",
         "What are common setup issues developers face and their solutions? List troubleshooting steps for typical errors. "
         "Include: dependency installation errors, configuration issues, database connection problems, build failures, "
         "and runtime errors. For each issue, provide: symptoms, common causes, and step-by-step solutions. "
         "**Comprehensive troubleshooting guide with solutions.**"),

        ("Platform-Specific Issues",
         "What platform-specific issues might developers encounter? List issues specific to: Windows, macOS, and Linux. "
         "Include: path issues, permission problems, platform-specific dependency issues, and their solutions. "
         "**Platform-specific troubleshooting guide.**"),

        ("Environment-Specific Problems",
         "What environment-specific problems occur? Include: virtual environment issues, Docker problems, "
         "containerization issues, and cloud development environment problems. Provide solutions for each. "
         "**Environment-specific troubleshooting guide.**"),

        ("Version Compatibility Issues",
         "What version compatibility issues might arise? Include: dependency version conflicts, framework version "
         "mismatches, and tool version incompatibilities. How are these resolved? **Version compatibility troubleshooting.**"),

        # 4. Hello World Setup
        ("Minimal Setup Verification",
         "How do I create a minimal 'Hello World' example to verify the setup works? What's the simplest way to test "
         "the development environment? Provide: a minimal code example, how to run it, and what output to expect. "
         "**Simple Hello World example with verification steps.**"),

        ("Quick Start Guide",
         "What's the quickest way to get started? Provide a minimal setup path that gets a developer running the "
         "application in the shortest time. Include only essential steps, skipping optional configurations. "
         "**Minimal quick start guide.**"),

        ("Setup Verification Checklist",
         "How do I verify that the setup is correct? Provide a checklist of: verification steps, test commands to run, "
         "expected outputs, and how to confirm each component is working. **Setup verification checklist.**"),

        # 5. Git Basics based on env/OS
        ("Git Workflow Overview",
         "What are the Git commands and workflows for this project? Describe: branching strategy, commit conventions, "
         "pull request process, and typical Git workflow. **Git workflow and conventions overview.**"),

        ("Git Setup for Linux",
         "Provide Git setup instructions for Linux. Include: Git installation, configuration, SSH key setup, "
         "repository cloning, and common Git commands. Include Linux-specific considerations. "
         "**Linux-specific Git setup and commands.**"),

        ("Git Setup for macOS",
         "Provide Git setup instructions for macOS. Include: Git installation (via Homebrew or Xcode), configuration, "
         "SSH key setup, repository cloning, and common Git commands. Include macOS-specific considerations. "
         "**macOS-specific Git setup and commands.**"),

        ("Git Setup for Windows",
         "Provide Git setup instructions for Windows. Include: Git installation (Git for Windows), configuration, "
         "SSH key setup (using PuTTY or OpenSSH), repository cloning, and common Git commands. Include Windows-specific "
         "considerations (line endings, path handling). **Windows-specific Git setup and commands.**"),

        ("Git Branching Strategy",
         "What branching strategy does this project use? Describe: main/master branch, feature branches, release branches, "
         "hotfix branches, and how to create and manage branches. Include branch naming conventions. "
         "**Branching strategy and conventions.**"),

        ("Git Commit and PR Guidelines",
         "What are the commit message conventions and pull request guidelines? Include: commit message format, "
         "PR description requirements, code review process, and merge procedures. **Git commit and PR guidelines.**"),
    ]

    # Collect responses
    dev_setup_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": getattr(chatbot, "repo_info", {}).get('name', 'unknown'),
            "provider": provider,
            "model": getattr(chatbot, "model", None)
        },
        "sections": {
            "prerequisites": {
                "teaching_content": []
            },
            "installation_steps": {
                "teaching_content": []
            },
            "faqs": {
                "teaching_content": []
            },
            "hello_world_setup": {
                "teaching_content": []
            },
            "git_basics": {
                "teaching_content": []
            }
        }
    }

    # Map questions to sections
    section_mapping = {
        0: "prerequisites",
        1: "prerequisites",
        2: "prerequisites",
        3: "prerequisites",
        4: "installation_steps",
        5: "installation_steps",
        6: "installation_steps",
        7: "installation_steps",
        8: "installation_steps",
        9: "installation_steps",
        10: "faqs",
        11: "faqs",
        12: "faqs",
        13: "faqs",
        14: "hello_world_setup",
        15: "hello_world_setup",
        16: "hello_world_setup",
        17: "git_basics",
        18: "git_basics",
        19: "git_basics",
        20: "git_basics",
        21: "git_basics",
        22: "git_basics",
    }

    total = len(questions)
    print(f"Asking {total} dev setup questions...\n")

    for idx, (key, question) in enumerate(questions, 1):
        print(f"[{idx}/{total}] {key}...")

        try:
            response = chatbot.chat(question)
            answer = response.get('answer') if isinstance(response, dict) else getattr(response, 'answer',
                                                                                       str(response))
            quality = response.get('context_quality', 1.0) if isinstance(response, dict) else getattr(response,
                                                                                                      'context_quality',
                                                                                                      1.0)

            section = section_mapping.get(idx - 1, "git_basics")
            dev_setup_data["sections"][section]["teaching_content"].append({
                "title": key,
                "topic": question,
                "content": answer,
                "quality": quality
            })
        except Exception as e:
            print(f"Error: {e}")
            section = section_mapping.get(idx - 1, "git_basics")
            dev_setup_data["sections"][section]["teaching_content"].append({
                "title": key,
                "topic": question,
                "content": f"Error: {str(e)}",
                "quality": 0.0
            })

    # Save to file
    output_dir = ONBOARDING_ROOT / "reading"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / f"onboarding_dev_setup.json"

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(dev_setup_data, f, indent=2, ensure_ascii=False)

    # Calculate success stats
    total_answers = sum(len(section.get("teaching_content", [])) for section in dev_setup_data["sections"].values())
    successful_answers = sum(
        1 for section in dev_setup_data["sections"].values()
        for item in section.get("teaching_content", [])
        if not str(item.get('content', '')).startswith('Error:')
    )

    print(f"\nDone! Saved to: {json_file}")
    print(f"📊 Answered {successful_answers}/{total_answers} questions successfully")
    print(f"\nData organized into {len(dev_setup_data['sections'])} sections:")
    for section_name, section_data in dev_setup_data["sections"].items():
        teaching_count = len(section_data.get("teaching_content", []))
        print(f"   - {section_name}: {teaching_count} teaching content items")

    # Generate MCQ questions for each section
    print("\n" + "=" * 80)
    print("Starting MCQ QNA Generation...")
    print("=" * 80)
    dev_setup_data = generate_section_qna(dev_setup_data, chatbot, gmail_db_path, provider, model)
    
    # Save updated file with QNA
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(dev_setup_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Updated file saved with QNA sections: {json_file}")

    return json_file


def add_qna_to_existing_dev_setup(
    json_file_path: str = None,
    gmail_db_path: str = None,
    provider: str = 'openai',
    model: str = None
) -> Path:
    """
    Add MCQ QNA questions to an existing dev setup JSON file
    
    Args:
        json_file_path: Path to existing dev setup JSON file (if None, uses default path)
        gmail_db_path: Optional path to Gmail database
        provider: LLM provider (openai/anthropic/ollama)
        model: Model name (optional, uses default for provider)
    
    Returns:
        Path to updated JSON file
    """
    print("╔" + "═" * 78 + "╗")
    print("║" + " ADD QNA TO EXISTING DEV SETUP ".center(78) + "║")
    print("╚" + "═" * 78 + "╝\n")
    
    # Determine file path
    if json_file_path is None:
        json_file_path = str(ONBOARDING_ROOT / "reading" / "onboarding_dev_setup.json")
    
    json_file = Path(json_file_path)
    
    if not json_file.exists():
        print(f"✗  File not found: {json_file}")
        return None
    
    print(f"📄 Loading existing dev setup: {json_file.name}")
    
    # Load existing data
    with open(json_file, 'r', encoding='utf-8') as f:
        dev_setup_data = json.load(f)
    
    # Initialize chatbot
    print("⚙  Initializing chatbot...")
    try:
        RAGChatbotClass = get_rag_chatbot_class()
        chatbot = RAGChatbotClass(
            vector_db_path=VECTOR_DB_PATH,
            gmail_db_path=gmail_db_path,
            provider=provider,
            model=model,
            verbose=False
        )
        print("✓  Chatbot initialized successfully\n")
    except Exception as e:
        print(f"✗  Failed to initialize chatbot: {e}")
        return None
    
    # Generate QNA
    dev_setup_data = generate_section_qna(dev_setup_data, chatbot, gmail_db_path, provider, model)
    
    # Save updated file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(dev_setup_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓  Updated file saved: {json_file}\n")
    
    return json_file


if __name__ == "__main__":
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = None

    # Uncomment to just add QNA to existing file:
    # add_qna_to_existing_dev_setup(gmail_db_path=GMAIL_DB_PATH, provider=PROVIDER, model=MODEL)
    
    # Generate complete dev setup with QNA:
    generate_dev_setup_data(GMAIL_DB_PATH, PROVIDER, MODEL)

