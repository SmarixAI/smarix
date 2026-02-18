import json
import logging
import os
from datetime import datetime

from employee_aggregator import EmployeeAggregator
from domain_builder import DomainBuilder
from risk_engine import RiskEngine
from finalcall_llm_generator import FinalCallGenerator
from handover_llm_generator import HandoverGenerator
from documentation_llm_generator import DocumentationGenerator


# --------------------------------------------------
# CENTRAL LOGGING CONFIGURATION (ONLY HERE)
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("offboarding_debug.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MainRunner")


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

INPUT_FILE = "taskwarrior-flutter.json"
EMPLOYEE_NAME = "inderjeet20"
OUTPUT_DIR = "offboarding_outputs"


# --------------------------------------------------
# HELPER
# --------------------------------------------------

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

def main():

    logger.info("==================================================")
    logger.info("Starting Offboarding Knowledge Transfer Pipeline")

    ensure_output_dir()

    # Step 1 — Load repo data
    logger.info("Loading repository data...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        repo_data = json.load(f)

    # Step 2 — Aggregate employee data
    logger.info("Running EmployeeAggregator...")
    employee_data = EmployeeAggregator.extract(repo_data, EMPLOYEE_NAME)

    # Step 3 — Build domains
    logger.info("Running DomainBuilder...")
    domains = DomainBuilder.build(employee_data)

    # Step 4 — Attach risk (volume + structural)
    logger.info("Running RiskEngine...")
    domains_with_risk = RiskEngine.attach(domains)

    # --------------------------------------------------
    # Step 5 — Prepare Context Per Generator
    # --------------------------------------------------

    # FinalCall → only risky domains + structural signals
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

    # Handover → operational ownership info
    handover_input = [
        {
            "domain": d["domain"],
            "files": d.get("files", []),
            "stats": d.get("stats", {}),
            "structural_signals": d.get("structural_signals", [])
        }
        for d in domains_with_risk
    ]

    # Documentation → architecture-only view
    documentation_input = [
        {
            "domain": d["domain"],
            "files": d.get("files", []),
            "stats": d.get("stats", {})
        }
        for d in domains_with_risk
    ]

    # --------------------------------------------------
    # Step 6A — Final Call
    # --------------------------------------------------

    logger.info("Running FinalCallGenerator...")
    finalcall_report = FinalCallGenerator().generate(finalcall_input)

    # --------------------------------------------------
    # Step 6B — Handover
    # --------------------------------------------------

    logger.info("Running HandoverGenerator...")
    handover_report = HandoverGenerator().generate(handover_input)

    # --------------------------------------------------
    # Step 6C — Documentation
    # --------------------------------------------------

    logger.info("Running DocumentationGenerator...")
    documentation_report = DocumentationGenerator().generate(documentation_input)


    # --------------------------------------------------
    # Step 6 — Save All Outputs
    # --------------------------------------------------

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("Saving reports...")

    with open(f"{OUTPUT_DIR}/finalcall_report_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(finalcall_report, f, indent=4)

    with open(f"{OUTPUT_DIR}/handover_report_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(handover_report, f, indent=4)

    with open(f"{OUTPUT_DIR}/documentation_report_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(documentation_report, f, indent=4)

    logger.info("All reports saved successfully.")
    logger.info("Pipeline completed successfully.")
    logger.info("==================================================")


if __name__ == "__main__":
    main()
