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
            spec = importlib.util.spec_from_file_location(
                "rag_chatbot_dynamic", str(path)
            )
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


def get_search_keywords_for_conventions(topic: str) -> str:
    """
    Returns precise keywords to find relevant convention info.
    """
    mapping = {
        "Formatting": "editorconfig prettier eslint styleguide format indentation spacing line length",
        "Indentation": "indent tab space width size indentation rule",
        "Line Length": "max_line_length printWidth wrap line length limit",
        "Organization": "file structure organization order import sort grouping",
        "Linting": "lint linter eslintrc pylintrc analysis_options rules warn error",
        "Folder Naming": "directory folder naming convention case structure",
        "File Naming": "file naming convention extension suffix prefix case",
        "Variable Naming": "variable naming convention camelCase snake_case constant",
        "Function Naming": "function method naming convention verb prefix style",
        "Class Naming": "class interface type enum naming convention PascalCase",
        "Constant Naming": "constant static final naming UPPER_CASE convention",
        "PR Title": "pull request title semantic commit conventional commit prefix format",
        "PR Description": "pull request template PULL_REQUEST_TEMPLATE description checklist",
        "PR Review": "review process code review approval merge criteria contributing",
        "PR Best Practices": "contributing guidelines best practices branch naming commit message",
        "Issue Creation": "issue template ISSUE_TEMPLATE bug report feature request",
        "Issue Labeling": "labels taxonomy priority status type enhancement bug",
        "Issue Priority": "priority severity critical high medium low triage",
        "Issue Workflow": "issue lifecycle workflow status transition close resolve",
        "Testing Requirements": "testing requirements coverage standard unit integration",
        "Unit Testing": "unit test naming convention mock stub spy assertion",
        "Integration Testing": "integration test setup teardown database api",
        "E2E Testing": "e2e end-to-end cypress selenium playwright test",
        "Test Coverage": "coverage threshold minimum report lcov codecov",
        "Running Tests": "npm test make test pytest go test flutter test command",
        "Documentation": "docstring comment javadoc jsdoc documentation style",
        "External Resource": "api documentation swagger openapi external reference",
        "Commenting": "comment style TODO FIXME note warning explanation",
        "API Documentation": "api endpoint route controller documentation swagger",
        "Dependency": "dependency version lock package requirements manager",
    }

    for key, value in mapping.items():
        if key in topic:
            return value
    return "code conventions guidelines"


def retrieve_context(chatbot, keywords: str, limit: int = 20) -> str:
    """
    Directly retrieves chunks from Vector DB.
    """
    print(f"   🔍 Searching context with keywords: '{keywords[:50]}...'")
    query_embedding = chatbot.get_query_embedding(keywords)

    chunks = []

    # Direct Search
    if hasattr(chatbot.vector_db, "search"):
        chunks = chatbot.vector_db.search(query_embedding, top_k=limit)

    # Fallback to specific indices
    if hasattr(chatbot.vector_db, "indices"):
        for idx in ["docs", "code", "github"]:
            if idx in chatbot.vector_db.indices:
                res = chatbot.vector_db.indices[idx].search(
                    query_embedding, top_k=limit
                )
                if isinstance(res, list):
                    chunks.extend(res)

    # Flatten if needed
    if isinstance(chunks, dict):
        flat = []
        for v in chunks.values():
            if isinstance(v, list):
                flat.extend(v)
        chunks = flat

    # Deduplicate
    seen = set()
    unique_chunks = []
    for c in chunks:
        content = c.get("content") or c.get("text", "")
        # Prefer chunks that look like config files or documentation
        if content and content not in seen:
            seen.add(content)
            unique_chunks.append(c)

    if not unique_chunks:
        return ""

    context_parts = []
    for c in unique_chunks[:limit]:
        path = c.get("metadata", {}).get("file_path", "unknown")
        content = c.get("content") or c.get("text", "")
        context_parts.append(f"File: {path}\n```\n{content[:2000]}\n```")

    return "\n\n".join(context_parts)


