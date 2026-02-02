"""
Enhanced PR → Coding Question Generator

Generates HIGH-QUALITY, PRACTICAL coding questions from PRs to prepare employees
for real-world code reviews and production work.

Key Improvements:
- Multi-level difficulty (Junior, Mid)
- Comprehensive Q&A with explanations
- Real-world scenarios and edge cases
- Best practices and anti-patterns
- Performance, security, and scalability considerations
- Code review checklists
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
import time

# ------------------------------------------------------------------
# ENV
# ------------------------------------------------------------------

load_dotenv()
client = OpenAI()  # uses OPENAI_API_KEY from env

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------

PR_CHUNKS_PATH = Path(
    "/Users/vishalkeshari/Desktop/smarix/backend/data/DataProcessing/"
    "CCExtractor/taskwarrior-flutter/chunks/pr_chunks.json"
)

OUTPUT_PATH = Path(
    "/Users/vishalkeshari/Desktop/smarix/backend/main/Onboarding/"
    "bugfix/onboarding_coding_questions_enhanced.json"
)

# ------------------------------------------------------------------
# Category classification with more granularity
# ------------------------------------------------------------------

def classify_pr(pr: dict) -> Set[str]:
    """Classify PR into multiple categories for targeted learning"""
    categories = set()
    
    for f in pr.get("file_changes", []):
        name = f["filename"].lower()
        patch = f.get("patch", "").lower()
        
        # UI/Frontend
        if any(k in name for k in ["view", "widget", "ui", "screen", "component"]):
            categories.add("UI")
        
        # State Management
        if any(k in name for k in ["provider", "bloc", "state", "store", "redux"]):
            categories.add("State Management")
        
        # API/Backend Integration
        if any(k in name for k in ["api", "service", "repository", "client", "http"]):
            categories.add("API")
        
        # Testing
        if name.startswith("test/"):
            categories.add("Testing")
        
        # Performance
        if any(k in patch for k in ["cache", "optimize", "performance", "async", "lazy"]):
            categories.add("Performance")
        
        # Security
        if any(k in patch for k in ["auth", "security", "encrypt", "validate", "sanitize"]):
            categories.add("Security")
        
        # Architecture/Design
        if any(k in name for k in ["model", "entity", "dto", "interface", "abstract"]):
            categories.add("Architecture")
        
        # General Feature
        if name.startswith("lib/") and not any(c in categories for c in ["UI", "State Management"]):
            categories.add("Feature")
    
    return categories if categories else {"General"}

# ------------------------------------------------------------------
# Build comprehensive PR context
# ------------------------------------------------------------------

def build_pr_context(pr: dict) -> str:
    """Build rich context from PR for better question generation"""
    pr_number = pr["entities"]["pr_number"]
    
    lines = [
        f"PR #{pr_number}",
        "",
        "FILES CHANGED:"
    ]
    
    # Summary of changes
    total_additions = sum(f.get("additions", 0) for f in pr.get("file_changes", []))
    total_deletions = sum(f.get("deletions", 0) for f in pr.get("file_changes", []))
    
    lines.append(f"Total: +{total_additions} -{total_deletions} across {len(pr.get('file_changes', []))} files")
    lines.append("")
    
    for f in pr.get("file_changes", []):
        lines.append(f"\n{'='*60}")
        lines.append(f"File: {f['filename']}")
        lines.append(f"Status: {f['status']} | +{f['additions']} -{f['deletions']}")
        
        if f.get("patch"):
            lines.append("\nDIFF:")
            # Include more context (up to 4000 chars per file)
            lines.append(f["patch"][:4000])
            if len(f["patch"]) > 4000:
                lines.append("\n... (diff truncated)")
    
    return "\n".join(lines)

# ------------------------------------------------------------------
# Enhanced prompts for quality questions
# ------------------------------------------------------------------

SYSTEM_PROMPT = """
You are a Staff Software Engineer and Technical Interviewer at a top tech company.

Your task is to generate PRODUCTION-READY PR review questions that prepare engineers 
for real-world code reviews and production challenges.

REQUIREMENTS:

1. PROBLEM IDENTIFICATION:
   - What specific problem did the original code have?
   - What symptoms would users/developers experience?
   - Why is this a problem in production?

2. SOLUTION ANALYSIS:
   - How does this PR solve the problem?
   - What design decisions were made?
   - What alternative approaches exist?

3. REAL-WORLD IMPACT:
   - Performance implications
   - Security considerations
   - Edge cases and error handling
   - Scalability concerns
   - Maintainability impact

4. LEARNING OUTCOMES:
   - Key concepts the engineer should understand
   - Best practices demonstrated
   - Anti-patterns avoided
   - Industry standards followed

