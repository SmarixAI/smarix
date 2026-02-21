# domain_builder.py

from collections import defaultdict
from typing import Dict, Any, List
import logging

# IMPORTANT:
# Logging must be configured ONLY in run_finalcall.py
logger = logging.getLogger("DomainBuilder")


# -----------------------------
# Noise Filtering Rules
# -----------------------------

NOISE_PREFIXES = [
    "linux/",
    "windows/",
    "macos/",
    "ios/",
    "android/",
]

NOISE_FILES = [
    "pubspec.yaml",
    "pubspec.lock",
]

GENERATED_KEYWORDS = [
    "generated",
    "plugin_registrant",
]


class DomainBuilder:

    MAX_DEPTH = 4

    # -----------------------------------------
    # Step 1: Choose Best Directory Depth
    # -----------------------------------------
    @staticmethod
    def _choose_best_depth(files: List[Dict[str, Any]]) -> int:

        logger.info("Choosing best directory depth...")

        depth_counts = {}

        for depth in range(1, DomainBuilder.MAX_DEPTH + 1):
            groups = set()

            for f in files:
                prefixes = f.get("prefixes", [])
                if len(prefixes) >= depth:
                    groups.add(prefixes[depth - 1])

            depth_counts[depth] = len(groups)
            logger.info(f"Depth {depth}: {len(groups)} unique groups")

        # Prefer deeper grouping first
        for depth in reversed(range(1, DomainBuilder.MAX_DEPTH + 1)):
            count = depth_counts.get(depth, 0)
            if 2 <= count <= 8:
                logger.info(f"Selected depth: {depth}")
                return depth

        logger.info("Fallback depth selected: 3")
        return 3

    # -----------------------------------------
    # Step 2: Build Domains
    # -----------------------------------------
    @staticmethod
    def build(employee_data: Dict[str, Any]) -> List[Dict[str, Any]]:

        logger.info("--------------------------------------------------")
        logger.info("Starting domain building process...")

        files = employee_data.get("files", [])
        logger.info(f"Total files received from aggregator: {len(files)}")

        # ---- Bias toward main source code ----
        source_files = [
            f for f in files if f.get("file", "").startswith("lib/")
        ]

        if source_files:
            logger.info(f"Applying lib/ bias. Using {len(source_files)} source files.")
            files = source_files
        else:
            logger.info("No lib/ bias applied.")

        # ---- Remove noise files ----
        cleaned_files = []
        removed_count = 0

        for f in files:
            file_path = f.get("file", "").lower()

            if any(file_path.startswith(p) for p in NOISE_PREFIXES):
                logger.info(f"Removing platform noise file: {file_path}")
                removed_count += 1
                continue

            if file_path in NOISE_FILES:
                logger.info(f"Removing config noise file: {file_path}")
                removed_count += 1
                continue

            if any(k in file_path for k in GENERATED_KEYWORDS):
                logger.info(f"Removing generated file: {file_path}")
                removed_count += 1
                continue

            cleaned_files.append(f)

        logger.info(f"Files after noise removal: {len(cleaned_files)}")
        logger.info(f"Total noise files removed: {removed_count}")

        if not cleaned_files:
            logger.warning("No files left after cleaning. Returning empty domain list.")
            return []

        # ---- Choose best grouping depth ----
        depth = DomainBuilder._choose_best_depth(cleaned_files)

        clusters = defaultdict(lambda: {
            "files": [],
            "total_prs": 0,
            "total_commits": 0,
            "total_additions": 0,
            "total_deletions": 0,
            "tags": set(),
            "structural_signals": set(),
            "breaking_change": False,
        })


        logger.info("Grouping files into domains...")

        # ---- Actual grouping logic ----
        for f in cleaned_files:

            prefixes = f.get("prefixes", [])

            if len(prefixes) < depth:
                logger.debug(f"Skipping file due to insufficient depth: {f.get('file')}")
                continue

            domain = prefixes[depth - 1]

            clusters[domain]["files"].append(f.get("file"))
            clusters[domain]["total_prs"] += f.get("prs", 0)
            clusters[domain]["total_commits"] += f.get("commits", 0)
            clusters[domain]["total_additions"] += f.get("additions", 0)
            clusters[domain]["total_deletions"] += f.get("deletions", 0)
            clusters[domain]["tags"].update(f.get("tags", []))

            clusters[domain]["structural_signals"].update(
                f.get("structural_signals", [])
            )

            if f.get("breaking_change"):
                clusters[domain]["breaking_change"] = True


        logger.info(f"Total domains created: {len(clusters)}")

        # ---- Prepare structured output ----
        output = []

        for domain, data in clusters.items():
            logger.info(
                f"Domain '{domain}' → "
                f"Files={len(data['files'])}, "
                f"PRs={data['total_prs']}, "
                f"Commits={data['total_commits']}, "
                f"Additions={data['total_additions']}"
            )

            output.append({
                "domain": domain,
                "files": data["files"],
                "stats": {
                    "prs": data["total_prs"],
                    "commits": data["total_commits"],
                    "additions": data["total_additions"],
                    "deletions": data["total_deletions"],
                },
                "tags": list(data["tags"]),
                "structural_signals": list(data["structural_signals"]),
                "breaking_change": data["breaking_change"],

            })

        logger.info("Domain building completed.")
        logger.info("--------------------------------------------------\n")

        return output
