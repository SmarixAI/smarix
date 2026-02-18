from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class RiskEngine:

    # -----------------------------------------
    # Structural Risk Weights
    # -----------------------------------------
    STRUCTURAL_WEIGHTS = {
        "breaking_change": 20,
        "db_schema_change": 15,
        "api_contract_change": 10,
        "engine_logic_change": 12,
        "notification_logic_change": 6,
        "network_layer_change": 7,
        "rust_bridge_change": 8,
        "sql_logic_change": 10,
        "lifecycle_change": 5,
        "dependency_update": 3,
        "new_file_added": 4,
        "method_added": 2,
        "method_removed": 4,
        "class_added": 2,
        "class_removed": 5,
    }

    # -----------------------------------------
    # Volume-Based Score Calculation
    # -----------------------------------------
    @staticmethod
    def _volume_score(domain: Dict[str, Any]) -> int:

        stats = domain.get("stats", {})

        prs = stats.get("prs", 0)
        commits = stats.get("commits", 0)
        additions = stats.get("additions", 0)

        score = (
            prs * 2
            + commits
            + additions // 100
        )

        logger.info(
            f"[VolumeScore] {domain.get('domain')} → "
            f"PRS={prs}, COMMITS={commits}, ADDITIONS={additions}, SCORE={score}"
        )

        return score

    # -----------------------------------------
    # Structural Score Calculation
    # -----------------------------------------
    @staticmethod
    def _structural_score(domain: Dict[str, Any]) -> int:

        score = 0

        # Breaking change flag at domain level
        if domain.get("breaking_change"):
            score += RiskEngine.STRUCTURAL_WEIGHTS["breaking_change"]

        signals = domain.get("structural_signals", [])

        for signal in signals:
            weight = RiskEngine.STRUCTURAL_WEIGHTS.get(signal, 0)
            score += weight

        logger.info(
            f"[StructuralScore] {domain.get('domain')} → "
            f"SIGNALS={signals}, SCORE={score}"
        )

        return score

    # -----------------------------------------
    # Combined Score
    # -----------------------------------------
    @staticmethod
    def _score(domain: Dict[str, Any]) -> int:

        try:
            volume = RiskEngine._volume_score(domain)
            structural = RiskEngine._structural_score(domain)

            total_score = volume + structural

            logger.info(
                f"[TotalScore] {domain.get('domain')} → "
                f"VOLUME={volume}, STRUCTURAL={structural}, TOTAL={total_score}"
            )

            return total_score

        except Exception:
            logger.exception(f"Error scoring domain: {domain}")
            return 0

    # -----------------------------------------
    # Risk Level Classification
    # -----------------------------------------
    @staticmethod
    def _risk_level(score: int, tags: List[str]) -> str:

        logger.info(
            f"[RiskLevel] SCORE={score}, TAGS={tags}"
        )

        if "documentation" in tags:
            return "LOW"

        if score >= 45:
            return "CRITICAL"

        if score >= 25:
            return "HIGH"

        if score >= 15:
            return "MEDIUM"

        return "LOW"

    # -----------------------------------------
    # Attach Risk To All Domains
    # -----------------------------------------
    @staticmethod
    def attach(domains: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        logger.info("--------------------------------------------------")
        logger.info(f"Starting risk attachment for {len(domains)} domains")

        for domain in domains:

            domain_name = domain.get("domain", "unknown")
            logger.info(f"Processing domain: {domain_name}")

            score = RiskEngine._score(domain)

            tags = domain.get("tags", [])
            risk_level = RiskEngine._risk_level(score, tags)

            domain["risk_score"] = score
            domain["risk_level"] = risk_level

            logger.info(
                f"[FinalRisk] {domain_name} → SCORE={score}, LEVEL={risk_level}"
            )

        logger.info("Risk attachment completed.\n")

        return domains
