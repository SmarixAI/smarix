"""
Main Onboarding Data Generator
Runs all onboarding data generators sequentially to create complete documentation
"""

import sys
from pathlib import Path
from datetime import datetime
import argparse

# Add repository root to path for imports
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Import Reading generators
from main.Onboarding.generators.reading.generate_repo_structure import generate_repo_structure_data
from main.Onboarding.generators.reading.generate_tech_stacks import generate_tech_stack_data
from main.Onboarding.generators.reading.generate_reading_overview import generate_reading_overview
from main.Onboarding.generators.reading.generate_app_features import generate_app_features_data
from main.Onboarding.generators.reading.generate_dev_setup import generate_dev_setup_data
from main.Onboarding.generators.reading.generate_code_conventions import generate_code_conventions_data

# Import BugFix generators
from main.Onboarding.generators.BugFix.generate_coding_questions import generate_coding_questions
from main.Onboarding.generators.BugFix.generate_pr_tutorial import generate_pr_tutorials

# Import Practice generators
from main.Onboarding.generators.Practice.generate_practice_questions import generate_practice_questions

# Import QnA generators
from main.Onboarding.generators.QnA.generate_reading_questions import generate_overview_questions
from main.Onboarding.generators.QnA.generate_repo_structure_questions import generate_repo_structure_questions
from main.Onboarding.generators.QnA.generate_tech_stack_questions import generate_tech_stack_questions
from main.Onboarding.generators.QnA.generate_app_features_questions import generate_app_features_questions
from main.Onboarding.generators.QnA.generate_dev_setup_questions import generate_dev_setup_questions
from main.Onboarding.generators.QnA.generate_code_convention_questions import generate_code_conventions_questions


