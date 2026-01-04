"""
Code Conventions Data Generator
Extracts comprehensive code styling, naming, PR, issues, testing, and referencing guidelines
"""

import sys
import os
import json
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


RAGChatbot = _load_rag_chatbot_class()


def generate_code_conventions_data( gmail_db_path=None, provider='openai', model=None):
    """Generate comprehensive code conventions analysis data"""

    print("Starting Code Conventions Data Generation...\n")

    # Initialize chatbot
    print("Loading chatbot...")
    chatbot = RAGChatbot(
        vector_db_path=VECTOR_DB_PATH,
        gmail_db_path=gmail_db_path,
        provider=provider,
        model=model,
        verbose=False
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
            "styling_rules": {},
            "naming_guidelines": {},
            "pr_rules": {},
            "issues_rules": {},
            "testing_guidelines": {},
            "referencing": {}
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

        try:
            response = chatbot.chat(question)
            answer = response.get('answer') if isinstance(response, dict) else getattr(response, 'answer',
                                                                                       str(response))
            quality = response.get('context_quality', 1.0) if isinstance(response, dict) else getattr(response,
                                                                                                      'context_quality',
                                                                                                      1.0)

            section = section_mapping.get(idx - 1, "referencing")
            code_conventions_data["sections"][section][key] = {
                "question": question,
                "answer": answer,
                "quality": quality
            }
        except Exception as e:
            print(f"Error: {e}")
            section = section_mapping.get(idx - 1, "referencing")
            code_conventions_data["sections"][section][key] = {
                "question": question,
                "answer": f"Error: {str(e)}",
                "quality": 0.0
            }

    # Save to file
    output_dir = ONBOARDING_ROOT / "reading"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / f"onboarding_code_conventions.json"

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(code_conventions_data, f, indent=2, ensure_ascii=False)

    # Calculate success stats
    total_answers = sum(len(section) for section in code_conventions_data["sections"].values())
    successful_answers = sum(
        1 for section in code_conventions_data["sections"].values()
        for item in section.values()
        if not str(item.get('answer', '')).startswith('Error:')
    )

    print(f"\nDone! Saved to: {json_file}")
    print(f"📊 Answered {successful_answers}/{total_answers} questions successfully")
    print(f"\nData organized into {len(code_conventions_data['sections'])} sections:")
    for section_name, section_data in code_conventions_data["sections"].items():
        print(f"   - {section_name}: {len(section_data)} questions")

    return json_file


if __name__ == "__main__":
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = None

    generate_code_conventions_data(GMAIL_DB_PATH, PROVIDER, MODEL)

