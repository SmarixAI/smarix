
import json
import os
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize OpenAI client with API key from .env
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("⚠️  Warning: OPENAI_API_KEY not found in .env file")
    print(f"   Looking for .env at: {env_path}")
    client = None
else:
    print(f"✓ OpenAI API key loaded from {env_path}")
    client = OpenAI(api_key=api_key)

def load_repo_data(filepath):
    """Load the repository data from JSON file with proper UTF-8 encoding"""
    # FIX: Added encoding='utf-8' to handle Unicode characters
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_code_changes_from_pr(pr_data, file_path):
    """Extract actual code changes (patch/diff) for a specific file from PR data"""
    changed_files = pr_data.get('changed_files', [])
    
    for file_item in changed_files:
        if isinstance(file_item, dict):
            filename = file_item.get('filename') or file_item.get('path', '')
            # Match by full path or just filename
            if filename == file_path or filename.endswith(file_path.split('/')[-1]) or file_path.endswith(filename.split('/')[-1]):
                patch = file_item.get('patch', '')
                additions = file_item.get('additions', 0)
                deletions = file_item.get('deletions', 0)
                status = file_item.get('status', 'modified')
                return {
                    'patch': patch,
                    'additions': additions,
                    'deletions': deletions,
                    'changes': additions + deletions,
                    'status': status
                }
    
    return None

def analyze_code_changes_with_ai(file_info, pr_info, employee_name, code_changes):
    """Use AI to analyze actual code changes (additions/deletions) and determine importance"""
    if not client:
        return False, []
    
    file_path = file_info.get('path', '')
    file_name = file_info.get('name', '')
    lines = file_info.get('lines', 0)
    
    # Build prompt with actual code changes
    changes_summary = ""
    if code_changes and code_changes.get('patch'):
        patch = code_changes.get('patch', '')[:3000]  # Limit patch size for API
        additions = code_changes.get('additions', 0)
        deletions = code_changes.get('deletions', 0)
        status = code_changes.get('status', 'modified')
        
        changes_summary = f"""
        Code Changes Summary:
        - Status: {status}
        - Lines Added: {additions}
        - Lines Deleted: {deletions}
        - Total Changes: {additions + deletions}
        
        Actual Code Changes (Patch/Diff showing what was added/deleted):
        {patch}
        """
    else:
        # Fallback to file content if no patch available
        file_content = file_info.get('content', '')[:2000]
        changes_summary = f"""
        File Content (first 2000 chars - no patch available):
        {file_content}
        """
    
    prompt = f"""
    Analyze the ACTUAL CODE CHANGES made by employee {employee_name} and determine:
    1. Do these changes impact something critical/important? (Yes/No)
    2. What specific questions should be asked about these changes?

    File: {file_path}
    File Name: {file_name}
    Lines of Code: {lines}
    PR Title: {pr_info.get('title', 'N/A')}
    PR Description: {pr_info.get('body', 'N/A')[:300]}
    
    {changes_summary}

    Respond in JSON format:
    {{
        "is_important": true/false,
        "reason": "brief explanation of why this is/isn't important",
        "impact_analysis": "what does this change impact? (e.g., business logic, security, performance, architecture)",
        "specific_questions": ["question1", "question2", "question3", "question4", "question5"]
    }}

    Mark as important if the changes:
    - Modify critical business logic or algorithms
    - Add/remove security-sensitive code
    - Change core system behavior or architecture
    - Introduce new dependencies or integrations
    - Modify data models or database schemas
    - Change API contracts or interfaces
    - Add complex error handling or edge cases
    - Modify authentication/authorization logic
    - Remove important functionality
    - Add new features that need explanation
    """
    
    try:
        # Try with response_format first (for newer API versions)
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer analyzing code changes for knowledge transfer. Analyze the actual code changes (additions/deletions shown in the patch) to understand their impact. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
        except TypeError:
            # Fallback for older API versions without response_format
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer analyzing code changes for knowledge transfer. Analyze the actual code changes (additions/deletions shown in the patch) to understand their impact. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
        
        content = response.choices[0].message.content.strip()
        # Try to extract JSON
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError("No valid JSON found in response")
        
        is_important = result.get('is_important', False)
        specific_questions = result.get('specific_questions', [])
        impact_analysis = result.get('impact_analysis', '')
        
        if is_important and impact_analysis:
            print(f"  ✓ AI analyzed changes: {impact_analysis}")
        
        return is_important, specific_questions
    except Exception as e:
        print(f"  ⚠️  AI code change analysis failed for {file_name}: {e}")
        # Fallback: consider important if large changes or core file
        if code_changes:
            total_changes = code_changes.get('additions', 0) + code_changes.get('deletions', 0)
            is_important = total_changes > 50 or any(keyword in file_path.lower() for keyword in ['service', 'api', 'controller', 'model', 'core'])
        else:
            is_important = lines > 100 or any(keyword in file_path.lower() for keyword in ['service', 'api', 'controller', 'model', 'core'])
        return is_important, []

