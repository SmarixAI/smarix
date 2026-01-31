"""
Dev Setup Data Generator
Extracts comprehensive development setup, installation, and configuration information
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


def get_search_keywords_for_setup(topic: str) -> str:
    """
    Returns precise keywords to find relevant setup info.
    """
    mapping = {
        "Required Software": "prerequisites requirements tools install sdk jdk python node docker",
        "System Requirements": "os system requirements ram cpu disk windows macos linux",
        "Environment Prerequisites": "ide vscode plugins extensions editorconfig settings",
        "External Service": "api key secret aws azure firebase google cloud service account",
        "Cloning": "git clone repository setup init submodule",
        "Dependency Installation": "install dependencies npm install pip install flutter pub get bundle install",
        "Configuration Setup": "config .env example environment variables setup configuration",
        "Database Setup": "database setup migration seed schema db create init sql docker-compose",
        "Build": "build compile make gradle maven npm run build webpack",
        "Running": "run start serve dev debug launch execution",
        "Issues": "troubleshoot error common issues fix solution faq help",
        "Platform-Specific": "windows macos linux platform specific issues instructions",
        "Environment-Specific": "virtualenv venv conda docker container environment issue",
        "Version Compatibility": "compatibility version mismatch conflict dependency requirement",
        "Hello World": "hello world example sample test run verify minimal",
        "Quick Start": "quick start guide fast setup simple instruction",
        "Verification": "verify check validate test confirm setup success",
        "Git Workflow": "git flow workflow branch commit pr pull request",
        "Git Setup": "git config setup user email ssh key gpg",
        "Git Branching": "branching strategy master main develop feature release hotfix",
        "Git Commit": "commit message convention style guide contributing",
    }

    for key, value in mapping.items():
        if key in topic:
            return value
    return "setup installation guide"


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
        # Prefer chunks that look like instructions or config files
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


def generate_section_qna(dev_setup_data, chatbot):
    """
    Generate MCQ questions for each section using strict JSON format
    """
    print("\n" + "=" * 80)
    print("GENERATING MCQ QUESTIONS FOR SECTIONS")
    print("=" * 80 + "\n")

    sections = dev_setup_data.get("sections", {})
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
            You are a technical quiz generator. Generate ONE multiple-choice question (MCQ) based on the provided setup/installation content.
            
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
    return dev_setup_data


def generate_dev_setup_data(gmail_db_path=None, provider="openai", model=None):
    """Generate comprehensive development setup analysis data using Context-First RAG"""

    print("Starting Dev Setup Data Generation (Context-First)...\n")

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
        # 1. Pre-requisites
        (
            "Required Software and Tools",
            "List required software, tools, versions. "
            "**Comprehensive list of prerequisites.**",
        ),
        (
            "System Requirements",
            "List OS versions, RAM, disk space requirements. "
            "**List system requirements.**",
        ),
        (
            "Development Environment Prerequisites",
            "List IDE recommendations and plugins. " "**List dev env prerequisites.**",
        ),
        (
            "External Service Prerequisites",
            "List cloud services, API keys, accounts needed. "
            "**List external service setup.**",
        ),
        # 2. Installation Steps
        (
            "Repository Cloning and Initial Setup",
            "Instructions for cloning and initial setup. "
            "**Step-by-step cloning instructions.**",
        ),
        (
            "Dependency Installation",
            "Instructions for installing dependencies (npm, pip, pub). "
            "**Step-by-step dependency installation.**",
        ),
        (
            "Configuration Setup",
            "Instructions for environment variables and config files. "
            "**Step-by-step configuration.**",
        ),
        (
            "Database Setup and Migration",
            "Instructions for DB setup and migrations. "
            "**Step-by-step database setup.**",
        ),
        (
            "Build and Compilation",
            "Instructions for building the application. "
            "**Step-by-step build instructions.**",
        ),
        (
            "Running the Application",
            "Instructions for running locally. " "**Step-by-step run instructions.**",
        ),
        # 3. FAQs
        (
            "Common Setup Issues and Solutions",
            "Troubleshooting guide for common errors. " "**Troubleshooting guide.**",
        ),
        (
            "Platform-Specific Issues",
            "Issues specific to Windows, macOS, Linux. "
            "**Platform troubleshooting.**",
        ),
        (
            "Environment-Specific Problems",
            "Issues with Docker, virtualenvs, etc. " "**Environment troubleshooting.**",
        ),
        (
            "Version Compatibility Issues",
            "Dependency conflict resolution. " "**Version compatibility guide.**",
        ),
        # 4. Hello World Setup
        (
            "Minimal Setup Verification",
            "Simplest way to verify setup works. " "**Hello World example.**",
        ),
        (
            "Quick Start Guide",
            "Minimal path to get running quickly. " "**Quick start guide.**",
        ),
        (
            "Setup Verification Checklist",
            "Checklist to confirm setup is correct. " "**Verification checklist.**",
        ),
        # 5. Git Basics
        (
            "Git Workflow Overview",
            "Branching strategy and PR process. " "**Git workflow overview.**",
        ),
        (
            "Git Setup for Linux",
            "Git installation and config for Linux. " "**Linux Git setup.**",
        ),
        (
            "Git Setup for macOS",
            "Git installation and config for macOS. " "**macOS Git setup.**",
        ),
        (
            "Git Setup for Windows",
            "Git installation and config for Windows. " "**Windows Git setup.**",
        ),
        (
            "Git Branching Strategy",
            "Branch naming and management strategy. " "**Branching strategy.**",
        ),
        (
            "Git Commit and PR Guidelines",
            "Commit message and PR conventions. " "**Commit guidelines.**",
        ),
    ]

    dev_setup_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": getattr(chatbot, "repo_info", {}).get("name", "unknown"),
            "provider": provider,
            "model": getattr(chatbot, "model", None),
        },
        "sections": {
            "prerequisites": {"teaching_content": []},
            "installation_steps": {"teaching_content": []},
            "faqs": {"teaching_content": []},
            "hello_world_setup": {"teaching_content": []},
            "git_basics": {"teaching_content": []},
        },
    }

    # Map questions to sections
    section_mapping = {
        0: "prerequisites",
        1: "prerequisites",
        2: "prerequisites",
        3: "prerequisites",
        4: "installation_steps",
        5: "installation_steps",
        6: "installation_steps",
        7: "installation_steps",
        8: "installation_steps",
        9: "installation_steps",
        10: "faqs",
        11: "faqs",
        12: "faqs",
        13: "faqs",
        14: "hello_world_setup",
        15: "hello_world_setup",
        16: "hello_world_setup",
        17: "git_basics",
        18: "git_basics",
        19: "git_basics",
        20: "git_basics",
        21: "git_basics",
        22: "git_basics",
    }

    total = len(questions)
    print(f"Asking {total} dev setup questions...\n")

    for idx, (key, question) in enumerate(questions, 1):
        print(f"[{idx}/{total}] {key}...")

        # 1. Get Keywords
        keywords = get_search_keywords_for_setup(key)

        # 2. Retrieve Context (Raw)
        context = retrieve_context(chatbot, keywords)

        if not context:
            print("   ⚠️ No specific context found. Using broad knowledge...")
            context = "No specific setup instructions found in README or docs. Infer standard setup based on project type."

        # 3. Generate Answer
        system_prompt = (
            "You are a DevOps Engineer / Senior Developer. "
            "Explain the development setup clearly using the provided context."
        )

        user_prompt = f"""
        QUESTION: {question}
        
        CONTEXT FROM REPO:
        {context[:20000]}
        
        INSTRUCTIONS:
        - Use ONLY the provided context if possible (README, CONTRIBUTING, docs).
        - Be specific about commands and configuration values.
        - If instructions are missing, provide standard commands for the identified technology stack.
        - Assess if the user would be able to understand response better with the use of diagrams and trigger them.
        - You can insert a diagram by adding the 

