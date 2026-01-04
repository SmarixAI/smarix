"""
Simple Onboarding Data Generator
Single command to extract all onboarding info from existing RAG chatbot
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
        verbose=False
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
        "data": {}
    }

    total = len(questions)
    print(f"Asking {total} questions...\n")

    for idx, (key, question) in enumerate(questions, 1):
        print(f"[{idx}/{total}] {key}...")

        try:
            response = chatbot.chat(question)
            # The exact response shape may differ by your chatbot implementation;
            # adapt the keys ('answer', 'context_quality') if needed.
            answer = response.get('answer') if isinstance(response, dict) else getattr(response, 'answer', str(response))
            quality = response.get('context_quality', 1.0) if isinstance(response, dict) else getattr(response, 'context_quality', 1.0)
            reading_overview_data["data"][key] = {
                "question": question,
                "answer": answer,
                "quality": quality
            }
        except Exception as e:
            print(f"Error: {e}")
            reading_overview_data["data"][key] = {
                "question": question,
                "answer": f"Error: {str(e)}",
                "quality": 0.0
            }

    # Save to file
    output_dir = ONBOARDING_ROOT / "reading"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / f"onboarding_project_overview.json"

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(reading_overview_data, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Saved to: {json_file}")
    print(f"Answered {len([d for d in reading_overview_data['data'].values() if not str(d.get('answer')).startswith('Error:')])}/{total} questions successfully")

    return json_file


if __name__ == "__main__":
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = None

    generate_reading_overview(GMAIL_DB_PATH, PROVIDER, MODEL)