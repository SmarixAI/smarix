"""
Simple Onboarding Data Generator
Single command to extract all onboarding info from existing RAG chatbot
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

    raise ImportError("Could not import RAGChatbot class")


RAGChatbot = _load_rag_chatbot_class()


def get_search_keywords_for_topic(topic_title: str) -> str:
    """
    Returns specific search keywords to find relevant technical chunks
    for abstract topics.
    """
    mapping = {
        "Welcome": "README.md overview introduction purpose main goal business value",
        "Main Features": "features capabilities user stories core functionality modules",
        "UI/UX": "frontend UI components css react html styling views routes navigation",
        "Authentication": "auth login security user role permission session jwt oauth guard",
        "Workflows": "workflow user journey process flow controller service logic",
        "Data Handling": "database schema model storage repository sql entity relationship",
        "Architecture": "architecture design pattern system structure diagrams flow backend frontend",
        "System Flow": "request response flow api gateway controller service sequence interaction",
        "Best Practices": "best practices standards conventions structure clean code refactoring",
        "Issues": "TODO FIXME bugs issues debt roadmap limitations",
        "Use Cases": "use case user scenario persona example usage application",
        "Tech Stack": "package.json requirements.txt pom.xml build.gradle Dockerfile technologies framework dependencies",
        "Languages": "language breakdown extension file types usage statistics",
        "Frameworks": "framework configuration settings config setup startup main application",
        "Database": "schema migration table sql ddl entity model db context",
        "Project Structure": "directory structure folder organization hierarchy layout",
        "Metrics": "statistics lines of code count complexity coverage metrics",
        "Testing": "test spec unit integration e2e testing suite coverage",
        "External Connections": "api integration external service http client endpoints webhook key",
    }

    # Fuzzy match title to keys
    for key, value in mapping.items():
        if key in topic_title:
            return value
    return "codebase overview"


def retrieve_context(chatbot, keywords: str, limit: int = 15) -> str:
    """
    Directly retrieves chunks from Vector DB to bypass strict chat filters.
    """
    print(f"   🔍 Searching context with keywords: '{keywords[:50]}...'")
    query_embedding = chatbot.get_query_embedding(keywords)

    chunks = []

    # Try 1: Direct Search
    if hasattr(chatbot.vector_db, "search"):
        chunks = chatbot.vector_db.search(query_embedding, top_k=limit)

    # Try 2: Specific Indices (Fallback or Augment)
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

    # Deduplicate based on content
    seen = set()
    unique_chunks = []
    for c in chunks:
        content = c.get("content") or c.get("text", "")
        if content not in seen:
            seen.add(content)
            unique_chunks.append(c)

    if not unique_chunks:
        return ""

    # Format context
    context_parts = []
    for c in unique_chunks[:limit]:
        path = c.get("metadata", {}).get("file_path", "unknown")
        content = c.get("content") or c.get("text", "")
        context_parts.append(f"File: {path}\n```\n{content[:1500]}\n```")

    return "\n\n".join(context_parts)


def parse_single_mcq_from_response(response_text: str) -> dict:
    """Parse a single MCQ question from chatbot's response"""
    question_pattern = r"###\s+Question\s+(\d+)\s+\(MCQ\s*-\s*(\w+)\)"
    match = re.search(question_pattern, response_text)

    # Simple fallback parsing logic
    if not match:
        # Look for explicit Answer marker
        parts = response_text.split("**Answer:**")
        if len(parts) < 2:
            return None

        q_text_raw = parts[0]
        ans_text_raw = parts[1]

        # Extract options
        options = {}
        q_lines = []
        for line in q_text_raw.split("\n"):
            opt_match = re.match(r"^([A-D])\.\s+(.+)$", line.strip())
            if opt_match:
                options[opt_match.group(1)] = opt_match.group(2)
            else:
                q_lines.append(line)

        # Extract answer
        ans_match = re.match(r"\s*([A-D])", ans_text_raw.strip())
        correct = ans_match.group(1) if ans_match else None

        if len(options) == 4 and correct:
            return {
                "question": " ".join(q_lines).strip(),
                "options": options,
                "correct_answer": correct,
                "explanation": ans_text_raw.replace(correct, "", 1).strip(" -"),
            }
        return None

    return None  # If we need complex regex, keep the original function logic


