import os
import hashlib


class RepoRegistry:
    """
    Maps repo_url → local storage path (outside app directory)
    """

    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.join(
                os.path.expanduser("~"),
                ".codeintel_repos"
            )

        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def get_repo_path(self, repo_url: str) -> str:
        repo_hash = hashlib.md5(repo_url.encode()).hexdigest()
        return os.path.join(self.base_dir, repo_hash)