OUTPUT MUST BE:
- Specific to the actual code changes
- Grounded in the diff (no speculation)
- Practical for production environments
- Educational with clear explanations

If the PR lacks sufficient signal for a quality question, respond with:
INSUFFICIENT_PR_SIGNAL
"""

def user_prompt(category: str, context: str, pr_number: int, difficulty: str) -> str:
    difficulty_guide = {
        "Junior": "Focus on: understanding the change, basic concepts, obvious improvements",
        "Mid": "Focus on: design patterns, trade-offs, alternative solutions, edge cases"
    }
    
    return f"""
PR CONTEXT:
{context}

TASK:
Generate a {difficulty}-level {category} coding interview question based on PR #{pr_number}.

{difficulty_guide[difficulty]}

OUTPUT FORMAT (JSON ONLY, NO MARKDOWN):
{{
  "title": "Concise, specific title (< 100 chars)",
  "difficulty": "{difficulty}",
  "category": "{category}",
  
  "scenario": {{
    "context": "Real-world context explaining when/why this matters",
    "problem_statement": "Clear description of what needs to be reviewed/understood"
  }}
  
  "questions": [
    "Question 1: What problem does this PR solve?",
    "Question 2: How does the implementation address the problem?",
    "Question 3: What edge cases or risks should be considered?",
    "Question 4: (difficulty-appropriate follow-up)"
  ],
  
  "model_answer": {{
    "problem_analysis": "Detailed explanation of the original problem",
    "solution_explanation": "How and why the PR fixes it",
    "trade_offs": "Design decisions and their implications",
    "best_practices": ["Practice 1", "Practice 2"],
    "edge_cases": ["Edge case 1", "Edge case 2"],
    "testing_strategy": "How to test this change"
  }},
  
  "key_concepts": ["Concept 1", "Concept 2", "Concept 3"]
}}

