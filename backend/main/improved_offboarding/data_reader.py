"""
Data Reader Utility
Reads git repository data from data/datacollection folder
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class DataReader:
    """Utility class to read git repository data"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize data reader
        
        Args:
            base_path: Base path to data collection folder (default: auto-detect)
        """
        if base_path is None:
            # Auto-detect path - try multiple locations
            # Start from project root (go up from this file to find project root)
            current_file = Path(__file__).resolve()
            # Go up: improved_offboarding -> main -> backend -> project_root
            project_root = current_file.parent.parent.parent.parent
            
            possible_paths = [
                project_root / "backend" / "data" / "DataCollectionFromGit",
                project_root / "data" / "DataCollectionFromGit",
                Path("backend/data/DataCollectionFromGit"),  # Relative to current working directory
                Path("data/DataCollectionFromGit"),  # Relative to current working directory
            ]
            
            for path in possible_paths:
                if path.exists():
                    self.base_path = path.resolve()
                    print(f"📂 Using data path: {self.base_path}")
                    break
            else:
                # Default fallback
                self.base_path = (project_root / "backend" / "data" / "DataCollectionFromGit").resolve()
                print(f"⚠️  Using default data path: {self.base_path}")
        else:
            self.base_path = Path(base_path).resolve()
    
    def read_repo_data(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Read repository data from JSON file
        
        Args:
            owner: Repository owner (e.g., 'torvalds')
            repo: Repository name (e.g., 'test-tlb')
            
        Returns:
            Dictionary containing repository data or None if not found
        """
        # Try different possible file paths
        possible_paths = [
            self.base_path / owner / repo / f"{repo}.json",
            self.base_path / owner / repo / "repo_data.json",
            self.base_path / owner / f"{repo}.json",
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"✓ Loaded data from {path}")
                        return data
                except Exception as e:
                    print(f"Error reading {path}: {e}")
                    continue
        
        print(f"⚠ Repository data not found for {owner}/{repo}")
        return None
    
    def list_available_repos(self) -> list:
        """List all available repositories in the data folder"""
        repos = []
        if self.base_path.exists():
            for owner_dir in self.base_path.iterdir():
                if owner_dir.is_dir():
                    for repo_dir in owner_dir.iterdir():
                        if repo_dir.is_dir():
                            # Look for JSON files
                            json_files = list(repo_dir.glob("*.json"))
                            if json_files:
                                repos.append({
                                    'owner': owner_dir.name,
                                    'repo': repo_dir.name,
                                    'path': str(repo_dir)
                                })
        return repos

