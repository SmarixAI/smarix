"""
Top Contributor Detection
Automatically identifies the contributor with the most contributions
"""

from typing import Dict, Any, Optional, Tuple


def find_top_contributor(prerequisite_data: Dict[str, Any]) -> Optional[str]:
    """
    Find the contributor with the most contributions from prerequisite data
    
    Args:
        prerequisite_data: Complete prerequisite analysis results
        
    Returns:
        Username of top contributor, or None if no contributors found
    """
    data_collection = prerequisite_data.get('data_collection', {})
    contributors_data = data_collection.get('multi_repo_contribution', {}).get('contributors', {})
    
    if not contributors_data:
        return None
    
    # Score each contributor
    contributor_scores = []
    
    for username, contrib_data in contributors_data.items():
        prs = contrib_data.get('prs', 0)
        commits = contrib_data.get('commits', 0)
        files_modified = contrib_data.get('files_modified_count', 0)
        
        # Calculate contribution score
        # Weight: PRs (3x), Commits (2x), Files (1x)
        score = (prs * 3) + (commits * 2) + files_modified
        
        contributor_scores.append({
            'username': username,
            'score': score,
            'prs': prs,
            'commits': commits,
            'files_modified': files_modified
        })
    
    # Sort by score (descending)
    contributor_scores.sort(key=lambda x: x['score'], reverse=True)
    
    if contributor_scores:
        top_contributor = contributor_scores[0]
        return top_contributor['username']
    
    return None


def find_top_contributor_from_repo_data(repo_data: Dict[str, Any]) -> Optional[str]:
    """
    Find the top contributor directly from raw repository data
    
    Args:
        repo_data: Raw repository data from DataCollectionFromGit
        
    Returns:
        Username of top contributor, or None if no contributors found
    """
    # Count contributions from PRs
    pr_contributions = {}
    for pr in repo_data.get('prs', []):
        author = pr.get('user', {}).get('login') or pr.get('author', {}).get('login') or pr.get('author')
        if author:
            if author not in pr_contributions:
                pr_contributions[author] = {'prs': 0, 'commits': 0, 'files': set()}
            pr_contributions[author]['prs'] += 1
            
            # Count files in PR
            files = pr.get('files', [])
            if isinstance(files, list):
                for file_info in files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    if filename:
                        pr_contributions[author]['files'].add(filename)
    
    # Count contributions from commits
    commit_contributions = {}
    for commit in repo_data.get('commits', []):
        author_info = commit.get('author') or commit.get('commit', {}).get('author', {})
        author = author_info.get('login') or author_info.get('name', 'unknown')
        if author:
            if author not in commit_contributions:
                commit_contributions[author] = {'prs': 0, 'commits': 0, 'files': set()}
            commit_contributions[author]['commits'] += 1
    
    # Merge contributions
    all_contributors = {}
    for author, data in pr_contributions.items():
        all_contributors[author] = {
            'prs': data['prs'],
            'commits': 0,
            'files_modified': len(data['files'])
        }
    
    for author, data in commit_contributions.items():
        if author not in all_contributors:
            all_contributors[author] = {'prs': 0, 'commits': 0, 'files_modified': 0}
        all_contributors[author]['commits'] += data['commits']
    
    if not all_contributors:
        return None
    
    # Score each contributor
    contributor_scores = []
    for username, contrib_data in all_contributors.items():
        prs = contrib_data.get('prs', 0)
        commits = contrib_data.get('commits', 0)
        files_modified = contrib_data.get('files_modified', 0)
        
        # Calculate contribution score
        score = (prs * 3) + (commits * 2) + files_modified
        
        contributor_scores.append({
            'username': username,
            'score': score,
            'prs': prs,
            'commits': commits,
            'files_modified': files_modified
        })
    
    # Sort by score (descending)
    contributor_scores.sort(key=lambda x: x['score'], reverse=True)
    
    if contributor_scores:
        top_contributor = contributor_scores[0]
        return top_contributor['username']
    
    return None


def get_top_contributor_info(prerequisite_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about the top contributor
    
    Args:
        prerequisite_data: Complete prerequisite analysis results
        
    Returns:
        Dictionary with top contributor info, or None
    """
    data_collection = prerequisite_data.get('data_collection', {})
    contributors_data = data_collection.get('multi_repo_contribution', {}).get('contributors', {})
    
    if not contributors_data:
        return None
    
    # Score each contributor
    contributor_scores = []
    
    for username, contrib_data in contributors_data.items():
        prs = contrib_data.get('prs', 0)
        commits = contrib_data.get('commits', 0)
        files_modified = contrib_data.get('files_modified_count', 0)
        
        # Calculate contribution score
        score = (prs * 3) + (commits * 2) + files_modified
        
        contributor_scores.append({
            'username': username,
            'score': score,
            'prs': prs,
            'commits': commits,
            'files_modified': files_modified,
            'first_contribution': contrib_data.get('first_contribution'),
            'last_contribution': contrib_data.get('last_contribution'),
            'files': contrib_data.get('files_modified', [])
        })
    
    # Sort by score (descending)
    contributor_scores.sort(key=lambda x: x['score'], reverse=True)
    
    if contributor_scores:
        return contributor_scores[0]
    
    return None

