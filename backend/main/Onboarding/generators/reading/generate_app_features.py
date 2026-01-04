"""
App Features Data Generator
Extracts comprehensive application features, flows, and architecture information
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


def generate_app_features_data(db_path, gmail_db_path=None, provider='openai', model=None):
    """Generate comprehensive application features analysis data"""

    print("Starting App Features Data Generation...\n")

    # Initialize chatbot
    print("Loading chatbot...")
    chatbot = RAGChatbot(
        vector_db_path=VECTOR_DB_PATH,
        gmail_db_path=gmail_db_path,
        provider=provider,
        model=model,
        verbose=False,
    )

    # Define app features specific questions
    questions = [
        # 1. Complete Flow of the Application
        ("User Journey Start to Finish",
         "Describe the complete user journey from start to finish. What happens step-by-step when a user first opens "
         "the application? Walk through: initial launch, onboarding (if any), main screen access, navigation patterns, "
         "and typical user workflows. Include what happens when the app starts, what screens are shown, and how users "
         "progress through the application. **Step-by-step user journey description - no code snippets.**"),

        ("Application Initialization Flow",
         "What happens when the application starts? Trace the initialization sequence: entry point execution, "
         "configuration loading, service initialization, database setup, authentication checks, and initial UI rendering. "
         "What components are initialized first, and in what order? **Describe initialization sequence with component references.**"),

        ("Navigation and Routing Flow",
         "How does navigation work in this application? What routing system is used? Describe the navigation structure: "
         "main routes, nested routes, route guards, deep linking, and how users move between different screens. "
         "What happens when a user clicks a navigation element? **Explain navigation architecture and flow patterns.**"),

        ("Data Loading and Synchronization Flow",
         "How does the application load and synchronize data? Describe the flow: when data is fetched, from where "
         "(local storage, remote API, cache), how it's processed, and how the UI updates. Include error handling "
         "and offline behavior. **Describe data flow patterns - no implementation code.**"),

        ("User Interaction Flow",
         "What happens when a user interacts with the application? Trace a typical interaction: user action (click, "
         "input, swipe), event handling, state updates, API calls (if any), UI updates, and feedback to the user. "
         "Describe the complete cycle from user action to UI response. **Explain interaction flow patterns.**"),

        ("Application Lifecycle Flow",
         "How does the application handle lifecycle events? Describe what happens during: app launch, backgrounding, "
         "foregrounding, app termination, and system events (low memory, network changes, etc.). How are resources "
         "managed throughout the lifecycle? **Describe lifecycle management patterns.**"),

        # 2. Feature Level Flow and Architecture (Major)
        ("Feature Identification and Categorization",
         "Identify all major features in the application. List each feature with a brief description. Categorize them "
         "by type: core features, secondary features, utility features, and administrative features. For each feature, "
         "identify where it's implemented in the codebase (directory/module references). **List all features with locations.**"),

        ("Feature Trigger Mechanisms",
         "For each major feature, explain what triggers it. How is a feature activated? Is it triggered by: user action, "
         "system event, scheduled task, API response, or other mechanism? Describe the entry points for each major feature. "
         "**Explain trigger mechanisms for each feature - reference code locations.**"),

        ("Frontend Feature Flow",
         "For each major feature, describe what happens in the frontend: which UI components are involved, what user "
         "interactions are possible, how the UI updates, and what visual feedback is provided. Trace the frontend flow "
         "from feature activation to completion. **Describe frontend flow for each major feature.**"),

        ("Backend API Calls for Features",
         "For each major feature that requires backend communication, describe: which API endpoints are called, what "
         "data is sent, what data is received, error handling, and response processing. Map each feature to its backend "
         "API interactions. **List API calls per feature with endpoint references.**"),

        ("Database Operations for Features",
         "For each major feature, describe the database operations: what data is read, what data is written, what tables "
         "or collections are involved, and what queries or operations are performed. Include transaction handling if applicable. "
         "**Map database operations to features - include table/collection references.**"),

        ("Feature Response Handling",
         "For each major feature, describe how responses are handled: success cases, error cases, loading states, "
         "validation, and user feedback. How does the application communicate results back to the user? "
         "**Explain response handling patterns for each feature.**"),

        ("Feature Dependencies and Integration",
         "How do features interact with each other? Describe feature dependencies: which features depend on others, "
         "shared services or utilities, data sharing between features, and integration points. Create a dependency map. "
         "**Map feature dependencies and integration points.**"),

        ("Feature State Management",
         "For each major feature, describe how state is managed: what state variables exist, how state is updated, "
         "where state is stored (local, global, component-level), and how state changes trigger UI updates. "
         "**Explain state management per feature.**"),

        # 3. Summary
        ("Features Summary Table",
         "Create a comprehensive summary table of all major features with columns: Feature Name, Purpose, Key Components "
         "(frontend/backend/database), Primary User Actions, Entry Point, and Dependencies. This table should serve as "
         "a quick reference for understanding all features at a glance. **Structured table format - master feature reference.**"),

        ("Feature Architecture Overview",
         "Provide an architectural overview of how features are organized: are features modular, how are they structured "
         "(by domain, by layer, by functionality), what patterns are used (feature modules, microservices, monolith), "
         "and how new features should be added. **Describe feature architecture and organization patterns.**"),

        ("Feature Implementation Patterns",
         "What patterns are consistently used across features? Identify common patterns for: feature structure, API "
         "communication, error handling, validation, state management, and UI updates. These patterns help developers "
         "understand how to implement new features consistently. **List implementation patterns with examples.**"),

        ("Feature Testing Strategy",
         "How are features tested? Describe the testing approach for features: unit tests, integration tests, E2E tests, "
         "and where test files are located. What testing patterns are used? How should new features be tested? "
         "**Explain feature testing strategy and patterns.**"),
    ]

    # Collect responses
    app_features_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": getattr(chatbot, "repo_info", {}).get('name', 'unknown'),
            "provider": provider,
            "model": getattr(chatbot, "model", None)
        },
        "sections": {
            "complete_flow": {},
            "feature_level_flow_architecture": {},
            "summary": {}
        }
    }

    # Map questions to sections
    section_mapping = {
        0: "complete_flow",
        1: "complete_flow",
        2: "complete_flow",
        3: "complete_flow",
        4: "complete_flow",
        5: "complete_flow",
        6: "feature_level_flow_architecture",
        7: "feature_level_flow_architecture",
        8: "feature_level_flow_architecture",
        9: "feature_level_flow_architecture",
        10: "feature_level_flow_architecture",
        11: "feature_level_flow_architecture",
        12: "feature_level_flow_architecture",
        13: "feature_level_flow_architecture",
        14: "summary",
        15: "summary",
        16: "summary",
        17: "summary",
    }

    total = len(questions)
    print(f"Asking {total} app features questions...\n")

    for idx, (key, question) in enumerate(questions, 1):
        print(f"[{idx}/{total}] {key}...")

        try:
            response = chatbot.chat(question)
            answer = response.get('answer') if isinstance(response, dict) else getattr(response, 'answer',
                                                                                       str(response))
            quality = response.get('context_quality', 1.0) if isinstance(response, dict) else getattr(response,
                                                                                                      'context_quality',
                                                                                                      1.0)

            section = section_mapping.get(idx - 1, "summary")
            app_features_data["sections"][section][key] = {
                "question": question,
                "answer": answer,
                "quality": quality
            }
        except Exception as e:
            print(f"Error: {e}")
            section = section_mapping.get(idx - 1, "summary")
            app_features_data["sections"][section][key] = {
                "question": question,
                "answer": f"Error: {str(e)}",
                "quality": 0.0
            }

    # Save to file
    output_dir = ONBOARDING_ROOT / "reading"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / f"onboarding_app_features.json"

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(app_features_data, f, indent=2, ensure_ascii=False)

    # Calculate success stats
    total_answers = sum(len(section) for section in app_features_data["sections"].values())
    successful_answers = sum(
        1 for section in app_features_data["sections"].values()
        for item in section.values()
        if not str(item.get('answer', '')).startswith('Error:')
    )


    return json_file


if __name__ == "__main__":
    GITHUB_DB_PATH = "../../../../data/VectorDB/multi_index"
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = None

    generate_app_features_data(GITHUB_DB_PATH, GMAIL_DB_PATH, PROVIDER, MODEL)

