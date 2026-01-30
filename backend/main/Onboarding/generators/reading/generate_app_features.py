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


def get_rag_chatbot_class():
    """Get RAGChatbot class, loading it if not already loaded."""
    global RAGChatbot
    if RAGChatbot is None:
        RAGChatbot = _load_rag_chatbot_class()
    return RAGChatbot

# Initialize as None, will be loaded on first use
RAGChatbot = None


def parse_single_mcq_from_response(response_text: str) -> dict:
    """
    Parse a single MCQ question from chatbot's response
    Returns a dict with question, options, correct_answer, and explanation
    """
    question_pattern = r'###\s+Question\s+(\d+)\s+\(MCQ\s*-\s*(\w+)\)'
    match = re.search(question_pattern, response_text)
    
    if not match:
        lines = response_text.split('\n')
        question_text = []
        options = {}
        correct_answer = None
        explanation = ""
        
        answer_section = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if '**Answer:**' in line or 'Answer:' in line:
                answer_section = True
                answer_line = line.split(':', 1)[-1].strip() if ':' in line else line.replace('**Answer:**', '').strip()
                if answer_line:
                    answer_match = re.match(r'^([A-D])\s*[-–—]\s*(.+)', answer_line, re.DOTALL)
                    if answer_match:
                        correct_answer = answer_match.group(1)
                        explanation = answer_match.group(2).strip()
                    else:
                        letter_match = re.match(r'^([A-D])', answer_line)
                        if letter_match:
                            correct_answer = letter_match.group(1)
                            explanation = answer_line[1:].strip()
                continue
            
            if answer_section:
                explanation += " " + line if explanation else line
                continue
            
            option_match = re.match(r'^([A-D])\.\s+(.+)$', line)
            if option_match:
                option_letter = option_match.group(1)
                option_text = option_match.group(2).strip()
                options[option_letter] = option_text
            else:
                question_text.append(line)
        
        if len(options) == 4 and correct_answer and correct_answer in options:
            return {
                'question': ' '.join(question_text),
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation.strip()
            }
        return None
    
    start_idx = match.end()
    content = response_text[start_idx:].strip()
    answer_split = re.split(r'\*\*Answer:\*\*', content, maxsplit=1)
    
    if len(answer_split) < 2:
        return None
    
    question_part = answer_split[0].strip()
    answer_part = answer_split[1].strip()
    
    lines = question_part.split('\n')
    question_text = []
    options = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        option_match = re.match(r'^([A-D])\.\s+(.+)$', line)
        if option_match:
            option_letter = option_match.group(1)
            option_text = option_match.group(2).strip()
            options[option_letter] = option_text
        else:
            question_text.append(line)
    
    correct_answer = None
    explanation = ""
    
    answer_match = re.match(r'^([A-D])\s*[-–—]\s*(.+)', answer_part, re.DOTALL)
    if answer_match:
        correct_answer = answer_match.group(1)
        explanation = answer_match.group(2).strip()
    else:
        letter_match = re.match(r'^([A-D])', answer_part)
        if letter_match:
            correct_answer = letter_match.group(1)
            explanation = answer_part[1:].strip()
    
    if len(options) == 4 and correct_answer and correct_answer in options:
        return {
            'question': ' '.join(question_text),
            'options': options,
            'correct_answer': correct_answer,
            'explanation': explanation
        }
    
    return None


def generate_section_qna(app_features_data, chatbot, gmail_db_path=None, provider='openai', model=None):
    """
    Generate MCQ questions for each section based on teaching_content
    Adds a 'qna' array to each section
    """
    print("\n" + "=" * 80)
    print("GENERATING MCQ QUESTIONS FOR EACH SECTION")
    print("=" * 80 + "\n")
    
    sections = app_features_data.get("sections", {})
    total_qnas = 0
    
    for section_name, section_content in sections.items():
        if not isinstance(section_content, dict):
            continue
            
        print(f"Processing section: {section_name}")
        
        # Get teaching_content array from section
        teaching_content = section_content.get("teaching_content", [])
        
        if not teaching_content:
            print(f"  ⚠ No teaching_content found, skipping...\n")
            continue
        
        qna_list = []
        
        for idx, item_data in enumerate(teaching_content, 1):
            if not isinstance(item_data, dict):
                continue
                
            topic_text = item_data.get("topic", "")
            content_text = item_data.get("content", "")
            title = item_data.get("title", f"Item {idx}")
            
            if not topic_text or not content_text or str(content_text).startswith("Error:"):
                print(f"  [{idx}/{len(teaching_content)}] ⚠ Skipping '{title}' (invalid data)")
                continue
            
            print(f"  [{idx}/{len(teaching_content)}] Generating MCQ for '{title}'...")
            
            # Create prompt for generating MCQ
            mcq_prompt = f"""Based on the following topic information, generate ONE multiple-choice question (MCQ) for new employee onboarding.

TOPIC: {title}

INFORMATION ABOUT THIS TOPIC:
{content_text[:2000]}

CRITICAL REQUIREMENTS:
- Generate EXACTLY ONE multiple-choice question (MCQ format)
- The question must have exactly 4 options (A, B, C, D)
- Only ONE option should be correct
- The question should test understanding of the key concepts from the topic
- Focus on important, practical knowledge that helps new employees understand application features
- Provide a clear explanation (3-5 sentences) that helps users learn
- Format the response as:
  ### Question 1 (MCQ - Medium)
  [Your question text here]
  A. [Option A]
  B. [Option B]
  C. [Option C]
  D. [Option D]
  **Answer:** [Correct letter] - [Detailed explanation]

Generate the MCQ question now."""

            schema_name = f"{REPO_OWNER}_{REPO_NAME}".replace("-", "_")
            try:
                response = chatbot.chat(mcq_prompt, schema_name=schema_name)
                answer = response.get('answer', '') if isinstance(response, dict) else getattr(response, 'answer', str(response))
                
                if answer:
                    mcq = parse_single_mcq_from_response(answer)
                    if mcq:
                        mcq['subsection'] = title
                        qna_list.append(mcq)
                        print(f"    ✓ Generated MCQ successfully")
                    else:
                        print(f"    ✗ Failed to parse MCQ from response")
                else:
                    print(f"    ✗ Empty response from chatbot")
                    
            except Exception as e:
                print(f"    ✗ Error: {e}")
                continue
        
        # Add qna list to section
        if qna_list:
            sections[section_name]["qna"] = qna_list
            total_qnas += len(qna_list)
            print(f"  ✓ Added {len(qna_list)} MCQ questions to section '{section_name}'\n")
        else:
            print(f"  ⚠ No MCQ questions generated for section '{section_name}'\n")
    
    print(f"✓ Total MCQ questions generated: {total_qnas}")
    print("=" * 80 + "\n")
    
    return app_features_data


