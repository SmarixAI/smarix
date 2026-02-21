import json
import logging
import os
import sys
import argparse
from datetime import datetime
import boto3

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
# S3 CONFIG
# --------------------------------------------------

S3_BUCKET = "smarix-data-apsouth1"
S3_SOURCE_PREFIX = "DataCollectionFromGit/"
S3_OUTPUT_PREFIX = "Offboarding/"

s3 = boto3.client("s3")

# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] %(levelname)s - %(message)s",
)
logger = logging.getLogger("OffboardingPipeline")

# --------------------------------------------------
# S3 HELPERS
# --------------------------------------------------

def list_all_repo_json_files():
    """
    Traverse:
    DataCollectionFromGit/<org>/<repo>/<repo>.json
    """
    repo_files = []

    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(
        Bucket=S3_BUCKET,
        Prefix=S3_SOURCE_PREFIX
    )

    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]

            # Must end with .json and have org/repo structure
            if key.endswith(".json") and key.count("/") >= 3:
                repo_files.append(key)

    return repo_files


def read_json_from_s3(key: str):
    logger.info(f"Reading: s3://{S3_BUCKET}/{key}")
    obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
    return json.loads(obj["Body"].read().decode("utf-8"))


def upload_json_to_s3(data: dict, key: str):
    logger.info(f"Uploading: s3://{S3_BUCKET}/{key}")
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(data, indent=4),
        ContentType="application/json"
    )

# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------

def run_pipeline(employee_name: str):

    logger.info("==================================================")
    logger.info(f"Starting Offboarding Pipeline for: {employee_name}")

    # --------------------------------------------------
    # Step 1 — Collect All Repo Data
    # --------------------------------------------------

    repo_keys = list_all_repo_json_files()

    if not repo_keys:
        raise ValueError("No repository JSON files found in S3.")

    logger.info(f"Found {len(repo_keys)} repositories.")

    # --------------------------------------------------
    # Step 1 & 2 — Extract Employee Data Repo-by-Repo
    # --------------------------------------------------

    all_employee_data = []

    for key in repo_keys:
        repo_data = read_json_from_s3(key)

        # Your aggregator expects dict per repo
        if not isinstance(repo_data, dict):
            logger.warning(f"Skipping invalid repo format: {key}")
            continue

        extracted = EmployeeAggregator.extract(repo_data, employee_name)

        if extracted:
            if isinstance(extracted, list):
                all_employee_data.extend(extracted)
            else:
                all_employee_data.append(extracted)

    if not all_employee_data:
        raise ValueError(f"No data found for employee: {employee_name}")

    merged_employee_data = {
        "prs": [],
        "commits": [],
        "files": []
    }

    for data in all_employee_data:
        if not isinstance(data, dict):
            continue

        merged_employee_data["prs"].extend(data.get("prs", []))
        merged_employee_data["commits"].extend(data.get("commits", []))
        merged_employee_data["files"].extend(data.get("files", []))

    if not merged_employee_data["prs"] and not merged_employee_data["commits"]:
        logger.warning(f"No contribution data found for employee: {employee_name}")

        merged_employee_data = {
            "prs": [],
            "commits": [],
            "files": [],
            "metadata": {
                "employee": employee_name,
                "note": "No contributions found in available repositories."
            }
        }


    employee_data = merged_employee_data


    # if not employee_data:
    #     raise ValueError(f"No data found for employee: {employee_name}")

    # --------------------------------------------------
    # Step 3 — Domain Building
    # --------------------------------------------------

    domains = DomainBuilder.build(employee_data)

    # --------------------------------------------------
    # Step 4 — Risk Engine
    # --------------------------------------------------

    domains_with_risk = RiskEngine.attach(domains)

    # --------------------------------------------------
    # Step 5 — Prepare Generator Inputs
    # --------------------------------------------------

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

    handover_input = [
        {
            "domain": d["domain"],
            "files": d.get("files", []),
            "stats": d.get("stats", {}),
            "structural_signals": d.get("structural_signals", [])
        }
        for d in domains_with_risk
    ]

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

    finalcall_report = FinalCallGenerator().generate(finalcall_input)
    handover_report = HandoverGenerator().generate(handover_input)
    documentation_report = DocumentationGenerator().generate(documentation_input)

    # --------------------------------------------------
    # Step 7 — Upload to S3 (NO TIMESTAMP FOLDER)
    # --------------------------------------------------

    base_output_path = f"{S3_OUTPUT_PREFIX}{employee_name}/"

    upload_json_to_s3(finalcall_report, base_output_path + "finalcall.json")
    upload_json_to_s3(handover_report, base_output_path + "handover.json")
    upload_json_to_s3(documentation_report, base_output_path + "documentation.json")

    logger.info("Pipeline completed successfully.")

    return {
        "success": True,
        "employee": employee_name,
        "s3_output_path": f"s3://{S3_BUCKET}/{base_output_path}"
    }

# --------------------------------------------------
# CLI ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Offboarding Pipeline from S3")

    parser.add_argument("--employee_name", required=True)

    args = parser.parse_args()

    try:
        result = run_pipeline(employee_name=args.employee_name)
        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        logger.exception("Pipeline failed.")
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)
