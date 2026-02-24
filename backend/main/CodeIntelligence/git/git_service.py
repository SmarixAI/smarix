import os
import subprocess
from .repo_registry import RepoRegistry
from .exceptions import RepoCloneError, BranchCheckoutError


class GitService:
    def __init__(self, base_repo_dir="repos"):
        self.registry = RepoRegistry(base_repo_dir)

    def _run_git(self, args, cwd=None):
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(result.stderr.strip())

        return result.stdout.strip()

    def ensure_repo(self, repo_url: str) -> str:
        """
        Clone repo if not exists.
        Otherwise fetch updates.
        Returns local repo path.
        """
        repo_path = self.registry.get_repo_path(repo_url)

        if not os.path.exists(repo_path):
            try:
                print(f"Cloning {repo_url}")
                self._run_git(["git", "clone", repo_url, repo_path])
            except Exception as e:
                raise RepoCloneError(str(e))
        else:
            print("Fetching latest updates")
            self._run_git(["git", "fetch"], cwd=repo_path)

        return repo_path

    def checkout_branch(self, repo_path: str, branch: str):
        try:
            self._run_git(["git", "checkout", branch], cwd=repo_path)
            self._run_git(["git", "pull"], cwd=repo_path)
        except Exception as e:
            raise BranchCheckoutError(str(e))

    def get_current_commit(self, repo_path: str) -> str:
        return self._run_git(["git", "rev-parse", "HEAD"], cwd=repo_path)

    def prepare_snapshot(self, repo_url: str, branch: str):
        """
        High-level function:
        - Ensure repo exists
        - Checkout branch
        - Return repo_path + commit_hash
        """
        repo_path = self.ensure_repo(repo_url)
        self.checkout_branch(repo_path, branch)
        commit_hash = self.get_current_commit(repo_path)

        return {
            "repo_path": repo_path,
            "branch": branch,
            "commit_hash": commit_hash
        }
