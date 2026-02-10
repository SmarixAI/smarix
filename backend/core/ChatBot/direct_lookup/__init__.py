"""
Direct lookup module for fast retrieval of specific entities by exact match.
"""
from .pr_lookup import PRDirectLookup, get_pr_lookup
from .issue_lookup import IssueDirectLookup, get_issue_lookup

__all__ = ["PRDirectLookup", "get_pr_lookup", "IssueDirectLookup", "get_issue_lookup"]
