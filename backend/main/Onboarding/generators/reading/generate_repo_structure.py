"""
Repository Structure Data Generator - Improved for Reliable QnA & Context Retrieval
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

    raise ImportError("Could not import RAGChatbot class")


# Initialize as None, will be loaded on first use
RAGChatbot = None


def get_rag_chatbot_class():
    """Get RAGChatbot class, loading it if not already loaded."""
    global RAGChatbot
    if RAGChatbot is None:
        RAGChatbot = _load_rag_chatbot_class()
    return RAGChatbot


def get_search_keywords_for_structure(topic: str) -> str:
    """
    Returns precise keywords to find relevant structure info.
    """
    mapping = {
        "Root Directory": "root directory ls -la tree structure top-level files README LICENSE .gitignore",
        "Hierarchy": "directory tree structure organization hierarchy nesting depth recursive list",
        "Configuration": "config settings .env .yaml .json .xml .toml .ini setup build",
        "Asset": "assets resources images fonts icons public static data media",
        "Data Models": "models entities schemas domain data types interfaces struct class",
        "Views": "views screens pages components widgets ui layout template",
        "Business Logic": "services controllers providers bloc redux store actions logic usecases",
        "State Management": "state store provider context bloc riverpod redux mobx",
        "Utilities": "utils helpers common shared lib core extensions constants",
        "Feature": "features modules components domains functional areas organization",
        "Boundaries": "dependencies imports architecture layers boundaries communication",
        "Cross-cutting": "auth logging error handling networking localization theme analytics",
        "File Naming": "file naming convention pattern prefix suffix extension case",
        "Directory Naming": "directory folder naming convention structure organization",
        "Code Naming": "class function variable constant naming style guide convention",
        "Critical": "main entry point app start important core kernel critical",
        "Patterns": "architecture design patterns mvc mvvm clean architecture layered",
        "Special": "generated build tools scripts bin docs examples migration seeds",
        "Navigation": "import export require include navigation routing paths",
        "Best Practices": "structure organization clean code separation concerns modularity",
    }

    # Fuzzy match
    for key, value in mapping.items():
        if key in topic:
            return value
    return "repository structure"


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
        # Prefer chunks that look like file lists or directory structures
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


def generate_section_qna(repo_structure_data, chatbot):
    """
    Generate MCQ questions for each section using strict JSON format
    """
    print("\n" + "=" * 80)
    print("GENERATING MCQ QUESTIONS FOR SECTIONS")
    print("=" * 80 + "\n")

    sections = repo_structure_data.get("sections", {})
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
            You are a technical quiz generator. Generate ONE multiple-choice question (MCQ) based on the provided repository structure content.
            
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
    return repo_structure_data


def generate_repo_structure_data(gmail_db_path=None, provider="openai", model=None):
    """Generate comprehensive repository structure analysis data using Context-First RAG"""

    print("Starting Repository Structure Data Generation (Context-First)...\n")

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
        # 1. Complete Repository Structure
        (
            "Root Directory Overview",
            "List top-level directories/files and their purpose. "
            "**Provide directory tree structure.**",
        ),
        (
            "Complete Directory Hierarchy",
            "Create a full directory map of src/lib. " "**Full directory tree.**",
        ),
        (
            "Key Configuration Files Location",
            "List all config files (build, env, ci/cd) with paths. "
            "**List config files.**",
        ),
        (
            "Asset and Resource Organization",
            "Locate assets folders (images, fonts, data). "
            "**Map asset organization.**",
        ),
        # 2. Model/Module-wise Structure
        (
            "Data Models Organization",
            "List all data model files and their locations. " "**List model files.**",
        ),
        (
            "Views and UI Components Structure",
            "Identify UI directories (screens, components). "
            "**Map UI organization.**",
        ),
        (
            "Business Logic and Services Organization",
            "Locate services, controllers, providers. " "**Describe logic layer.**",
        ),
        (
            "State Management Structure",
            "Identify state management files/folders. " "**Map state management.**",
        ),
        (
            "Utilities and Shared Code Structure",
            "Find utils, helpers, shared folders. " "**List utility organization.**",
        ),
        # 3. Feature-level Structure
        (
            "Feature-based Organization",
            "Analyze if code is organized by feature. " "**Identify features.**",
        ),
        (
            "Feature Module Boundaries",
            "Describe boundaries and dependencies between features. "
            "**Map feature boundaries.**",
        ),
        (
            "Cross-cutting Concerns Organization",
            "Where are auth, logging, error handling located? "
            "**Map cross-cutting concerns.**",
        ),
        # 4. Naming Conventions
        (
            "File Naming Conventions",
            "Analyze file naming patterns (snake_case, suffixes). "
            "**List file naming conventions.**",
        ),
        (
            "Directory Naming Conventions",
            "Analyze directory naming patterns. " "**Document directory naming.**",
        ),
        (
            "Code Naming Conventions",
            "Analyze class/function naming patterns. "
            "**List code naming conventions.**",
        ),
        # 5. Important Notes
        (
            "Critical Directories and Files",
            "Rank the most important directories for new devs. "
            "**Prioritized list.**",
        ),
        (
            "Code Organization Patterns",
            "Identify the architectural pattern (MVC, Clean, Layered). "
            "**Describe pattern.** [Image of application architecture diagram]",
        ),
        (
            "Special Directories and Their Purposes",
            "Identify generated, script, or doc directories. "
            "**List special directories.**",
        ),
        (
            "Navigation and Import Patterns",
            "Analyze import styles and navigation structure. " "**Document patterns.**",
        ),
        (
            "Structure Best Practices and Issues",
            "Critique the structure: strengths vs issues (nesting, mixed concerns). "
            "**Critical assessment.**",
        ),
    ]

    repo_structure_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": getattr(chatbot, "repo_info", {}).get("name", "unknown"),
            "provider": provider,
            "model": getattr(chatbot, "model", None),
        },
        "sections": {
            "complete_structure": {"teaching_content": []},
            "model_module_structure": {"teaching_content": []},
            "feature_level_structure": {"teaching_content": []},
            "naming_conventions": {"teaching_content": []},
            "important_notes": {"teaching_content": []},
        },
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

        # 1. Get Keywords
        keywords = get_search_keywords_for_structure(key)

        # 2. Retrieve Context (Raw)
        context = retrieve_context(chatbot, keywords)

        if not context:
            print("   ⚠️ No specific context found. Using broad knowledge...")
            context = "No specific directory structure info found. Infer based on standard project conventions."

        # 3. Generate Answer
        system_prompt = (
            "You are a Senior Software Architect. "
            "Analyze the repository structure based on the provided file lists and code."
        )

        user_prompt = f"""
        QUESTION: {question}
        
        CONTEXT FROM REPO:
        {context[:20000]}
        
        INSTRUCTIONS:
        - Analyze the context to answer the question.
        - Be specific about file paths and directory names.
        - Use tree view formatting for directories where helpful.
        - If an image tag is requested, ensure it is included.
        """

        try:
            answer = chatbot.call_llm(system_prompt, user_prompt)

            # Helper to add image tag if missed
            if "Patterns" in key and "[Image of" not in answer:
                answer += "\n\n[Image of application architecture diagram]\n"

            section = section_mapping.get(idx - 1, "important_notes")
            repo_structure_data["sections"][section]["teaching_content"].append(
                {"title": key, "topic": question, "content": answer, "quality": 1.0}
            )
            print(f"   ✓ Generated response ({len(answer)} chars)")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            section = section_mapping.get(idx - 1, "important_notes")
            repo_structure_data["sections"][section]["teaching_content"].append(
                {
                    "title": key,
                    "topic": question,
                    "content": f"Error: {str(e)}",
                    "quality": 0.0,
                }
            )

    # Upload Draft to S3
    s3_key = (
        f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_repo_structure.json"
    )
    try:
        s3_manager.upload_json(repo_structure_data, s3_key)
        print(f"\n✓ Draft Uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"\n❌ Failed to upload: {e}")

    # Generate MCQ
    repo_structure_data = generate_section_qna(repo_structure_data, chatbot)

    # Upload Final
    try:
        s3_manager.upload_json(repo_structure_data, s3_key)
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

    generate_repo_structure_data(GMAIL_DB_PATH, PROVIDER, MODEL)