def generate_section_specific_content_with_ai(file_info, pr_info, code_changes, section_type, context):
    """Use AI to generate section-specific content (title, description, questions) for Final Call, Handover, or Documentation"""
    if not client:
        # Fallback if client not initialized
        file_names = file_info.get('name', 'file')
        short_title = f"Knowledge transfer for {file_names}"
        if section_type == 'final_call':
            description = f"Critical questions to extract knowledge about {file_names} before departure"
            questions = ["What critical information should be captured?"]
        elif section_type == 'handover':
            description = f"Handover session for {file_names} - knowledge transfer to successor"
            questions = ["What should be covered in the handover session?"]
        else:  # documentation
            description = f"Documentation requirements for {file_names}"
            questions = ["What needs to be documented?"]
        return short_title, description, questions
    
    # Build section-specific prompts
    section_prompts = {
        'final_call': {
            'focus': 'URGENT CRITICAL QUESTIONS that must be asked before the employee leaves',
            'purpose': 'extract critical knowledge quickly in a final call session',
            'tone': 'urgent, focused on critical information that cannot be lost',
            'questions_focus': 'critical business logic, edge cases, failure scenarios, undocumented behavior, production issues'
        },
        'handover': {
            'focus': 'DETAILED KNOWLEDGE TRANSFER for pairing sessions with a successor',
            'purpose': 'facilitate hands-on knowledge transfer through pairing and walkthroughs',
            'tone': 'comprehensive, focused on teaching and demonstrating',
            'questions_focus': 'architecture walkthrough, integration points, testing strategies, common mistakes, examples'
        },
        'documentation': {
            'focus': 'WRITTEN DOCUMENTATION requirements that need to be created',
            'purpose': 'identify what needs to be documented in writing for future reference',
            'tone': 'focused on creating permanent written records',
            'questions_focus': 'what to document, documentation structure, missing documentation, maintenance procedures'
        }
    }
    
    section_info = section_prompts.get(section_type, section_prompts['final_call'])
    
    # Build code changes context
    changes_context = ""
    if code_changes and code_changes.get('patch'):
        patch = code_changes.get('patch', '')[:2000]
        additions = code_changes.get('additions', 0)
        deletions = code_changes.get('deletions', 0)
        changes_context = f"""
        Code Changes:
        - Lines Added: {additions}
        - Lines Deleted: {deletions}
        - Patch (first 2000 chars): {patch}
        """
    
    prompt = f"""
    Generate {section_type.replace('_', ' ').title()} content for employee offboarding.

    File: {file_info.get('path', 'N/A')}
    File Type: {file_info.get('extension', 'N/A')}
    Lines of Code: {file_info.get('lines', 'N/A')}
    PR Title: {pr_info.get('title', 'N/A')}
    PR Description: {pr_info.get('body', 'N/A')[:300]}
    {changes_context}
    Context: {context}

    Focus: {section_info['focus']}
    Purpose: {section_info['purpose']}
    Tone: {section_info['tone']}

    Respond in JSON format:
    {{
        "short_title": "A brief, clear title (5-10 words) specific to {section_type}. Examples: Final Call: 'Critical Build Configuration Questions', Handover: 'Build System Handover Session', Documentation: 'Build Configuration Documentation'",
        "description": "A {section_type}-specific description (100-150 words) explaining: 1. What needs to be covered in this {section_type} session, 2. Why it's important for this specific section, 3. What the outcome should be",
        "questions": ["question1", "question2", "question3", "question4", "question5"]
    }}

    Requirements:
    - short_title should be unique to {section_type} (NOT generic)
    - description should be tailored to {section_type} purpose
    - questions should focus on: {section_info['questions_focus']}
    - Questions should be specific to {section_type} and different from other sections
    - NOT just the filename - use meaningful titles
    """
    
    try:
        # Try with response_format first (for newer API versions)
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are an expert at creating {section_type.replace('_', ' ')} content for employee offboarding. Each section should have UNIQUE, section-specific content. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
        except TypeError:
            # Fallback for older API versions without response_format
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are an expert at creating {section_type.replace('_', ' ')} content for employee offboarding. Each section should have UNIQUE, section-specific content. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
        
        content = response.choices[0].message.content.strip()
        # Try to extract JSON
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError("No valid JSON found in response")
        
        short_title = result.get('short_title', '')
        description = result.get('description', '')
        questions = result.get('questions', [])
        
        # Fallback if AI didn't provide all fields
        if not short_title or not description:
            file_names = file_info.get('name', 'file')
            short_title = short_title or f"{section_type.replace('_', ' ').title()}: {file_names}"
            description = description or f"{section_type.replace('_', ' ').title()} for {file_info.get('path', 'file')}"
        
        if not questions:
            questions = ["What should be covered in this session?"]
        
        return short_title, description, questions[:6]  # Limit to 6 questions
    except Exception as e:
        print(f"  ⚠️  AI {section_type} content generation failed: {e}")
        # Fallback to manual description
        file_names = file_info.get('name', 'file')
        short_title = f"{section_type.replace('_', ' ').title()}: {file_names}"
        description = f"{section_type.replace('_', ' ').title()} for {file_info.get('path', 'file')}"
        questions = ["What should be covered in this session?"]
        return short_title, description, questions

def calculate_priority(file_info, pr_info):
    """Calculate priority based on file characteristics"""
    # Simple heuristic-based priority
    lines = file_info.get('lines', 0)
    extension = file_info.get('extension', '')

    # Configuration and asset files - LOW
    asset_extensions = [
        '.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.bmp', '.tiff',
        '.txt', '.md', '.markdown', '.lock', '.LICENSE', '.pdf', '.doc', '.docx',
        '.woff', '.woff2', '.ttf', '.eot', '.otf', '.mp4', '.mp3', '.avi', '.mov'
    ]
    if extension in asset_extensions:
        return 'low'

    # Core logic files - HIGH/CRITICAL
    code_extensions = [
        '.dart', '.java', '.py', '.cpp', '.c', '.js', '.ts', '.tsx', '.jsx',
        '.vue', '.swift', '.kt', '.scala', '.go', '.rs', '.php', '.rb', '.r',
        '.cs', '.m', '.mm', '.h', '.hpp', '.hxx', '.cc', '.cxx', '.clj', '.cljs',
        '.elm', '.ex', '.exs', '.erl', '.hs', '.lua', '.pl', '.pm', '.sh', '.bash',
        '.zsh', '.fish', '.ps1', '.psm1', '.vbs', '.sql', '.rq', '.sparql'
    ]
    if extension in code_extensions:
        if lines > 200:
            return 'critical'
        elif lines > 100:
            return 'high'
        else:
            return 'medium'

    # Configuration files - MEDIUM
    config_extensions = [
        '.xml', '.yaml', '.yml', '.json', '.json5', '.toml', '.ini', '.conf',
        '.properties', '.gradle', '.maven', '.sbt', '.cmake', '.make', '.mk',
        '.env', '.config', '.cfg', '.settings', '.prefs', '.plist'
    ]
    if extension in config_extensions:
        return 'medium'

    # Build files and scripts
    build_files = ['Makefile', 'makefile', 'CMakeLists.txt', 'build.gradle', 
                   'pom.xml', 'package.json', 'Cargo.toml', 'go.mod', 'go.sum',
                   'requirements.txt', 'Pipfile', 'setup.py', 'pyproject.toml',
                   'composer.json', 'Gemfile', 'Rakefile', 'Podfile', 'pubspec.yaml']
    file_name = file_info.get('name', '').lower()
    if any(build_file.lower() in file_name for build_file in build_files):
        return 'medium'

    return 'medium'

