"""
App Features Data Generator
Extracts comprehensive application features, flows, and architecture information
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


# Initialize as None, will be loaded on first use
RAGChatbot = None


def get_rag_chatbot_class():
    """Get RAGChatbot class, loading it if not already loaded."""
    global RAGChatbot
    if RAGChatbot is None:
        RAGChatbot = _load_rag_chatbot_class()
    return RAGChatbot


def get_search_keywords_for_features(topic: str) -> str:
    """
    Returns precise keywords to find relevant feature/flow info.
    """
    mapping = {
        "User Journey": "main entry point navigation routes flow user onboarding home screen login",
        "Initialization": "startup init main application didFinishLaunching bootstrap configure setup",
        "Navigation": "router navigation routes deep link navigator push pop go_router react-router",
        "Data Loading": "api service repository fetch load data sync http client cache local storage",
        "User Interaction": "onPressed onClick event handler listener controller interaction input form",
        "Lifecycle": "lifecycle onResume onPause background terminate dispose destroy mount unmount",
        "Feature Identification": "feature modules domains capabilities core functionality exports",
        "Trigger": "event bus stream notification trigger action dispatch invoke",
        "Frontend": "view screen widget component ui state render build layout template",
        "Backend API": "api endpoint rest graphql client http request response fetch axios dio",
        "Database": "query insert update delete sql schema entity model collection document",
        "Response Handling": "error handler try catch success response status code validation snackbar toast alert",
        "Dependencies": "dependency injection provider import export require module",
        "State": "state store bloc provider context redux riverpod mobx signal observable",
        "Summary": "overview summary features list capabilities map",
        "Architecture": "architecture pattern design structure clean hexagonal onion mvc mvvm",
        "Patterns": "pattern factory builder observer singleton strategy adapter decorator",
        "Testing": "test unit integration e2e spec suite mock spy stub",
    }

    for key, value in mapping.items():
        if key in topic:
            return value
    return "application features"


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
        for idx in ["code", "github", "docs"]:
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


def generate_section_qna(app_features_data, chatbot):
    """
    Generate MCQ questions for each section using strict JSON format
    """
    print("\n" + "=" * 80)
    print("GENERATING MCQ QUESTIONS FOR SECTIONS")
    print("=" * 80 + "\n")

    sections = app_features_data.get("sections", {})
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
            if (
                not content
                or str(content).startswith("Error:")
                or len(str(content)) < 50
            ):
                continue

            print(f"  [{idx}/{len(teaching_content)}] Generating MCQ for '{title}'...")

            mcq_prompt = f"""
            You are a technical quiz generator. Generate ONE multiple-choice question (MCQ) based on the provided application feature/flow.
            
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
                    mcq_prompt,
                )

                mcq = parse_json_mcq(response)

                if mcq:
                    mcq["subsection"] = title
                    qna_list.append(mcq)
                    print(f"    ✓ Generated MCQ: {mcq['question'][:50]}...")
                else:
                    print(
                        f"    ✗ Failed to parse MCQ. Raw response preview: {response[:100]}..."
                    )
            except Exception as e:
                print(f"    ✗ Error: {e}")

        if qna_list:
            sections[section_name]["qna"] = qna_list
            total_qnas += len(qna_list)

    print(f"\n✓ Total MCQ questions generated: {total_qnas}")
    return app_features_data


