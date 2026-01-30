"""
Code Conventions Data Generator
Extracts comprehensive code styling, naming, PR, issues, testing, and referencing guidelines
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
            
            option_match = re.match(r'^([A-D])\.\s+(.+)$', line)
            if option_match:
                option_letter = option_match.group(1)
                option_text = option_match.group(2).strip()
                options[option_letter] = option_text
            else:
                question_text.append(line)
        
        if len(options) == 4 and correct_answer and correct_answer in options:
            return {
                'question': ' '.join(question_text),
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation.strip()
            }
        return None
    
    start_idx = match.end()
    content = response_text[start_idx:].strip()
    answer_split = re.split(r'\*\*Answer:\*\*', content, maxsplit=1)
    
    if len(answer_split) < 2:
        return None
    
    question_part = answer_split[0].strip()
    answer_part = answer_split[1].strip()
    
    lines = question_part.split('\n')
    question_text = []
    options = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        option_match = re.match(r'^([A-D])\.\s+(.+)$', line)
        if option_match:
            option_letter = option_match.group(1)
            option_text = option_match.group(2).strip()
            options[option_letter] = option_text
        else:
            question_text.append(line)
    
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
    
    if len(options) == 4 and correct_answer and correct_answer in options:
        return {
            'question': ' '.join(question_text),
            'options': options,
            'correct_answer': correct_answer,
            'explanation': explanation
        }
    
    return None


def generate_section_qna(code_conventions_data, chatbot, gmail_db_path=None, provider='openai', model=None):
    """
    Generate MCQ questions for each section based on teaching_content
    Adds a 'qna' array to each section
    """
    print("\n" + "=" * 80)
    print("GENERATING MCQ QUESTIONS FOR EACH SECTION")
    print("=" * 80 + "\n")
    
    sections = code_conventions_data.get("sections", {})
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
- Focus on important, practical knowledge that helps new employees understand code conventions
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
    
    return code_conventions_data


def generate_code_conventions_data( gmail_db_path=None, provider='openai', model=None):
    """Generate comprehensive code conventions analysis data"""

    print("Starting Code Conventions Data Generation...\n")

    # Initialize chatbot
    print("Loading chatbot...")
    RAGChatbotClass = get_rag_chatbot_class()
    chatbot = RAGChatbotClass(
        vector_db_path=VECTOR_DB_PATH,
        gmail_db_path=gmail_db_path,
        provider=provider,
        model=model,
        verbose=False,
        disable_conversation_storage=True  # Skip conversation storage for generators
    )

    # Define code conventions specific questions
    questions = [
        # 1. Styling Rules
        ("Code Formatting Standards",
         "What are the code styling and formatting rules for this project? Include: indentation (spaces vs tabs, "
         "how many spaces), spacing rules (around operators, brackets, commas), line length limits, and code "
         "organization standards. Are there automated formatters configured? **Comprehensive styling rules with examples.**"),

        ("Indentation and Spacing",
         "What are the indentation and spacing conventions? Specify: tab size, indentation style (tabs or spaces), "
         "spacing around operators, spacing in function calls, spacing in control structures, and blank line usage. "
         "**Detailed indentation and spacing rules.**"),

        ("Line Length and Wrapping",
         "What are the line length rules? Include: maximum line length, line wrapping rules, how to break long lines, "
         "and formatting for multi-line statements. **Line length and wrapping conventions.**"),

        ("Code Organization Standards",
         "How should code be organized? Include: file structure, import organization, class organization, function "
         "ordering, and module organization. What patterns are used for organizing code within files? "
         "**Code organization standards and patterns.**"),

        ("Linting and Formatting Tools",
         "What linting and formatting tools are used? Include: linter configuration, formatter configuration, "
         "pre-commit hooks, and how to run linting/formatting. What rules are enforced? "
         "**Linting and formatting tool configuration and usage.**"),

        # 2. Naming Guidelines
        ("Folder and Directory Naming",
         "What are the naming conventions for folders and directories? Include: casing (lowercase, snake_case, "
         "camelCase, PascalCase), plural vs singular, abbreviations, and special directories. Provide examples. "
         "**Folder naming conventions with examples.**"),

        ("File Naming Conventions",
         "What are the naming conventions for files? Include: file extensions, naming patterns (prefixes, suffixes), "
         "casing conventions, test file naming, and configuration file naming. Provide examples for each file type. "
         "**File naming conventions with examples.**"),

        ("Variable Naming Conventions",
         "What are the naming conventions for variables? Include: casing (camelCase, snake_case, etc.), naming "
         "patterns, prefixes/suffixes (private variables, constants), and naming for different variable types "
         "(local, instance, class, global). Provide examples. **Variable naming conventions with examples.**"),

        ("Function and Method Naming",
         "What are the naming conventions for functions and methods? Include: casing conventions, verb prefixes "
         "(get, set, is, has, etc.), naming patterns, and conventions for different function types (public, private, "
         "static, async). Provide examples. **Function naming conventions with examples.**"),

        ("Class and Type Naming",
         "What are the naming conventions for classes, interfaces, types, and enums? Include: casing conventions "
         "(PascalCase, etc.), naming patterns, suffixes (Controller, Service, Manager, etc.), and conventions for "
         "different types. Provide examples. **Class and type naming conventions with examples.**"),

        ("Constant Naming Conventions",
         "What are the naming conventions for constants? Include: casing (UPPER_CASE, etc.), naming patterns, "
         "and conventions for different constant types (module-level, class-level, enum values). Provide examples. "
         "**Constant naming conventions with examples.**"),

        # 3. PR Rules
        ("Pull Request Title Format",
         "What are the pull request guidelines and review process? Include: PR title format, description requirements, "
         "and approval workflow. What format should PR titles follow? **PR title format and requirements.**"),

        ("Pull Request Description Requirements",
         "What should be included in a pull request description? Include: required sections, template format, "
         "what information to provide, and how to structure the description. **PR description requirements and template.**"),

        ("Pull Request Review Process",
         "What is the pull request review process? Include: who reviews PRs, review requirements, approval criteria, "
         "how to request reviews, and merge procedures. **PR review and approval workflow.**"),

        ("Pull Request Best Practices",
         "What are the best practices for creating pull requests? Include: branch naming, commit message guidelines, "
         "PR size recommendations, testing requirements, and documentation requirements. **PR best practices and guidelines.**"),

        # 4. Issues Rules
        ("Issue Creation Guidelines",
         "What are the guidelines for creating and managing issues? Include: issue templates, when to create issues, "
         "what information to include, and how to structure issue descriptions. **Issue creation guidelines and templates.**"),

        ("Issue Labeling Conventions",
         "What are the issue labeling conventions? Include: label categories (bug, feature, enhancement, etc.), "
         "priority levels, status labels, and how to apply labels. **Issue labeling system and conventions.**"),

        ("Issue Priority Levels",
         "What are the issue priority levels and how are they determined? Include: priority definitions, when to use "
         "each priority, and how priority affects issue handling. **Issue priority system and guidelines.**"),

        ("Issue Management Workflow",
         "What is the issue management workflow? Include: issue lifecycle, status transitions, assignment process, "
         "and how issues are tracked and closed. **Issue management workflow and processes.**"),

        # 5. Testing Guidelines
        ("Testing Requirements and Standards",
         "What are the testing requirements and conventions? Include: unit test standards, integration test standards, "
         "E2E test standards, test coverage requirements, and testing best practices. **Comprehensive testing guidelines.**"),

        ("Unit Testing Conventions",
         "What are the unit testing conventions? Include: test file organization, test naming conventions, test "
         "structure, mocking patterns, and assertion styles. Provide examples. **Unit testing conventions with examples.**"),

        ("Integration Testing Standards",
         "What are the integration testing standards? Include: what to test, how to structure integration tests, "
         "test data management, and integration test patterns. **Integration testing standards and patterns.**"),

        ("E2E Testing Guidelines",
         "What are the E2E testing guidelines? Include: E2E test scope, test structure, test data setup, and E2E "
         "testing best practices. **E2E testing guidelines and best practices.**"),

        ("Test Coverage Requirements",
         "What are the test coverage requirements? Include: minimum coverage thresholds, coverage reporting, and how "
         "coverage is measured and enforced. **Test coverage requirements and reporting.**"),

        ("Running Tests",
         "How are tests run? Include: test commands, test environments, CI/CD test execution, and debugging tests. "
         "**Test execution instructions and commands.**"),

        # 6. Referencing
        ("Documentation Standards",
         "What are the documentation and code reference standards? Include: code documentation style (comments, "
         "docstrings), API documentation format, and inline documentation conventions. **Documentation standards and formats.**"),

        ("External Resource Documentation",
         "How should external resources be documented? Include: how to document API usage, third-party library "
         "references, external service integrations, and dependency documentation. **External resource documentation guidelines.**"),

        ("Code Commenting Conventions",
         "What are the code commenting conventions? Include: when to comment, comment style, documentation comments, "
         "TODO/FIXME conventions, and comment formatting. **Code commenting standards and conventions.**"),

        ("API Documentation Standards",
         "What are the API documentation standards? Include: how to document API endpoints, request/response formats, "
         "error handling documentation, and API versioning documentation. **API documentation standards and formats.**"),

        ("Dependency Documentation",
         "How should dependencies be documented? Include: dependency version documentation, dependency purpose "
         "documentation, and how to document why specific dependencies are used. **Dependency documentation guidelines.**"),
    ]

    # Collect responses
    code_conventions_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": getattr(chatbot, "repo_info", {}).get('name', 'unknown'),
            "provider": provider,
            "model": getattr(chatbot, "model", None)
        },
        "sections": {
            "styling_rules": {
                "teaching_content": []
            },
            "naming_guidelines": {
                "teaching_content": []
            },
            "pr_rules": {
                "teaching_content": []
            },
            "issues_rules": {
                "teaching_content": []
            },
            "testing_guidelines": {
                "teaching_content": []
            },
            "referencing": {
                "teaching_content": []
            }
        }
    }

    # Map questions to sections
    section_mapping = {
        0: "styling_rules",
        1: "styling_rules",
        2: "styling_rules",
        3: "styling_rules",
        4: "styling_rules",
        5: "naming_guidelines",
        6: "naming_guidelines",
        7: "naming_guidelines",
        8: "naming_guidelines",
        9: "naming_guidelines",
        10: "naming_guidelines",
        11: "pr_rules",
        12: "pr_rules",
        13: "pr_rules",
        14: "pr_rules",
        15: "issues_rules",
        16: "issues_rules",
        17: "issues_rules",
        18: "issues_rules",
        19: "testing_guidelines",
        20: "testing_guidelines",
        21: "testing_guidelines",
        22: "testing_guidelines",
        23: "testing_guidelines",
        24: "testing_guidelines",
        25: "referencing",
        26: "referencing",
        27: "referencing",
        28: "referencing",
        29: "referencing",
    }

    total = len(questions)
    print(f"Asking {total} code conventions questions...\n")

    for idx, (key, question) in enumerate(questions, 1):
        print(f"[{idx}/{total}] {key}...")

        schema_name = f"{REPO_OWNER}_{REPO_NAME}".replace("-", "_")
        try:
            response = chatbot.chat(question, schema_name=schema_name)
            answer = response.get('answer') if isinstance(response, dict) else getattr(response, 'answer',
                                                                                       str(response))
            quality = response.get('context_quality', 1.0) if isinstance(response, dict) else getattr(response,
                                                                                                      'context_quality',
                                                                                                      1.0)

            section = section_mapping.get(idx - 1, "referencing")
            code_conventions_data["sections"][section]["teaching_content"].append({
                "title": key,
                "topic": question,
                "content": answer,
                "quality": quality
            })
        except Exception as e:
            print(f"Error: {e}")
            section = section_mapping.get(idx - 1, "referencing")
            code_conventions_data["sections"][section]["teaching_content"].append({
                "title": key,
                "topic": question,
                "content": f"Error: {str(e)}",
                "quality": 0.0
            })

    # Save to file
    # Upload to S3
    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_code_conventions.json"

    try:
        s3_manager.upload_json(code_conventions_data, s3_key)
        print(f"\n✓ Uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"\n❌ Failed to upload to S3: {e}")
        raise


    # Calculate success stats
    total_answers = sum(len(section.get("teaching_content", [])) for section in code_conventions_data["sections"].values())
    successful_answers = sum(
        1 for section in code_conventions_data["sections"].values()
        for item in section.get("teaching_content", [])
        if not str(item.get('content', '')).startswith('Error:')
    )

    print(f"📊 Answered {successful_answers}/{total_answers} questions successfully")
    print(f"\nData organized into {len(code_conventions_data['sections'])} sections:")
    for section_name, section_data in code_conventions_data["sections"].items():
        teaching_count = len(section_data.get("teaching_content", []))
        print(f"   - {section_name}: {teaching_count} teaching content items")

    # Generate MCQ questions for each section
    print("\n" + "=" * 80)
    print("Starting MCQ QNA Generation...")
    print("=" * 80)
    code_conventions_data = generate_section_qna(code_conventions_data, chatbot, gmail_db_path, provider, model)
    
    # Save updated file with QNA
    # Upload updated version with QNA to S3
    try:
        s3_manager.upload_json(code_conventions_data, s3_key)
        print(f"✓ Updated file with QNA uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"❌ Failed to upload updated file: {e}")
        raise

    return s3_key


def add_qna_to_existing_code_conventions(
    json_file_path: str = None,
    gmail_db_path: str = None,
    provider: str = 'openai',
    model: str = None
) -> str:
    """
    Add MCQ QNA questions to an existing code conventions JSON file
    
    Args:
        json_file_path: Path to existing code conventions JSON file (if None, uses default path)
        gmail_db_path: Optional path to Gmail database
        provider: LLM provider (openai/anthropic/ollama)
        model: Model name (optional, uses default for provider)
    
    Returns:
        Path to updated JSON file
    """
    print("╔" + "═" * 78 + "╗")
    print("║" + " ADD QNA TO EXISTING CODE CONVENTIONS ".center(78) + "║")
    print("╚" + "═" * 78 + "╝\n")
    
    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_code_conventions.json"

    print(f"📄 Loading existing code conventions from S3...")

    try:
        code_conventions_data = s3_manager.download_json(s3_key)
        print(f"✓  Loaded from: s3://{s3_manager.bucket}/{s3_key}\n")
    except Exception as e:
        print(f"✗  File not found in S3: {e}")
        return None

    
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
    
    code_conventions_data = generate_section_qna(code_conventions_data, chatbot, gmail_db_path, provider, model)
    
    try:
        s3_manager.upload_json(code_conventions_data, s3_key)
        print(f"✓  Updated file uploaded to S3: s3://{s3_manager.bucket}/{s3_key}\n")
    except Exception as e:
        print(f"✗  Failed to upload to S3: {e}")
        return None

    return s3_key



if __name__ == "__main__":
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = None

    # Uncomment to just add QNA to existing file:
    # add_qna_to_existing_code_conventions(gmail_db_path=GMAIL_DB_PATH, provider=PROVIDER, model=MODEL)
    
    # Generate complete code conventions with QNA:
    generate_code_conventions_data(GMAIL_DB_PATH, PROVIDER, MODEL)