def generate_final_call_questions(file_info, pr_info):
    """Generate questions to extract critical knowledge before departure"""
    extension = file_info.get('extension', '')
    file_path = file_info.get('path', '')
    file_name = file_info.get('name', '')
    pr_title = pr_info.get('title', 'this change')

    questions = []

    # Define extension lists
    code_extensions = [
        '.dart', '.java', '.py', '.cpp', '.c', '.js', '.ts', '.tsx', '.jsx',
        '.vue', '.swift', '.kt', '.scala', '.go', '.rs', '.php', '.rb', '.r',
        '.cs', '.m', '.mm', '.h', '.hpp', '.hxx', '.cc', '.cxx', '.clj', '.cljs',
        '.elm', '.ex', '.exs', '.erl', '.hs', '.lua', '.pl', '.pm', '.sh', '.bash',
        '.zsh', '.fish', '.ps1', '.psm1', '.vbs', '.sql', '.rq', '.sparql'
    ]
    config_extensions = [
        '.xml', '.yaml', '.yml', '.json', '.json5', '.toml', '.ini', '.conf',
        '.properties', '.gradle', '.maven', '.sbt', '.cmake', '.make', '.mk',
        '.env', '.config', '.cfg', '.settings', '.prefs', '.plist', '.kt'
    ]
    build_files = ['Makefile', 'makefile', 'CMakeLists.txt', 'build.gradle', 
                   'pom.xml', 'package.json', 'Cargo.toml', 'go.mod', 'go.sum',
                   'requirements.txt', 'Pipfile', 'setup.py', 'pyproject.toml',
                   'composer.json', 'Gemfile', 'Rakefile', 'Podfile', 'pubspec.yaml',
                   'webpack.config', 'vite.config', 'rollup.config', 'tsconfig.json',
                   'babel.config', '.eslintrc', '.prettierrc']
    doc_extensions = ['.md', '.markdown', '.txt', '.rst', '.adoc', '.asciidoc', 
                      '.org', '.wiki', '.tex', '.latex', '']

    # Core logic files
    if extension in code_extensions:
        questions = [
            f"What critical business logic in {file_name} isn't documented?",
            f"What edge cases or failure scenarios have you encountered with this code?",
            f"What technical debt or known issues should the next person be aware of?",
            "What performance considerations are important here?",
            "What external dependencies or integrations does this component rely on?",
            f"Can you explain the key design decisions you made?",
            "What would cause this to break in production and how would you debug it?"
        ]

    # Configuration files
    elif extension in config_extensions:
        questions = [
            f"What critical configurations in {file_name} must not be changed?",
            "What environment-specific settings exist and why?",
            "What happens if these configurations are modified incorrectly?",
            f"Can you explain the context behind these configurations?",
            "What deployment or build processes depend on these configurations?"
        ]

    # Build files
    elif any(build_file.lower() in file_name.lower() for build_file in build_files):
        questions = [
            "What are the critical build targets and their purposes?",
            "What dependencies must be installed for the build to work?",
            "What compiler flags or options are important and why?",
            "What testing procedures are defined in the build process?",
            "What platform-specific considerations exist?"
        ]

    # Documentation files
    elif extension in doc_extensions:
        if 'README' in file_name:
            questions = [
                "What critical setup or usage information is in the README?",
                "What common issues or FAQs should be added?",
                "What's missing from the README that users frequently ask about?",
                "How should the README be maintained going forward?"
            ]
        elif 'LICENSE' in file_name:
            questions = [
                "What are the licensing requirements for this project?",
                "Are there any third-party license considerations?",
                "What attribution requirements exist?"
            ]
        else:
            questions = [
                f"What critical information is in {file_name}?",
                "Who is the audience for this documentation?",
                "What processes or procedures are documented here?"
            ]

    else:
        questions = [
            f"What is the purpose of {file_name}?",
            "What would break if this file was modified incorrectly?",
            "What context should the next person know about this?"
        ]

    return questions[:6]  # Limit to 6 questions

