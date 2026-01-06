"""
Main Processor for Improved Offboarding Prerequisites
Orchestrates all three modules: Data Collection, Risk Analysis, and AI Intelligence
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from .data_reader import DataReader
from .data_collection import DataCollectionProcessor
from .risk_analysis import RiskAnalysisProcessor
from .ai_intelligence import AIIntelligenceProcessor


class ImprovedOffboardingProcessor:
    """
    Main processor that orchestrates all prerequisite features (1-30)
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the processor
        
        Args:
            output_dir: Directory to save output JSON files (default: auto-detect)
        """
        if output_dir is None:
            # Auto-detect output directory
            # Start from project root (go up from this file to find project root)
            current_file = Path(__file__).resolve()
            # Go up: improved_offboarding -> main -> backend -> project_root
            project_root = current_file.parent.parent.parent.parent
            
            possible_paths = [
                project_root / "backend" / "data" / "improved_offboarding",
                project_root / "data" / "improved_offboarding",
                Path("backend/data/improved_offboarding"),  # Relative to current working directory
                Path("data/improved_offboarding"),  # Relative to current working directory
            ]
            
            for path in possible_paths:
                parent = path.parent
                if parent.exists():
                    self.output_dir = path.resolve()
                    break
            else:
                # Default fallback
                self.output_dir = (project_root / "backend" / "data" / "improved_offboarding").resolve()
        else:
            self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.data_reader = DataReader()
        self.data_collection = DataCollectionProcessor()
        self.risk_analysis = RiskAnalysisProcessor()
        self.ai_intelligence = AIIntelligenceProcessor()
    
    def process_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Process a repository through all prerequisite features
        
        Args:
            owner: Repository owner (e.g., 'torvalds')
            repo: Repository name (e.g., 'test-tlb')
            
        Returns:
            Complete results dictionary with all features
        """
        print(f"\n{'='*80}")
        print(f"Processing Repository: {owner}/{repo}")
        print(f"{'='*80}\n")
        
        # Step 1: Read repository data
        print("📖 Step 1/4: Reading repository data...")
        repo_data = self.data_reader.read_repo_data(owner, repo)
        
        if not repo_data:
            print(f"❌ Failed to load repository data for {owner}/{repo}")
            return {'error': f'Repository data not found for {owner}/{repo}'}
        
        print(f"   ✓ Loaded repository data")
        print(f"   - Files: {len(repo_data.get('code_files', []))}")
        print(f"   - PRs: {len(repo_data.get('prs', []))}")
        print(f"   - Commits: {len(repo_data.get('commits', []))}")
        
        # Step 2: Data Collection (Features 1-10)
        print("\n📊 Step 2/4: Processing Data Collection features (1-10)...")
        data_collection_results = self.data_collection.process(repo_data)
        print(f"   ✓ Completed data collection")
        print(f"   - PR activity: {data_collection_results['pr_activity']['total_prs']} PRs")
        print(f"   - Commit timeline: {data_collection_results['commit_timeline']['total_commits']} commits")
        print(f"   - File ownership: {data_collection_results['file_ownership_history']['total_files_tracked']} files")
        
        # Step 3: Risk & Knowledge Analysis (Features 11-20)
        print("\n🔍 Step 3/4: Processing Risk & Knowledge Analysis features (11-20)...")
        risk_analysis_results = self.risk_analysis.process(repo_data, data_collection_results)
        print(f"   ✓ Completed risk analysis")
        print(f"   - Knowledge loss risk: {len(risk_analysis_results['knowledge_loss_risk']['high_risk_files'])} high-risk files")
        print(f"   - Single owners: {risk_analysis_results['single_owner_detection']['total_single_owner_files']} files")
        print(f"   - Bus factor: {risk_analysis_results['bus_factor_analysis']['average_bus_factor']:.2f} avg")
        
        # Step 4: AI Intelligence (Features 21-30)
        print("\n🤖 Step 4/4: Processing AI Intelligence features (21-30)...")
        ai_intelligence_results = self.ai_intelligence.process(
            repo_data, 
            data_collection_results, 
            risk_analysis_results
        )
        print(f"   ✓ Completed AI intelligence")
        print(f"   - PR clusters: {ai_intelligence_results['semantic_pr_clustering']['total_clusters']} clusters")
        print(f"   - Knowledge units: {ai_intelligence_results['knowledge_unit_identification']['total_systems']} systems")
        print(f"   - Roles detected: {ai_intelligence_results['role_detection']['total_contributors_analyzed']} contributors")
        
        # Combine all results
        complete_results = {
            'metadata': {
                'repository': f"{owner}/{repo}",
                'processed_at': datetime.now().isoformat(),
                'processor_version': '1.0.0',
                'features_implemented': list(range(1, 31))
            },
            'data_collection': data_collection_results,
            'risk_analysis': risk_analysis_results,
            'ai_intelligence': ai_intelligence_results,
            'summary': self._generate_summary(data_collection_results, risk_analysis_results, ai_intelligence_results)
        }
        
        # Save results
        output_file = self.output_dir / f"{owner}_{repo}_prerequisites.json"
        print(f"\n💾 Saving results to {output_file}...")
        self._save_results(complete_results, output_file)
        print(f"   ✓ Results saved successfully")
        
        return complete_results
    
    def _generate_summary(self, data_collection: Dict[str, Any], 
                         risk_analysis: Dict[str, Any],
                         ai_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of all results"""
        return {
            'data_collection_summary': {
                'total_prs': data_collection.get('pr_activity', {}).get('total_prs', 0),
                'total_commits': data_collection.get('commit_activity', {}).get('total_commits', 0),
                'total_files': data_collection.get('file_activity', {}).get('total_files', 0),
                'total_contributors': data_collection.get('multi_repo_contribution', {}).get('total_contributors', 0),
                'critical_subsystems': len(data_collection.get('critical_subsystems', {}).get('critical_subsystems', []))
            },
            'risk_analysis_summary': {
                'high_risk_files': len(risk_analysis.get('knowledge_loss_risk', {}).get('high_risk_files', [])),
                'single_owner_files': risk_analysis.get('single_owner_detection', {}).get('total_single_owner_files', 0),
                'average_bus_factor': risk_analysis.get('bus_factor_analysis', {}).get('average_bus_factor', 0),
                'knowledge_hotspots': risk_analysis.get('knowledge_hotspots', {}).get('total_hotspots', 0),
                'critical_files': risk_analysis.get('criticality_scoring', {}).get('critical_files_count', 0)
            },
            'ai_intelligence_summary': {
                'pr_clusters': ai_intelligence.get('semantic_pr_clustering', {}).get('total_clusters', 0),
                'knowledge_units': {
                    'systems': ai_intelligence.get('knowledge_unit_identification', {}).get('total_systems', 0),
                    'modules': ai_intelligence.get('knowledge_unit_identification', {}).get('total_modules', 0),
                    'features': ai_intelligence.get('knowledge_unit_identification', {}).get('total_features', 0)
                },
                'roles_detected': ai_intelligence.get('role_detection', {}).get('total_contributors_analyzed', 0),
                'knowledge_gaps': ai_intelligence.get('knowledge_gap_detection', {}).get('total_gaps', 0)
            }
        }
    
    def _save_results(self, results: Dict[str, Any], output_file: Path) -> None:
        """Save results to JSON file"""
        def convert_to_serializable(obj):
            """Convert objects to JSON-serializable format"""
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, set):
                return list(obj)
            elif hasattr(obj, '__dict__'):
                return convert_to_serializable(obj.__dict__)
            else:
                return obj
        
        serializable_results = convert_to_serializable(results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    def process_multiple_repos(self, repos: list) -> Dict[str, Any]:
        """
        Process multiple repositories
        
        Args:
            repos: List of tuples (owner, repo)
            
        Returns:
            Dictionary with results for each repository
        """
        all_results = {}
        
        for owner, repo in repos:
            try:
                results = self.process_repository(owner, repo)
                all_results[f"{owner}/{repo}"] = results
            except Exception as e:
                print(f"❌ Error processing {owner}/{repo}: {e}")
                all_results[f"{owner}/{repo}"] = {'error': str(e)}
        
        return all_results