def parse_json_mcq(response_text: str) -> dict:
    """Robustly parse JSON MCQ from response"""
    try:
        # 1. Try finding JSON block
        json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try finding raw JSON (starts with { ends with })
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                return None

        data = json.loads(json_str)
        
        # Validate structure
        required_keys = ["question", "options", "correct_answer", "explanation"]
        if not all(key in data for key in required_keys):
            print(f"    ⚠️ Missing keys in JSON. Found: {list(data.keys())}")
            return None
            
        # Validate options
        if not isinstance(data["options"], dict) or len(data["options"]) < 2:
            print("    ⚠️ Invalid options format")
            return None
            
        return data

    except json.JSONDecodeError as e:
        print(f"    ⚠️ JSON Decode Error: {e}")
        return None
    except Exception as e:
        print(f"    ⚠️ Parse Error: {e}")
        return None


def generate_section_qna(code_conventions_data, chatbot):
    """
    Generate MCQ questions for each section using strict JSON format
    """
    print("\n" + "=" * 80)
    print("GENERATING MCQ QUESTIONS FOR SECTIONS")
    print("=" * 80 + "\n")

    sections = code_conventions_data.get("sections", {})
    total_qnas = 0

    for section_name, section_content in sections.items():
        if not isinstance(section_content, dict):
            continue

        teaching_content = section_content.get("teaching_content", [])
        if not teaching_content:
            continue

        qna_list = []

        for idx, item_data in enumerate(teaching_content, 1):
            title = item_data.get("title", f"Item {idx}")
            content = item_data.get("content", "")

            # Skip if content is an error or too short
            if not content or str(content).startswith("Error:") or len(str(content)) < 50:
                continue

            print(f"  [{idx}/{len(teaching_content)}] Generating MCQ for '{title}'...")

            mcq_prompt = f"""
            You are a technical quiz generator. Generate ONE multiple-choice question (MCQ) based on the provided code convention topic.
            
            TOPIC: {title}
            CONTENT: {content[:3000]}
            
            OUTPUT FORMAT:
            You MUST return a valid JSON object. Do not include markdown formatting outside the JSON.
            {{
                "question": "The question text here?",
                "options": {{
                    "A": "Option 1",
                    "B": "Option 2",
                    "C": "Option 3",
                    "D": "Option 4"
                }},
                "correct_answer": "A",
                "explanation": "Explanation of why A is correct."
            }}
            """

            try:
                # System prompt ensures JSON behavior
                response = chatbot.call_llm(
                    "You are a helpful assistant that outputs only valid JSON.",
                    mcq_prompt
                )
                
                mcq = parse_json_mcq(response)
                
                if mcq:
                    mcq["subsection"] = title
                    qna_list.append(mcq)
                    print(f"    ✓ Generated MCQ: {mcq['question'][:50]}...")
                else:
                    print(f"    ✗ Failed to parse MCQ. Raw response preview: {response[:100]}...")
            except Exception as e:
                print(f"    ✗ Error calling LLM: {e}")

        if qna_list:
            sections[section_name]["qna"] = qna_list
            total_qnas += len(qna_list)

    print(f"\n✓ Total MCQ questions generated: {total_qnas}")
    return code_conventions_data


