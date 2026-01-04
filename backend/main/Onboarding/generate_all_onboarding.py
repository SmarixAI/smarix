"""
Main Onboarding Data Generator
Runs all onboarding data generators sequentially to create complete documentation
"""

import sys
from pathlib import Path
from datetime import datetime
import argparse

# ---------------------------------------------------------------------
# Bootstrap backend root + repo context
# ---------------------------------------------------------------------

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.repo_context import get_repo_context

ctx = get_repo_context()

VECTOR_DB_PATH = ctx["vector_db"]
ONBOARDING_ROOT = ctx["onboarding"]

# ---------------------------------------------------------------------
# Import Reading generators
# ---------------------------------------------------------------------

from main.Onboarding.generators.reading.generate_repo_structure import (
    generate_repo_structure_data
)
from main.Onboarding.generators.reading.generate_tech_stacks import (
    generate_tech_stack_data
)
from main.Onboarding.generators.reading.generate_reading_overview import (
    generate_reading_overview
)
from main.Onboarding.generators.reading.generate_app_features import (
    generate_app_features_data
)
from main.Onboarding.generators.reading.generate_dev_setup import (
    generate_dev_setup_data
)
from main.Onboarding.generators.reading.generate_code_conventions import (
    generate_code_conventions_data
)

# ---------------------------------------------------------------------
# Import BugFix generators
# ---------------------------------------------------------------------

from main.Onboarding.generators.BugFix.generate_coding_questions import (
    generate_coding_questions
)
from main.Onboarding.generators.BugFix.generate_pr_tutorial import (
    generate_pr_tutorials
)

# ---------------------------------------------------------------------
# Import Practice generators
# ---------------------------------------------------------------------

from main.Onboarding.generators.Practice.generate_practice_questions import (
    generate_practice_questions
)

# ---------------------------------------------------------------------
# Import QnA generators
# ---------------------------------------------------------------------

from main.Onboarding.generators.QnA.generate_reading_questions import (
    generate_overview_questions
)
from main.Onboarding.generators.QnA.generate_repo_structure_questions import (
    generate_repo_structure_questions
)
from main.Onboarding.generators.QnA.generate_tech_stack_questions import (
    generate_tech_stack_questions
)
from main.Onboarding.generators.QnA.generate_app_features_questions import (
    generate_app_features_questions
)
from main.Onboarding.generators.QnA.generate_dev_setup_questions import (
    generate_dev_setup_questions
)
from main.Onboarding.generators.QnA.generate_code_convention_questions import (
    generate_code_conventions_questions
)

# ---------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------