def generate_all_onboarding_data(
    github_db_path,
    gmail_db_path=None,
    provider='openai',
    model=None,
    generators_to_run=None
):
    """
    Generate all onboarding documentation data
    
    Args:
        github_db_path: Path to GitHub vector database
        gmail_db_path: Optional path to Gmail vector database
        provider: LLM provider (default: 'openai')
        model: Optional model name
        generators_to_run: Optional list of generator names to run. If None, runs all.
                         Reading: 'repo_structure', 'tech_stacks', 'reading_overview',
                                  'app_features', 'dev_setup', 'code_conventions'
                         BugFix: 'coding_questions', 'pr_tutorials'
                         Practice: 'practice_questions'
                         QnA: 'repo_structure_questions', 'tech_stack_questions', 'overview_questions',
                              'app_features_questions', 'dev_setup_questions', 'code_conventions_questions'
    
    Returns:
        Dictionary mapping generator names to output file paths
    """
    
    print("\n" + "="*70)
    print("ONBOARDING DATA GENERATION - ALL GENERATORS")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Define all generators
    all_generators = {
        # Reading generators
        'repo_structure': {
            'name': 'Repository Structure',
            'func': generate_repo_structure_data,
            'output': 'onboarding_repo_structure.json',
            'category': 'reading'
        },
        'tech_stacks': {
            'name': 'Tech Stack',
            'func': generate_tech_stack_data,
            'output': 'onboarding_tech_stack.json',
            'category': 'reading'
        },
        'reading_overview': {
            'name': 'Reading Overview',
            'func': generate_reading_overview,
            'output': 'onboarding_project_overview.json',
            'category': 'reading'
        },
        'app_features': {
            'name': 'App Features',
            'func': generate_app_features_data,
            'output': 'onboarding_app_features.json',
            'category': 'reading'
        },
        'dev_setup': {
            'name': 'Dev Setup',
            'func': generate_dev_setup_data,
            'output': 'onboarding_dev_setup.json',
            'category': 'reading'
        },
        'code_conventions': {
            'name': 'Code Conventions',
            'func': generate_code_conventions_data,
            'output': 'onboarding_code_conventions.json',
            'category': 'reading'
        },
        # BugFix generators
        'coding_questions': {
            'name': 'Coding Questions',
            'func': generate_coding_questions,
            'output': 'onboarding_coding_questions.json',
            'category': 'bugfix'
        },
        'pr_tutorials': {
            'name': 'PR Tutorials',
            'func': generate_pr_tutorials,
            'output': 'onboarding_pr_tutorials.json',
            'category': 'bugfix'
        },
        # Practice generators
        'practice_questions': {
            'name': 'Practice Questions',
            'func': generate_practice_questions,
            'output': 'onboarding_practice_questions.json',
            'category': 'practice'
        },
        # QnA generators
        'repo_structure_questions': {
            'name': 'Repo Structure Questions',
            'func': generate_repo_structure_questions,
            'output': 'onboarding_repo_structure_questions.json',
            'category': 'qna'
        },
        'tech_stack_questions': {
            'name': 'Tech Stack Questions',
            'func': generate_tech_stack_questions,
            'output': 'onboarding_tech_stack_questions.json',
            'category': 'qna'
        },
        'overview_questions': {
            'name': 'Overview Questions',
            'func': generate_overview_questions,
            'output': 'onboarding_overview_questions.json',
            'category': 'qna'
        },
        'app_features_questions': {
            'name': 'App Features Questions',
            'func': generate_app_features_questions,
            'output': 'onboarding_app_features_questions.json',
            'category': 'qna'
        },
        'dev_setup_questions': {
            'name': 'Dev Setup Questions',
            'func': generate_dev_setup_questions,
            'output': 'onboarding_dev_setup_questions.json',
            'category': 'qna'
        },
        'code_conventions_questions': {
            'name': 'Code Conventions Questions',
            'func': generate_code_conventions_questions,
            'output': 'onboarding_code_conventions_questions.json',
            'category': 'qna'
        }
    }
    
    # Determine which generators to run
    if generators_to_run is None:
        generators_to_run = list(all_generators.keys())
    else:
        # Validate generator names
        invalid = [g for g in generators_to_run if g not in all_generators]
        if invalid:
            print(f"⚠️  Warning: Invalid generator names: {invalid}")
            generators_to_run = [g for g in generators_to_run if g in all_generators]
    
    print(f"Running {len(generators_to_run)} generator(s): {', '.join([all_generators[g]['name'] for g in generators_to_run])}\n")
    
    results = {}
    start_time = datetime.now()
    
    for idx, gen_key in enumerate(generators_to_run, 1):
        gen_info = all_generators[gen_key]
        gen_name = gen_info['name']
        
        print("\n" + "-"*70)
        print(f"[{idx}/{len(generators_to_run)}] Running {gen_name} Generator...")
        print("-"*70 + "\n")
        
        try:
            gen_start = datetime.now()
            # Call generator function - most use db_path instead of github_db_path
            # Some generators have additional parameters, but they have defaults
            if gen_key in ['coding_questions', 'pr_tutorials', 'practice_questions']:
                # BugFix and Practice generators use db_path parameter
                output_file = gen_info['func'](
                    db_path=github_db_path,
                    gmail_db_path=gmail_db_path,
                    provider=provider,
                    model=model
                )
            elif gen_key.startswith(('repo_structure_questions', 'tech_stack_questions', 
                                     'overview_questions', 'app_features_questions', 
                                     'dev_setup_questions', 'code_conventions_questions')):
                # QnA generators use db_path parameter
                output_file = gen_info['func'](
                    db_path=github_db_path,
                    gmail_db_path=gmail_db_path,
                    provider=provider,
                    model=model
                )
            else:
                # Reading generators use github_db_path parameter
                output_file = gen_info['func'](
                    github_db_path,
                    gmail_db_path,
                    provider,
                    model
                )
            gen_duration = (datetime.now() - gen_start).total_seconds()
            
            # Check if generator returned None (indicating failure)
            if output_file is None:
                print(f"\n❌ {gen_name} returned None - generation failed")
                results[gen_key] = {
                    'status': 'error',
                    'error': 'Generator returned None - likely due to connection error or invalid response',
                    'duration_seconds': gen_duration
                }
            else:
                results[gen_key] = {
                    'status': 'success',
                    'output_file': str(output_file),
                    'duration_seconds': gen_duration
                }
                
                print(f"\n✅ {gen_name} completed in {gen_duration:.1f}s")
                print(f"   Output: {output_file}\n")
            
        except Exception as e:
            print(f"\n❌ {gen_name} failed: {str(e)}\n")
            import traceback
            traceback.print_exc()
            
            results[gen_key] = {
                'status': 'error',
                'error': str(e),
                'duration_seconds': 0
            }
    
    # Summary
    total_duration = (datetime.now() - start_time).total_seconds()
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    failed = len(results) - successful
    
    print("\n" + "="*70)
    print("GENERATION SUMMARY")
    print("="*70)
    print(f"Total duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
    print(f"Successful: {successful}/{len(generators_to_run)}")
    print(f"Failed: {failed}/{len(generators_to_run)}")
    print("\nResults:")
    for gen_key, result in results.items():
        status_icon = "✅" if result['status'] == 'success' else "❌"
        gen_name = all_generators[gen_key]['name']
        if result['status'] == 'success':
            print(f"  {status_icon} {gen_name}: {result['output_file']} ({result['duration_seconds']:.1f}s)")
        else:
            print(f"  {status_icon} {gen_name}: {result.get('error', 'Unknown error')}")
    print("="*70 + "\n")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate all onboarding documentation data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all generators
  python generate_all_onboarding.py

  # Run specific generators
  python generate_all_onboarding.py --generators repo_structure tech_stacks

  # Custom database paths
  python generate_all_onboarding.py --github-db path/to/github/db --gmail-db path/to/gmail/db
        """
    )
    
    parser.add_argument(
        '--github-db',
        type=str,
        default='../../data/VectorDB/multi_index',
        help='Path to multi-index vector database'
    )
    
    parser.add_argument(
        '--gmail-db',
        type=str,
        default='../../data/VectorDB/gmail_chunks',
        help='Path to Gmail vector database (optional)'
    )
    
    parser.add_argument(
        '--provider',
        type=str,
        default='openai',
        help='LLM provider (default: openai)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Optional model name'
    )
    
    parser.add_argument(
        '--generators',
        nargs='+',
        choices=[
            # Reading
            'repo_structure', 'tech_stacks', 'reading_overview', 
            'app_features', 'dev_setup', 'code_conventions',
            # BugFix
            'coding_questions', 'pr_tutorials',
            # Practice
            'practice_questions',
            # QnA
            'repo_structure_questions', 'tech_stack_questions', 'overview_questions',
            'app_features_questions', 'dev_setup_questions', 'code_conventions_questions'
        ],
        default=None,
        help='Specific generators to run (default: all)'
    )
    
    args = parser.parse_args()
    
    generate_all_onboarding_data(
        github_db_path=args.github_db,
        gmail_db_path=args.gmail_db if args.gmail_db else None,
        provider=args.provider,
        model=args.model,
        generators_to_run=args.generators
    )

