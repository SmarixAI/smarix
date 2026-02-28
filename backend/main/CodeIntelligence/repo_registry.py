import os


class RepoRegistry:

    BASE_RAW_DIR = os.path.join(
        os.path.dirname(__file__),
        "../../data/DataCollectionFromGit"
    )

    BASE_INTEL_DIR = os.path.join(
        os.path.dirname(__file__),
        "../../data/CodeIntelligence"
    )

    def list_extractors(self):
        base = os.path.abspath(self.BASE_RAW_DIR)
        return [
            d for d in os.listdir(base)
            if os.path.isdir(os.path.join(base, d))
        ]

    def list_repos(self, extractor_id):
        extractor_path = os.path.join(
            os.path.abspath(self.BASE_RAW_DIR),
            extractor_id
        )

        return [
            d for d in os.listdir(extractor_path)
            if os.path.isdir(os.path.join(extractor_path, d))
        ]

    def get_repo_json_path(self, extractor_id, repo_id):
        return os.path.abspath(
            os.path.join(
                self.BASE_RAW_DIR,
                extractor_id,
                repo_id,
                f"{repo_id}.json"
            )
        )

    def get_intelligence_path(self, extractor_id, repo_id):
        return os.path.abspath(
            os.path.join(
                self.BASE_INTEL_DIR,
                extractor_id,
                repo_id,
                "intelligence.json"
            )
        )