def generate_app_features_data(
    db_path, gmail_db_path=None, provider="openai", model=None
):
    """Generate comprehensive application features analysis data using Context-First RAG"""

    print("Starting App Features Data Generation (Context-First)...\n")

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
        # 1. Complete Flow of the Application
        (
            "User Journey Start to Finish",
            "Describe the complete user journey from start to finish. "
            "**Step-by-step user journey description.** ",
        ),
        (
            "Application Initialization Flow",
            "Trace the initialization sequence: entry point, config, auth checks. "
            "**Describe initialization sequence.**",
        ),
        (
            "Navigation and Routing Flow",
            "How does navigation work? Describe routes and deep linking. "
            "**Explain navigation architecture.**",
        ),
        (
            "Data Loading and Synchronization Flow",
            "How does the app load and sync data? Local vs Remote. "
            "**Describe data flow patterns.**",
        ),
        (
            "User Interaction Flow",
            "Trace a typical interaction: action -> event -> state -> UI. "
            "**Explain interaction flow.**",
        ),
        (
            "Application Lifecycle Flow",
            "How are lifecycle events handled (background, terminate)? "
            "**Describe lifecycle management.**",
        ),
        # 2. Feature Level Flow and Architecture (Major)
        (
            "Feature Identification and Categorization",
            "Identify all major features. Core vs Secondary. "
            "**List all features with locations.**",
        ),
        (
            "Feature Trigger Mechanisms",
            "What triggers each feature? User action or system event? "
            "**Explain trigger mechanisms.**",
        ),
        (
            "Frontend Feature Flow",
            "Describe the frontend flow for major features. "
            "**Describe frontend flow.**",
        ),
        (
            "Backend API Calls for Features",
            "Map features to their backend API endpoints. "
            "**List API calls per feature.**",
        ),
        (
            "Database Operations for Features",
            "Describe database operations for major features. "
            "**Map DB operations to features.**",
        ),
        (
            "Feature Response Handling",
            "How are success/error responses handled per feature? "
            "**Explain response handling.**",
        ),
        (
            "Feature Dependencies and Integration",
            "How do features interact? Shared services? "
            "**Map feature dependencies.**",
        ),
        (
            "Feature State Management",
            "How is state managed within features? Local vs Global. "
            "**Explain state management.**",
        ),
        # 3. Summary
        (
            "Features Summary Table",
            "Create a table: Feature Name | Purpose | Components | Dependencies. "
            "**Structured table format.**",
        ),
        (
            "Feature Architecture Overview",
            "Provide an architectural overview of feature organization. "
            "**Describe feature architecture.** [Image of feature architecture diagram]",
        ),
        (
            "Feature Implementation Patterns",
            "Identify consistent patterns used across features. "
            "**List implementation patterns.**",
        ),
        (
            "Feature Testing Strategy",
            "How are features tested? Unit/Integration/E2E. "
            "**Explain testing strategy.**",
        ),
    ]

    app_features_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": getattr(chatbot, "repo_info", {}).get("name", "unknown"),
            "provider": provider,
            "model": getattr(chatbot, "model", None),
        },
        "sections": {
            "complete_flow": {"teaching_content": []},
            "feature_level_flow_architecture": {"teaching_content": []},
            "summary": {"teaching_content": []},
        },
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

        # 1. Get Keywords
        keywords = get_search_keywords_for_features(key)

        # 2. Retrieve Context (Raw)
        context = retrieve_context(chatbot, keywords)

        if not context:
            print("   ⚠️ No specific context found. Using broad knowledge...")
            context = "No specific feature implementation details found in code. Infer based on standard application patterns."

        # 3. Generate Answer
        system_prompt = (
            "You are a Senior Software Architect. "
            "Analyze the application features and flows based on the provided code."
        )

        user_prompt = f"""
        QUESTION: {question}
        
        CONTEXT FROM REPO:
        {context[:20000]}
        
        INSTRUCTIONS:
        - Analyze the context to answer the question.
        - Be specific about component names and file paths.
        - Describe flows logically (step 1, step 2...).
        - If an image tag is requested, ensure it is included.
        - Assess if the user would be able to understand response better with the use of diagrams and trigger them.
        - You can insert a diagram by adding the 

[Image of X]
 tag where X is a contextually relevant and domain-specific query to fetch the diagram.
        - Place the image tag immediately before or after the relevant text without disrupting the flow of the response.
        """

        try:
            answer = chatbot.call_llm(system_prompt, user_prompt)

            # Helper to add image tag if missed
            if "User Journey" in key and "[Image of" not in answer:
                answer += "\n\n"
            if "Architecture Overview" in key and "[Image of" not in answer:
                answer += "\n\n[Image of application architecture diagram]"

            section = section_mapping.get(idx - 1, "summary")
            app_features_data["sections"][section]["teaching_content"].append(
                {"title": key, "topic": question, "content": answer, "quality": 1.0}
            )
            print(f"   ✓ Generated response ({len(answer)} chars)")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            section = section_mapping.get(idx - 1, "summary")
            app_features_data["sections"][section]["teaching_content"].append(
                {
                    "title": key,
                    "topic": question,
                    "content": f"Error: {str(e)}",
                    "quality": 0.0,
                }
            )

    # Upload Draft to S3
    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_app_features.json"
    try:
        s3_manager.upload_json(app_features_data, s3_key)
        print(f"\n✓ Draft Uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"\n❌ Failed to upload: {e}")

    # Generate MCQ
    app_features_data = generate_section_qna(app_features_data, chatbot)

    # Upload Final
    try:
        s3_manager.upload_json(app_features_data, s3_key)
        print(
            f"✓ Final file with QNA uploaded to S3: s3://{s3_manager.bucket}/{s3_key}"
        )
    except Exception as e:
        print(f"❌ Failed to upload updated file: {e}")
        raise

    return s3_key


def add_qna_to_existing_app_features(
    json_file_path: str = None,
    gmail_db_path: str = None,
    provider: str = "openai",
    model: str = None,
) -> str:
    """
    Add MCQ QNA questions to an existing app features JSON file
    """
    print("╔" + "═" * 78 + "╗")
    print("║" + " ADD QNA TO EXISTING APP FEATURES ".center(78) + "║")
    print("╚" + "═" * 78 + "╝\n")

    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_app_features.json"

    print(f"📄 Loading existing app features from S3...")

    try:
        app_features_data = s3_manager.download_json(s3_key)
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

    app_features_data = generate_section_qna(app_features_data, chatbot)

    try:
        s3_manager.upload_json(app_features_data, s3_key)
        print(f"✓  Updated file uploaded to S3: s3://{s3_manager.bucket}/{s3_key}\n")
    except Exception as e:
        print(f"✗  Failed to upload to S3: {e}")
        return None

    return s3_key


if __name__ == "__main__":
    # Use repo context to get correct vector DB path (new structure: data/VectorDB/{owner}/{repo_name})
    GITHUB_DB_PATH = str(VECTOR_DB_PATH)
    GMAIL_DB_PATH = None
    PROVIDER = "openai"
    MODEL = "gpt-4o-mini"

    # Uncomment to just add QNA to existing file:
    # add_qna_to_existing_app_features(gmail_db_path=GMAIL_DB_PATH, provider=PROVIDER, model=MODEL)

    # Generate complete app features with QNA:
    generate_app_features_data(GITHUB_DB_PATH, GMAIL_DB_PATH, PROVIDER, MODEL)