def generate_code_conventions_data(gmail_db_path=None, provider="openai", model=None):
    """Generate comprehensive code conventions analysis data using Context-First RAG"""

    print("Starting Code Conventions Data Generation (Context-First)...\n")

    print("Loading chatbot...")
    RAGChatbotClass = get_rag_chatbot_class()
    chatbot = RAGChatbotClass(
        vector_db_path=VECTOR_DB_PATH,
        gmail_db_path=gmail_db_path,
        provider=provider,
        model=model,
        verbose=False,
        disable_conversation_storage=True,
    )

    questions = [
        # 1. Styling Rules
        (
            "Code Formatting Standards",
            "What are the code styling rules? Indentation, spacing, line length. "
            "**Comprehensive styling rules.**",
        ),
        (
            "Indentation and Spacing",
            "Specific indentation (tabs/spaces) and spacing rules. "
            "**Detailed indentation rules.**",
        ),
        (
            "Line Length and Wrapping",
            "Max line length and wrapping conventions. " "**Line length rules.**",
        ),
        (
            "Code Organization Standards",
            "File structure and import organization. " "**Organization standards.**",
        ),
        (
            "Linting and Formatting Tools",
            "What linters (ESLint, Pylint) and formatters (Prettier) are used? "
            "**Tool configuration.**",
        ),
        # 2. Naming Guidelines
        (
            "Folder and Directory Naming",
            "Directory naming conventions (case, pluralization). "
            "**Folder naming conventions.**",
        ),
        (
            "File Naming Conventions",
            "File naming patterns and extensions. " "**File naming conventions.**",
        ),
        (
            "Variable Naming Conventions",
            "Variable naming (camelCase, snake_case). "
            "**Variable naming conventions.**",
        ),
        (
            "Function and Method Naming",
            "Function naming patterns. " "**Function naming conventions.**",
        ),
        (
            "Class and Type Naming",
            "Class/Interface naming (PascalCase). " "**Class naming conventions.**",
        ),
        (
            "Constant Naming Conventions",
            "Constant naming (UPPER_CASE). " "**Constant naming conventions.**",
        ),
        # 3. PR Rules
        (
            "Pull Request Title Format",
            "PR title guidelines (Conventional Commits). " "**PR title format.**",
        ),
        (
            "Pull Request Description Requirements",
            "What goes in a PR description? Templates? "
            "**PR description requirements.**",
        ),
        (
            "Pull Request Review Process",
            "Reviewer process and approval criteria. " "**PR review workflow.** ",
        ),
        (
            "Pull Request Best Practices",
            "Best practices for size, commits, and branching. "
            "**PR best practices.**",
        ),
        # 4. Issues Rules
        (
            "Issue Creation Guidelines",
            "How to create issues? Templates used? " "**Issue creation guidelines.**",
        ),
        (
            "Issue Labeling Conventions",
            "Label categories and usage. " "**Labeling conventions.**",
        ),
        (
            "Issue Priority Levels",
            "Priority definitions (High, Medium, Low). " "**Priority system.**",
        ),
        (
            "Issue Management Workflow",
            "Issue lifecycle and status transitions. "
            "**Issue management workflow.** ",
        ),
        # 5. Testing Guidelines
        (
            "Testing Requirements and Standards",
            "General testing requirements and standards. " "**Testing guidelines.**",
        ),
        (
            "Unit Testing Conventions",
            "Unit test structure and naming. " "**Unit testing conventions.**",
        ),
        (
            "Integration Testing Standards",
            "Integration test approach and data. " "**Integration testing standards.**",
        ),
        (
            "E2E Testing Guidelines",
            "E2E test scope and tools. " "**E2E testing guidelines.**",
        ),
        (
            "Test Coverage Requirements",
            "Minimum coverage thresholds. " "**Coverage requirements.**",
        ),
        ("Running Tests", "Commands to run tests. " "**Test execution.**"),
        # 6. Referencing
        (
            "Documentation Standards",
            "Code comment and docstring styles. " "**Documentation standards.**",
        ),
        (
            "External Resource Documentation",
            "How to document external APIs/libs. " "**External docs.**",
        ),
        (
            "Code Commenting Conventions",
            "When and how to comment (TODOs). " "**Commenting conventions.**",
        ),
        (
            "API Documentation Standards",
            "API docs format (Swagger/OpenAPI). " "**API doc standards.**",
        ),
        (
            "Dependency Documentation",
            "How dependencies are tracked/documented. " "**Dependency docs.**",
        ),
    ]

    code_conventions_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": getattr(chatbot, "repo_info", {}).get("name", "unknown"),
            "provider": provider,
            "model": getattr(chatbot, "model", None),
        },
        "sections": {
            "styling_rules": {"teaching_content": []},
            "naming_guidelines": {"teaching_content": []},
            "pr_rules": {"teaching_content": []},
            "issues_rules": {"teaching_content": []},
            "testing_guidelines": {"teaching_content": []},
            "referencing": {"teaching_content": []},
        },
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

        # 1. Get Keywords
        keywords = get_search_keywords_for_conventions(key)

        # 2. Retrieve Context (Raw)
        context = retrieve_context(chatbot, keywords)

        if not context:
            print("   ⚠️ No specific context found. Using broad knowledge...")
            context = "No specific configuration files found. Infer based on standard community conventions for the languages used."

        # 3. Generate Answer
        system_prompt = (
            "You are a Technical Lead focusing on Code Quality and Standards. "
            "Explain the coding conventions based on the provided configuration and code."
        )

        user_prompt = f"""
        QUESTION: {question}
        
        CONTEXT FROM REPO:
        {context[:20000]}
        
        INSTRUCTIONS:
        - Analyze the context (config files, existing code) to answer.
        - Be specific about rules found in configs (e.g. indentation size).
        - Assess if the user would be able to understand response better with the use of diagrams and trigger them.
        - You can insert a diagram by adding the 

[Image of X]
 tag where X is a contextually relevant and domain-specific query to fetch the diagram.
        - Place the image tag immediately before or after the relevant text without disrupting the flow of the response.
        """

        try:
            answer = chatbot.call_llm(system_prompt, user_prompt)

            # Insert diagram tags if relevant keywords are in the topic but not generated in the answer
            if "Review Process" in key and "[Image of" not in answer:
                answer += "\n\n"
            if "Issue Management" in key and "[Image of" not in answer:
                answer += "\n\n"
            if "Git Workflow" in key and "[Image of" not in answer:
                answer += "\n\n[Image of git flow diagram]"

            section = section_mapping.get(idx - 1, "referencing")
            code_conventions_data["sections"][section]["teaching_content"].append(
                {"title": key, "topic": question, "content": answer, "quality": 1.0}
            )
            print(f"   ✓ Generated response ({len(answer)} chars)")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            section = section_mapping.get(idx - 1, "referencing")
            code_conventions_data["sections"][section]["teaching_content"].append(
                {
                    "title": key,
                    "topic": question,
                    "content": f"Error: {str(e)}",
                    "quality": 0.0,
                }
            )

    # Upload Draft to S3
    s3_key = (
        f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_code_conventions.json"
    )
    try:
        s3_manager.upload_json(code_conventions_data, s3_key)
        print(f"\n✓ Draft Uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"\n❌ Failed to upload: {e}")

    # Generate MCQ
    code_conventions_data = generate_section_qna(code_conventions_data, chatbot)

    # Upload Final
    try:
        s3_manager.upload_json(code_conventions_data, s3_key)
        print(
            f"✓ Final file with QNA uploaded to S3: s3://{s3_manager.bucket}/{s3_key}"
        )
    except Exception as e:
        print(f"❌ Failed to upload updated file: {e}")
        raise

    return s3_key


def add_qna_to_existing_code_conventions(
    json_file_path: str = None,
    gmail_db_path: str = None,
    provider: str = "openai",
    model: str = None,
) -> str:
    """
    Add MCQ QNA questions to an existing code conventions JSON file
    """
    print("╔" + "═" * 78 + "╗")
    print("║" + " ADD QNA TO EXISTING CODE CONVENTIONS ".center(78) + "║")
    print("╚" + "═" * 78 + "╝\n")

    s3_key = (
        f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_code_conventions.json"
    )

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
            verbose=False,
        )
        print("✓  Chatbot initialized successfully\n")
    except Exception as e:
        print(f"✗  Failed to initialize chatbot: {e}")
        return None

    code_conventions_data = generate_section_qna(code_conventions_data, chatbot)

    try:
        s3_manager.upload_json(code_conventions_data, s3_key)
        print(f"✓  Updated file uploaded to S3: s3://{s3_manager.bucket}/{s3_key}\n")
    except Exception as e:
        print(f"✗  Failed to upload to S3: {e}")
        return None

    return s3_key


if __name__ == "__main__":
    GMAIL_DB_PATH = None
    PROVIDER = "openai"
    MODEL = "gpt-4o-mini"

    # Uncomment to just add QNA to existing file:
    # add_qna_to_existing_code_conventions(gmail_db_path=GMAIL_DB_PATH, provider=PROVIDER, model=MODEL)

    # Generate complete code conventions with QNA:
    generate_code_conventions_data(GMAIL_DB_PATH, PROVIDER, MODEL)