"""
Repository Structure Data Generator
Extracts comprehensive repository organization and structure information
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


def generate_section_qna(repo_structure_data, chatbot, gmail_db_path=None, provider='openai', model=None):
    """
    Generate MCQ questions for each section based on teaching_content
    Adds a 'qna' array to each section
    """
    print("\n" + "=" * 80)
    print("GENERATING MCQ QUESTIONS FOR EACH SECTION")
    print("=" * 80 + "\n")
    
    sections = repo_structure_data.get("sections", {})
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
- Focus on important, practical knowledge that helps new employees understand the repository structure
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
    
    return repo_structure_data


def generate_repo_structure_data( gmail_db_path=None, provider='openai', model=None):
    """Generate comprehensive repository structure analysis data"""

    print("Starting Repository Structure Data Generation...\n")

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

    # Define repository structure specific questions
    questions = [
        # 1. Complete Repository Structure
        ("Root Directory Overview",
         "List ALL top-level directories and files in the repository root. For each directory, provide a brief "
         "description of its purpose. Include hidden directories (starting with .) if they're significant "
         "(.github, .vscode, etc.). For important root files (README.md, LICENSE, .gitignore, package.json, "
         "pubspec.yaml, etc.), explain their role. Create a hierarchical tree view showing: root → main directories → "
         "their immediate subdirectories (2-3 levels deep). "
         "**Provide directory tree structure - plain text format, no code.**"),

        ("Complete Directory Hierarchy",
         "Create a comprehensive directory structure map showing the full repository organization. "
         "Focus on the main source code directory (lib, src, app, etc.) and expand it to show all subdirectories "
         "and their nesting levels. Show: which directories contain source files, which contain tests, which are "
         "for configuration, and which are for assets/resources. Use indentation or tree notation to show hierarchy. "
         "Example format: 'lib/ → models/ → task.dart, → views/ → home/ → home_view.dart'. "
         "**Full directory tree - organize by functional areas, no file contents.**"),

        ("Key Configuration Files Location",
         "Identify and list ALL configuration files in the repository with their exact paths. Look for: "
         "build configs (CMakeLists.txt, build.gradle, webpack.config.js), dependency files (pubspec.yaml, package.json, "
         "requirements.txt), environment configs (.env files, config.yaml), CI/CD configs (.github/workflows/, "
         ".gitlab-ci.yml), editor configs (.vscode/, .editorconfig), linter configs (.eslintrc, analysis_options.yaml), "
         "Docker configs (Dockerfile, docker-compose.yml). For each file, state: path, purpose, and what it configures. "
         "**List all config files with paths and purposes.**"),

        ("Asset and Resource Organization",
         "Locate all asset and resource directories. Search for directories named: assets, resources, public, static, "
         "images, fonts, icons, sounds, data, fixtures, locales, i18n, translations, etc. For each found, describe: "
         "what it contains (images, fonts, data files, etc.), file formats present, and how these assets are used in the app. "
         "If no dedicated asset directories exist, state 'No asset directories found'. "
         "**Map asset organization - describe structure, don't list every file.**"),

        # 2. Model/Module-wise Structure
        ("Data Models Organization",
         "Search for data model, entity, or schema files. Look in directories like: models, entities, schemas, domain, "
         "data, or files ending in _model.dart, .model.ts, Model.java, etc. List all model files found with their paths. "
         "For each model, identify: what entity it represents (User, Task, Product, etc.), where it's located, and "
         "what other models it relates to. Group related models together. "
         "**List all model files organized by domain/feature - file paths only, no code.**"),

        ("Views and UI Components Structure",
         "Identify all UI-related code organization. Search for directories: views, screens, pages, components, widgets, "
         "ui, layouts, templates, etc. List the structure showing: how views are organized (by feature, by type, flat), "
         "what major screens/pages exist, how reusable components are organized. Show the hierarchy: "
         "parent screens → child components. "
         "**Map UI code organization - show directory structure and component hierarchy.**"),

        ("Business Logic and Services Organization",
         "Locate business logic code. Search for directories: services, controllers, blocs, providers, repositories, "
         "use_cases, interactors, managers, handlers, utils, helpers, etc. Describe how business logic is organized: "
         "by feature, by layer, by responsibility. List major service/controller files and their purposes. "
         "Show how logic is separated from UI and data layers. "
         "**Describe logic layer organization - show directory structure and key files.**"),

        ("State Management Structure",
         "If the app uses state management, identify how state code is organized. Look for directories or files: "
         "state, store, redux, bloc, providers, controllers, notifiers, etc. Show: where state classes are defined, "
         "where state logic lives, how state is separated by feature/domain. If using a specific pattern (BLoC, Redux, "
         "Provider), show how that pattern structures the code. "
         "**Map state management organization - describe structure, reference directories.**"),

        ("Utilities and Shared Code Structure",
         "Find shared/common code organization. Search for directories: utils, helpers, common, shared, core, lib, "
         "constants, enums, extensions, mixins, etc. List what types of utilities exist: string helpers, date formatters, "
         "validators, extensions, constants, enums, shared widgets, etc. Show how reusable code is organized. "
         "**List utility organization - categorize by type of utility.**"),

        # 3. Feature-level Structure
        ("Feature-based Organization",
         "Analyze if the codebase uses feature-based organization. Look for: top-level directories named after features "
         "(auth, dashboard, profile, settings, tasks, products, orders, etc.) or subdirectories within src/lib organized "
         "by feature. For each feature found, show its internal structure: does it contain its own models, views, "
         "controllers, and tests? List all major features identified and their organization pattern. "
         "**Identify all features and show their internal structure - create feature map.**"),

        ("Feature Module Boundaries",
         "For each major feature identified, describe its boundaries and dependencies. What files/directories belong to "
         "each feature? Do features have: their own subdirectories, clear entry points, isolated dependencies? "
         "How do features communicate (shared services, events, direct imports)? Show which features depend on which. "
         "Create a diagram or list showing feature dependencies. "
         "**Map feature boundaries and inter-feature dependencies.**"),

        ("Cross-cutting Concerns Organization",
         "Identify how cross-cutting concerns are organized: authentication, authorization, logging, error handling, "
         "networking, localization, theming, analytics, etc. Where is this code located? Is it in a shared directory, "
         "or distributed across features? Show: where each concern is implemented, whether it's centralized or distributed. "
         "**Map cross-cutting concerns to their locations in the codebase.**"),

        # 4. Naming Conventions
        ("File Naming Conventions",
         "Analyze file naming patterns throughout the repository. Look for patterns in: file extensions, prefixes, "
         "suffixes, casing (snake_case, camelCase, PascalCase, kebab-case). Examples: 'Does the project use "
         "_test.dart or .test.ts for tests?', 'Are views named *_view.dart or *_screen.dart?', 'Are models named "
         "*_model.dart or just *.dart?'. Document all observed file naming patterns with examples. "
         "**List file naming conventions with real examples from the repo.**"),

        ("Directory Naming Conventions",
         "Analyze directory naming patterns. Observe: casing used (lowercase, snake_case, camelCase, PascalCase), "
         "plural vs singular (models vs model, views vs view), naming patterns for feature directories, "
         "naming for platform-specific directories (android, ios, web). List all directory naming patterns observed. "
         "**Document directory naming conventions with examples.**"),

        ("Code Naming Conventions",
         "Analyze naming conventions in the code by examining class, function, and variable names. Look for patterns in: "
         "class names (PascalCase, prefixes, suffixes like Controller, Service, Manager), function/method names "
         "(camelCase, verb prefixes like get*, set*, is*, has*), variable names (camelCase, snake_case, prefixes like "
         "_private, m_member), constant names (UPPER_CASE, kConstant). Provide examples from actual code. "
         "**List code naming conventions with examples from the codebase.**"),

        # 5. Important Notes
        ("Critical Directories and Files",
         "Identify the MOST IMPORTANT directories and files that a new developer should understand first. "
         "Which directories contain the core application logic? Which files are entry points? What configuration files "
         "are critical? Rank by importance: 1) Entry points (main.dart, index.js, app.py), 2) Core logic directories, "
         "3) Critical configuration files, 4) Important documentation files. "
         "**Prioritized list of critical files/directories with explanations.**"),

        ("Code Organization Patterns",
         "Identify the overall code organization pattern used. Is it: layered architecture (presentation/business/data), "
         "feature-based, MVC/MVVM/MVP, clean architecture, onion architecture, or mixed? How strictly is the pattern "
         "followed? Show evidence from the directory structure. Are there any deviations or exceptions? "
         "**Describe the architectural organization pattern with directory evidence.**"),

        ("Special Directories and Their Purposes",
         "Identify any special-purpose directories that might not be obvious. Examples: generated code directories "
         "(generated/, .generated/, build/), platform-specific directories (android/, ios/, web/), documentation "
         "(docs/, documentation/), scripts (scripts/, tools/, bin/), examples (examples/, samples/), migration files "
         "(migrations/, db/), fixtures/seeds (fixtures/, seeds/, test_data/). Explain each special directory's purpose. "
         "**List special directories and their specific roles.**"),

        ("Navigation and Import Patterns",
         "Analyze how files import/reference each other. Look at import statements to understand: are there barrel files "
         "(index files that re-export)? Are there path aliases or shortcuts? How deep are import paths? "
         "What import patterns are used (relative paths '../../', absolute paths from root)? Show common import "
         "patterns with examples. "
         "**Document import/navigation patterns - show examples of typical imports.**"),

        ("Structure Best Practices and Issues",
         "Analyze the repository structure for best practices and issues. Good signs: clear separation of concerns, "
         "consistent naming, appropriate nesting depth (not too deep), logical grouping. Issues to look for: "
         "deeply nested directories (5+ levels), inconsistent naming, mixed concerns in same directory, "
         "orphaned files in wrong locations, missing separation between logic and UI. "
         "**Critical assessment of structure quality - both strengths and improvement areas.**"),
    ]

    # Collect responses
    repo_structure_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": getattr(chatbot, "repo_info", {}).get('name', 'unknown'),
            "provider": provider,
            "model": getattr(chatbot, "model", None)
        },
        "sections": {
            "complete_structure": {
                "teaching_content": []
            },
            "model_module_structure": {
                "teaching_content": []
            },
            "feature_level_structure": {
                "teaching_content": []
            },
            "naming_conventions": {
                "teaching_content": []
            },
            "important_notes": {
                "teaching_content": []
            }
        }
    }

    # Map questions to sections
    section_mapping = {
        0: "complete_structure",
        1: "complete_structure",
        2: "complete_structure",
        3: "complete_structure",
        4: "model_module_structure",
        5: "model_module_structure",
        6: "model_module_structure",
        7: "model_module_structure",
        8: "model_module_structure",
        9: "feature_level_structure",
        10: "feature_level_structure",
        11: "feature_level_structure",
        12: "naming_conventions",
        13: "naming_conventions",
        14: "naming_conventions",
        15: "important_notes",
        16: "important_notes",
        17: "important_notes",
        18: "important_notes",
        19: "important_notes",
    }

    total = len(questions)
    print(f"Asking {total} repository structure questions...\n")

    for idx, (key, question) in enumerate(questions, 1):
        print(f"[{idx}/{total}] {key}...")

        try:
            response = chatbot.chat(question)
            answer = response.get('answer') if isinstance(response, dict) else getattr(response, 'answer',
                                                                                       str(response))
            quality = response.get('context_quality', 1.0) if isinstance(response, dict) else getattr(response,
                                                                                                      'context_quality',
                                                                                                      1.0)

            section = section_mapping.get(idx - 1, "important_notes")
            repo_structure_data["sections"][section]["teaching_content"].append({
                "title": key,
                "topic": question,
                "content": answer,
                "quality": quality
            })
        except Exception as e:
            print(f"Error: {e}")
            section = section_mapping.get(idx - 1, "important_notes")
            repo_structure_data["sections"][section]["teaching_content"].append({
                "title": key,
                "topic": question,
                "content": f"Error: {str(e)}",
                "quality": 0.0
            })

    # Save to file
    output_dir = ONBOARDING_ROOT / "reading"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / f"onboarding_repo_structure.json"

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(repo_structure_data, f, indent=2, ensure_ascii=False)

    # Calculate success stats
    total_answers = sum(len(section.get("teaching_content", [])) for section in repo_structure_data["sections"].values())
    successful_answers = sum(
        1 for section in repo_structure_data["sections"].values()
        for item in section.get("teaching_content", [])
        if not str(item.get('content', '')).startswith('Error:')
    )

    print(f"\nDone! Saved to: {json_file}")
    print(f"📊 Answered {successful_answers}/{total_answers} questions successfully")
    print(f"\nData organized into {len(repo_structure_data['sections'])} sections:")
    for section_name, section_data in repo_structure_data["sections"].items():
        teaching_count = len(section_data.get("teaching_content", []))
        print(f"   - {section_name}: {teaching_count} teaching content items")

    # Generate MCQ questions for each section
    print("\n" + "=" * 80)
    print("Starting MCQ QNA Generation...")
    print("=" * 80)
    repo_structure_data = generate_section_qna(repo_structure_data, chatbot, gmail_db_path, provider, model)
    
    # Save updated file with QNA
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(repo_structure_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Updated file saved with QNA sections: {json_file}")

    return json_file


def add_qna_to_existing_repo_structure(
    json_file_path: str = None,
    gmail_db_path: str = None,
    provider: str = 'openai',
    model: str = None
) -> Path:
    """
    Add MCQ QNA questions to an existing repo structure JSON file
    
    Args:
        json_file_path: Path to existing repo structure JSON file (if None, uses default path)
        gmail_db_path: Optional path to Gmail database
        provider: LLM provider (openai/anthropic/ollama)
        model: Model name (optional, uses default for provider)
    
    Returns:
        Path to updated JSON file
    """
    print("╔" + "═" * 78 + "╗")
    print("║" + " ADD QNA TO EXISTING REPO STRUCTURE ".center(78) + "║")
    print("╚" + "═" * 78 + "╝\n")
    
    # Determine file path
    if json_file_path is None:
        json_file_path = str(ONBOARDING_ROOT / "reading" / "onboarding_repo_structure.json")
    
    json_file = Path(json_file_path)
    
    if not json_file.exists():
        print(f"✗  File not found: {json_file}")
        return None
    
    print(f"📄 Loading existing repo structure: {json_file.name}")
    
    # Load existing data
    with open(json_file, 'r', encoding='utf-8') as f:
        repo_structure_data = json.load(f)
    
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
    repo_structure_data = generate_section_qna(repo_structure_data, chatbot, gmail_db_path, provider, model)
    
    # Save updated file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(repo_structure_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓  Updated file saved: {json_file}\n")
    
    return json_file


if __name__ == "__main__":
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = None

    # Uncomment to just add QNA to existing file:
    # add_qna_to_existing_repo_structure(gmail_db_path=GMAIL_DB_PATH, provider=PROVIDER, model=MODEL)
    
    # Generate complete repo structure with QNA:
    generate_repo_structure_data(GMAIL_DB_PATH, PROVIDER, MODEL)
