"""
Tech Stack Data Generator - Improved for Better RAG Retrieval
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import importlib
import importlib.util

# Make repository root importable BEFORE trying to import the chatbot module.
repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

load_dotenv()


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
    for path in repo_root.rglob("chatbot.py"):
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


RAGChatbot = _load_rag_chatbot_class()


def generate_tech_stack_data(db_path, gmail_db_path=None, provider='openai', model=None):
    """Generate comprehensive tech stack analysis data"""

    print("Starting Tech Stack Data Generation...\n")

    # Initialize chatbot
    print("Loading chatbot...")
    chatbot = RAGChatbot(
        vector_db_path=db_path,
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
            "complete_tech_stack_overview": {},
            "application_flow_tech_stack": {},
            "module_wise_tech_breakdown": {},
            "technology_rationale": {},
            "reference_summary": {}
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

        try:
            response = chatbot.chat(question)
            answer = response.get('answer') if isinstance(response, dict) else getattr(response, 'answer', str(response))
            quality = response.get('context_quality', 1.0) if isinstance(response, dict) else getattr(response, 'context_quality', 1.0)

            section = section_mapping.get(idx - 1, "reference_summary")
            tech_stack_data["sections"][section][key] = {
                "question": question,
                "answer": answer,
                "quality": quality
            }
        except Exception as e:
            print(f"Error: {e}")
            section = section_mapping.get(idx - 1, "reference_summary")
            tech_stack_data["sections"][section][key] = {
                "question": question,
                "answer": f"Error: {str(e)}",
                "quality": 0.0
            }

    # Save to file
    output_dir = repo_root / "data" / "Onboarding" / "onboarding_reading_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / f"onboarding_tech_stack.json"

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(tech_stack_data, f, indent=2, ensure_ascii=False)

    # Calculate success stats
    total_answers = sum(len(section) for section in tech_stack_data["sections"].values())
    successful_answers = sum(
        1 for section in tech_stack_data["sections"].values()
        for item in section.values()
        if not str(item.get('answer', '')).startswith('Error:')
    )

    print(f"\nDone! Saved to: {json_file}")
    print(f"📊 Answered {successful_answers}/{total_answers} questions successfully")
    print(f"\nData organized into {len(tech_stack_data['sections'])} sections:")
    for section_name, section_data in tech_stack_data["sections"].items():
        print(f"   - {section_name}: {len(section_data)} questions")

    return json_file


if __name__ == "__main__":
    GITHUB_DB_PATH = "../../../../data/VectorDB/multi_index"
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = None

    generate_tech_stack_data(GITHUB_DB_PATH, GMAIL_DB_PATH, PROVIDER, MODEL)