def generate_handover_questions(file_info, pr_info):
    """Generate questions for knowledge transfer to successor"""
    extension = file_info.get('extension', '')
    file_path = file_info.get('path', '')
    file_name = file_info.get('name', '')

    questions = []

    # Define extension lists
    code_extensions = [
        '.dart', '.java', '.py', '.cpp', '.c', '.js', '.ts', '.tsx', '.jsx',
        '.vue', '.swift', '.kt', '.scala', '.go', '.rs', '.php', '.rb', '.r',
        '.cs', '.m', '.mm', '.h', '.hpp', '.hxx', '.cc', '.cxx', '.clj', '.cljs',
        '.elm', '.ex', '.exs', '.erl', '.hs', '.lua', '.pl', '.pm', '.sh', '.bash',
        '.zsh', '.fish', '.ps1', '.psm1', '.vbs', '.sql', '.rq', '.sparql'
    ]
    config_extensions = [
        '.xml', '.yaml', '.yml', '.json', '.json5', '.toml', '.ini', '.conf',
        '.properties', '.gradle', '.maven', '.sbt', '.cmake', '.make', '.mk',
        '.env', '.config', '.cfg', '.settings', '.prefs', '.plist', '.kt'
    ]
    build_files = ['Makefile', 'makefile', 'CMakeLists.txt', 'build.gradle', 
                   'pom.xml', 'package.json', 'Cargo.toml', 'go.mod', 'go.sum',
                   'requirements.txt', 'Pipfile', 'setup.py', 'pyproject.toml',
                   'composer.json', 'Gemfile', 'Rakefile', 'Podfile', 'pubspec.yaml',
                   'webpack.config', 'vite.config', 'rollup.config', 'tsconfig.json',
                   'babel.config', '.eslintrc', '.prettierrc']

    if extension in code_extensions:
        questions = [
            f"Can you walk the successor through the architecture of {file_name}?",
            "What are the main functions/classes and their responsibilities?",
            "How does this integrate with other parts of the system?",
            "What testing strategy should be used for changes here?",
            "What common mistakes should the successor avoid?",
            "Where can they find examples of similar implementations?"
        ]

    elif extension in config_extensions:
        questions = [
            f"Can you explain the structure and purpose of {file_name}?",
            "What values are safe to modify vs. dangerous to change?",
            "How do you test changes to these configurations?",
            "What's the deployment process when this changes?"
        ]

    elif any(build_file.lower() in file_name.lower() for build_file in build_files):
        questions = [
            "Can you walk through the build process step by step?",
            "How do you debug build failures?",
            "What's the typical development workflow with this build system?",
            "What make targets are most commonly used?"
        ]

    else:
        questions = [
            f"Can you explain how {file_name} fits into the project?",
            "What should the successor know to maintain this?",
            "What resources or tools are needed to work with this?"
        ]

    return questions[:5]

def generate_documentation_questions(file_info, pr_info):
    """Generate questions focused on what needs to be documented"""
    extension = file_info.get('extension', '')
    file_path = file_info.get('path', '')
    file_name = file_info.get('name', '')

    questions = []

    # Define extension lists
    code_extensions = [
        '.dart', '.java', '.py', '.cpp', '.c', '.js', '.ts', '.tsx', '.jsx',
        '.vue', '.swift', '.kt', '.scala', '.go', '.rs', '.php', '.rb', '.r',
        '.cs', '.m', '.mm', '.h', '.hpp', '.hxx', '.cc', '.cxx', '.clj', '.cljs',
        '.elm', '.ex', '.exs', '.erl', '.hs', '.lua', '.pl', '.pm', '.sh', '.bash',
        '.zsh', '.fish', '.ps1', '.psm1', '.vbs', '.sql', '.rq', '.sparql'
    ]
    config_extensions = [
        '.xml', '.yaml', '.yml', '.json', '.json5', '.toml', '.ini', '.conf',
        '.properties', '.gradle', '.maven', '.sbt', '.cmake', '.make', '.mk',
        '.env', '.config', '.cfg', '.settings', '.prefs', '.plist', '.kt'
    ]
    build_files = ['Makefile', 'makefile', 'CMakeLists.txt', 'build.gradle', 
                   'pom.xml', 'package.json', 'Cargo.toml', 'go.mod', 'go.sum',
                   'requirements.txt', 'Pipfile', 'setup.py', 'pyproject.toml',
                   'composer.json', 'Gemfile', 'Rakefile', 'Podfile', 'pubspec.yaml',
                   'webpack.config', 'vite.config', 'rollup.config', 'tsconfig.json',
                   'babel.config', '.eslintrc', '.prettierrc']

    if extension in code_extensions:
        questions = [
            f"What functions/classes in {file_name} need inline documentation?",
            "What architectural diagrams would help explain this component?",
            "What API contracts or interfaces need to be documented?",
            "What example use cases should be documented?",
            "What troubleshooting guide should exist for this code?"
        ]

    elif extension in config_extensions:
        questions = [
            "What configuration options need documentation?",
            "What are the valid values and constraints for each setting?",
            "What examples of correct configurations should be documented?",
            "What troubleshooting steps should be documented?"
        ]

    elif any(build_file.lower() in file_name.lower() for build_file in build_files):
        questions = [
            "What build targets need documentation?",
            "What build prerequisites should be documented?",
            "What troubleshooting steps for build failures should be documented?",
            "What platform-specific instructions are needed?"
        ]

    else:
        questions = [
            f"What about {file_name} should be documented for future reference?",
            "What README or wiki entry should exist for this?",
            "What common questions should be answered in documentation?"
        ]

    return questions[:5]

def find_top_contributor(repo_data):
    """Find the user with the most contributions from commits and PRs"""
    contributor_stats = defaultdict(lambda: {'commits': 0, 'prs': 0, 'total': 0})
    all_contributors = set()  # Track all contributor names for name matching
    
    # Count commits
    commits = repo_data.get('commits', [])
    for commit in commits:
        author = commit.get('author', {})
        if isinstance(author, dict):
            author_name = author.get('name') or author.get('login') or 'unknown'
        else:
            author_name = str(author) if author else 'unknown'
        if author_name != 'unknown':
            contributor_stats[author_name]['commits'] += 1
            contributor_stats[author_name]['total'] += 1
            all_contributors.add(author_name)
    
    # Count PRs
    prs = repo_data.get('prs', [])
    for pr in prs:
        user = pr.get('user', {})
        if isinstance(user, dict):
            user_name = user.get('login') or user.get('name') or 'unknown'
        else:
            user_name = str(user) if user else 'unknown'
        if user_name != 'unknown':
            contributor_stats[user_name]['prs'] += 1
            contributor_stats[user_name]['total'] += 1
            all_contributors.add(user_name)
    
    if not contributor_stats:
        return None, None, set()
    
    # Find top contributor by total contributions
    top_contributor = max(contributor_stats.items(), key=lambda x: x[1]['total'])
    return top_contributor[0], top_contributor[1], all_contributors