def generate_app_features_data(db_path, gmail_db_path=None, provider='openai', model=None):
    """Generate comprehensive application features analysis data"""

    print("Starting App Features Data Generation...\n")

    # Initialize chatbot
    print("Loading chatbot...")
    RAGChatbotClass = get_rag_chatbot_class()
    chatbot = RAGChatbotClass(
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
            "complete_flow": {
                "teaching_content": []
            },
            "feature_level_flow_architecture": {
                "teaching_content": []
            },
            "summary": {
                "teaching_content": []
            }
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

        schema_name = f"{REPO_OWNER}_{REPO_NAME}".replace("-", "_")
        try:
            response = chatbot.chat(question, schema_name=schema_name)
            answer = response.get('answer') if isinstance(response, dict) else getattr(response, 'answer',
                                                                                       str(response))
            quality = response.get('context_quality', 1.0) if isinstance(response, dict) else getattr(response,
                                                                                                      'context_quality',
                                                                                                      1.0)

            section = section_mapping.get(idx - 1, "summary")
            app_features_data["sections"][section]["teaching_content"].append({
                "title": key,
                "topic": question,
                "content": answer,
                "quality": quality
            })
        except Exception as e:
            print(f"Error: {e}")
            section = section_mapping.get(idx - 1, "summary")
            app_features_data["sections"][section]["teaching_content"].append({
                "title": key,
                "topic": question,
                "content": f"Error: {str(e)}",
                "quality": 0.0
            })

    s3_key = f"Onboarding/{REPO_OWNER}/{REPO_NAME}/reading/onboarding_app_features.json"

    try:
        s3_manager.upload_json(app_features_data, s3_key)
        print(f"\n✓ Uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"\n❌ Failed to upload to S3: {e}")
        raise

    # Calculate success stats
    total_answers = sum(len(section.get("teaching_content", [])) for section in app_features_data["sections"].values())
    successful_answers = sum(
        1 for section in app_features_data["sections"].values()
        for item in section.get("teaching_content", [])
        if not str(item.get('content', '')).startswith('Error:')
    )

    print(f"📊 Answered {successful_answers}/{total_answers} questions successfully")
    print(f"\nData organized into {len(app_features_data['sections'])} sections:")
    for section_name, section_data in app_features_data["sections"].items():
        teaching_count = len(section_data.get("teaching_content", []))
        print(f"   - {section_name}: {teaching_count} teaching content items")

    # Generate MCQ questions for each section
    print("\n" + "=" * 80)
    print("Starting MCQ QNA Generation...")
    print("=" * 80)
    app_features_data = generate_section_qna(app_features_data, chatbot, gmail_db_path, provider, model)
    
    # Save updated file with QNA
    try:
        s3_manager.upload_json(app_features_data, s3_key)
        print(f"✓ Updated file with QNA uploaded to S3: s3://{s3_manager.bucket}/{s3_key}")
    except Exception as e:
        print(f"❌ Failed to upload updated file: {e}")
        raise

    return s3_key


def add_qna_to_existing_app_features(
    json_file_path: str = None,
    gmail_db_path: str = None,
    provider: str = 'openai',
    model: str = None
) -> str:
    """
    Add MCQ QNA questions to an existing app features JSON file
    
    Args:
        json_file_path: Path to existing app features JSON file (if None, uses default path)
        gmail_db_path: Optional path to Gmail database
        provider: LLM provider (openai/anthropic/ollama)
        model: Model name (optional, uses default for provider)
    
    Returns:
        Path to updated JSON file
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
            verbose=False
        )
        print("✓  Chatbot initialized successfully\n")
    except Exception as e:
        print(f"✗  Failed to initialize chatbot: {e}")
        return None
    
    app_features_data = generate_section_qna(app_features_data, chatbot, gmail_db_path, provider, model)
    
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
    GMAIL_DB_PATH = "../../../../data/VectorDB/gmail_chunks"
    PROVIDER = "openai"
    MODEL = None

    # Uncomment to just add QNA to existing file:
    # add_qna_to_existing_app_features(gmail_db_path=GMAIL_DB_PATH, provider=PROVIDER, model=MODEL)
    
    # Generate complete app features with QNA:
    generate_app_features_data(GITHUB_DB_PATH, GMAIL_DB_PATH, PROVIDER, MODEL)

