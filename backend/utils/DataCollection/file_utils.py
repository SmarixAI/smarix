"""File utility functions and helpers."""

import os
import json
import hashlib
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from config.DataCollection.settings import Config


class FileUtils:
    """Utility class for file operations"""
    
    def __init__(self):
        self.config = Config()
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> None:
        """Create directory if it doesn't exist."""
        if directory_path:  # Avoid creating empty string directories
            Path(directory_path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension in lowercase."""
        return Path(filename).suffix.lower()
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """Get file size in megabytes."""
        try:
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        except OSError:
            return 0.0
    
    @staticmethod
    def is_binary_file(file_content: str) -> bool:
        """Check if file content appears to be binary."""
        try:
            # Try to encode as UTF-8
            file_content.encode('utf-8')
            # Check for null bytes (common in binary files)
            return '\x00' in file_content
        except UnicodeEncodeError:
            return True
    
    @staticmethod
    def count_lines_of_code(content: str) -> Dict[str, int]:
        """Count different types of lines in code."""
        if not content:
            return {'total': 0, 'code': 0, 'empty': 0, 'comments': 0}
        
        lines = content.splitlines()
        total_lines = len(lines)
        empty_lines = sum(1 for line in lines if not line.strip())
        
        # Enhanced comment detection for multiple languages
        comment_patterns = [
            '#',      # Python, Ruby, Shell
            '//',     # JavaScript, Java, C++, Go
            '/*',     # Multi-line comments
            '*',      # Continuation of multi-line comments
            '<!--',   # HTML comments
            '--',     # SQL, Haskell
            ';',      # Lisp, Assembly
            '%',      # LaTeX, Erlang
            '"',      # VimScript (when at start)
        ]
        
        comment_lines = 0
        for line in lines:
            stripped = line.strip()
            if stripped and any(stripped.startswith(pattern) for pattern in comment_patterns):
                comment_lines += 1
        
        code_lines = total_lines - empty_lines - comment_lines
        
        return {
            'total': total_lines,
            'code': max(0, code_lines),  # Ensure non-negative
            'empty': empty_lines,
            'comments': comment_lines
        }
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file system usage."""
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        sanitized = filename
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = 'unnamed_file'
        
        # Limit length (Windows has 260 char path limit)
        if len(sanitized) > 200:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:200-len(ext)] + ext
        
        return sanitized
    
    @staticmethod
    def save_json_data(data: Dict[str, Any], filepath: str, indent: int = 2) -> bool:
        """Save data to JSON file with error handling."""
        try:
            # Ensure directory exists
            directory = os.path.dirname(filepath)
            if directory:
                FileUtils.ensure_directory_exists(directory)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False, sort_keys=True)
            
            # Verify file was written successfully
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                return True
            else:
                print(f"⚠️  Warning: JSON file {filepath} appears empty after writing")
                return False
                
        except Exception as e:
            print(f"❌ Error saving JSON to {filepath}: {e}")
            return False
    
    @staticmethod
    def load_json_data(filepath: str) -> Optional[Dict[str, Any]]:
        """Load data from JSON file with error handling."""
        try:
            if not os.path.exists(filepath):
                print(f"⚠️  File {filepath} does not exist")
                return None
            
            if os.path.getsize(filepath) == 0:
                print(f"⚠️  File {filepath} is empty")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {filepath}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error loading JSON from {filepath}: {e}")
            return None
    
    @staticmethod
    def save_csv_data(data: List[Dict[str, Any]], filepath: str) -> bool:
        """Save data to CSV file."""
        try:
            if not data:
                print(f"⚠️  No data to save to {filepath}")
                return False
            
            directory = os.path.dirname(filepath)
            if directory:
                FileUtils.ensure_directory_exists(directory)
            
            # Get all unique keys from all dictionaries
            fieldnames = set()
            for row in data:
                fieldnames.update(row.keys())
            
            fieldnames = sorted(list(fieldnames))
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            return True
        except Exception as e:
            print(f"❌ Error saving CSV to {filepath}: {e}")
            return False
    
    def is_supported_code_file(self, filename: str) -> bool:
        """Check if file is a supported code file."""
        extension = self.get_file_extension(filename)
        return extension in self.config.SUPPORTED_CODE_EXTENSIONS
    
    def should_process_file(self, file_item: Dict) -> bool:
        """Determine if file should be processed based on various criteria."""
        # Check file size
        if file_item.get('size', 0) > self.config.MAX_FILE_SIZE:
            return False
        
        # Check if it's a supported file type
        filename = file_item.get('name', '')
        if not self.is_supported_code_file(filename):
            return False
        
        return True
    
    @staticmethod
    def get_relative_path(full_path: str, base_path: str) -> str:
        """Get relative path from base path."""
        try:
            return os.path.relpath(full_path, base_path)
        except ValueError:
            return full_path
    
    @staticmethod
    def get_file_hash(content: str) -> str:
        """Generate MD5 hash for duplicate detection."""
        if not content:
            return hashlib.md5(b'').hexdigest()
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def get_file_hash_sha256(content: str) -> str:
        """Generate SHA256 hash for more secure duplicate detection."""
        if not content:
            return hashlib.sha256(b'').hexdigest()
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def is_duplicate_file(self, file_data: Dict, processed_hashes: Set[str]) -> bool:
        """Check if file is duplicate based on content hash."""
        content = file_data.get('content', '')
        file_hash = self.get_file_hash(content)
        
        if file_hash in processed_hashes:
            return True
        
        processed_hashes.add(file_hash)
        return False
    
    @staticmethod
    def find_duplicate_groups(files: List[Dict]) -> List[List[Dict]]:
        """Find groups of duplicate files."""
        hash_groups = {}
        
        for file_data in files:
            content = file_data.get('content', '')
            file_hash = FileUtils.get_file_hash(content)
            
            if file_hash not in hash_groups:
                hash_groups[file_hash] = []
            hash_groups[file_hash].append(file_data)
        
        # Return only groups with more than one file (duplicates)
        duplicate_groups = [group for group in hash_groups.values() if len(group) > 1]
        return duplicate_groups
    
    @staticmethod
    def calculate_directory_stats(files: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive statistics for a directory of files."""
        if not files:
            return {
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_kb': 0,
                'total_size_mb': 0,
                'total_lines': 0,
                'extensions': {},
                'average_file_size': 0,
                'average_lines_per_file': 0,
                'complexity_stats': {},
                'duplicate_stats': {}
            }
        
        total_files = len(files)
        total_size = sum(file.get('size', 0) for file in files)
        total_lines = sum(file.get('lines', 0) for file in files)
        
        # Group by extension
        extensions = {}
        complexity_scores = []
        
        for file in files:
            ext = FileUtils.get_file_extension(file.get('name', ''))
            if ext not in extensions:
                extensions[ext] = {
                    'count': 0, 
                    'size': 0, 
                    'lines': 0,
                    'avg_complexity': 0
                }
            
            extensions[ext]['count'] += 1
            extensions[ext]['size'] += file.get('size', 0)
            extensions[ext]['lines'] += file.get('lines', 0)
            
            # Track complexity if available
            complexity = file.get('complexity_score', 0)
            if complexity > 0:
                complexity_scores.append(complexity)
        
        # Calculate average complexity per extension
        for ext_data in extensions.values():
            if ext_data['count'] > 0:
                ext_data['avg_file_size'] = ext_data['size'] / ext_data['count']
                ext_data['avg_lines'] = ext_data['lines'] / ext_data['count']
        
        # Find duplicates
        duplicate_groups = FileUtils.find_duplicate_groups(files)
        total_duplicates = sum(len(group) - 1 for group in duplicate_groups)  # -1 because first occurrence isn't duplicate
        
        # Complexity statistics
        complexity_stats = {}
        if complexity_scores:
            complexity_stats = {
                'min': min(complexity_scores),
                'max': max(complexity_scores),
                'average': sum(complexity_scores) / len(complexity_scores),
                'files_with_complexity': len(complexity_scores)
            }
        
        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_kb': total_size / 1024,
            'total_size_mb': total_size / (1024 * 1024),
            'total_lines': total_lines,
            'extensions': extensions,
            'average_file_size': total_size / total_files if total_files > 0 else 0,
            'average_lines_per_file': total_lines / total_files if total_files > 0 else 0,
            'complexity_stats': complexity_stats,
            'duplicate_stats': {
                'duplicate_groups': len(duplicate_groups),
                'total_duplicates': total_duplicates,
                'space_wasted_bytes': sum(
                    sum(file.get('size', 0) for file in group[1:])  # Skip first file in each group
                    for group in duplicate_groups
                )
            }
        }
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    @staticmethod
    def get_file_type_category(filename: str) -> str:
        """Categorize file type for better organization."""
        ext = FileUtils.get_file_extension(filename).lower()
        
        categories = {
            'python': ['.py', '.pyw', '.pyx', '.pyz'],
            'javascript': ['.js', '.jsx', '.ts', '.tsx', '.mjs'],
            'web': ['.html', '.htm', '.css', '.scss', '.sass', '.less'],
            'java': ['.java', '.class', '.jar'],
            'c_cpp': ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp'],
            'database': ['.sql', '.db', '.sqlite', '.sqlite3'],
            'config': ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'],
            'documentation': ['.md', '.rst', '.txt', '.doc', '.docx', '.pdf'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico'],
            'data': ['.csv', '.xml', '.xlsx', '.xls'],
            'other': []
        }
        
        for category, extensions in categories.items():
            if ext in extensions:
                return category
        
        return 'other'
    
    def get_processing_summary(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive processing summary."""
        all_files = (
            repo_data.get('code_files', []) + 
            repo_data.get('documentation', []) + 
            repo_data.get('dependencies', [])
        )
        
        stats = self.calculate_directory_stats(all_files)
        
        # Add analysis summary
        analyzed_files = repo_data.get('analyzed_files', [])
        total_functions = sum(len(analysis.get('functions', [])) for analysis in analyzed_files)
        total_classes = sum(len(analysis.get('classes', [])) for analysis in analyzed_files)
        total_imports = sum(len(analysis.get('imports', [])) for analysis in analyzed_files)
        
        # Language distribution from analyzed files
        language_analysis = {}
        for analysis in analyzed_files:
            lang = analysis.get('language', 'unknown')
            if lang not in language_analysis:
                language_analysis[lang] = {
                    'files': 0, 'functions': 0, 'classes': 0, 'imports': 0
                }
            
            language_analysis[lang]['files'] += 1
            language_analysis[lang]['functions'] += len(analysis.get('functions', []))
            language_analysis[lang]['classes'] += len(analysis.get('classes', []))
            language_analysis[lang]['imports'] += len(analysis.get('imports', []))
        
        return {
            'file_stats': stats,
            'analysis_summary': {
                'total_functions': total_functions,
                'total_classes': total_classes,
                'total_imports': total_imports,
                'analyzed_files_count': len(analyzed_files),
                'language_breakdown': language_analysis
            },
            'duplicate_info': repo_data.get('duplicate_files', []),
            'processing_time': repo_data.get('stats', {}).get('processing_time', 0)
        }

    ##
    @staticmethod
    def detect_technologies_from_files(all_files: List[Dict]) -> Dict[str, Any]:
        """Detect technologies, frameworks, and languages from files"""
        technologies = {
            'languages': {},
            'frameworks': {},
            'databases': {},
            'tools': {},
            'cloud_services': {},
            'package_managers': {},
            'testing_frameworks': {},
            'build_tools': {},
            'deployment_tools': {},
            'web_technologies': {}
        }
        
        for file_data in all_files:
            filename = file_data.get('name', '')
            content = file_data.get('content', '')
            extension = file_data.get('extension', '')
            
            # Detect from file extensions
            FileUtils._detect_from_extensions(extension, filename, technologies)
            
            # Detect from file content
            FileUtils._detect_from_content(content, filename, technologies)
            
            # Detect from filenames
            FileUtils._detect_from_filename(filename, technologies)
        
        # Clean up and calculate confidence scores
        return FileUtils._finalize_technology_detection(technologies, all_files)
    
    @staticmethod
    def _detect_from_extensions(extension: str, filename: str, technologies: Dict):
        """Detect technologies from file extensions"""
        ext_mapping = {
            # Programming Languages
            '.py': ('Python', 'languages'),
            '.js': ('JavaScript', 'languages'),
            '.ts': ('TypeScript', 'languages'),
            '.jsx': ('React JSX', 'frameworks'),
            '.tsx': ('React TypeScript', 'frameworks'),
            '.java': ('Java', 'languages'),
            '.cpp': ('C++', 'languages'),
            '.c': ('C', 'languages'),
            '.cs': ('C#', 'languages'),
            '.php': ('PHP', 'languages'),
            '.rb': ('Ruby', 'languages'),
            '.go': ('Go', 'languages'),
            '.rs': ('Rust', 'languages'),
            '.kt': ('Kotlin', 'languages'),
            '.swift': ('Swift', 'languages'),
            '.scala': ('Scala', 'languages'),
            '.r': ('R', 'languages'),
            '.m': ('Objective-C', 'languages'),
            '.pl': ('Perl', 'languages'),
            '.sh': ('Shell Script', 'languages'),
            '.ps1': ('PowerShell', 'languages'),
            
            # Web Technologies
            '.html': ('HTML', 'web_technologies'),
            '.htm': ('HTML', 'web_technologies'),
            '.css': ('CSS', 'web_technologies'),
            '.scss': ('SASS/SCSS', 'web_technologies'),
            '.sass': ('SASS', 'web_technologies'),
            '.less': ('LESS', 'web_technologies'),
            '.vue': ('Vue.js', 'frameworks'),
            '.svelte': ('Svelte', 'frameworks'),
            
            # Data & Config
            '.json': ('JSON', 'tools'),
            '.xml': ('XML', 'tools'),
            '.yaml': ('YAML', 'tools'),
            '.yml': ('YAML', 'tools'),
            '.toml': ('TOML', 'tools'),
            '.ini': ('INI Config', 'tools'),
            '.sql': ('SQL', 'databases'),
            '.csv': ('CSV Data', 'tools'),
            
            # Build & Package Files
            '.dockerfile': ('Docker', 'deployment_tools'),
            '.gradle': ('Gradle', 'build_tools'),
            '.pom': ('Maven', 'build_tools'),
        }
        
        if extension in ext_mapping:
            tech_name, category = ext_mapping[extension]
            technologies[category][tech_name] = technologies[category].get(tech_name, 0) + 1
    
    @staticmethod
    def _detect_from_filename(filename: str, technologies: Dict):
        """Detect technologies from specific filenames"""
        filename_lower = filename.lower()
        
        filename_mapping = {
            # Package Managers
            'package.json': ('npm', 'package_managers'),
            'package-lock.json': ('npm', 'package_managers'),
            'yarn.lock': ('Yarn', 'package_managers'),
            'pnpm-lock.yaml': ('pnpm', 'package_managers'),
            'requirements.txt': ('pip', 'package_managers'),
            'pipfile': ('Pipenv', 'package_managers'),
            'poetry.lock': ('Poetry', 'package_managers'),
            'composer.json': ('Composer', 'package_managers'),
            'go.mod': ('Go Modules', 'package_managers'),
            'cargo.toml': ('Cargo', 'package_managers'),
            'gemfile': ('Bundler', 'package_managers'),
            
            # Build Tools
            'makefile': ('Make', 'build_tools'),
            'cmake.txt': ('CMake', 'build_tools'),
            'build.gradle': ('Gradle', 'build_tools'),
            'pom.xml': ('Maven', 'build_tools'),
            'webpack.config.js': ('Webpack', 'build_tools'),
            'rollup.config.js': ('Rollup', 'build_tools'),
            'vite.config.js': ('Vite', 'build_tools'),
            'gulpfile.js': ('Gulp', 'build_tools'),
            
            # Deployment & DevOps
            'dockerfile': ('Docker', 'deployment_tools'),
            'docker-compose.yml': ('Docker Compose', 'deployment_tools'),
            'docker-compose.yaml': ('Docker Compose', 'deployment_tools'),
            'kubernetes.yaml': ('Kubernetes', 'deployment_tools'),
            'k8s.yaml': ('Kubernetes', 'deployment_tools'),
            'terraform.tf': ('Terraform', 'deployment_tools'),
            'ansible.yml': ('Ansible', 'deployment_tools'),
            'vagrant': ('Vagrant', 'deployment_tools'),
            
            # CI/CD
            '.github': ('GitHub Actions', 'deployment_tools'),
            '.gitlab-ci.yml': ('GitLab CI', 'deployment_tools'),
            '.travis.yml': ('Travis CI', 'deployment_tools'),
            'jenkinsfile': ('Jenkins', 'deployment_tools'),
            '.circleci': ('CircleCI', 'deployment_tools'),
            
            # Testing
            'pytest.ini': ('pytest', 'testing_frameworks'),
            'jest.config.js': ('Jest', 'testing_frameworks'),
            'karma.conf.js': ('Karma', 'testing_frameworks'),
            'cypress.json': ('Cypress', 'testing_frameworks'),
            
            # Databases
            'sqlite3': ('SQLite', 'databases'),
            'mongo': ('MongoDB', 'databases'),
        }
        
        for pattern, (tech_name, category) in filename_mapping.items():
            if pattern in filename_lower:
                technologies[category][tech_name] = technologies[category].get(tech_name, 0) + 1
    
    @staticmethod
    def _detect_from_content(content: str, filename: str, technologies: Dict):
        """Detect technologies from file content"""
        if not content:
            return
        
        content_lower = content.lower()
        
        # Framework and Library Detection
        framework_patterns = {
            # Python Frameworks
            'flask': ('Flask', 'frameworks'),
            'django': ('Django', 'frameworks'),
            'fastapi': ('FastAPI', 'frameworks'),
            'tornado': ('Tornado', 'frameworks'),
            'pyramid': ('Pyramid', 'frameworks'),
            'bottle': ('Bottle', 'frameworks'),
            'streamlit': ('Streamlit', 'frameworks'),
            'gradio': ('Gradio', 'frameworks'),
            
            # JavaScript Frameworks
            'react': ('React', 'frameworks'),
            'angular': ('Angular', 'frameworks'),
            'vue': ('Vue.js', 'frameworks'),
            'express': ('Express.js', 'frameworks'),
            'nextjs': ('Next.js', 'frameworks'),
            'nuxt': ('Nuxt.js', 'frameworks'),
            'svelte': ('Svelte', 'frameworks'),
            'ember': ('Ember.js', 'frameworks'),
            'backbone': ('Backbone.js', 'frameworks'),
            'jquery': ('jQuery', 'frameworks'),
            'lodash': ('Lodash', 'frameworks'),
            'axios': ('Axios', 'frameworks'),
            
            # Databases
            'postgresql': ('PostgreSQL', 'databases'),
            'mysql': ('MySQL', 'databases'),
            'sqlite': ('SQLite', 'databases'),
            'mongodb': ('MongoDB', 'databases'),
            'redis': ('Redis', 'databases'),
            'elasticsearch': ('Elasticsearch', 'databases'),
            'cassandra': ('Cassandra', 'databases'),
            'mariadb': ('MariaDB', 'databases'),
            'oracle': ('Oracle', 'databases'),
            'dynamodb': ('DynamoDB', 'databases'),
            
            # Cloud Services
            'aws': ('Amazon Web Services', 'cloud_services'),
            'azure': ('Microsoft Azure', 'cloud_services'),
            'gcp': ('Google Cloud Platform', 'cloud_services'),
            'heroku': ('Heroku', 'cloud_services'),
            'netlify': ('Netlify', 'cloud_services'),
            'vercel': ('Vercel', 'cloud_services'),
            'digitalocean': ('DigitalOcean', 'cloud_services'),
            'firebase': ('Firebase', 'cloud_services'),
            'supabase': ('Supabase', 'cloud_services'),
            
            # Testing Frameworks
            'pytest': ('pytest', 'testing_frameworks'),
            'unittest': ('unittest', 'testing_frameworks'),
            'jest': ('Jest', 'testing_frameworks'),
            'mocha': ('Mocha', 'testing_frameworks'),
            'jasmine': ('Jasmine', 'testing_frameworks'),
            'cypress': ('Cypress', 'testing_frameworks'),
            'selenium': ('Selenium', 'testing_frameworks'),
            'playwright': ('Playwright', 'testing_frameworks'),
            
            # Machine Learning
            'tensorflow': ('TensorFlow', 'frameworks'),
            'pytorch': ('PyTorch', 'frameworks'),
            'scikit-learn': ('Scikit-learn', 'frameworks'),
            'pandas': ('Pandas', 'frameworks'),
            'numpy': ('NumPy', 'frameworks'),
            'keras': ('Keras', 'frameworks'),
            'opencv': ('OpenCV', 'frameworks'),
            'huggingface': ('Hugging Face', 'frameworks'),
        }
        
        for pattern, (tech_name, category) in framework_patterns.items():
            if pattern in content_lower:
                technologies[category][tech_name] = technologies[category].get(tech_name, 0) + 1
    
    @staticmethod
    def _finalize_technology_detection(technologies: Dict, all_files: List[Dict]) -> Dict[str, Any]:
        """Clean up and add metadata to technology detection"""
        total_files = len(all_files)
        
        # Calculate confidence scores and clean up
        final_technologies = {}
        
        for category, techs in technologies.items():
            if techs:  # Only include categories with detected technologies
                final_technologies[category] = {}
                for tech_name, count in techs.items():
                    confidence = min((count / total_files) * 100, 100)  # Percentage, max 100%
                    final_technologies[category][tech_name] = {
                        'files_count': count,
                        'confidence_percentage': round(confidence, 1),
                        'usage_level': FileUtils._get_usage_level(confidence)
                    }
                
                # Sort by file count
                final_technologies[category] = dict(sorted(
                    final_technologies[category].items(), 
                    key=lambda x: x[1]['files_count'], 
                    reverse=True
                ))
        
        # Add summary statistics
        final_technologies['summary'] = {
            'total_technologies_detected': sum(len(techs) for techs in final_technologies.values() if isinstance(techs, dict)),
            'primary_language': FileUtils._get_primary_language(final_technologies.get('languages', {})),
            'tech_stack_complexity': FileUtils._calculate_tech_complexity(final_technologies),
            'total_files_analyzed': total_files
        }
        
        return final_technologies
    
    @staticmethod
    def _get_usage_level(confidence: float) -> str:
        """Determine usage level based on confidence percentage"""
        if confidence >= 20:
            return 'Heavy'
        elif confidence >= 10:
            return 'Moderate'
        elif confidence >= 5:
            return 'Light'
        else:
            return 'Minimal'
    
    @staticmethod
    def _get_primary_language(languages: Dict) -> str:
        """Get the primary programming language"""
        if not languages:
            return 'Unknown'
        
        primary = max(languages.items(), key=lambda x: x[1]['files_count'])
        return primary[0]
    
    @staticmethod
    def _calculate_tech_complexity(technologies: Dict) -> str:
        """Calculate overall technology stack complexity"""
        total_techs = sum(
            len(techs) for category, techs in technologies.items() 
            if isinstance(techs, dict) and category != 'summary'
        )
        
        if total_techs >= 20:
            return 'Very High'
        elif total_techs >= 15:
            return 'High'
        elif total_techs >= 10:
            return 'Medium'
        elif total_techs >= 5:
            return 'Low'
        else:
            return 'Very Low'