def find_closest_user_name(task_description, all_contributors):
    """Find the closest matching user name from contributors based on task description"""
    if not all_contributors or not task_description:
        return None
    
    # Extract potential names/keywords from task description
    description_lower = task_description.lower()
    best_match = None
    best_score = 0.0
    
    for contributor in all_contributors:
        contributor_lower = contributor.lower()
        
        # Check for exact substring match (highest priority)
        if contributor_lower in description_lower or description_lower in contributor_lower:
            return contributor
        
        # Calculate similarity score
        score = SequenceMatcher(None, description_lower, contributor_lower).ratio()
        
        # Also check if any word in description matches contributor name
        description_words = description_lower.split()
        for word in description_words:
            if len(word) > 3:  # Only check meaningful words
                word_score = SequenceMatcher(None, word, contributor_lower).ratio()
                if word_score > 0.7:  # High similarity threshold
                    score = max(score, word_score * 1.2)  # Boost score for word matches
        
        if score > best_score:
            best_score = score
            best_match = contributor
    
    # Return match if similarity is above threshold
    if best_score > 0.5:
        return best_match
    
    return None

def filter_data_by_contributor(repo_data, contributor_name):
    """Filter repository data to only include contributions from the specified contributor"""
    filtered_data = {
        'code_files': [],
        'documentation': [],
        'pull_requests': []
    }
    
    # Get files changed by this contributor
    contributor_files = set()
    
    # Check commits
    commits = repo_data.get('commits', [])
    for commit in commits:
        author = commit.get('author', {})
        if isinstance(author, dict):
            author_name = author.get('name') or author.get('login') or 'unknown'
        else:
            author_name = str(author) if author else 'unknown'
        
        if author_name == contributor_name:
            changed_files = commit.get('changed_files', [])
            for file_path in changed_files:
                if isinstance(file_path, dict):
                    file_path = file_path.get('filename') or file_path.get('path', '')
                contributor_files.add(file_path)
    
    # Check PRs
    prs = repo_data.get('prs', [])
    for pr in prs:
        user = pr.get('user', {})
        if isinstance(user, dict):
            user_name = user.get('login') or user.get('name') or 'unknown'
        else:
            user_name = str(user) if user else 'unknown'
        
        if user_name == contributor_name:
            changed_files = pr.get('changed_files', [])
            for file_item in changed_files:
                if isinstance(file_item, dict):
                    file_path = file_item.get('filename') or file_item.get('path', '')
                else:
                    file_path = str(file_item)
                if file_path:
                    contributor_files.add(file_path)
            
            # Add PR to filtered data
            filtered_data['pull_requests'].append(pr)
    
    # Filter code files
    code_files = repo_data.get('code_files', [])
    for file_info in code_files:
        file_path = file_info.get('path', '')
        if file_path in contributor_files:
            filtered_data['code_files'].append(file_info)
    
    # Filter documentation
    documentation = repo_data.get('documentation', [])
    for doc_info in documentation:
        doc_path = doc_info.get('path', '')
        if doc_path in contributor_files:
            filtered_data['documentation'].append(doc_info)
    
    return filtered_data

def group_files_by_component(files):
    """Group related files together by functional area"""
    groups = {}

    for file_info in files:
        path = file_info.get('path', '')
        name = file_info.get('name', '')
        extension = file_info.get('extension', '')

        # Determine component based on path and file type
        if 'test' in path.lower() or 'spec' in path.lower():
            component = 'testing'
        elif extension in ['.svg', '.png', '.jpg', '.gif', '.ico']:
            component = 'assets'
        elif 'LICENSE' in name or 'license' in name.lower():
            component = 'licensing'
        elif 'README' in name or 'readme' in name.lower():
            component = 'documentation'
        elif 'Makefile' in name or 'makefile' in name:
            component = 'build_system'
        elif any(config in name.lower() for config in ['manifest', 'gradle', 'config', 'pubspec']):
            component = 'configuration'
        elif 'model' in path.lower() or 'entity' in path.lower():
            component = 'data_models'
        elif 'service' in path.lower() or 'api' in path.lower():
            component = 'services'
        elif 'view' in path.lower() or 'ui' in path.lower() or 'widget' in path.lower():
            component = 'ui_components'
        elif 'util' in path.lower() or 'helper' in path.lower():
            component = 'utilities'
        elif extension in ['.c', '.cpp', '.h', '.hpp']:
            component = 'core_logic'
        elif extension in ['.dart', '.java', '.py', '.js', '.ts']:
            component = 'application_logic'
        else:
            component = 'miscellaneous'

        if component not in groups:
            groups[component] = []
        groups[component].append(file_info)

    return groups

