import os
from .ignore_rules import IGNORE_DIRS


LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js"],
    "typescript": [".ts", ".tsx"],
    "java": [".java"],
    "go": [".go"],
    "ruby": [".rb"],
    "php": [".php"],
    "csharp": [".cs"],
    "cpp": [".cpp", ".hpp", ".h"],
    "kotlin": [".kt"],
    "swift": [".swift"]
}

TEMPLATE_EXTENSIONS = [".html", ".jinja", ".jinja2"]
STATIC_EXTENSIONS = [".css", ".scss", ".sass", ".png", ".jpg", ".jpeg", ".svg"]
CONFIG_EXTENSIONS = [".yaml", ".yml", ".json", ".toml", ".ini", ".env"]

TEST_DIR_NAMES = {"tests", "test", "__tests__", "spec"}

TEST_FILE_PATTERNS = {
    ".py": ["test_", "_test.py"],
    ".js": [".test.js", ".spec.js"],
    ".ts": [".test.ts", ".spec.ts"],
    ".java": ["Test.java"],
    ".go": ["_test.go"],
    ".rb": ["_spec.rb", "_test.rb"],
}

ALL_LANGUAGE_EXTS = set(
    ext for exts in LANGUAGE_EXTENSIONS.values() for ext in exts
)




class ProjectStructureScanner:

    def __init__(self, root_path):
        self.root_path = root_path

    def scan(self):
        all_files = []
        file_count_by_ext = {}

        languages = {lang: [] for lang in LANGUAGE_EXTENSIONS}
        templates = []
        static_assets = []
        config_files = []
        test_files = []

        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, self.root_path)

                all_files.append(full_path)

                ext = os.path.splitext(file)[1]
                file_count_by_ext[ext] = file_count_by_ext.get(ext, 0) + 1

                # Detect language
                for lang, extensions in LANGUAGE_EXTENSIONS.items():
                    if ext in extensions:
                        languages[lang].append(full_path)

                # Templates
                if ext in TEMPLATE_EXTENSIONS:
                    templates.append(full_path)

                # Static assets
                if ext in STATIC_EXTENSIONS:
                    static_assets.append(full_path)

                # Config files
                if ext in CONFIG_EXTENSIONS:
                    config_files.append(full_path)

                # Tests
                if self.is_test_file(relative_path, ext, file):
                    test_files.append(relative_path)



        return {
            "total_files": len(all_files),
            "file_count_by_extension": file_count_by_ext,
            "languages": languages,
            "templates": templates,
            "static_assets": static_assets,
            "config_files": config_files,
            "test_files": test_files
        }
    
    def is_test_file(self, relative_path, ext, filename):
        parts = relative_path.split(os.sep)

        # Must be language file
        if ext not in ALL_LANGUAGE_EXTS:
            return False

        # Rule 1: Inside test directory
        if any(part.lower() in {"tests", "test", "__tests__", "spec"} for part in parts):
            return True

        # Rule 2: Naming conventions
        if ext == ".py" and (
            filename.startswith("test_") or filename.endswith("_test.py")
        ):
            return True

        if ext in {".js", ".ts"} and (
            filename.endswith(".test.js")
            or filename.endswith(".spec.js")
            or filename.endswith(".test.ts")
            or filename.endswith(".spec.ts")
        ):
            return True

        if ext == ".go" and filename.endswith("_test.go"):
            return True

        if ext == ".java" and filename.endswith("Test.java"):
            return True

        return False


