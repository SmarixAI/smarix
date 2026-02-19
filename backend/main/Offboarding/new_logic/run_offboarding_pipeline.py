import json
import logging
import os
import sys
import argparse
from datetime import datetime

# --------------------------------------------------
# Ensure project root is on sys.path
# --------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.main.Offboarding.new_logic.employee_aggregator import EmployeeAggregator
from backend.main.Offboarding.new_logic.domain_builder import DomainBuilder
from backend.main.Offboarding.new_logic.risk_engine import RiskEngine
from backend.main.Offboarding.new_logic.finalcall_llm_generator import FinalCallGenerator
from backend.main.Offboarding.new_logic.handover_llm_generator import HandoverGenerator
from backend.main.Offboarding.new_logic.documentation_llm_generator import DocumentationGenerator


# --------------------------------------------------
# CENTRAL LOGGING CONFIGURATION
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("offboarding_debug.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("OffboardingPipeline")


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def ensure_output_dir(output_dir: str):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------

def run_pipeline(input_file: str, employee_name: str, output_dir: str):

    logger.info("==================================================")
    logger.info("Starting Offboarding Knowledge Transfer Pipeline")
    logger.info(f"Employee: {employee_name}")
    logger.info(f"Input File: {input_file}")
    logger.info(f"Output Directory: {output_dir}")

    ensure_output_dir(output_dir)

    # --------------------------------------------------
    # Step 1 — Load Repository Data
    # --------------------------------------------------

    logger.info("Loading repository data...")
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with open(input_file, "r", encoding="utf-8") as f:
        repo_data = json.load(f)

    # --------------------------------------------------
    # Step 2 — Aggregate Employee Data
    # --------------------------------------------------

    logger.info("Running EmployeeAggregator...")
    employee_data = EmployeeAggregator.extract(repo_data, employee_name)

    if not employee_data:
        raise ValueError(f"No data found for employee: {employee_name}")

    # --------------------------------------------------
    # Step 3 — Build Domains
    # --------------------------------------------------

    logger.info("Running DomainBuilder...")
    domains = DomainBuilder.build(employee_data)

    # --------------------------------------------------
    # Step 4 — Attach Risk
    # --------------------------------------------------

    logger.info("Running RiskEngine...")
    domains_with_risk = RiskEngine.attach(domains)

    # --------------------------------------------------
    # Step 5 — Prepare Generator Inputs
    # --------------------------------------------------

    # FinalCall → Only HIGH & CRITICAL domains
    finalcall_input = [
        {
            "domain": d["domain"],
            "risk_score": d["risk_score"],
            "risk_level": d["risk_level"],
            "structural_signals": d.get("structural_signals", [])
        }
        for d in domains_with_risk
        if d["risk_level"] in ["HIGH", "CRITICAL"]
    ]

    # Handover → Ownership + Files + Structural signals
    handover_input = [
        {
            "domain": d["domain"],
            "files": d.get("files", []),
            "stats": d.get("stats", {}),
            "structural_signals": d.get("structural_signals", [])
        }
        for d in domains_with_risk
    ]

    # Documentation → Architecture-only
    documentation_input = [
        {
            "domain": d["domain"],
            "files": d.get("files", []),
            "stats": d.get("stats", {})
        }
        for d in domains_with_risk
    ]

    # --------------------------------------------------
    # Step 6 — Generate Reports
    # --------------------------------------------------

    logger.info("Running FinalCallGenerator...")
    finalcall_report = FinalCallGenerator().generate(finalcall_input)

    logger.info("Running HandoverGenerator...")
    handover_report = HandoverGenerator().generate(handover_input)

    logger.info("Running DocumentationGenerator...")
    documentation_report = DocumentationGenerator().generate(documentation_input)

    # --------------------------------------------------
    # Step 7 — Save Outputs
    # --------------------------------------------------

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    finalcall_path = os.path.join(output_dir, f"finalcall.json")
    handover_path = os.path.join(output_dir, f"handover.json")
    documentation_path = os.path.join(output_dir, f"documentation.json")

    logger.info("Saving reports...")

    with open(finalcall_path, "w", encoding="utf-8") as f:
        json.dump(finalcall_report, f, indent=4)

    with open(handover_path, "w", encoding="utf-8") as f:
        json.dump(handover_report, f, indent=4)

    with open(documentation_path, "w", encoding="utf-8") as f:
        json.dump(documentation_report, f, indent=4)

    logger.info("All reports saved successfully.")
    logger.info("Pipeline completed successfully.")
    logger.info("==================================================")

    return {
        "success": True,
        "employee": employee_name,
        "files": {
            "finalcall": finalcall_path,
            "handover": handover_path,
            "documentation": documentation_path
        }
    }


# --------------------------------------------------
# CLI ENTRY POINT (Used by FastAPI subprocess)
# --------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Offboarding Knowledge Transfer Pipeline")

    parser.add_argument("--input_file", required=True, help="Path to repository JSON file")
    parser.add_argument("--employee_name", required=True, help="Employee username")
    parser.add_argument("--output_dir", required=True, help="Directory to save outputs")

    args = parser.parse_args()

    try:
        result = run_pipeline(
            input_file=args.input_file,
            employee_name=args.employee_name,
            output_dir=args.output_dir
        )

        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        logger.exception("Pipeline failed.")
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)