def generate_knowledge_transfer_tasks(repo_data, use_ai=False, all_contributors=None, employee_name=None):
    """Generate three types of knowledge transfer task lists"""

    code_files = repo_data.get('code_files', [])
    documentation = repo_data.get('documentation', [])
    pull_requests = repo_data.get('pull_requests', [])

    # Combine code files and documentation
    all_files = code_files + documentation

    if not all_files:
        print("Warning: No files found in repository data")
        return {
            "final_call_tasks": {"category": "Final Call: Questions extract critical knowledge before departure", "tasks": []},
            "handover_tasks": {"category": "Handover: Questions adapted for knowledge transfer to candidates", "tasks": []},
            "documentation_tasks": {"category": "Documentation: Questions focus on what needs to be documented", "tasks": []}
        }

    # Group files by component
    file_groups = group_files_by_component(all_files)

    print(f"\nFound {len(all_files)} files grouped into {len(file_groups)} components:")
    for component, files in file_groups.items():
        print(f"  - {component}: {len(files)} files")

    # Create task lists for each category
    final_call_tasks = []
    handover_tasks = []
    documentation_tasks = []

    task_id_counter = 1

    for component, files in file_groups.items():
        # Skip empty groups
        if not files:
            continue

        # For large groups, take top files by lines of code
        if len(files) > 5:
            sorted_files = sorted(files, key=lambda x: x.get('lines', 0), reverse=True)[:5]
        else:
            sorted_files = files

        # Get relevant PR info (if available)
        pr_info = pull_requests[0] if pull_requests else {}

        # Calculate priority based on most important file
        priority = calculate_priority(sorted_files[0], pr_info)

        # File references
        references = ', '.join([f.get('path', '') for f in sorted_files])

        # Extract actual code changes from PR if available
        code_changes = None
        if pull_requests:
            file_path = sorted_files[0].get('path', '')
            code_changes = extract_code_changes_from_pr(pull_requests[0], file_path)
            if code_changes:
                print(f"  📝 Found code changes: +{code_changes.get('additions', 0)}/-{code_changes.get('deletions', 0)} lines")

        # Generate section-specific content using AI
        context = f"Component: {component.replace('_', ' ').title()}"
        file_names = ', '.join([f.get('name', '') for f in sorted_files[:3]])
        
        if use_ai:
            # Generate Final Call content
            try:
                fc_title, fc_description, fc_questions = generate_section_specific_content_with_ai(
                    sorted_files[0], pr_info, code_changes, 'final_call', context
                )
                print(f"  ✓ Generated Final Call content: {fc_title}")
            except Exception as e:
                print(f"  ⚠️  AI Final Call generation failed for {component}: {e}")
                fc_title = f"Final Call: {component.replace('_', ' ').title()}"
                fc_description = f"Critical questions about {file_names}"
                fc_questions = generate_final_call_questions(sorted_files[0], pr_info)
            
            # Generate Handover content
            try:
                ho_title, ho_description, ho_questions = generate_section_specific_content_with_ai(
                    sorted_files[0], pr_info, code_changes, 'handover', context
                )
                print(f"  ✓ Generated Handover content: {ho_title}")
            except Exception as e:
                print(f"  ⚠️  AI Handover generation failed for {component}: {e}")
                ho_title = f"Handover: {component.replace('_', ' ').title()}"
                ho_description = f"Handover session for {file_names}"
                ho_questions = generate_handover_questions(sorted_files[0], pr_info)
            
            # Generate Documentation content
            try:
                doc_title, doc_description, doc_questions = generate_section_specific_content_with_ai(
                    sorted_files[0], pr_info, code_changes, 'documentation', context
                )
                print(f"  ✓ Generated Documentation content: {doc_title}")
            except Exception as e:
                print(f"  ⚠️  AI Documentation generation failed for {component}: {e}")
                doc_title = f"Documentation: {component.replace('_', ' ').title()}"
                doc_description = f"Documentation requirements for {file_names}"
                doc_questions = generate_documentation_questions(sorted_files[0], pr_info)
        else:
            # Fallback without AI
            fc_title = f"Final Call: {component.replace('_', ' ').title()}"
            fc_description = f"Critical questions about {file_names}"
            fc_questions = generate_final_call_questions(sorted_files[0], pr_info)
            
            ho_title = f"Handover: {component.replace('_', ' ').title()}"
            ho_description = f"Handover session for {file_names}"
            ho_questions = generate_handover_questions(sorted_files[0], pr_info)
            
            doc_title = f"Documentation: {component.replace('_', ' ').title()}"
            doc_description = f"Documentation requirements for {file_names}"
            doc_questions = generate_documentation_questions(sorted_files[0], pr_info)
        
        # Use AI to analyze importance for final call
        is_important_file = False
        if use_ai and employee_name:
            try:
                is_important_file, _ = analyze_code_changes_with_ai(
                    sorted_files[0], pr_info, employee_name, code_changes
                )
            except Exception as e:
                print(f"  ⚠️  AI code change analysis failed: {e}")

        # Create Final Call task with section-specific content
        final_call_tasks.append({
            "taskId": f"FC{task_id_counter}",
            "title": fc_title,
            "description": fc_description,
            "reference": references,
            "questions": fc_questions,
            "priority": priority,
            "knowledge_type": ["TECHNICAL"],
            "estimated_time_minutes": 45 if priority in ['critical', 'high'] else 30,
            "knowledge_capture_method": "LIVE_WALKTHROUGH",
            "ai_analyzed": is_important_file
        })

        # Find suggested handover recipient using AI if available
        suggested_recipient = None
        suggested_recipient_reason = None
        if all_contributors:
            if use_ai and client:
                # Use AI to suggest the best recipient
                try:
                    suggestion_prompt = f"""
                    Based on this handover task, suggest the best person from the contributor list to handover this work to.
                    
                    Task: {ho_title}
                    Description: {ho_description}
                    Files: {references}
                    
                    Contributors: {', '.join(list(all_contributors)[:20])}
                    
                    Respond in JSON:
                    {{
                        "suggested_recipient": "name from contributors list",
                        "reason": "brief explanation why this person"
                    }}
                    """
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are an expert at matching tasks to team members based on their expertise. Respond only with valid JSON."},
                            {"role": "user", "content": suggestion_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=200,
                        response_format={"type": "json_object"}
                    )
                    content = response.choices[0].message.content.strip()
                    # Try to extract JSON
                    try:
                        if content.startswith('{'):
                            suggestion_result = json.loads(content)
                        else:
                            # Try to find JSON in the response
                            import re
                            json_match = re.search(r'\{[^}]+\}', content)
                            if json_match:
                                suggestion_result = json.loads(json_match.group())
                            else:
                                raise ValueError("No JSON found in response")
                    except:
                        # If JSON parsing fails, use string matching
                        suggested_recipient = find_closest_user_name(ho_title, all_contributors)
                        suggestion_result = {}
                    
                    if suggestion_result:
                        suggested_recipient = suggestion_result.get('suggested_recipient')
                        suggested_recipient_reason = suggestion_result.get('reason', '')
                        
                        # Verify the suggested name exists in contributors
                        if suggested_recipient and suggested_recipient not in all_contributors:
                            # Fallback to string matching
                            suggested_recipient = find_closest_user_name(ho_title, all_contributors)
                    else:
                        suggested_recipient = find_closest_user_name(ho_title, all_contributors)
                except Exception as e:
                    print(f"  ⚠️  AI recipient suggestion failed: {e}")
                    suggested_recipient = find_closest_user_name(ho_title, all_contributors)
            else:
                # Fallback to string matching
                suggested_recipient = find_closest_user_name(ho_title, all_contributors)
        
        # Create Handover task with section-specific content
        handover_task = {
            "taskId": f"HO{task_id_counter}",
            "title": ho_title,
            "description": ho_description,
            "reference": references,
            "questions": ho_questions,
            "priority": priority,
            "knowledge_type": ["TECHNICAL", "PROCESS"],
            "estimated_time_minutes": 60 if priority in ['critical', 'high'] else 30,
            "knowledge_capture_method": "PAIRING_SESSION",
            "ai_analyzed": is_important_file
        }
        
        # Add suggested recipient if found (always try to suggest someone)
        if suggested_recipient:
            handover_task["suggested_recipient"] = suggested_recipient
            if suggested_recipient_reason:
                handover_task["suggested_recipient_reason"] = suggested_recipient_reason
            print(f"  ✓ Suggested handover recipient: {suggested_recipient}" + (f" ({suggested_recipient_reason})" if suggested_recipient_reason else ""))
        elif all_contributors:
            # If no suggestion found, use the first available contributor as fallback
            suggested_recipient = list(all_contributors)[0] if all_contributors else None
            if suggested_recipient:
                handover_task["suggested_recipient"] = suggested_recipient
                handover_task["suggested_recipient_reason"] = "Fallback: First available contributor"
                print(f"  ℹ️  Using fallback handover recipient: {suggested_recipient}")
        
        handover_tasks.append(handover_task)

        # Create Documentation task with section-specific content
        documentation_tasks.append({
            "taskId": f"DOC{task_id_counter}",
            "title": doc_title,
            "description": doc_description,
            "reference": references,
            "questions": doc_questions,
            "priority": priority,
            "knowledge_type": ["TECHNICAL"],
            "estimated_time_minutes": 30,
            "knowledge_capture_method": "WRITTEN_DOCUMENTATION"
        })

        task_id_counter += 1

    return {
        "final_call_tasks": {
            "category": "Final Call: Questions extract critical knowledge before departure",
            "tasks": final_call_tasks
        },
        "handover_tasks": {
            "category": "Handover: Questions adapted for knowledge transfer to candidates",
            "tasks": handover_tasks
        },
        "documentation_tasks": {
            "category": "Documentation: Questions focus on what needs to be documented",
            "tasks": documentation_tasks
        }
    }