CRITICAL: Ensure all analysis is grounded in the actual diff. Do not invent features or systems not visible in the code.
"""

# ------------------------------------------------------------------
# Question generation with retry logic
# ------------------------------------------------------------------

def generate_question_for_pr(
    pr: dict,
    category: str,
    difficulty: str,
    max_retries: int = 3
) -> Optional[dict]:
    """Generate a single question with retry logic for better quality"""
    
    pr_number = pr["entities"]["pr_number"]
    context = build_pr_context(pr)
    
    for attempt in range(max_retries):
        try:
            print(f"   Attempt {attempt + 1}/{max_retries}...")
            
            response = client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4 for better quality
                temperature=0.3,  # Lower for consistency
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt(category, context, pr_number, difficulty)}
                ]
            )
            
            answer = response.choices[0].message.content.strip()
            
            if answer == "INSUFFICIENT_PR_SIGNAL":
                print("   ⚠️ Insufficient signal")
                return None
            
            # Clean markdown formatting if present
            if answer.startswith("```json"):
                answer = answer.split("```json")[1].split("```")[0].strip()
            elif answer.startswith("```"):
                answer = answer.split("```")[1].split("```")[0].strip()
            
            # Parse and validate
            question_data = json.loads(answer)
            
            # Validation
            required_fields = ["title", "scenario", "questions", "model_answer", "key_concepts"]
            if all(field in question_data for field in required_fields):
                return question_data
            else:
                print(f"   ⚠️ Missing required fields, retrying...")
                continue
                
        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON parse error: {e}, retrying...")
            time.sleep(1)
            continue
        except Exception as e:
            print(f"   ❌ Error: {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(1)
    
    return None


def extract_before_after_from_patch(patch: str) -> tuple[str, str]:
    """
    Extract approximate before_code and after_code from a unified diff.
    This is BEST-EFFORT and used only for learning / comparison UI.
    """
    before_lines = []
    after_lines = []

    for line in patch.splitlines():
        if line.startswith("-") and not line.startswith("---"):
            before_lines.append(line[1:])
        elif line.startswith("+") and not line.startswith("+++"):
            after_lines.append(line[1:])
        elif line.startswith(" "):
            # context line → belongs to both
            before_lines.append(line[1:])
            after_lines.append(line[1:])

    return (
        "\n".join(before_lines).strip(),
        "\n".join(after_lines).strip(),
    )

def build_solution_from_pr(pr: dict) -> dict:
    files = []

    for f in pr.get("file_changes", []):
        patch = f.get("patch", "")
        before_code, after_code = extract_before_after_from_patch(patch)

        files.append({
            "filename": f["filename"],
            "before_code": before_code,
            "after_code": after_code,
            "diff": patch
        })

    return {"files": files}

# ------------------------------------------------------------------
# Main generation logic
# ------------------------------------------------------------------

def generate_questions():
    """Main function to generate comprehensive question set"""
    
    print("🚀 Enhanced PR Question Generator")
    print("=" * 60)
    
    print("\n📥 Loading PR chunks...")
    pr_chunks: List[dict] = json.loads(PR_CHUNKS_PATH.read_text())
    print(f"✅ Loaded {len(pr_chunks)} PR chunks")
    
    # Select diverse PRs across categories
    selected_prs: Dict[str, List[dict]] = {}
    used_pr_numbers: Set[int] = set()
    
    target_categories = ["UI", "Feature", "Testing", "API"]
    prs_per_category = 1  # Get 1 PRs per category for variety
    
    print("\n🎯 Selecting PRs across categories...")
    for pr in pr_chunks:
        pr_number = pr["entities"]["pr_number"]
        if pr_number in used_pr_numbers:
            continue
        
        categories = classify_pr(pr)

        # 🔒 Only keep target categories
        filtered_categories = categories.intersection(target_categories)

        if not filtered_categories:
            continue

        for category in filtered_categories:
            if category not in selected_prs:
                selected_prs[category] = []

            if len(selected_prs[category]) < prs_per_category:
                selected_prs[category].append(pr)
                used_pr_numbers.add(pr_number)
                break
    
    print("\n📊 Selected PRs by category:")
    for category, prs in selected_prs.items():
        print(f"   {category}: {len(prs)} PRs - {[pr['entities']['pr_number'] for pr in prs]}")
    
    # Generate questions with multiple difficulty levels
    all_questions = []
    question_counter = 1
    
    difficulties = ["Junior", "Mid"]
    
    print("\n🎓 Generating questions...")
    print("=" * 60)
    
    for category, prs in selected_prs.items():
        for pr in prs:
            pr_number = pr["entities"]["pr_number"]
            
            # Generate one question per difficulty level for each PR
            for difficulty in difficulties:
                print(f"\n[{question_counter}] {category} | {difficulty} | PR #{pr_number}")
                
                question_data = generate_question_for_pr(pr, category, difficulty)

                solution = build_solution_from_pr(pr)
                
                if question_data:
                    all_questions.append({
                        "question_id": question_counter,
                        "pr_number": pr_number,
                        "category": category,
                        "difficulty": difficulty,
                        "pr_metadata": {
                            "files_changed": len(pr.get("file_changes", [])),
                            "additions": sum(f.get("additions", 0) for f in pr.get("file_changes", [])),
                            "deletions": sum(f.get("deletions", 0) for f in pr.get("file_changes", [])),
                            "filenames": [f["filename"] for f in pr.get("file_changes", [])]
                        },
                        "question_data": question_data,
                        "solution": solution,
                        "code_diff": [
                            {
                                "filename": f["filename"],
                                "status": f["status"],
                                "patch": f.get("patch", "")[:3000]
                            }
                            for f in pr.get("file_changes", [])
                        ]
                    })
                    print("   ✅ Generated successfully")
                    question_counter += 1
                else:
                    print("   ⏭️  Skipped (insufficient quality)")
                
                # Rate limiting
                time.sleep(0.5)
    
    # Organize output
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repo": "CCExtractor/taskwarrior-flutter",
            "generator": "enhanced_pr_question_generator_v2",
            "total_questions": len(all_questions),
            "difficulty_distribution": {
                "Junior": len([q for q in all_questions if q["difficulty"] == "Junior"]),
                "Mid": len([q for q in all_questions if q["difficulty"] == "Mid"])
            },
            "category_distribution": {}
        },
        "questions": all_questions,
        "learning_path": {
            "beginner": [q["question_id"] for q in all_questions if q["difficulty"] == "Junior"],
            "intermediate": [q["question_id"] for q in all_questions if q["difficulty"] == "Mid"]
        }
    }
    
    # Calculate category distribution
    for q in all_questions:
        cat = q["category"]
        output["metadata"]["category_distribution"][cat] = \
            output["metadata"]["category_distribution"].get(cat, 0) + 1
    
    # Save output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2))
    
    print("\n" + "=" * 60)
    print("🎉 GENERATION COMPLETE!")
    print(f"📊 Total questions: {len(all_questions)}")
    print(f"📁 Output: {OUTPUT_PATH}")
    print("\n📈 Distribution:")
    print(f"   Junior: {output['metadata']['difficulty_distribution']['Junior']}")
    print(f"   Mid: {output['metadata']['difficulty_distribution']['Mid']}")
    print("\n💡 Categories:")
    for cat, count in output["metadata"]["category_distribution"].items():
        print(f"   {cat}: {count}")

# ------------------------------------------------------------------


if __name__ == "__main__":
    generate_questions()