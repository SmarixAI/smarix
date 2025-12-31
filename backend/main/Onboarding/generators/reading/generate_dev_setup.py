"""
Dev Setup Data Generator
Extracts comprehensive development setup, installation, and configuration information
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


def generate_dev_setup_data(db_path, gmail_db_path=None, provider='openai', model=None):
    """Generate comprehensive development setup analysis data"""

    print("Starting Dev Setup Data Generation...\n")

    # Initialize chatbot
    print("Loading chatbot...")
    chatbot = RAGChatbot(
        vector_db_path=db_path,
        gmail_db_path=gmail_db_path,
        provider=provider,
        model=model,
        verbose=False
    )

    # Define dev setup specific questions
    questions = [
        # 1. Pre-requisites
        ("Required Software and Tools",
         "What are all the prerequisites needed before setting up this project? List required software, tools, versions, "
         "and system requirements. Include: programming languages and their versions, frameworks, build tools, "
         "package managers, databases, development tools (IDEs, editors), and any other dependencies. "
         "**Comprehensive list of prerequisites with version requirements.**"),

        ("System Requirements",
         "What are the system requirements for development? Include: operating system versions (Windows, macOS, Linux), "
         "minimum RAM, disk space, processor requirements, and any platform-specific requirements. "
         "**List system requirements for each supported platform.**"),

        ("Development Environment Prerequisites",
         "What development environment setup is required? Include: IDE or editor recommendations, required extensions "
         "or plugins, development server requirements, and any environment-specific configurations. "
         "**List development environment prerequisites.**"),

        ("External Service Prerequisites",
         "What external services or accounts are needed? Include: cloud services, API keys, database instances, "
         "authentication providers, and any third-party services that must be configured before development. "
         "**List external service prerequisites and setup requirements.**"),

        # 2. Installation Steps
        ("Repository Cloning and Initial Setup",
         "Provide step-by-step installation instructions from cloning the repository to running the application locally. "
         "Start with: how to clone the repository, which branch to use, and initial repository setup steps. "
         "**Step-by-step cloning and initial setup instructions.**"),

        ("Dependency Installation",
         "How are dependencies installed? Provide detailed steps for: installing package dependencies, setting up "
         "virtual environments (if applicable), installing global tools, and configuring package managers. "
         "Include all commands needed. **Step-by-step dependency installation instructions with commands.**"),

        ("Configuration Setup",
         "What configuration is needed? Describe: environment variable setup, configuration file creation, "
         "API key configuration, database connection setup, and any other configuration steps. Include where to find "
         "example configuration files. **Step-by-step configuration instructions.**"),

        ("Database Setup and Migration",
         "How is the database set up? Provide steps for: database installation, schema creation, running migrations, "
         "seeding initial data, and database connection configuration. **Step-by-step database setup instructions.**"),

        ("Build and Compilation",
         "How is the application built? Provide steps for: compiling the code, building assets, running build scripts, "
         "and preparing the application for execution. Include build commands and expected outputs. "
         "**Step-by-step build instructions with commands.**"),

        ("Running the Application",
         "How do you run the application locally? Provide steps for: starting development servers, running the "
         "application, accessing the application, and verifying it's working correctly. Include all necessary commands. "
         "**Step-by-step instructions for running the application.**"),

        # 3. FAQs
        ("Common Setup Issues and Solutions",
         "What are common setup issues developers face and their solutions? List troubleshooting steps for typical errors. "
         "Include: dependency installation errors, configuration issues, database connection problems, build failures, "
         "and runtime errors. For each issue, provide: symptoms, common causes, and step-by-step solutions. "
         "**Comprehensive troubleshooting guide with solutions.**"),

        ("Platform-Specific Issues",
         "What platform-specific issues might developers encounter? List issues specific to: Windows, macOS, and Linux. "
         "Include: path issues, permission problems, platform-specific dependency issues, and their solutions. "
         "**Platform-specific troubleshooting guide.**"),

        ("Environment-Specific Problems",
         "What environment-specific problems occur? Include: virtual environment issues, Docker problems, "
         "containerization issues, and cloud development environment problems. Provide solutions for each. "
         "**Environment-specific troubleshooting guide.**"),

        ("Version Compatibility Issues",
         "What version compatibility issues might arise? Include: dependency version conflicts, framework version "
         "mismatches, and tool version incompatibilities. How are these resolved? **Version compatibility troubleshooting.**"),

        # 4. Hello World Setup
        ("Minimal Setup Verification",
         "How do I create a minimal 'Hello World' example to verify the setup works? What's the simplest way to test "
         "the development environment? Provide: a minimal code example, how to run it, and what output to expect. "
         "**Simple Hello World example with verification steps.**"),

        ("Quick Start Guide",
         "What's the quickest way to get started? Provide a minimal setup path that gets a developer running the "
         "application in the shortest time. Include only essential steps, skipping optional configurations. "
         "**Minimal quick start guide.**"),

        ("Setup Verification Checklist",
         "How do I verify that the setup is correct? Provide a checklist of: verification steps, test commands to run, "
         "expected outputs, and how to confirm each component is working. **Setup verification checklist.**"),

        # 5. Git Basics based on env/OS
        ("Git Workflow Overview",
         "What are the Git commands and workflows for this project? Describe: branching strategy, commit conventions, "
         "pull request process, and typical Git workflow. **Git workflow and conventions overview.**"),

        ("Git Setup for Linux",
         "Provide Git setup instructions for Linux. Include: Git installation, configuration, SSH key setup, "
         "repository cloning, and common Git commands. Include Linux-specific considerations. "
         "**Linux-specific Git setup and commands.**"),

        ("Git Setup for macOS",
         "Provide Git setup instructions for macOS. Include: Git installation (via Homebrew or Xcode), configuration, "
         "SSH key setup, repository cloning, and common Git commands. Include macOS-specific considerations. "
         "**macOS-specific Git setup and commands.**"),

        ("Git Setup for Windows",
         "Provide Git setup instructions for Windows. Include: Git installation (Git for Windows), configuration, "
         "SSH key setup (using PuTTY or OpenSSH), repository cloning, and common Git commands. Include Windows-specific "
         "considerations (line endings, path handling). **Windows-specific Git setup and commands.**"),

        ("Git Branching Strategy",
         "What branching strategy does this project use? Describe: main/master branch, feature branches, release branches, "
         "hotfix branches, and how to create and manage branches. Include branch naming conventions. "
         "**Branching strategy and conventions.**"),

        ("Git Commit and PR Guidelines",
         "What are the commit message conventions and pull request guidelines? Include: commit message format, "
         "PR description requirements, code review process, and merge procedures. **Git commit and PR guidelines.**"),
    ]

    # Collect responses
    dev_setup_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repository": getattr(chatbot, "repo_info", {}).get('name', 'unknown'),
            "provider": provider,
            "model": getattr(chatbot, "model", None)
        },
        "sections": {
            "prerequisites": {},
            "installation_steps": {},
            "faqs": {},
            "hello_world_setup": {},
            "git_basics": {}
        }
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

        try:
            response = chatbot.chat(question)
            answer = response.get('answer') if isinstance(response, dict) else getattr(response, 'answer',
                                                                                       str(response))
            quality = response.get('context_quality', 1.0) if isinstance(response, dict) else getattr(response,
                                                                                                      'context_quality',
                                                                                                      1.0)

            section = section_mapping.get(idx - 1, "git_basics")
            dev_setup_data["sections"][section][key] = {
                "question": question,
                "answer": answer,
                "quality": quality
            }
        except Exception as e:
            print(f"Error: {e}")
            section = section_mapping.get(idx - 1, "git_basics")
            dev_setup_data["sections"][section][key] = {
                "question": question,
                "answer": f"Error: {str(e)}",
                "quality": 0.0
            }

    # Save to file
    output_dir = repo_root / "data" / "Onboarding" / "onboarding_reading_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / f"onboarding_dev_setup.json"

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(dev_setup_data, f, indent=2, ensure_ascii=False)

    # Calculate success stats
    total_answers = sum(len(section) for section in dev_setup_data["sections"].values())
    successful_answers = sum(
        1 for section in dev_setup_data["sections"].values()
        for item in section.values()
        if not str(item.get('answer', '')).startswith('Error:')
    )

    print(f"\nDone! Saved to: {json_file}")
    print(f"📊 Answered {successful_answers}/{total_answers} questions successfully")
    print(f"\nData organized into {len(dev_setup_data['sections'])} sections:")
    for section_name, section_data in dev_setup_data["sections"].items():
        print(f"   - {section_name}: {len(section_data)} questions")

    return json_file


if __name__ == "__main__":
    GITHUB_DB_PATH = "../../../../data/VectorDB/multi_index"
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = None

    generate_dev_setup_data(GITHUB_DB_PATH, GMAIL_DB_PATH, PROVIDER, MODEL)

