"""
Tech Stack Data Generator - Improved for Better RAG Retrieval & Reliable QnA
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

    raise ImportError("Could not import RAGChatbot class")


# Initialize as None, will be loaded on first use
RAGChatbot = None


def get_rag_chatbot_class():
    """Get RAGChatbot class, loading it if not already loaded."""
    global RAGChatbot
    if RAGChatbot is None:
        RAGChatbot = _load_rag_chatbot_class()
    return RAGChatbot


def get_search_keywords_for_tech(topic: str) -> str:
    """
    Returns precise keywords to find relevant config/code files for tech stack analysis.
    """
    mapping = {
        "Languages": "extension file types .py .js .ts .java .kt .swift .dart .go .rs .rb .php statistics",
        "Dependencies": "package.json pubspec.yaml requirements.txt pom.xml build.gradle go.mod Cargo.toml Gemfile dependencies",
        "Frameworks": "framework import react flutter angular vue django flask spring express rails laravel",
        "Build Tools": "CMakeLists.txt Makefile build.gradle webpack vite tsconfig babel rollup gradle maven",
        "Application Type": "main entry point index app startup initialization platform mobile web desktop",
        "Data Storage": "database sqlite postgresql mysql mongodb redis firebase realm hive sharedpreferences schema model",
        "Networking": "http dio axios fetch retrofit okhttp requests api endpoint graphql websocket client",
        "State Management": "state management provider riverpod bloc redux mobx getx context vuex pinia ngrx recoil",
        "UI Layer": "ui widget component view layout css html xml swiftui jetpack compose styling",
        "Directory Structure": "directory structure folder lib src app components services models utils",
        "Platform": "android ios web windows linux macos native configuration manifest plist",
        "Testing": "test spec unit integration e2e testing framework jest mocha pytest junit",
        "Automation": "ci cd github actions workflow docker jenkins circleci script build deploy",
        "Ecosystem": "ecosystem stack technology platform language environment coherence",
        "Cross-Platform": "cross-platform multi-platform shared code specific implementation",
        "Versions": "version sdk constraint engine minimum requirement compatibility",
        "Prerequisites": "install setup prerequisite sdk runtime tool env environment",
        "Maturity": "deprecated outdated legacy maintenance support update upgrade",
    }

    # Fuzzy match
    for key, value in mapping.items():
        if key in topic:
            return value
    return "technology configuration"


def retrieve_context(chatbot, keywords: str, limit: int = 15) -> str:
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
        for idx in ["code", "github"]:
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


def generate_section_qna(tech_stack_data, chatbot):
    """
    Generate MCQ questions for each section in tech stack data using strict JSON format
    """
    print("\n" + "=" * 80)
    print("GENERATING MCQ QUESTIONS FOR TECH STACK SECTIONS")
    print("=" * 80 + "\n")

    sections = tech_stack_data.get("sections", {})
    total_qnas = 0

    for section_name, section_content in sections.items():
        if not isinstance(section_content, dict):
            continue

        teaching_content = section_content.get("teaching_content", [])
        if not teaching_content:
            continue

        qna_list = []

        # Only generate a max of 2 questions per section to save time/tokens if list is huge
        # But for tech stack usually we have ~4 items per section, so iterating all is fine.
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
            You are a technical quiz generator. Generate ONE multiple-choice question (MCQ) based on the provided technical content.
            
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
                print(f"    ✗ Error calling LLM: {e}")

        if qna_list:
            sections[section_name]["qna"] = qna_list
            total_qnas += len(qna_list)

    print(f"\n✓ Total MCQ questions generated: {total_qnas}")
    return tech_stack_data


def generate_tech_stack_data(gmail_db_path=None, provider="openai", model=None):
    """Generate comprehensive tech stack analysis data using Context-First RAG"""

    print("Starting Tech Stack Data Generation (Context-First)...\n")

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
        # 1. Complete Tech Stack Overview
        (
            "Programming Languages Used",
            "List EVERY programming language found in the codebase. Count files/percentage. "
            "**List all languages with file counts.**",
        ),
        (
            "Package Dependencies",
            "Extract TOP 15-20 dependencies from package.json, pubspec.yaml etc. "
            "**List package names with purposes.**",
        ),
        (
            "Frameworks and Major Libraries",
            "List the PRIMARY frameworks (Flutter, React, etc.) and major libraries. "
            "**List names only.**",
        ),
        (
            "Build Tools and Compilation",
            "List build systems, bundlers, transpilers. " "**List build toolchain.**",
        ),
        # 2. Application Flow wrt Tech Stacks
        (
            "Application Type and Entry Point",
            "Is this mobile, web, backend? Identify entry point file. "
            "**Describe app type and startup.**",
        ),
        (
            "Data Storage Technologies",
            "List databases, local storage, ORMs found. " "**List storage tech.**",
        ),
        (
            "Networking and API Communication",
            "List HTTP clients, GraphQL, WebSocket libraries. "
            "**List networking libs.**",
        ),
        (
            "State Management Pattern",
            "Identify state management libraries (Provider, Redux, etc). "
            "**Identify pattern.**",
        ),
        (
            "UI Layer Technologies",
            "List UI frameworks (Flutter widgets, React components) and styling. "
            "**List UI tech.**",
        ),
        # 3. Module-wise Tech Stack
        (
            "Project Directory Structure",
            "List main directories and explain contents. "
            "**Describe directory organization.**",
        ),
        (
            "Platform-Specific Technologies",
            "List native technologies in android/ios/web folders. "
            "**List platform-specific tech.**",
        ),
        (
            "Testing Infrastructure",
            "List testing frameworks and types of tests found. "
            "**List testing tech.**",
        ),
        (
            "Development Automation",
            "List CI/CD tools, scripts, Docker. " "**List automation tools.**",
        ),
        # 4. Technology Rationale
        (
            "Technology Ecosystem",
            "Identify the primary ecosystem (e.g. Flutter/Dart, Node.js). "
            "**Identify dominant ecosystem.**",
        ),
        (
            "Cross-Platform Strategy",
            "How is cross-platform handled? Shared code vs specific? "
            "**Describe strategy.**",
        ),
        # 5. Reference/Summary
        (
            "Complete Technology Inventory",
            "Create a comprehensive table: Name | Type | Purpose | Reference. "
            "**Structured table format.**",
        ),
        (
            "Version Requirements",
            "Extract minimum SDK/framework versions from config files. "
            "**Extract version numbers.**",
        ),
        (
            "Developer Prerequisites",
            "List required installs (SDKs, tools) in priority order. "
            "**Prioritized setup list.**",
        ),
        (
            "Technology Maturity and Updates",
            "Assess stack maturity, deprecated packages, legacy code. "
            "**Critical assessment.**",
        ),
    ]

    tech_stack_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": getattr(chatbot, "repo_info", {}).get("name", "unknown"),
            "provider": provider,
            "model": getattr(chatbot, "model", None),
        },
        "sections": {
            "complete_tech_stack_overview": {"teaching_content": []},
            "application_flow_tech_stack": {"teaching_content": []},
            "module_wise_tech_breakdown": {"teaching_content": []},
            "technology_rationale": {"teaching_content": []},
            "reference_summary": {"teaching_content": []},
        },
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

        # 1. Get Keywords
        keywords = get_search_keywords_for_tech(key)

        # 2. Retrieve Context (Raw)
        context = retrieve_context(chatbot, keywords)

        if not context:
            print("   ⚠️ No specific context found. Using broad knowledge...")
            context = "No specific configuration files found. Infer based on standard project structures."

        # 3. Generate Answer
        system_prompt = (
            "You are a Senior Software Architect. "
            "Analyze the tech stack based on the provided configuration files and code."
        )

        user_prompt = f"""
        QUESTION: {question}
        
        CONTEXT FROM REPO:
        {context[:20000]}
        
        INSTRUCTIONS:
        - Analyze the context to answer the question.
        - Be specific about versions and library names if visible.
        - If files are missing, state what is likely used based on file extensions.
        """

        try:
            answer = chatbot.call_llm(system_prompt, user_prompt)

            section = section_mapping.get(idx - 1, "reference_summary")
            tech_stack_data["sections"][section]["teaching_content"].append(
                {"title": key, "topic": question, "content": answer, "quality": 1.0}
            )
            print(f"   ✓ Generated response ({len(answer)} chars)")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            section = section_mapping.get(idx - 1, "reference_summary")
            tech_stack_data["sections"][section]["teaching_content"].append(
                {
                    "title": key,
                    "topic": question,
                    "content": f"Error: {str(e)}",
                    "quality": 0.0,
                }
            )

    # Upload Draft to S3
    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_tech_stack.json"
    try:
        s3_manager.upload_json(tech_stack_data, s3_key)
        print(f"\n✓ Draft Uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"\n❌ Failed to upload: {e}")

    # Generate MCQ
    tech_stack_data = generate_section_qna(tech_stack_data, chatbot)

    # Upload Final
    try:
        s3_manager.upload_json(tech_stack_data, s3_key)
        print(
            f"✓ Final file with QNA uploaded to S3: s3://{s3_manager.bucket}/{s3_key}"
        )
    except Exception as e:
        print(f"❌ Failed to upload updated file: {e}")
        raise

    return s3_key


if __name__ == "__main__":
    GMAIL_DB_PATH = None
    PROVIDER = "openai"
    MODEL = "gpt-4o-mini"

    generate_tech_stack_data(GMAIL_DB_PATH, PROVIDER, MODEL)