def generate_all_onboarding_data(
    gmail_db_path=None,
    provider="openai",
    model=None,
    generators_to_run=None
):
    """
    Generate all onboarding documentation data.
    This orchestrator is intentionally thin — all paths are resolved
    via repo_context inside individual generators.
    """

    print("\n" + "=" * 70)
    print("ONBOARDING DATA GENERATION - ALL GENERATORS")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    all_generators = {
        # ---------------- Reading ----------------
        "repo_structure": {
            "name": "Repository Structure",
            "func": generate_repo_structure_data,
            "category": "reading",
        },
        "tech_stacks": {
            "name": "Tech Stack",
            "func": generate_tech_stack_data,
            "category": "reading",
        },
        "reading_overview": {
            "name": "Reading Overview",
            "func": generate_reading_overview,
            "category": "reading",
        },
        "app_features": {
            "name": "App Features",
            "func": generate_app_features_data,
            "category": "reading",
        },
        "dev_setup": {
            "name": "Dev Setup",
            "func": generate_dev_setup_data,
            "category": "reading",
        },
        "code_conventions": {
            "name": "Code Conventions",
            "func": generate_code_conventions_data,
            "category": "reading",
        },

        # ---------------- BugFix ----------------
        "coding_questions": {
            "name": "Coding Questions",
            "func": generate_coding_questions,
            "category": "bugfix",
        },
        "pr_tutorials": {
            "name": "PR Tutorials",
            "func": generate_pr_tutorials,
            "category": "bugfix",
        },

        # ---------------- Practice ----------------
        "practice_questions": {
            "name": "Practice Questions",
            "func": generate_practice_questions,
            "category": "practice",
        },

        # ---------------- QnA ----------------
        "repo_structure_questions": {
            "name": "Repo Structure Questions",
            "func": generate_repo_structure_questions,
            "category": "qna",
        },
        "tech_stack_questions": {
            "name": "Tech Stack Questions",
            "func": generate_tech_stack_questions,
            "category": "qna",
        },
        "overview_questions": {
            "name": "Overview Questions",
            "func": generate_overview_questions,
            "category": "qna",
        },
        "app_features_questions": {
            "name": "App Features Questions",
            "func": generate_app_features_questions,
            "category": "qna",
        },
        "dev_setup_questions": {
            "name": "Dev Setup Questions",
            "func": generate_dev_setup_questions,
            "category": "qna",
        },
        "code_conventions_questions": {
            "name": "Code Conventions Questions",
            "func": generate_code_conventions_questions,
            "category": "qna",
        },
    }

    if generators_to_run is None:
        generators_to_run = list(all_generators.keys())
    else:
        invalid = [g for g in generators_to_run if g not in all_generators]
        if invalid:
            print(f"⚠️ Invalid generators ignored: {invalid}")
            generators_to_run = [g for g in generators_to_run if g in all_generators]

    print(
        f"Running {len(generators_to_run)} generator(s): "
        f"{', '.join(all_generators[g]['name'] for g in generators_to_run)}\n"
    )

    results = {}
    start_time = datetime.now()

    for idx, gen_key in enumerate(generators_to_run, 1):
        gen = all_generators[gen_key]

        print("\n" + "-" * 70)
        print(f"[{idx}/{len(generators_to_run)}] Running {gen['name']}...")
        print("-" * 70 + "\n")

        try:
            gen_start = datetime.now()

            if gen["category"] in {"bugfix", "practice"}:
                output = gen["func"](
                    db_path=VECTOR_DB_PATH,
                    gmail_db_path=gmail_db_path,
                    provider=provider,
                    model=model,
                )

            elif gen["category"] == "qna":
                output = gen["func"](
                    gmail_db_path=gmail_db_path,
                    provider=provider,
                    model=model,
                )

            else:  # reading
                output = gen["func"](
                    gmail_db_path=gmail_db_path,
                    provider=provider,
                    model=model,
                )

            duration = (datetime.now() - gen_start).total_seconds()

            if output is None:
                raise RuntimeError("Generator returned None")

            results[gen_key] = {
                "status": "success",
                "output": str(output),
                "duration_seconds": duration,
            }

            print(f"✅ Completed in {duration:.1f}s")
            print(f"   Output: {output}\n")

        except Exception as e:
            print(f"❌ Failed: {e}\n")
            results[gen_key] = {
                "status": "error",
                "error": str(e),
            }

    total_duration = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 70)
    print("GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total time: {total_duration:.1f}s\n")

    for key, res in results.items():
        icon = "✅" if res["status"] == "success" else "❌"
        print(f"{icon} {all_generators[key]['name']}: {res.get('output', res.get('error'))}")

    print("=" * 70 + "\n")
    return results


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate all onboarding documentation data"
    )

    parser.add_argument(
        "--gmail-db",
        type=str,
        default=None,
        help="Optional Gmail vector DB path",
    )

    parser.add_argument(
        "--provider",
        type=str,
        default="openai",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
    )

    parser.add_argument(
        "--generators",
        nargs="+",
        default=None,
        help="Specific generators to run (default: all)",
    )

    args = parser.parse_args()

    generate_all_onboarding_data(
        gmail_db_path=args.gmail_db,
        provider=args.provider,
        model=args.model,
        generators_to_run=args.generators,
    )