def generate_data_qna(
    reading_overview_data, chatbot, gmail_db_path=None, provider="openai", model=None
):
    """Generate MCQ questions for teaching_content items"""
    print("\n" + "=" * 80)
    print("GENERATING MCQ QUESTIONS FOR READING OVERVIEW")
    print("=" * 80 + "\n")

    sections = reading_overview_data.get("sections", {})
    data_section = sections.get("data", {})
    teaching_content = data_section.get("teaching_content", [])

    qna_list = []

    for idx, item_data in enumerate(teaching_content, 1):
        title = item_data.get("title", f"Item {idx}")
        content_text = item_data.get("content", "")

        if not content_text or str(content_text).startswith("Error:"):
            continue

        print(f"  [{idx}/{len(teaching_content)}] Generating MCQ for '{title}'...")

        mcq_prompt = f"""
        Based on this topic, generate ONE multiple-choice question (MCQ).
        
        TOPIC: {title}
        CONTENT: {content_text[:3000]}
        
        FORMAT:
        [Question Text]
        A. Option A
        B. Option B
        C. Option C
        D. Option D
        **Answer:** [Letter] - [Explanation]
        """

        try:
            # For MCQ, we can use the content we just generated as context, no need to search DB again
            response = chatbot.call_llm("You are a quiz generator.", mcq_prompt)

            mcq = parse_single_mcq_from_response(response)
            if mcq:
                mcq["subsection"] = title
                qna_list.append(mcq)
                print(f"    ✓ Generated MCQ")
            else:
                print(f"    ✗ Parse failed")

        except Exception as e:
            print(f"    ✗ Error: {e}")
            continue

    if qna_list:
        if "data" not in sections:
            sections["data"] = {}
        sections["data"]["qna"] = qna_list
        reading_overview_data["sections"] = sections

    return reading_overview_data