[Image of X]
 tag where X is a contextually relevant and domain-specific query to fetch the diagram.
        - Place the image tag immediately before or after the relevant text without disrupting the flow of the response.
        """

        try:
            answer = chatbot.call_llm(system_prompt, user_prompt)

            # Insert diagram tags if relevant keywords are in the topic but not generated in the answer
            if "Git Workflow" in key and "[Image of" not in answer:
                answer += "\n\n[Image of git branching strategy diagram]"
            if "Git Branching" in key and "[Image of" not in answer:
                answer += "\n\n"

            section = section_mapping.get(idx - 1, "git_basics")
            dev_setup_data["sections"][section]["teaching_content"].append(
                {"title": key, "topic": question, "content": answer, "quality": 1.0}
            )
            print(f"   ✓ Generated response ({len(answer)} chars)")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            section = section_mapping.get(idx - 1, "git_basics")
            dev_setup_data["sections"][section]["teaching_content"].append(
                {
                    "title": key,
                    "topic": question,
                    "content": f"Error: {str(e)}",
                    "quality": 0.0,
                }
            )

    # Upload Draft to S3
    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_dev_setup.json"
    try:
        s3_manager.upload_json(dev_setup_data, s3_key)
        print(f"\n✓ Draft Uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"\n❌ Failed to upload: {e}")

    # Generate MCQ
    dev_setup_data = generate_section_qna(dev_setup_data, chatbot)

    # Upload Final
    try:
        s3_manager.upload_json(dev_setup_data, s3_key)
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

    generate_dev_setup_data(GMAIL_DB_PATH, PROVIDER, MODEL)