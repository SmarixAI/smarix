"""
Tech Stack Data Generator - Improved for Better RAG Retrieval
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

# Calculate BACKEND_ROOT - go up 4 levels from this file
# File: backend/main/Onboarding/generators/reading/generate_tech_stacks.py
# Up 4: reading -> generators -> Onboarding -> main -> backend
BACKEND_ROOT = Path(__file__).resolve().parents[4]  # backend/
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Also add the parent directory in case we need it
PARENT_DIR = BACKEND_ROOT.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

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
        except Exception as e:
            # Debug: uncomment to see import errors
            # print(f"Failed to import {cand}: {e}")
            pass

    # Fallback: try direct path to chatbot.py
    chatbot_path = BACKEND_ROOT / "core" / "ChatBot" / "chatbot.py"
    if chatbot_path.exists():
        try:
            # Ensure BACKEND_ROOT is in sys.path for imports to work
            if str(BACKEND_ROOT) not in sys.path:
                sys.path.insert(0, str(BACKEND_ROOT))
            
            # Try importing using the module path
            try:
                from core.ChatBot.chatbot import RAGChatbot
                return RAGChatbot
            except ImportError:
                # If that fails, try loading directly
                spec = importlib.util.spec_from_file_location("core.ChatBot.chatbot", str(chatbot_path))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore
                if hasattr(mod, "RAGChatbot"):
                    return mod.RAGChatbot
        except Exception as e:
            # Print error for debugging
            print(f"Warning: Failed to load from direct path {chatbot_path}: {e}")
            import traceback
            traceback.print_exc()
            pass

    # Fallback: search the repo for a file named chatbot.py and load it dynamically
    for path in BACKEND_ROOT.rglob("chatbot.py"):
        try:
            spec = importlib.util.spec_from_file_location("rag_chatbot_dynamic", str(path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            if hasattr(mod, "RAGChatbot"):
                return getattr(mod, "RAGChatbot")
        except Exception as e:
            # Debug: uncomment to see load errors
            # print(f"Failed to load from path {path}: {e}")
            pass

    raise ImportError(
        f"Could not import RAGChatbot. Tried import paths: {', '.join(candidates)}. "
        f"Also searched repository for chatbot.py. BACKEND_ROOT: {BACKEND_ROOT}. "
        f"Make sure project is on PYTHONPATH and package markers (__init__.py) exist where needed."
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
                try:
                    if ':' in line:
                        split_result = line.split(':', 1)
                        answer_line = split_result[-1].strip() if split_result else line.replace('**Answer:**', '').strip()
                    else:
                        answer_line = line.replace('**Answer:**', '').strip()
                    
                    if answer_line:
                        answer_match = re.match(r'^([A-D])\s*[-–—]\s*(.+)', answer_line, re.DOTALL)
                        if answer_match:
                            correct_answer = answer_match.group(1)
                            explanation = answer_match.group(2).strip()
                        else:
                            letter_match = re.match(r'^([A-D])', answer_line)
                            if letter_match:
                                correct_answer = letter_match.group(1)
                                explanation = answer_line[1:].strip() if len(answer_line) > 1 else ""
                except (IndexError, AttributeError):
                    pass
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
        
        if len(options) == 4 and correct_answer and correct_answer in options and question_text:
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
    
    try:
        question_part = answer_split[0].strip()
        answer_part = answer_split[1].strip()
    except IndexError:
        return None
    
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
            explanation = answer_part[1:].strip() if len(answer_part) > 1 else ""
    
    # Validate this is a proper MCQ
    if len(options) == 4 and correct_answer and correct_answer in options and question_text:
        return {
            'question': ' '.join(question_text),
            'options': options,
            'correct_answer': correct_answer,
            'explanation': explanation
        }
    
    return None


def generate_section_qna(tech_stack_data, chatbot, gmail_db_path=None, provider='openai', model=None):
    """
    Generate MCQ questions for each section in tech stack data
    Adds a 'qna' array to each section
    """
    print("\n" + "=" * 80)
    print("GENERATING MCQ QUESTIONS FOR TECH STACK SECTIONS")
    print("=" * 80 + "\n")
    
    sections = tech_stack_data.get("sections", {})
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
- Focus on important, practical knowledge that helps new employees understand the codebase
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
    
    return tech_stack_data


def generate_tech_stack_data(gmail_db_path=None, provider='openai', model=None):
    """Generate comprehensive tech stack analysis data"""

    print("Starting Tech Stack Data Generation...\n")

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

    # Define tech stack specific questions - optimized for RAG retrieval
    questions = [
        # 1. Complete Tech Stack Overview
        ("Programming Languages Used",
         "Search for files with extensions like .dart, .java, .py, .js, .ts, .cpp, .swift, .kt, .go, .rb, .rs, .php. "
         "List EVERY programming language found in the codebase. For each language, count or estimate: "
         "number of files, percentage of codebase, and what parts of the application use it. "
         "Example format: 'Dart: 150 files (80%), used for mobile app logic and UI'. "
         "**List all languages with file counts - no code snippets.**"),

        ("Package Dependencies",
         "Look for files named: pubspec.yaml, package.json, requirements.txt, pom.xml, build.gradle, go.mod, "
         "Gemfile, Cargo.toml, Package.swift, or similar dependency files. "
         "Extract and list the TOP 15-20 dependencies from these files. For each dependency, state: "
         "its name, what it provides (UI, networking, database, testing, etc.), and whether it's for "
         "production or development use. If you find these files, extract the actual package names. "
         "**Extract from dependency files and list package names with purposes.**"),

        ("Frameworks and Major Libraries",
         "Identify the main frameworks by looking at: import statements, dependency files, and file structure. "
         "Common frameworks include: Flutter, React, Angular, Vue, Django, Flask, Spring Boot, Express, "
         "Rails, Laravel, .NET, etc. List the PRIMARY framework(s) that structure this application. "
         "Also identify major libraries for: UI components, state management, routing, networking, database access. "
         "**List framework names and major library names - no code.**"),

        ("Build Tools and Compilation",
         "Search for build configuration files: CMakeLists.txt, Makefile, build.gradle, webpack.config.js, "
         "vite.config.js, tsconfig.json, babel.config.js, etc. What build tools compile or bundle this code? "
         "What tools transpile or process code before execution? List: build systems (CMake, Gradle, Maven, npm, etc.), "
         "bundlers (Webpack, Vite, Rollup), transpilers (Babel, TypeScript), and compilers. "
         "**List build toolchain - configuration examples OK, no application code.**"),

        # 2. Application Flow wrt Tech Stacks
        ("Application Type and Entry Point",
         "Determine the application type by examining: main files (main.dart, index.js, app.py, main.go, etc.), "
         "project structure, and build outputs. Is this a: mobile app, web app, desktop app, CLI tool, "
         "backend API, library, or multi-platform project? Identify the entry point file(s). "
         "Describe what happens when the application starts - which technologies initialize first? "
         "**Describe app type and startup flow with technologies - no code snippets.**"),

        ("Data Storage Technologies",
         "Search for database-related code and imports. Look for: SQLite (sqflite, sqlite3), PostgreSQL (pg, psycopg2), "
         "MySQL, MongoDB, Redis, Firebase, Realm, Hive, SharedPreferences, AsyncStorage, IndexedDB, etc. "
         "What database or storage technology is used? Where is data stored (local device, remote server, cloud)? "
         "Look for: database initialization code, schema files, migration files, or ORM/query builder usage. "
         "**List all data storage technologies found - include schema definitions if present.**"),

        ("Networking and API Communication",
         "Look for HTTP client libraries and API code. Search for: http, dio, axios, fetch, retrofit, okhttp, "
         "requests, urllib, networking imports. Does this application make network requests? "
         "What library handles HTTP? Are there WebSocket connections? Does it define API endpoints? "
         "Look for: API client code, REST endpoint definitions, GraphQL queries, WebSocket handlers. "
         "**List networking libraries and communication patterns - no implementation code.**"),

        ("State Management Pattern",
         "For applications with UI, identify state management by searching for: Provider, Riverpod, Bloc, Redux, "
         "MobX, GetX, Context API, Vuex, Pinia, NgRx, Recoil, Zustand, setState, etc. "
         "How does the application manage state? What pattern or library coordinates data flow between UI and logic? "
         "If no state management library is found, describe how state is handled. "
         "**Identify state management approach - describe pattern, don't paste code.**"),

        ("UI Layer Technologies",
         "Identify UI technologies by examining: import statements, file extensions, and component files. "
         "For mobile: Flutter widgets, React Native, SwiftUI, Jetpack Compose, UIKit, XML layouts. "
         "For web: HTML/CSS/JS, React components, Vue templates, Angular components, Svelte. "
         "For desktop: Electron, Qt, GTK, WPF, JavaFX. What technologies render the user interface? "
         "What styling approach is used (CSS, SASS, styled-components, Tailwind, native styling)? "
         "**List UI technologies and styling approach - no code.**"),

        # 3. Module-wise Tech Stack
        ("Project Directory Structure",
         "Analyze the top-level directory structure. List main directories (lib, src, app, components, services, "
         "models, utils, test, android, ios, web, windows, linux, etc.) and explain what each contains. "
         "How is the codebase organized? Is there separation by: feature, layer (MVC), platform, or module? "
         "**Describe directory organization - plain text list, no code.**"),

        ("Platform-Specific Technologies",
         "Look for platform-specific directories: android, ios, web, windows, linux, macos, etc. "
         "For each platform directory found, identify what native technologies are used: "
         "Android: Kotlin/Java with Gradle; iOS: Swift/Objective-C with CocoaPods/SPM; "
         "Web: HTML/JS frameworks; Desktop: native APIs or cross-platform wrappers. "
         "**List platform-specific tech - mention directories and technologies used.**"),

        ("Testing Infrastructure",
         "Search for test files and test configuration. Look for: test directories, files ending in _test.dart, "
         ".test.js, .spec.ts, test_*.py, *_test.go, etc. Identify testing frameworks: flutter_test, jest, "
         "mocha, pytest, junit, go test, rspec, etc. What types of tests exist (unit, widget, integration, e2e)? "
         "Look for test configuration files. If tests exist, list the frameworks. If none, state 'No tests found'. "
         "**List testing technologies - be explicit about presence or absence.**"),

        ("Development Automation",
         "Look for CI/CD configuration and development scripts: .github/workflows, .gitlab-ci.yml, .circleci, "
         "jenkins files, docker-compose.yml, Dockerfile, scripts directory, npm scripts in package.json. "
         "What automation exists for: testing, building, deploying, linting, formatting? "
         "What tools automate development workflows (GitHub Actions, Docker, pre-commit hooks, etc.)? "
         "**List automation tools and their purposes - config examples OK.**"),

        # 4. Technology Rationale
        ("Technology Ecosystem",
         "Based on all technologies identified, what is the primary technology ecosystem? "
         "Examples: Dart/Flutter ecosystem, JavaScript/Node.js ecosystem, Python ecosystem, Java/JVM ecosystem, "
         "Go ecosystem, Ruby ecosystem, .NET ecosystem, etc. Are most technologies from one ecosystem, "
         "or is this a polyglot project mixing multiple ecosystems? Why might this ecosystem have been chosen? "
         "**Identify the dominant ecosystem and explain the technology cohesion.**"),

        ("Cross-Platform Strategy",
         "Analyze how the project handles multiple platforms. Is there: a single codebase for all platforms, "
         "platform-specific code in separate directories, conditional compilation, or separate apps per platform? "
         "What technologies enable cross-platform development (Flutter, React Native, Electron, etc.)? "
         "How much code is shared vs platform-specific? "
         "**Describe cross-platform approach and code sharing strategy.**"),

        # 5. Reference/Summary
        ("Complete Technology Inventory",
         "Create a comprehensive table with ALL technologies identified so far. For each technology list: "
         "Name | Type (Language/Framework/Library/Tool) | Purpose | File/Directory Reference. "
         "Include everything: languages, frameworks, libraries, databases, build tools, testing tools, CI/CD, etc. "
         "**Structured table format - serves as master reference.**"),

        ("Version Requirements",
         "Search dependency files for version numbers. Look at: pubspec.yaml (sdk, dependencies), "
         "package.json (engines, dependencies), requirements.txt, pom.xml, build.gradle, etc. "
         "Extract: minimum SDK/runtime versions, framework versions, and major dependency versions. "
         "Example: 'Dart SDK: >=2.19.0 <4.0.0', 'Flutter: SDK flutter', 'http: ^1.1.0'. "
         "If versions aren't specified, note which technologies lack version constraints. "
         "**Extract actual version numbers from configuration files.**"),

        ("Developer Prerequisites",
         "Based on all identified technologies, what must a developer install to work on this project? "
         "List in priority order: 1) Required SDKs/runtimes (Dart, Node.js, Python, JDK, etc.) "
         "2) Primary framework (Flutter, React, etc.) 3) Build tools 4) Development tools (IDE, debugger). "
         "What should they learn first? What's the minimum setup to run the app locally? "
         "**Prioritized setup list - focus on what's actually required.**"),

        ("Technology Maturity and Updates",
         "Analyze the tech stack's maturity: Are these technologies actively maintained and widely adopted? "
         "Are any deprecated or outdated? Look for: old framework versions, deprecated APIs in comments, "
         "TODO comments about upgrades. Are technologies modern (released in last 3-5 years) or established? "
         "What are the strengths (stability, community, performance) and potential risks (legacy, niche, abandoned)? "
         "**Critical assessment of stack's current state and future viability.**"),
    ]

    # Collect responses
    tech_stack_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": getattr(chatbot, "repo_info", {}).get('name', 'unknown'),
            "provider": provider,
            "model": getattr(chatbot, "model", None)
        },
        "sections": {
            "complete_tech_stack_overview": {
                "teaching_content": []
            },
            "application_flow_tech_stack": {
                "teaching_content": []
            },
            "module_wise_tech_breakdown": {
                "teaching_content": []
            },
            "technology_rationale": {
                "teaching_content": []
            },
            "reference_summary": {
                "teaching_content": []
            }
        }
    }

    # Map questions to sections
    section_mapping = {
        0: "complete_tech_stack_overview",
        1: "complete_tech_stack_overview",
        2: "complete_tech_stack_overview",
        3: "complete_tech_stack_overview",
        4: "application_flow_tech_stack",
        5: "application_flow_tech_stack",
        6: "application_flow_tech_stack",
        7: "application_flow_tech_stack",
        8: "application_flow_tech_stack",
        9: "module_wise_tech_breakdown",
        10: "module_wise_tech_breakdown",
        11: "module_wise_tech_breakdown",
        12: "module_wise_tech_breakdown",
        13: "technology_rationale",
        14: "technology_rationale",
        15: "reference_summary",
        16: "reference_summary",
        17: "reference_summary",
        18: "reference_summary",
    }

    total = len(questions)
    print(f"Asking {total} tech stack questions...\n")

    for idx, (key, question) in enumerate(questions, 1):
        print(f"[{idx}/{total}] {key}...")

        schema_name = f"{REPO_OWNER}_{REPO_NAME}".replace("-", "_")
        try:
            response = chatbot.chat(question, schema_name=schema_name)
            answer = response.get('answer') if isinstance(response, dict) else getattr(response, 'answer', str(response))
            quality = response.get('context_quality', 1.0) if isinstance(response, dict) else getattr(response, 'context_quality', 1.0)

            section = section_mapping.get(idx - 1, "reference_summary")
            tech_stack_data["sections"][section]["teaching_content"].append({
                "title": key,
                "topic": question,
                "content": answer,
                "quality": quality
            })
        except Exception as e:
            print(f"Error: {e}")
            section = section_mapping.get(idx - 1, "reference_summary")
            tech_stack_data["sections"][section]["teaching_content"].append({
                "title": key,
                "topic": question,
                "content": f"Error: {str(e)}",
                "quality": 0.0
            })

    # Upload to S3
    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_tech_stack.json"

    try:
        s3_manager.upload_json(tech_stack_data, s3_key)
        print(f"\n✓ Uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"\n❌ Failed to upload to S3: {e}")
        raise


    # Calculate success stats
    total_answers = sum(len(section.get("teaching_content", [])) for section in tech_stack_data["sections"].values())
    successful_answers = sum(
        1 for section in tech_stack_data["sections"].values()
        for item in section.get("teaching_content", [])
        if not str(item.get('content', '')).startswith('Error:')
    )

    print(f"📊 Answered {successful_answers}/{total_answers} questions successfully")
    print(f"\nData organized into {len(tech_stack_data['sections'])} sections:")
    for section_name, section_data in tech_stack_data["sections"].items():
        teaching_count = len(section_data.get("teaching_content", []))
        print(f"   - {section_name}: {teaching_count} teaching content items")

    # Generate MCQ questions for each section
    print("\n" + "=" * 80)
    print("Starting MCQ QNA Generation...")
    print("=" * 80)
    tech_stack_data = generate_section_qna(tech_stack_data, chatbot, gmail_db_path, provider, model)
    
    # Save updated file with QNA
    # Upload updated version with QNA to S3
    try:
        s3_manager.upload_json(tech_stack_data, s3_key)
        print(f"✓ Updated file with QNA uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"❌ Failed to upload updated file: {e}")
        raise


    return s3_key


def add_qna_to_existing_tech_stack(
    json_file_path: str = None,
    gmail_db_path: str = None,
    provider: str = 'openai',
    model: str = None
) -> str:
    """
    Add MCQ QNA questions to an existing tech stack JSON file
    
    Args:
        json_file_path: Path to existing tech stack JSON file (if None, uses default path)
        gmail_db_path: Optional path to Gmail database
        provider: LLM provider (openai/anthropic/ollama)
        model: Model name (optional, uses default for provider)
    
    Returns:
        Path to updated JSON file
    """
    print("╔" + "═" * 78 + "╗")
    print("║" + " ADD QNA TO EXISTING TECH STACK ".center(78) + "║")
    print("╚" + "═" * 78 + "╝\n")
    
    # Determine file path
    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_tech_stack.json"

    print(f"📄 Loading existing tech stack from S3...")

    try:
        tech_stack_data = s3_manager.download_json(s3_key)
        print(f"✓  Loaded from: s3://{s3_manager.bucket}/{s3_key}\n")
    except Exception as e:
        print(f"✗  File not found in S3: {e}")
        return None

    
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
    tech_stack_data = generate_section_qna(tech_stack_data, chatbot, gmail_db_path, provider, model)
    
    # Save updated file
    try:
        s3_manager.upload_json(tech_stack_data, s3_key)
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
    # add_qna_to_existing_tech_stack(gmail_db_path=GMAIL_DB_PATH, provider=PROVIDER, model=MODEL)
    
    # Generate complete tech stack with QNA:
    generate_tech_stack_data(GMAIL_DB_PATH, PROVIDER, MODEL)
