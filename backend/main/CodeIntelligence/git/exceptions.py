class GitError(Exception):
    pass


class RepoCloneError(GitError):
    pass


class BranchCheckoutError(GitError):
    pass