def generate_reading_overview(gmail_db_path=None, provider="openai", model=None):
    """Generate complete reading overview data using Context-First RAG"""

    print("Starting Reading Overview Data Generation (Context-First)...\n")

    print("Loading chatbot...")
    chatbot = RAGChatbot(
        vector_db_path=VECTOR_DB_PATH,
        gmail_db_path=gmail_db_path,
        provider=provider,
        model=model,
        verbose=False,
        disable_conversation_storage=True,
    )

    # Define questions with diagram instructions where needed
    questions = [
        (
            "Welcome: What Does This Application Do?",
            "As a new team member, start here: What is this application? What problem does it solve for users? "
            "**Focus on concepts, not code snippets.**",
        ),
        (
            "What Can Users Do? Main Features & Capabilities",
            "Walk me through all the features users can access. "
            "**Describe functionality conceptually.**",
        ),
        (
            "How Do Users Interact? UI/UX Overview",
            "Analyze the UI components. What screens exist? How do users navigate? "
            "**Infer the user journey from code structure.**",
        ),
        (
            "Who Can Access What? Authentication & Authorization",
            "Explain how authentication works. User roles? Login flow? "
            "**Conceptual explanation only.**",
        ),
        (
            "Day-to-Day User Journeys: Core Workflows",
            "Walk me through 2-3 typical user journeys step-by-step. "
            "**Explain workflows conceptually.**",
        ),
        (
            "How Is Data Handled? Storage & Management",
            "Help me understand the data layer: Models? Database? Caching? "
            "**Provide architecture explanation.**",
        ),
        (
            "How Is the Code Organized? Architecture & Patterns",
            "Give me the architectural overview: Patterns? Organization? Communication? "
            "**High-level architecture explanation.** [Image of application architecture diagram]",
        ),
        (
            "System Flow Diagram: How Everything Connects",
            "Describe the system flow. "
            "**IMPORTANT: Append the tag [Image of system flow diagram] at the end of your response.**",
        ),
        (
            "What Works Well? Strengths & Best Practices",
            "What architectural decisions are sound? Coding patterns? "
            "**Infer best practices.**",
        ),
        (
            "What Needs Attention? Known Issues & Roadmap",
            "Are there known bugs, technical debt, or TODOs? " "**Summarize issues.**",
        ),
        (
            "Who Uses This & Why? Use Cases & Scenarios",
            "Who uses this app? What problems are they solving? "
            "**Infer user personas.**",
        ),
        (
            "What Are We Built With? Complete Tech Stack",
            "List the complete technology stack: frameworks, DB, tools. "
            "**Technology overview only.**",
        ),
        (
            "Languages in Use: Breakdown & Purpose",
            "What programming languages are used and where? "
            "**Statistical breakdown.**",
        ),
        (
            "Frontend & Backend Frameworks: Configuration & Usage",
            "Detail the frameworks used. " "**Explain framework usage.**",
        ),
        (
            "Database Deep Dive: Schema & Relationships",
            "Explain the database setup and schema. "
            "**Schema definitions.** [Image of database schema ER diagram]",
        ),
        (
            "Where Does Everything Go? Project Structure",
            "Give me a directory-by-directory breakdown. "
            "**Directory tree and explanations.**",
        ),
        (
            "How Big Is This Project? Codebase Metrics",
            "Provide statistics: files, lines of code, modules. "
            "**Numbers and metrics only.**",
        ),
        (
            "How Do We Test? Testing Strategy & Coverage",
            "Explain the testing approach and frameworks. "
            "**Testing strategy explanation.**",
        ),
        (
            "External Connections: APIs & Third-Party Integrations",
            "List all integrations and API connections. " "**Conceptual overview.**",
        ),
    ]

    reading_overview_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": REPO_NAME,
            "provider": provider,
            "model": model,
        },
        "sections": {"data": {"teaching_content": []}},
    }

    total = len(questions)
    print(f"Asking {total} questions...\n")

    for idx, (key, question) in enumerate(questions, 1):
        print(f"[{idx}/{total}] {key}...")

        # 1. Get Search Keywords
        search_terms = get_search_keywords_for_topic(key)

        # 2. Retrieve Context (Raw)
        context = retrieve_context(chatbot, search_terms)

        if not context:
            print("   ⚠️ No specific context found. Using broad knowledge...")
            context = "No specific code chunks found. Answer based on general software engineering principles applied to the likely structure of this project."

        # 3. Generate Answer
        system_prompt = (
            "You are a Senior Technical Lead onboarding a new developer. "
            "Explain the codebase clearly using the provided context."
        )

        user_prompt = f"""
        QUESTION: {question}
        
        CONTEXT FROM REPO:
        {context[:20000]}
        
        INSTRUCTIONS:
        - Use ONLY the provided context if possible.
        - Be educational and welcoming.
        - If the context doesn't have the answer, state what you see based on the available files.
        - If a diagram tag is requested in the question, ensure it is included.
        """

        try:
            answer = chatbot.call_llm(system_prompt, user_prompt)

            reading_overview_data["sections"]["data"]["teaching_content"].append(
                {"title": key, "topic": question, "content": answer, "quality": 1.0}
            )
            print(f"   ✓ Generated response ({len(answer)} chars)")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            reading_overview_data["sections"]["data"]["teaching_content"].append(
                {
                    "title": key,
                    "topic": question,
                    "content": f"Error: {str(e)}",
                    "quality": 0.0,
                }
            )

    # Upload Draft to S3
    s3_key = (
        f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_project_overview.json"
    )

    try:
        s3_manager.upload_json(reading_overview_data, s3_key)
        print(f"\n✓ Draft Uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"\n❌ Failed to upload: {e}")
        raise

    # Generate MCQ
    reading_overview_data = generate_data_qna(
        reading_overview_data, chatbot, gmail_db_path, provider, model
    )

    # Upload Final
    try:
        s3_manager.upload_json(reading_overview_data, s3_key)
        print(
            f"✓ Final file with QNA uploaded to S3: s3://{s3_manager.bucket}/{s3_key}"
        )
    except Exception as e:
        print(f"❌ Failed to upload: {e}")
        raise

    return s3_key


if __name__ == "__main__":
    GMAIL_DB_PATH = None
    PROVIDER = "openai"
    MODEL = "gpt-4o-mini"

    generate_reading_overview(GMAIL_DB_PATH, PROVIDER, MODEL)
