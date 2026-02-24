import json
import os
import hashlib


class MetadataStore:

    def __init__(
        self,
        repo_url,
        commit_hash,
        base_data_dir="/Users/vishalkeshari/Desktop/smarix/backend/data"
    ):
        self.repo_hash = hashlib.md5(repo_url.encode()).hexdigest()
        self.commit_hash = commit_hash

        # backend/data/<repo_hash>/<commit_hash>/
        self.base_dir = os.path.join(
            base_data_dir,
            self.repo_hash,
            self.commit_hash
        )

        os.makedirs(self.base_dir, exist_ok=True)

    def get_metadata_path(self):
        return os.path.join(self.base_dir, "metadata.json")

    def save(self, data):
        with open(self.get_metadata_path(), "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        with open(self.get_metadata_path(), "r") as f:
            return json.load(f)
