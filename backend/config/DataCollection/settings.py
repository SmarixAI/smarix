import os
from typing import Set, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration settings loaded from environment variables"""
    
    # GitHub API settings
    GITHUB_TOKEN: Optional[str] = os.getenv('GITHUB_TOKEN')
    GITHUB_API_BASE_URL: str = os.getenv('GITHUB_API_BASE_URL', "https://api.github.com")
    
    # Processing limits
    MAX_FILE_SIZE: int = int(os.getenv('MAX_FILE_SIZE', 500 * 1024))  # 500KB default
    MAX_RECURSION_DEPTH: int = int(os.getenv('MAX_RECURSION_DEPTH', 4))
    # Allow special values for unlimited analysis: 'all' (case-insensitive) or non-positive numbers
    _max_files_env = os.getenv('MAX_FILES_TO_ANALYZE', '20')
    try:
        if isinstance(_max_files_env, str) and _max_files_env.lower() == 'all':
            MAX_FILES_TO_ANALYZE = None
        else:
            _max_val = int(_max_files_env)
            MAX_FILES_TO_ANALYZE = None if _max_val <= 0 else _max_val
    except Exception:
        # Fallback to a safe default
        MAX_FILES_TO_ANALYZE = 20
    
    # Rate limiting
    API_DELAY: float = float(os.getenv('API_DELAY', 0.1))
    RATE_LIMIT_RETRY_DELAY: int = int(os.getenv('RATE_LIMIT_RETRY_DELAY', 60))
    
    # Output settings
    OUTPUT_DIR: str = os.getenv('OUTPUT_DIR', './output')
    JSON_INDENT: int = int(os.getenv('JSON_INDENT', 2))
    DEBUG_MODE: bool = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Analysis settings
    ENABLE_PYTHON_AST: bool = os.getenv('ENABLE_PYTHON_AST', 'true').lower() == 'true'
    ENABLE_JS_ANALYSIS: bool = os.getenv('ENABLE_JS_ANALYSIS', 'true').lower() == 'true'
    INCLUDE_DOCS: bool = os.getenv('INCLUDE_DOCS', 'true').lower() == 'true'
    INCLUDE_DEPENDENCIES: bool = os.getenv('INCLUDE_DEPENDENCIES', 'true').lower() == 'true'
    
    # Duplicate detection settings (ADD THESE)
    SKIP_DUPLICATE_FILES: bool = os.getenv('SKIP_DUPLICATE_FILES', 'true').lower() == 'true'
    SHOW_DUPLICATE_STATS: bool = os.getenv('SHOW_DUPLICATE_STATS', 'true').lower() == 'true'
    MAX_DUPLICATES_TO_SHOW: int = int(os.getenv('MAX_DUPLICATES_TO_SHOW', 3))
    
    # Performance settings
    CONCURRENT_REQUESTS: int = int(os.getenv('CONCURRENT_REQUESTS', 1))
    ENABLE_CACHING: bool = os.getenv('ENABLE_CACHING', 'false').lower() == 'true'
    CACHE_DIR: str = os.getenv('CACHE_DIR', './.cache')
    CACHE_EXPIRATION: int = int(os.getenv('CACHE_EXPIRATION', 24))
    
    # Pagination and collection limits for non-file resources
    PER_PAGE: int = int(os.getenv('PER_PAGE', 100))
    MAX_PAGES: int = int(os.getenv('MAX_PAGES', 10))
    MAX_ISSUES: int = int(os.getenv('MAX_ISSUES', 500))
    MAX_PRS: int = int(os.getenv('MAX_PRS', 500))
    MAX_COMMITS: int = int(os.getenv('MAX_COMMITS', 1000))
    
    # Optional integrations
    DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
    REDIS_URL: Optional[str] = os.getenv('REDIS_URL')
    WEBHOOK_URL: Optional[str] = os.getenv('WEBHOOK_URL')
    
    # Supported file extensions
    SUPPORTED_CODE_EXTENSIONS: Set[str] = {
        '.py', '.js', '.java', '.cpp', '.c', '.ts', '.jsx', '.tsx',
        '.php', '.rb', '.go', '.rs', '.kt', '.swift', '.cs', '.scala',
        '.html', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
        '.dart', '.m', '.mm', '.sh', '.bat', '.ps1', '.pl', '.lua',
        '.r', '.jl', '.hs', '.erl', '.ex', '.exs', '.groovy', '.sql',
        '.yaml', '.yml', '.json', '.xml', '.toml', '.ini', '.cfg',
    }
    
    # Skip directories
    SKIP_DIRECTORIES: Set[str] = {
        '.git', 'node_modules', '__pycache__', '.pytest_cache',
        'build', 'dist', 'target', '.vscode', '.idea', 'venv', 'env',
        '.next', '.nuxt', 'coverage', '.nyc_output', 'logs'
    }

    # New: file extensions we want to skip entirely (binaries / media / large blobs)
    SKIP_EXTENSIONS: Set[str] = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
        '.exe', '.dll', '.so', '.dylib', '.zip', '.tar', '.gz',
        '.tgz', '.7z', '.pdf', '.pyc', '.class', '.jar', '.apk',
        '.mp4', '.mov', '.avi', '.mkv', '.woff', '.woff2', '.ttf'
    }
    
    # Documentation file patterns (as a set for fast membership tests)
    DOCUMENTATION_FILES: Set[str] = {
        'readme.md', 'readme.txt', 'readme.rst', 'changelog.md',
        'contributing.md', 'license', 'license.txt', 'license.md',
        'docs.md', 'documentation.md', 'api.md', 'guide.md',
        'architecture.md', 'arch.md', 'contributing.md', 'changes.md'
    }
    
    DOCUMENTATION_EXTENSIONS = ['.md', '.rst', '.txt', '.adoc']
    
    # Dependency file patterns (set for fast membership checks)
    DEPENDENCY_FILES: Set[str] = {
        'package.json', 'package-lock.json', 'yarn.lock',
        'requirements.txt', 'pipfile', 'pipfile.lock', 'poetry.lock',
        'pom.xml', 'build.gradle', 'build.gradle.kts',
        'composer.json', 'composer.lock',
        'go.mod', 'go.sum',
        'cargo.toml', 'cargo.lock',
        'gemfile', 'gemfile.lock',
        'setup.py', 'setup.cfg', 'pyproject.toml',
        'environment.yml', 'conda.yml'
    }

    # New: files considered especially important for onboarding/offboarding infra & setup
    IMPORTANT_INFRA_FILES: Set[str] = {
        'dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
        '.env', '.env.sample', '.env.example', 'makefile', 'Makefile',
        'Vagrantfile', 'Procfile', 'README', 'README.md', 'CONTRIBUTING.md',
        'ARCHITECTURE.md', 'architecture.md', 'setup.sh', 'bootstrap.sh',
        'install.sh', 'deploy.sh', 'ci.yml', '.github/workflows'
    }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        errors = []
        
        if not cls.GITHUB_TOKEN:
            errors.append("❌ GITHUB_TOKEN is not set. API rate limits will be very low.")
        
        if cls.MAX_FILE_SIZE <= 0:
            errors.append("❌ MAX_FILE_SIZE must be greater than 0")
        
        if cls.MAX_RECURSION_DEPTH < 1:
            errors.append("❌ MAX_RECURSION_DEPTH must be at least 1")
        
        if cls.API_DELAY < 0:
            errors.append("❌ API_DELAY cannot be negative")
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  {error}")
            return False
        
        print("✅ Configuration validation passed")
        return True
    
    @classmethod
    def print_config_summary(cls):
        """Print configuration summary for debugging"""
        print("\n📋 Configuration Summary:")
        print(f"  🔑 GitHub Token: {'✅ Set' if cls.GITHUB_TOKEN else '❌ Not Set'}")
        print(f"  📏 Max File Size: {cls.MAX_FILE_SIZE / 1024:.1f}KB")
        print(f"  🔍 Max Depth: {cls.MAX_RECURSION_DEPTH}")
        max_files_display = 'All' if cls.MAX_FILES_TO_ANALYZE is None else cls.MAX_FILES_TO_ANALYZE
        print(f"  📊 Max Files to Analyze: {max_files_display}")
        print(f"  ⏱️  API Delay: {cls.API_DELAY}s")
        print(f"  📁 Output Dir: {cls.OUTPUT_DIR}")
        print(f"  🐛 Debug Mode: {'✅ On' if cls.DEBUG_MODE else '❌ Off'}")
        print(f"  📝 Log Level: {cls.LOG_LEVEL}")
        print(f"  💾 Caching: {'✅ Enabled' if cls.ENABLE_CACHING else '❌ Disabled'}")
        print(f"  📚 Important infra files tracked: {len(cls.IMPORTANT_INFRA_FILES)}")
        print(f"  ⛔ Skip extensions count: {len(cls.SKIP_EXTENSIONS)}")
        print()