# Main execution
if __name__ == "__main__":
    print("Knowledge Transfer Task Generator")
    print("=" * 50)

    # Define paths
    #C:\Users\vishalke\smarix\backend\data\DataCollectionFromGit\CCExtractor\taskwarrior-flutter\taskwarrior-flutter.json
    input_file = Path(r"C:\Users\vishalke\smarix\backend\data\DataCollectionFromGit\CCExtractor\taskwarrior-flutter\taskwarrior-flutter.json")
    output_dir = Path(r"C:\Users\vishalke\smarix\backend\data\Offboarding")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load the repository data
    print(f"\nLoading repository data from {input_file}...")
    try:
        repo_data = load_repo_data(str(input_file))
        print(f"✓ Successfully loaded repository data")
    except FileNotFoundError:
        print(f"✗ Error: {input_file} not found")
        exit(1)
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        exit(1)

    # Find top contributor
    print("\nFinding user with most contributions...")
    top_contributor_result = find_top_contributor(repo_data)
    if not top_contributor_result or top_contributor_result[0] is None:
        print("✗ Error: No contributors found in repository data")
        exit(1)
    
    top_contributor_name, top_contributor_stats, all_contributors = top_contributor_result
    print(f"✓ Top contributor: {top_contributor_name}")
    print(f"  Commits: {top_contributor_stats['commits']}, PRs: {top_contributor_stats['prs']}, Total: {top_contributor_stats['total']}")
    print(f"  Total contributors in repository: {len(all_contributors)}")

    # Filter data to only include top contributor's contributions
    print(f"\nFiltering data for {top_contributor_name}...")
    filtered_data = filter_data_by_contributor(repo_data, top_contributor_name)
    print(f"✓ Filtered data: {len(filtered_data['code_files'])} code files, "
          f"{len(filtered_data['documentation'])} docs, {len(filtered_data['pull_requests'])} PRs")

    # Check for OpenAI API key
    use_ai = api_key is not None and client is not None
    if use_ai:
        print("✓ OpenAI API key detected - will use AI-enhanced descriptions")
    else:
        print("ℹ No OpenAI API key found - using standard descriptions")
        print("  (Set OPENAI_API_KEY in .env file to enable AI features)")

    # Generate tasks
    print("\nGenerating knowledge transfer tasks...")
    result = generate_knowledge_transfer_tasks(
        filtered_data, 
        use_ai=use_ai, 
        all_contributors=all_contributors,
        employee_name=top_contributor_name
    )

    # Helper function to load existing employee data
    def load_employee_data(file_path):
        """Load existing employee data from file, return empty structure if file doesn't exist"""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure it has the expected structure
                    if 'employees' in data:
                        return data
            except Exception as e:
                print(f"⚠️  Warning: Could not load existing data from {file_path}: {e}")
        return {"employees": []}

    # Helper function to save employee data
    def save_employee_data(file_path, employee_name, employee_data):
        """Save employee data, appending to existing data if file exists"""
        existing_data = load_employee_data(file_path)
        
        # Check if employee already exists and remove old entry
        existing_data["employees"] = [
            emp for emp in existing_data["employees"] 
            if emp.get("employee_name") != employee_name
        ]
        
        # Add new employee data
        new_employee_entry = {
            "employee_name": employee_name,
            **employee_data
        }
        
        existing_data["employees"].append(new_employee_entry)
        
        # Save updated data
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)

    # Helper function to get employeeId from users.json
    def get_employee_id_from_name(employee_name):
        """Try to get employeeId from users.json, otherwise use name as fallback"""
        try:
            repo_root = Path(__file__).resolve().parent.parent.parent
            users_file = repo_root / "data" / "Admin" / "users.json"
            
            if not users_file.exists():
                possible_paths = [
                    repo_root / "backend" / "data" / "Admin" / "users.json",
                    Path(r"C:\Users\vishalke\smarix\backend\data\Admin\users.json"),
                ]
                for path in possible_paths:
                    if path.exists():
                        users_file = path
                        break
            
            if users_file.exists():
                with open(users_file, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    users = users_data.get('users', [])
                    for user in users:
                        if user.get('name', '').lower() == employee_name.lower() or \
                           user.get('username', '').lower() == employee_name.lower():
                            return user.get('employeeId') or employee_name
        except Exception as e:
            print(f"  ⚠️  Could not load users.json: {e}")
        
        # Fallback: use name as employeeId
        return employee_name

    # Helper function to convert task to frontend format
    def convert_task_to_frontend_format(task, source='AI'):
        """Convert our task format to frontend expected format"""
        # Map priority from lowercase to capitalized
        priority_map = {
            'critical': 'High',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low'
        }
        
        # Extract tags from knowledge_type or other fields
        tags = task.get('knowledge_type', [])
        if not tags:
            tags = ['AI Generated']
        
        # Use short title if available, otherwise fall back to description
        task_title = task.get('title') or task.get('description', '')
        task_description = task.get('description', '')
        
        # Build frontend task
        frontend_task = {
            'id': task.get('taskId', ''),
            'title': task_title,  # Short title for display
            'description': task_description,  # Full description for expanded view
            'priority': priority_map.get(task.get('priority', 'low').lower(), 'Medium'),
            'tags': tags,
            'source': source
        }
        
        # Add optional fields if they exist
        if 'reference' in task:
            frontend_task['reference'] = task['reference']
        if 'questions' in task:
            frontend_task['questions'] = task['questions']
        if 'estimated_time_minutes' in task:
            frontend_task['estimated_time_minutes'] = task['estimated_time_minutes']
        if 'knowledge_capture_method' in task:
            frontend_task['knowledge_capture_method'] = task['knowledge_capture_method']
        if 'suggested_recipient' in task:
            frontend_task['suggested_recipient'] = task['suggested_recipient']
        if 'suggested_recipient_reason' in task:
            frontend_task['suggested_recipient_reason'] = task['suggested_recipient_reason']
        if 'ai_analyzed' in task:
            frontend_task['ai_analyzed'] = task['ai_analyzed']
        
        return frontend_task

    # Helper function to save frontend format file
    def save_frontend_format_file(output_dir, employee_name, result):
        """Save tasks in the format expected by the frontend"""
        employee_id = get_employee_id_from_name(employee_name)
        
        # Convert all tasks to frontend format
        ai_tasks = []
        
        # Add final call tasks
        for task in result['final_call_tasks']['tasks']:
            ai_tasks.append(convert_task_to_frontend_format(task, 'AI'))
        
        # Add handover tasks
        for task in result['handover_tasks']['tasks']:
            ai_tasks.append(convert_task_to_frontend_format(task, 'AI'))
        
        # Add documentation tasks
        for task in result['documentation_tasks']['tasks']:
            ai_tasks.append(convert_task_to_frontend_format(task, 'AI'))
        
        # Load existing file if it exists
        frontend_file = output_dir / "4employee_tasks_with_metadata_finalCallData.json"
        existing_data = {"employees": []}
        
        if frontend_file.exists():
            try:
                with open(frontend_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if 'employees' not in existing_data:
                        existing_data = {"employees": []}
            except Exception as e:
                print(f"  ⚠️  Could not load existing frontend file: {e}")
        
        # Remove existing entry for this employee
        existing_data["employees"] = [
            emp for emp in existing_data["employees"] 
            if emp.get("employeeId") != employee_id and emp.get("employee_name") != employee_name
        ]
        
        # Create new employee entry
        new_employee_entry = {
            "employeeId": employee_id,
            "employee_name": employee_name,  # Keep for backward compatibility
            "tasks": {
                "ai": ai_tasks,
                "manager": []  # Empty manager tasks array
            }
        }
        
        existing_data["employees"].append(new_employee_entry)
        
        # Save to file
        with open(frontend_file, "w", encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {frontend_file} (Employee: {employee_name}, ID: {employee_id}, Tasks: {len(ai_tasks)})")

    # Save to separate JSON files with employee name included
    print("\nSaving task lists...")
    final_call_path = output_dir / "final_call_tasks.json"
    save_employee_data(
        final_call_path,
        top_contributor_name,
        {"final_call_tasks": result["final_call_tasks"]}
    )
    print(f"✓ Saved {final_call_path} (Employee: {top_contributor_name})")

    handover_path = output_dir / "handover_tasks.json"
    save_employee_data(
        handover_path,
        top_contributor_name,
        {"handover_tasks": result["handover_tasks"]}
    )
    print(f"✓ Saved {handover_path} (Employee: {top_contributor_name})")

    documentation_path = output_dir / "documentation_tasks.json"
    save_employee_data(
        documentation_path,
        top_contributor_name,
        {"documentation_tasks": result["documentation_tasks"]}
    )
    print(f"✓ Saved {documentation_path} (Employee: {top_contributor_name})")
    
    # Save in frontend format
    print("\nSaving frontend format file...")
    save_frontend_format_file(output_dir, top_contributor_name, result)

    print("\n" + "=" * 50)
    print("Task Generation Summary:")
    print(f"  Employee: {top_contributor_name}")
    print(f"  Final Call Tasks: {len(result['final_call_tasks']['tasks'])}")
    print(f"  Handover Tasks: {len(result['handover_tasks']['tasks'])}")
    print(f"  Documentation Tasks: {len(result['documentation_tasks']['tasks'])}")
    print("=" * 50)


    # Display priority breakdown
    priorities = {}
    for task in result['final_call_tasks']['tasks']:
        p = task['priority']
        priorities[p] = priorities.get(p, 0) + 1

    print("\nPriority Breakdown:")
    for priority in ['critical', 'high', 'medium', 'low']:
        if priority in priorities:
            print(f"  {priority.upper()}: {priorities[priority]} tasks")

    print("\n✓ All files generated successfully!")
