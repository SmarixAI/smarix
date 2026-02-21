# change_analyzer.py

import re
import logging
from typing import Dict, Any, List


logger = logging.getLogger("OffboardingLogger")


class ChangeAnalyzer:
    """
    Lightweight patch-based change classifier.
    Uses regex heuristics (fast, deterministic).
    """

    # -----------------------------------------
    # Core Analysis Entry
    # -----------------------------------------
    @staticmethod
    def analyze(file_record: Dict[str, Any]) -> Dict[str, Any]:

        filename = file_record.get("filename", "")
        patch = file_record.get("patch", "") or ""
        status = file_record.get("status", "")

        signals = set()
        change_type = "minor"
        breaking = False

        # -----------------------------------------
        # File-Level Signals
        # -----------------------------------------

        if status == "added":
            signals.add("new_file_added")
            change_type = "feature"

        if status == "removed":
            signals.add("file_deleted")
            change_type = "breaking"
            breaking = True

        # -----------------------------------------
        # Structural Signals (Patch Based)
        # -----------------------------------------

        # Class definition changes
        if re.search(r"\+.*class\s+\w+", patch):
            signals.add("class_added")

        if re.search(r"-.*class\s+\w+", patch):
            signals.add("class_removed")
            breaking = True

        # Method signature changes
        if re.search(r"\+.*\)\s*{", patch):
            signals.add("method_added")

        if re.search(r"-.*\)\s*{", patch):
            signals.add("method_removed")
            breaking = True

        # Public API change detection
        if re.search(r"\+.*recur", patch) or re.search(r"\+.*rtype", patch):
            signals.add("api_contract_change")

        # Database schema detection
        if "task_database" in filename.lower():
            if re.search(r"\+.*recur", patch):
                signals.add("db_schema_change")

        # SQL change detection
        if re.search(r"insert into|update\s+\w+|alter table", patch, re.IGNORECASE):
            signals.add("sql_logic_change")

        # Lifecycle logic detection
        if re.search(r"status.*completed", patch):
            signals.add("lifecycle_change")

        # Notification logic change
        if re.search(r"notification", patch, re.IGNORECASE):
            signals.add("notification_logic_change")

        # Engine addition detection
        if "engine" in filename.lower():
            signals.add("engine_logic_change")

        # Rust bridge detection
        if filename.endswith(".rs"):
            signals.add("rust_bridge_change")

        # Network layer detection
        if "net/" in filename.lower():
            signals.add("network_layer_change")

        # Dependency change detection
        if filename.endswith("pubspec.yaml") or filename.endswith("pubspec.lock"):
            signals.add("dependency_update")

        # Formatting-only detection
        if not patch.strip():
            signals.add("formatting_only")

        # -----------------------------------------
        # Change Type Escalation
        # -----------------------------------------

        if "db_schema_change" in signals:
            change_type = "schema"

        if "engine_logic_change" in signals:
            change_type = "architectural"

        if "api_contract_change" in signals:
            change_type = "api"

        if breaking:
            change_type = "breaking"

        logger.info(
            f"[ChangeAnalyzer] {filename} → TYPE={change_type}, SIGNALS={list(signals)}"
        )

        return {
            "change_type": change_type,
            "structural_signals": list(signals),
            "breaking_change": breaking,
        }
