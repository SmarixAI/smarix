import os
from typing import Set, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration settings loaded from environment variables"""

    # ============================================
    # GITHUB API SETTINGS
    # ============================================
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    GITHUB_API_BASE_URL: str = os.getenv(
        "GITHUB_API_BASE_URL", "https://api.github.com"
    )

    # ============================================
    # ASYNC OPTIMIZATION SETTINGS (NEW)
    # ============================================
    # Concurrent request limits for async operations
    MAX_CONCURRENT_REQUESTS: int = int(
        os.getenv("MAX_CONCURRENT_REQUESTS", 50)
    )  # GitHub allows 100
    MAX_CONCURRENT_FILE_DOWNLOADS: int = int(
        os.getenv("MAX_CONCURRENT_FILE_DOWNLOADS", 30)
    )

    # Request timeout settings
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", 30))  # Seconds per request
    CONNECTION_TIMEOUT: int = int(
        os.getenv("CONNECTION_TIMEOUT", 10)
    )  # Seconds for connection

    # Rate limiting buffer
    RATE_LIMIT_BUFFER: int = int(
        os.getenv("RATE_LIMIT_BUFFER", 10)
    )  # Keep N requests in reserve

    # Feature flags for async mode
    ENABLE_ASYNC_MODE: bool = os.getenv("ENABLE_ASYNC_MODE", "true").lower() == "true"
    ENABLE_CONCURRENT_FILE_FETCH: bool = (
        os.getenv("ENABLE_CONCURRENT_FILE_FETCH", "true").lower() == "true"
    )
    SKIP_FULL_FILE_DOWNLOAD_IN_PRS: bool = (
        os.getenv("SKIP_FULL_FILE_DOWNLOAD_IN_PRS", "true").lower() == "true"
    )

    # ============================================
    # PROCESSING LIMITS
    # ============================================
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024))
    MAX_RECURSION_DEPTH: int = int(
        os.getenv("MAX_RECURSION_DEPTH", 10)
    )  # Increased from 4

    # Allow special values for unlimited analysis: 'all' (case-insensitive) or non-positive numbers
    _max_files_env = os.getenv("MAX_FILES_TO_ANALYZE", "1000")  # Increased default
    try:
        if isinstance(_max_files_env, str) and _max_files_env.lower() == "all":
            MAX_FILES_TO_ANALYZE = None
        else:
            _max_val = int(_max_files_env)
            MAX_FILES_TO_ANALYZE = None if _max_val <= 0 else _max_val
    except Exception:
        # Fallback to a safe default
        MAX_FILES_TO_ANALYZE = 1000

    # ============================================
    # RATE LIMITING
    # ============================================
    API_DELAY: float = float(
        os.getenv("API_DELAY", 0.0)
    )  # Reduced from 0.1 (async handles this better)
    RATE_LIMIT_RETRY_DELAY: int = int(os.getenv("RATE_LIMIT_RETRY_DELAY", 60))

    # ============================================
    # OUTPUT SETTINGS
    # ============================================
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./output")
    JSON_INDENT: int = int(os.getenv("JSON_INDENT", 2))
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # ============================================
    # ANALYSIS SETTINGS
    # ============================================
    ENABLE_PYTHON_AST: bool = os.getenv("ENABLE_PYTHON_AST", "true").lower() == "true"
    ENABLE_JS_ANALYSIS: bool = os.getenv("ENABLE_JS_ANALYSIS", "true").lower() == "true"
    INCLUDE_DOCS: bool = os.getenv("INCLUDE_DOCS", "true").lower() == "true"
    INCLUDE_DEPENDENCIES: bool = (
        os.getenv("INCLUDE_DEPENDENCIES", "true").lower() == "true"
    )

    # ============================================
    # DUPLICATE DETECTION SETTINGS
    # ============================================
    SKIP_DUPLICATE_FILES: bool = (
        os.getenv("SKIP_DUPLICATE_FILES", "true").lower() == "true"
    )
    SHOW_DUPLICATE_STATS: bool = (
        os.getenv("SHOW_DUPLICATE_STATS", "true").lower() == "true"
    )
    MAX_DUPLICATES_TO_SHOW: int = int(os.getenv("MAX_DUPLICATES_TO_SHOW", 3))

    # ============================================
    # PERFORMANCE SETTINGS
    # ============================================
    CONCURRENT_REQUESTS: int = int(
        os.getenv("CONCURRENT_REQUESTS", 1)
    )  # Legacy, use MAX_CONCURRENT_REQUESTS
    ENABLE_CACHING: bool = os.getenv("ENABLE_CACHING", "false").lower() == "true"
    CACHE_DIR: str = os.getenv("CACHE_DIR", "./.cache")
    CACHE_EXPIRATION: int = int(os.getenv("CACHE_EXPIRATION", 24))

    # ============================================
    # PAGINATION AND COLLECTION LIMITS (UNLIMITED)
    # ============================================
    PER_PAGE: int = int(os.getenv("PER_PAGE", 100))  # GitHub's maximum
    MAX_PAGES: int = int(
        os.getenv("MAX_PAGES", 100)
    )  # Fetch up to 100 pages (10,000 items max per endpoint)

    # UPDATED: Support unlimited fetching with None
    _max_issues_env = os.getenv("MAX_ISSUES", "unlimited")
    try:
        if isinstance(_max_issues_env, str) and _max_issues_env.lower() == "unlimited":
            MAX_ISSUES: Optional[int] = None  # Fetch ALL issues
        else:
            MAX_ISSUES: Optional[int] = int(_max_issues_env)
    except Exception:
        MAX_ISSUES: Optional[int] = None  # Default to unlimited

    _max_prs_env = os.getenv("MAX_PRS", "unlimited")
    try:
        if isinstance(_max_prs_env, str) and _max_prs_env.lower() == "unlimited":
            MAX_PRS: Optional[int] = None  # Fetch ALL PRs
        else:
            MAX_PRS: Optional[int] = int(_max_prs_env)
    except Exception:
        MAX_PRS: Optional[int] = None  # Default to unlimited

    _max_commits_env = os.getenv("MAX_COMMITS", "unlimited")
    try:
        if (
            isinstance(_max_commits_env, str)
            and _max_commits_env.lower() == "unlimited"
        ):
            MAX_COMMITS: Optional[int] = None  # Fetch ALL commits
        else:
            MAX_COMMITS: Optional[int] = int(_max_commits_env)
    except Exception:
        MAX_COMMITS: Optional[int] = None  # Default to unlimited

    # ============================================
    # OPTIONAL INTEGRATIONS
    # ============================================
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    WEBHOOK_URL: Optional[str] = os.getenv("WEBHOOK_URL")

    # ============================================
    # SUPPORTED FILE EXTENSIONS
    # ============================================
    SUPPORTED_CODE_EXTENSIONS: Set[str] = {
        # Core languages (50+)
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".mjs",
        ".cjs",
        ".java",
        ".kt",
        ".scala",
        ".go",
        ".rs",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".cs",
        ".php",
        ".rb",
        ".swift",
        ".dart",
        ".sql",
        ".proto",
        ".graphql",
        ".gql",
        ".vue",
        ".svelte",
        ".elm",
        ".sh",
        ".bash",
        ".ps1",
        ".bat",
        ".pl",
        ".lua",
        ".r",
        ".jl",
        ".hs",
        ".ml",
        ".ex",
        ".exs",
        ".clj",
        ".cljs",
        ".groovy",
        ".m",
        ".mm",
        ".f90",
        ".f",
        # Config-as-code
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".json",
        ".xml",
        ".dockerfile",
        # Build
        ".gradle",
        ".gradle.kts",
        ".makefile",
        ".cmake",
        ".bazel",
    }

    # ============================================
    # SKIP DIRECTORIES
    # ============================================
    SKIP_DIRECTORIES: Set[str] = {
        ".git",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        "build",
        "dist",
        "target",
        ".vscode",
        ".idea",
        "venv",
        "env",
        ".next",
        ".nuxt",
        "coverage",
        ".nyc_output",
        "logs",
        ".tox",
        "htmlcov",
        ".mypy_cache",
        ".ruff_cache",
        "site-packages",
    }

    # ============================================
    # SKIP EXTENSIONS (BINARIES/MEDIA)
    # ============================================
    SKIP_EXTENSIONS: Set[str] = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".ico",
        ".webp",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".tgz",
        ".7z",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".pyc",
        ".class",
        ".jar",
        ".apk",
        ".mp4",
        ".mov",
        ".avi",
        ".woff",
        ".ttf",
    }

    # ============================================
    # DOCUMENTATION FILES
    # ============================================
    DOCUMENTATION_FILES: Set[str] = {
        "readme.md",
        "readme.txt",
        "readme.rst",
        "changelog.md",
        "contributing.md",
        "license",
        "license.txt",
        "license.md",
        "docs.md",
        "documentation.md",
        "api.md",
        "guide.md",
        "architecture.md",
        "arch.md",
        "contributing.md",
        "changes.md",
        "faq.md",
        "troubleshooting.md",
        "deployment.md",
        "setup.md",
    }

    DOCUMENTATION_EXTENSIONS: Set[str] = {".md", ".rst", ".txt", ".adoc", ".tex"}

    # ============================================
    # DEPENDENCY FILES
    # ============================================
    DEPENDENCY_FILES: Set[str] = {
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "requirements.txt",
        "pipfile",
        "pipfile.lock",
        "poetry.lock",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "composer.json",
        "composer.lock",
        "go.mod",
        "go.sum",
        "cargo.toml",
        "cargo.lock",
        "gemfile",
        "gemfile.lock",
        "setup.py",
        "setup.cfg",
        "pyproject.toml",
        "environment.yml",
        "conda.yml",
        "mix.exs",
        "mix.lock",
    }

    # ============================================
    # IMPORTANT INFRASTRUCTURE FILES
    # ============================================
    IMPORTANT_INFRA_FILES: Set[str] = {
        "dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        ".env",
        ".env.sample",
        ".env.example",
        ".env.template",
        "makefile",
        "Makefile",
        "Vagrantfile",
        "Procfile",
        "README",
        "README.md",
        "CONTRIBUTING.md",
        "ARCHITECTURE.md",
        "architecture.md",
        "setup.sh",
        "bootstrap.sh",
        "install.sh",
        "deploy.sh",
        "ci.yml",
        ".github/workflows",
        "jenkinsfile",
        "Jenkinsfile",
        ".gitlab-ci.yml",
        ".travis.yml",
        "azure-pipelines.yml",
        "bitbucket-pipelines.yml",
        ".circleci/config.yml",
    }

    # ============================================
    # VALIDATION METHODS
    # ============================================
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        errors = []
        warnings = []

        # Critical checks
        if not cls.GITHUB_TOKEN:
            warnings.append(
                "⚠️  GITHUB_TOKEN is not set. API rate limits will be very low (60 req/hour)."
            )

        if cls.MAX_FILE_SIZE <= 0:
            errors.append("❌ MAX_FILE_SIZE must be greater than 0")

        if cls.MAX_RECURSION_DEPTH < 1:
            errors.append("❌ MAX_RECURSION_DEPTH must be at least 1")

        if cls.API_DELAY < 0:
            errors.append("❌ API_DELAY cannot be negative")

        # Async optimization checks
        if cls.MAX_CONCURRENT_REQUESTS > 100:
            warnings.append(
                f"⚠️  MAX_CONCURRENT_REQUESTS={cls.MAX_CONCURRENT_REQUESTS} exceeds GitHub's limit of 100"
            )

        if cls.MAX_CONCURRENT_REQUESTS < 1:
            errors.append("❌ MAX_CONCURRENT_REQUESTS must be at least 1")

        if not cls.ENABLE_ASYNC_MODE:
            warnings.append(
                "⚠️  ENABLE_ASYNC_MODE is disabled. Performance will be significantly slower."
            )

        # Print results
        if warnings:
            print("⚠️  Configuration warnings:")
            for warning in warnings:
                print(f"  {warning}")

        if errors:
            print("\n❌ Configuration validation errors:")
            for error in errors:
                print(f"  {error}")
            return False

        if not warnings:
            print("✅ Configuration validation passed (no warnings)")
        else:
            print("✅ Configuration validation passed (with warnings)")

        return True

    @classmethod
    def print_config_summary(cls):
        """Print configuration summary for debugging"""
        print("\n" + "=" * 60)
        print("📋 CONFIGURATION SUMMARY")
        print("=" * 60)

        print("\n🔧 CORE SETTINGS:")
        print(f"  🔑 GitHub Token: {'✅ Set' if cls.GITHUB_TOKEN else '❌ Not Set'}")
        print(f"  🌐 API Base URL: {cls.GITHUB_API_BASE_URL}")
        print(f"  📏 Max File Size: {cls.MAX_FILE_SIZE / (1024*1024):.1f}MB")
        print(f"  🔍 Max Recursion Depth: {cls.MAX_RECURSION_DEPTH}")

        max_files_display = (
            "All" if cls.MAX_FILES_TO_ANALYZE is None else cls.MAX_FILES_TO_ANALYZE
        )
        print(f"  📊 Max Files to Analyze: {max_files_display}")

        print("\n⚡ ASYNC OPTIMIZATION:")
        print(
            f"  🚀 Async Mode: {'✅ Enabled' if cls.ENABLE_ASYNC_MODE else '❌ Disabled'}"
        )
        print(f"  🔄 Max Concurrent Requests: {cls.MAX_CONCURRENT_REQUESTS}")
        print(
            f"  📥 Max Concurrent File Downloads: {cls.MAX_CONCURRENT_FILE_DOWNLOADS}"
        )
        print(f"  ⏱️  Request Timeout: {cls.REQUEST_TIMEOUT}s")
        print(f"  🔌 Connection Timeout: {cls.CONNECTION_TIMEOUT}s")
        print(f"  🛡️  Rate Limit Buffer: {cls.RATE_LIMIT_BUFFER}")

        print("\n📦 COLLECTION LIMITS:")
        print(f"  📄 Per Page: {cls.PER_PAGE}")
        print(f"  📚 Max Pages: {cls.MAX_PAGES}")
        print(
            f"  🐛 Max Issues: {'Unlimited' if cls.MAX_ISSUES is None else cls.MAX_ISSUES}"
        )
        print(f"  🔀 Max PRs: {'Unlimited' if cls.MAX_PRS is None else cls.MAX_PRS}")
        print(
            f"  💾 Max Commits: {'Unlimited' if cls.MAX_COMMITS is None else cls.MAX_COMMITS}"
        )

        print("\n🎯 OPTIMIZATION FLAGS:")
        print(
            f"  ⚡ Skip Full File Download in PRs: {'✅ Yes' if cls.SKIP_FULL_FILE_DOWNLOAD_IN_PRS else '❌ No'}"
        )
        print(
            f"  🔄 Concurrent File Fetch: {'✅ Yes' if cls.ENABLE_CONCURRENT_FILE_FETCH else '❌ No'}"
        )
        print(
            f"  🔍 Skip Duplicates: {'✅ Yes' if cls.SKIP_DUPLICATE_FILES else '❌ No'}"
        )

        print("\n📁 OUTPUT & ANALYSIS:")
        print(f"  📁 Output Dir: {cls.OUTPUT_DIR}")
        print(f"  🐛 Debug Mode: {'✅ On' if cls.DEBUG_MODE else '❌ Off'}")
        print(f"  📝 Log Level: {cls.LOG_LEVEL}")
        print(f"  💾 Caching: {'✅ Enabled' if cls.ENABLE_CACHING else '❌ Disabled'}")

        print("\n📊 FILE TRACKING:")
        print(f"  📚 Supported Code Extensions: {len(cls.SUPPORTED_CODE_EXTENSIONS)}")
        print(f"  ⛔ Skip Extensions: {len(cls.SKIP_EXTENSIONS)}")
        print(f"  📂 Skip Directories: {len(cls.SKIP_DIRECTORIES)}")
        print(f"  📖 Documentation Files: {len(cls.DOCUMENTATION_FILES)}")
        print(f"  📦 Dependency Files: {len(cls.DEPENDENCY_FILES)}")
        print(f"  🏗️  Infrastructure Files: {len(cls.IMPORTANT_INFRA_FILES)}")

        print("\n" + "=" * 60)

        # Performance estimate
        if cls.ENABLE_ASYNC_MODE and cls.GITHUB_TOKEN:
            print("⚡ PERFORMANCE ESTIMATE:")
            if (
                cls.MAX_ISSUES is None
                and cls.MAX_PRS is None
                and cls.MAX_COMMITS is None
            ):
                print(f"  🚀 UNLIMITED MODE: Fetching ALL data")
                print(f"  Expected time for medium repo: 12-20 minutes")
                print(f"  Expected time for large repo: 20-35 minutes")
            else:
                print(f"  Expected time for medium repo: 10-15 minutes")
                print(f"  Expected time for large repo: 15-25 minutes")
            print(f"  Speed improvement vs sync: 4-5x faster")
        elif cls.GITHUB_TOKEN:
            print("⚠️  PERFORMANCE WARNING:")
            print(f"  Async mode disabled - expect 45-60+ minutes")
        else:
            print("⚠️  PERFORMANCE WARNING:")
            print(f"  No GitHub token - severe rate limiting (60 req/hr)")
            print(f"  Expected time: 2-4+ hours")

        print("=" * 60 + "\n")

    @classmethod
    def get_optimal_settings_for_speed(cls):
        """Return optimal settings dict for maximum speed"""
        return {
            "ENABLE_ASYNC_MODE": True,
            "MAX_CONCURRENT_REQUESTS": 50,
            "MAX_CONCURRENT_FILE_DOWNLOADS": 30,
            "SKIP_FULL_FILE_DOWNLOAD_IN_PRS": True,
            "ENABLE_CONCURRENT_FILE_FETCH": True,
            "MAX_ISSUES": None,  # UNLIMITED
            "MAX_PRS": None,  # UNLIMITED
            "MAX_COMMITS": None,  # UNLIMITED
            "API_DELAY": 0.0,
            "PER_PAGE": 100,
            "MAX_PAGES": 100,
        }

    @classmethod
    def apply_optimal_settings(cls):
        """Apply optimal settings for speed (overwrites current)"""
        optimal = cls.get_optimal_settings_for_speed()
        for key, value in optimal.items():
            setattr(cls, key, value)
        print("✅ Applied optimal settings for maximum speed (UNLIMITED mode)")
