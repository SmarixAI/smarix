"""
Enterprise-Grade Multi-Source RAG Data Processing Pipeline
Implements: GitHub-first → Gmail correlation → Raw fallback with hybrid retrieval
Enhanced: Code analysis, repo structure, tech stack detection, metrics extraction
Handles: Edge cases, cross-references, metadata enrichment, and dual indexing
"""

import os
import sys
import json
import argparse
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional
from datetime import datetime
from collections import defaultdict, Counter
import re


STATE_FILE = Path(
    Path(__file__).resolve().parents[2]
    / "data"
    / "Admin"
    / "state"
    / "runtime_state.json"
)


def load_current_repo_from_state():
    if not STATE_FILE.exists():
        raise RuntimeError(f"❌ State file not found: {STATE_FILE}")

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

    curr_repo = state.get("curr_repo")
    if not curr_repo:
        raise RuntimeError("❌ curr_repo missing in runtime_state.json")

    owner = curr_repo.get("owner")
    name = curr_repo.get("name")

    if not owner or not name:
        raise RuntimeError("❌ curr_repo.owner or curr_repo.name missing")

    return owner, name


# Ensure the backend package directory is on sys.path
_backend_dir = Path(__file__).resolve().parents[2]
_backend_dir_str = str(_backend_dir)
if _backend_dir_str not in sys.path:
    sys.path.insert(0, _backend_dir_str)

REPO_OWNER, REPO_NAME = load_current_repo_from_state()
FULL_REPO_NAME = f"{REPO_OWNER}/{REPO_NAME}"


class GraphExtractor:
    """
    Extracts Graph Nodes and Edges from Code Analysis data.
    Prepares data for Neo4j/NetworkX.
    Supports AST for Python/JS and Regex Fallback for C/C++/Java/Go/Rust/Ruby/PHP etc.
    """

    # Regex patterns for fallback extraction
    # Format: "language": {"function": r"pattern", "class": r"pattern", "import": r"pattern"}
    LANGUAGE_REGEX = {
        # C-family (C, C++, Java, C#, Dart, Kotlin, Scala, Swift)
        "c": {
            "function": r"(?:[\w\[\]\*]+\s+)+(\w+)\s*\([^)]*\)\s*\{",
            "class": r"(?:struct|enum)\s+(\w+)",
            "import": r'#include\s*[<"]([^>"]+)[>"]',
        },
        "cpp": {
            "function": r"(?:[\w\[\]\*:<>]+\s+)+(\w+)\s*\([^)]*\)\s*\{",
            "class": r"(?:class|struct|enum|namespace)\s+(\w+)",
            "import": r'#include\s*[<"]([^>"]+)[>"]',
        },
        "java": {
            "function": r"(?:public|protected|private|static|\s)+[\w\[\]<>]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{",
            "class": r"(?:class|interface|enum)\s+(\w+)",
            "import": r"import\s+([\w\.]+);",
        },
        "csharp": {
            "function": r"(?:public|protected|private|static|virtual|override|\s)+[\w\[\]<>]+\s+(\w+)\s*\([^)]*\)\s*\{",
            "class": r"(?:class|interface|struct|enum)\s+(\w+)",
            "import": r"using\s+([\w\.]+);",
        },
        "dart": {
            "function": r"(?:[\w\[\]<>]+\s+)?(\w+)\s*\([^)]*\)\s*\{",
            "class": r"(?:class|mixin|enum)\s+(\w+)",
            "import": r"import\s+['\"]([^'\"]+)['\"];",
        },
        # Modern Compiled (Go, Rust)
        "go": {
            "function": r"func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(",  # Matches func Name() and func (r *Receiver) Name()
            "class": r"type\s+(\w+)\s+(?:struct|interface)",
            "import": r'import\s+(?:\(([^)]+)\)|"([^"]+)")',  # Handles block and single imports
        },
        "rust": {
            "function": r"fn\s+(\w+)\s*(?:<[^>]+>)?\s*\(",
            "class": r"(?:struct|enum|trait|impl)\s+(\w+)",
            "import": r"use\s+([\w:{}]+);",
        },
        # Scripting (Ruby, PHP, Shell)
        "ruby": {
            "function": r"def\s+(\w+)",
            "class": r"(?:class|module)\s+(\w+)",
            "import": r'require\s+[\'"]([^\'"]+)[\'"]',
        },
        "php": {
            "function": r"function\s+(\w+)\s*\(",
            "class": r"(?:class|interface|trait)\s+(\w+)",
            "import": r'(?:require|include)(?:_once)?\s*[\'"]([^\'"]+)[\'"]',
        },
        "shell": {
            "function": r"(\w+)\s*\(\)\s*\{",  # function_name() {
            "class": None,
            "import": r"source\s+([^\s]+)",
        },
    }

    def __init__(self, repo_name):
        self.repo_name = repo_name
        self.nodes = {}
        self.edges = []

    def _make_id(self, _type, name, parent_file):
        """Create deterministic Node IDs"""
        clean_path = parent_file.replace("/", "_").replace(".", "_")
        return f"{self.repo_name}::{clean_path}::{_type}::{name}"

    def process_analysis(
        self, file_path: str, analysis: Dict[str, Any], content: str = ""
    ):
        """Convert analysis into Nodes and Edges. Uses AST if available, else Regex."""

        if not analysis:
            analysis = {}

        # 1. Always create the File Node
        file_id = f"{self.repo_name}::{file_path}"
        lang = analysis.get("language") or "text"

        self.nodes[file_id] = {
            "id": file_id,
            "label": "File",
            "properties": {
                "name": Path(file_path).name,
                "path": file_path,
                "lang": lang,
            },
        }

        # 2. Check for Rich AST Data (Python/JS)
        has_ast = (
            isinstance(analysis.get("classes"), list) and len(analysis["classes"]) > 0
        ) or (
            isinstance(analysis.get("functions"), list)
            and len(analysis["functions"]) > 0
        )

        if has_ast:
            self._process_ast(file_path, file_id, analysis)
        elif content:
            # 3. Fallback: Use Regex for other languages
            # Normalize lang string (e.g., "c++" -> "cpp")
            norm_lang = lang.lower()
            if norm_lang == "c++":
                norm_lang = "cpp"

            self._process_generic(file_path, file_id, content, norm_lang)

    def _process_ast(self, file_path, file_id, analysis):
        """Handle rich data from Python/JS analyzers"""
        # Extract Classes
        for cls in analysis.get("classes", []):
            class_id = self._make_id("CLASS", cls["name"], file_path)
            self.nodes[class_id] = {
                "id": class_id,
                "label": "Class",
                "properties": {"name": cls["name"], "lineno": cls.get("lineno")},
            }
            self.edges.append(
                {"source": class_id, "target": file_id, "type": "DEFINED_IN"}
            )

            for base in cls.get("bases", []):
                base_id = self._make_id("CLASS", base, "EXTERNAL")
                self.edges.append(
                    {"source": class_id, "target": base_id, "type": "INHERITS"}
                )

        # Extract Functions
        for func in analysis.get("functions", []):
            func_id = self._make_id("FUNCTION", func["name"], file_path)
            self.nodes[func_id] = {
                "id": func_id,
                "label": "Function",
                "properties": {
                    "name": func["name"],
                    "args": func.get("args", []),
                    "lineno": func.get("lineno"),
                },
            }
            self.edges.append(
                {"source": func_id, "target": file_id, "type": "DEFINED_IN"}
            )

            for call in func.get("calls", []):
                call_target_id = f"CONCEPT::{call}"
                self.edges.append(
                    {"source": func_id, "target": call_target_id, "type": "CALLS"}
                )

        # Extract Imports
        for imp in analysis.get("imports", []):
            module_name = imp.get("module") if isinstance(imp, dict) else imp
            if module_name:
                mod_id = f"MODULE::{module_name}"
                self.edges.append(
                    {"source": file_id, "target": mod_id, "type": "IMPORTS"}
                )

    def _process_generic(self, file_path, file_id, content, lang):
        """Fallback: Regex extraction for various languages"""
        import re

        # Get patterns for this language, or default to empty
        patterns = self.LANGUAGE_REGEX.get(lang)

        # If language not found, try to map based on extension logic or defaults
        if not patterns:
            # Simple fallback for C-like languages if exact match missing
            if lang in ["h", "hpp", "cxx", "cc"]:
                patterns = self.LANGUAGE_REGEX["cpp"]
            elif lang in ["kt", "kotlin"]:
                patterns = self.LANGUAGE_REGEX["java"]  # Close enough
            elif lang in ["ts", "tsx", "js", "jsx"]:
                patterns = self.LANGUAGE_REGEX["dart"]  # Close enough structure
            else:
                return  # Unknown language, skip extraction

        # 1. Extract Functions
        if patterns.get("function"):
            for match in re.finditer(patterns["function"], content, re.MULTILINE):
                # Some patterns return groups, we want the name group (usually last one)
                func_name = match.group(1) if match.lastindex >= 1 else match.group(0)

                # Filter common keywords to avoid false positives
                if func_name in ["if", "for", "while", "switch", "catch", "return"]:
                    continue

                func_id = self._make_id("FUNCTION", func_name, file_path)
                self.nodes[func_id] = {
                    "id": func_id,
                    "label": "Function",
                    "properties": {"name": func_name, "lang": lang},
                }
                self.edges.append(
                    {"source": func_id, "target": file_id, "type": "DEFINED_IN"}
                )

        # 2. Extract Classes/Structs
        if patterns.get("class"):
            for match in re.finditer(patterns["class"], content, re.MULTILINE):
                class_name = match.group(1)
                class_id = self._make_id("CLASS", class_name, file_path)
                self.nodes[class_id] = {
                    "id": class_id,
                    "label": "Class",
                    "properties": {"name": class_name, "lang": lang},
                }
                self.edges.append(
                    {"source": class_id, "target": file_id, "type": "DEFINED_IN"}
                )

        # 3. Extract Imports/Includes
        if patterns.get("import"):
            for match in re.finditer(patterns["import"], content, re.MULTILINE):
                # Handles Go block imports slightly differently, but generally group 1 or 2 is the name
                module_name = (
                    match.group(1)
                    if match.group(1)
                    else match.group(2) if match.lastindex >= 2 else None
                )

                if module_name:
                    # Clean up quotes/newlines
                    module_name = (
                        module_name.strip().strip('"').strip("'").replace("\n", "")
                    )
                    mod_id = f"MODULE::{module_name}"
                    self.edges.append(
                        {"source": file_id, "target": mod_id, "type": "IMPORTS"}
                    )

    def get_graph_data(self):
        return {"nodes": list(self.nodes.values()), "edges": self.edges}

    def process_pr(self, pr: Dict[str, Any]):
        """Add PR nodes and link them to modified files and authors"""
        if not pr: return
        
        pr_number = pr.get("number")
        if not pr_number: return
        
        # Create PR Node
        pr_id = f"{self.repo_name}::PR::{pr_number}"
        self.nodes[pr_id] = {
            "id": pr_id,
            "label": "PullRequest",
            "properties": {
                "number": pr_number,
                "title": pr.get("title", ""),
                "state": pr.get("state", ""),
                "merged": pr.get("merged", False) or pr.get("is_merged", False)
            }
        }
        
        # Link PR -> Files (MODIFIES edge)
        files = pr.get("files", []) or pr.get("changed_files", [])
        for file in files:
            filename = file.get("filename") if isinstance(file, dict) else file
            if filename:
                file_id = f"{self.repo_name}::{filename}"
                self.edges.append({"source": pr_id, "target": file_id, "type": "MODIFIES"})

        # Link PR -> User (CREATED_BY edge)
        user = pr.get("user", {})
        if user and isinstance(user, dict):
            author_name = user.get("login")
            if author_name:
                author_id = f"User::{author_name}"
                if author_id not in self.nodes:
                    self.nodes[author_id] = {
                        "id": author_id, "label": "User", "properties": {"name": author_name}
                    }
                self.edges.append({"source": pr_id, "target": author_id, "type": "CREATED_BY"})

    def process_issue(self, issue: Dict[str, Any], linked_prs: List[str] = None):
        """Add Issue nodes and link to PRs"""
        if not issue: return
        
        issue_number = issue.get("number")
        if not issue_number: return
        
        # Create Issue Node
        issue_id = f"{self.repo_name}::Issue::{issue_number}"
        self.nodes[issue_id] = {
            "id": issue_id,
            "label": "Issue",
            "properties": {
                "number": issue_number,
                "title": issue.get("title", ""),
                "state": issue.get("state", "")
            }
        }
        
        # Link Issue -> PR (CLOSES edge)
        if linked_prs:
            for pr_num_str in linked_prs:
                clean_num = str(pr_num_str).replace("#", "").strip()
                if clean_num:
                    pr_id = f"{self.repo_name}::PR::{clean_num}"
                    self.edges.append({"source": pr_id, "target": issue_id, "type": "CLOSES"})

class CodeAnalyzer:
    """
    Advanced code analysis for repository structure and metrics
    """

    # Language detection patterns
    LANGUAGE_PATTERNS = {
        # Popular/major languages
        "python": [".py", ".pyw", ".pyx"],
        "javascript": [".js", ".mjs", ".cjs", ".jsx"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "kotlin": [".kt", ".kts"],
        "scala": [".scala"],
        "groovy": [".groovy"],
        "groovy-xml": [".gvy"],
        # C-family
        "c": [".c", ".h"],
        "cpp": [".cpp", ".cc", ".cxx", ".c++", ".hpp", ".hh", ".hxx"],
        "csharp": [".cs"],
        "objective-c": [".m", ".mm"],
        "swift": [".swift"],
        "rust": [".rs"],
        "go": [".go"],
        # Web / markup / styles
        "html": [".html", ".htm"],
        "css": [".css", ".scss", ".sass", ".less", ".styl"],
        "xml": [".xml"],
        "json": [".json"],
        "yaml": [".yml", ".yaml"],
        "markdown": [".md", ".markdown"],
        # Scripting / shells
        "shell": [".sh", ".bash", ".zsh", ".ksh"],
        "powershell": [".ps1", ".psm1"],
        "perl": [".pl", ".pm"],
        "ruby": [".rb"],
        "php": [".php"],
        "r": [".r", ".R"],
        # Functional / less common
        "haskell": [".hs"],
        "ocaml": [".ml", ".mli"],
        "elm": [".elm"],
        "clojure": [".clj", ".cljs", ".cljc"],
        "elixir": [".ex", ".exs"],
        "erlang": [".erl", ".hrl"],
        # Data / numeric / domain-specific
        "matlab": [".m"],
        "fortran": [".f90", ".f", ".f95"],
        "julia": [".jl"],
        # Mobile / Dart
        "dart": [".dart"],
        "flutter": [".dart"],
        # Build / configuration / misc
        "dockerfile": ["dockerfile", ".dockerfile"],
        "sql": [".sql"],
        "protobuf": [".proto"],
        "make": ["Makefile"],
        "cmake": ["CMakeLists.txt"],
        "gradle": ["build.gradle", ".gradle"],
        "maven": ["pom.xml"],
        "bazel": ["BUILD", "WORKSPACE"],
        "terraform": [".tf"],
        "graphql": [".graphql", ".gql"],
        "wasm": [".wasm"],
        "assembly": [".s", ".asm", ".S"],
    }

    FRAMEWORK_PATTERNS = {
        # JavaScript / Frontend
        "react": [
            r"from\s+[\'\"]react[\'\"]",
            r"ReactDOM\.render",
            r"\bcreateRoot\(",
            r"\buseState\b",
            r"\buseEffect\b",
            r"react-native",
        ],
        "react-native": [r"from\s+[\'\"]react-native[\'\"]", r"react-native"],
        "vue": [
            r"from\s+[\'\"]vue[\'\"]",
            r"<template>",
            r"export\s+default\s+{",
            r"vue-router",
        ],
        "svelte": [r"<script\s+lang=", r"svelte", r"from\s+[\'\"]svelte[\'\"]"],
        "angular": [r"@angular/", r"@Component", r"@NgModule", r"bootstrapModule"],
        "ember": [r"ember", r"@ember/"],
        "backbone": [r"Backbone\.Model", r"Backbone\.View"],
        # Fullstack / Node
        "express": [r"require\([\'\"]express[\'\"]\)", r"express\(\)"],
        "koa": [r"require\([\'\"]koa[\'\"]\)", r"new\s+Koa\("],
        "hapi": [r"@hapi/"],
        # Static site / meta frameworks
        "nextjs": [
            r"next(/|\\\w+)?",
            r"getStaticProps",
            r"getServerSideProps",
            r"next.config",
        ],
        "nuxt": [r"nuxt", r"nuxt.config"],
        "gatsby": [r"gatsby-\w+", r"export\s+const\s+query"],
        # Python web frameworks
        "django": [r"from\s+django", r"import\s+django", r"Django"],
        "flask": [r"from\s+flask\s+import", r"Flask\("],
        "fastapi": [r"from\s+fastapi\s+import", r"FastAPI\("],
        "tornado": [r"tornado.web", r"tornado."],
        "bottle": [r"from\s+bottle\s+import", r"bottle\."],
        "aiohttp": [r"from\s+aiohttp", r"aiohttp\."],
        # Java frameworks
        "spring": [
            r"@SpringBootApplication",
            r"@RestController",
            r"org\.springframework",
            r"SpringApplication.run",
        ],
        "quarkus": [r"io\.quarkus", r"@ApplicationScoped"],
        "micronaut": [r"io\.micronaut", r"Micronaut"],
        # JVM / others
        "playframework": [r"play.mvc", r"@Singleton"],
        "vertx": [r"io\.vertx"],
        # PHP frameworks
        "laravel": [r"use\s+Illuminate\\", r"extends\s+Controller", r"artisan"],
        "symfony": [r"Symfony\\Component", r"bin/console"],
        "cakephp": [r"CakePHP", r"Configure::write"],
        # Ruby
        "rails": [
            r"class\s+\w+\s+<\s+ApplicationController",
            r"Rails\.application",
            r"bundle exec rails",
        ],
        # .NET
        "aspnet": [r"using\s+Microsoft\.AspNetCore", r"Startup\.cs", r"Program\.cs"],
        # Mobile
        "flutter": [
            r"import\s+['\"]package:flutter\/",
            r"\bStatelessWidget\b",
            r"\bStatefulWidget\b",
            r"\brunApp\s*\(",
            r"\bMaterialApp\b",
            r"\bCupertinoApp\b",
        ],
        "ionic": [r"@ionic/", r"ionic-angular"],
        # Go
        "gin": [r"github\.com\/gin-gonic\/gin", r"gin\.Default\("],
        "echo": [r"github\.com\/labstack\/echo", r"echo\.New\("],
        "beego": [r"github\.com\/astaxie\/beego"],
        # Rust
        "actix": [r"actix_web", r"actix::"],
        "rocket": [r"rocket::", r"#\s*\[launch\]"],
        # Databases / ORMs
        "sequelize": [r"sequelize", r"Sequelize\("],
        "typeorm": [r"from\s+[\'\"]typeorm[\'\"]", r"TypeORM"],
        "hibernate": [r"org\.hibernate", r"hibernate"],
        # Data / ML
        "tensorflow": [r"import\s+tensorflow", r"from\s+tensorflow", r"tf\."],
        "pytorch": [r"import\s+torch", r"from\s+torch"],
        "keras": [r"from\s+keras", r"import\s+keras"],
        "jax": [r"import\s+jax"],
        # Python data libs (useful to detect data projects)
        "pandas": [r"import\s+pandas", r"pd\.DataFrame"],
        "numpy": [r"import\s+numpy", r"np\.array"],
        "scikit-learn": [r"from\s+sklearn", r"import\s+sklearn"],
        # Testing / infra frameworks
        "pytest": [r"pytest", r"def\s+test_"],
        "jest": [r"jest", r"describe\(", r"test\("],
        "mocha": [r"mocha", r"describe\(", r"it\("],
        "junit": [r"@Test", r"org\.junit"],
        # Static site generators / CMS
        "wordpress": [r"wp-content", r"WordPress", r"wp-admin"],
        "ghost": [r"Ghost", r"ghost-cli"],
        # Misc / catch-alls
        "docker": [r"FROM\s+\w+", r"Dockerfile"],
        "kubernetes": [r"kind:\s*(Deployment|Service|Ingress)", r"apiVersion:.*k8s"],
        "serverless": [r"serverless", r"serverless\.yml"],
        "electron": [r"electron", r"app\.whenReady\("],
    }

    TOOL_PATTERNS = {
        # CI / CD
        "github-actions": [
            ".github/workflows/",
            "actions/setup-node",
            "actions/checkout",
        ],
        "gitlab-ci": [".gitlab-ci.yml"],
        "azure-pipelines": ["azure-pipelines.yml"],
        "jenkins": ["Jenkinsfile"],
        "travis": [".travis.yml"],
        "circleci": [".circleci/config.yml"],
        "argo": ["argo", "argo-cd"],
        # Build / package managers
        "npm": ["package.json", "package-lock.json"],
        "yarn": ["yarn.lock", "yarn.lock"],
        "pnpm": ["pnpm-lock.yaml"],
        "pip": ["requirements.txt", "setup.py"],
        "pipenv": ["Pipfile", "Pipfile.lock"],
        "poetry": ["poetry.lock", "pyproject.toml"],
        "conda": ["environment.yml", "environment.yaml"],
        "composer": ["composer.json", "composer.lock"],
        "maven": ["pom.xml"],
        "gradle": ["build.gradle", "settings.gradle"],
        "sbt": ["build.sbt"],
        "cargo": ["Cargo.toml"],
        "go-mod": ["go.mod"],
        "bundler": ["Gemfile", "Gemfile.lock"],
        # Containers / orchestration
        "docker": ["Dockerfile", "docker-compose.yml", ".dockerignore"],
        "kubernetes": [
            "deployment.yaml",
            "service.yaml",
            "ingress.yaml",
            "k8s/",
            "kustomization.yaml",
        ],
        "helm": ["Chart.yaml", "values.yaml"],
        "kustomize": ["kustomization.yaml"],
        # IaC
        "terraform": [".tf", ".tfvars"],
        "cloudformation": ["AWSTemplateFormatVersion", "Resources:", "cloudformation"],
        "serverless": ["serverless.yml", "serverless.yaml"],
        "packer": ["packer", "templates.json"],
        # Testing / linting / quality
        "pytest": ["pytest.ini", "conftest.py", "test_*.py"],
        "jest": ["jest.config.js", ".spec.js", ".test.js"],
        "mocha": ["mocha.opts"],
        "junit": ["junit", "TEST-"],
        "eslint": [".eslintrc", ".eslintrc.js", ".eslintrc.json"],
        "tslint": ["tslint.json"],
        "stylelint": [".stylelintrc"],
        # Bundlers / transpilers / tooling
        "webpack": ["webpack.config.js"],
        "rollup": ["rollup.config.js"],
        "babel": [".babelrc", "babel.config.js"],
        "parcel": ["parcel", "parcel.config.js"],
        # Infra / orchestration / cloud tools
        "ansible": ["playbook.yml", "ansible.cfg", "roles/"],
        "helm": ["Chart.yaml"],
        "istio": ["istio", "istioctl"],
        "prometheus": ["prometheus.yml", "prometheus"],
        "grafana": ["grafana", "grafana.ini"],
        # Package managers / lockfiles (repeated intentionally to capture whichever is present)
        "npm": ["package.json"],
        "yarn": ["yarn.lock"],
        "pnpm": ["pnpm-lock.yaml"],
        "pip": ["requirements.txt", "setup.py", "pyproject.toml"],
        "poetry": ["poetry.lock"],
        # Mobile / SDK tools
        "flutter": ["pubspec.yaml", ".flutter-plugins"],
        "android-gradle": ["gradlew", "gradlew.bat", "android", "app/build.gradle"],
        "ios-cocoapods": ["Podfile", "Podfile.lock"],
        # Misc
        "make": ["Makefile"],
        "cmake": ["CMakeLists.txt"],
        "bazel": ["BUILD", "WORKSPACE"],
        "docker-compose": ["docker-compose.yml"],
        "serverless": ["serverless.yml"],
        "cloudbuild": ["cloudbuild.yaml"],
        "terraform": [".tf"],
    }

    def __init__(self):
        self.metrics = {
            "total_files": 0,
            "total_lines": 0,
            "total_code_lines": 0,
            "total_comment_lines": 0,
            "total_blank_lines": 0,
            "languages": Counter(),
            "frameworks": Counter(),
            "tools": Counter(),
            "file_types": Counter(),
            "largest_files": [],
            "most_complex_files": [],
        }
        self.repo_structure = {
            "directories": [],
            "max_depth": 0,
            "root_files": [],
            "src_paths": [],
            "test_paths": [],
            "config_paths": [],
            "doc_paths": [],
        }
        self.function_metrics = {
            "total_functions": 0,
            "total_classes": 0,
            "functions_by_language": Counter(),
            "classes_by_language": Counter(),
            "average_function_length": 0,
        }

    def detect_language(self, filepath: str) -> Optional[str]:
        """Detect programming language from file extension or filename"""
        if not filepath:
            return None
        filepath_lower = filepath.lower()
        filename = os.path.basename(filepath_lower)

        # Special cases
        if filename == "dockerfile" or filename.endswith(".dockerfile"):
            return "dockerfile"

        for lang, extensions in self.LANGUAGE_PATTERNS.items():
            for ext in extensions:
                if filepath_lower.endswith(ext):
                    return lang
        return None

    def count_lines(self, content: str, language: str) -> Dict[str, int]:
        """Count code, comment, and blank lines with better multiline handling"""
        if content is None:
            content = ""
        lines = content.splitlines()
        total = len(lines)
        blank = sum(1 for line in lines if not line.strip())

        # Patterns for single-line comments by language (simple heuristics)
        comment_patterns = {
            "python": [r"^\s*#"],
            "javascript": [r"^\s*//"],
            "java": [r"^\s*//"],
            "cpp": [r"^\s*//"],
            "c": [r"^\s*//"],
            "go": [r"^\s*//"],
            "rust": [r"^\s*//"],
            "ruby": [r"^\s*#"],
            "shell": [r"^\s*#"],
        }

        patterns = comment_patterns.get(language, [r"^\s*#", r"^\s*//"])
        comments = 0

        in_multiline = False
        multiline_start_tokens = ('"""', "'''", "/*")
        multiline_end_map = {'"""': '"""', "'''": "'''", "/*": "*/"}

        # We attempt a robust toggle: if a line contains a start token without end token, toggle.
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check for inline multiline start+end on same line
            inline_multistart = None
            for t in multiline_start_tokens:
                if (
                    t in stripped
                    and multiline_end_map[t] in stripped
                    and stripped.index(t) < stripped.rindex(multiline_end_map[t])
                ):
                    # start and end on same line — count as comment line but do not toggle
                    comments += 1
                    inline_multistart = t
                    break
            if inline_multistart:
                continue

            # Toggle start of multiline
            started = False
            for t in multiline_start_tokens:
                if t in stripped and multiline_end_map[t] not in stripped:
                    # start of multiline comment
                    in_multiline = (
                        not in_multiline if not in_multiline else in_multiline
                    )
                    comments += 1
                    started = True
                    break
            if started:
                continue

            # End of multiline
            for t, endt in multiline_end_map.items():
                if endt in stripped and in_multiline:
                    comments += 1
                    in_multiline = False
                    started = True
                    break
            if started:
                continue

            if in_multiline:
                comments += 1
                continue

            # Single-line comment patterns
            if any(re.match(p, line) for p in patterns):
                comments += 1
                continue

        code = total - blank - comments
        code = max(0, code)

        return {
            "total": total,
            "code": code,
            "comments": comments,
            "blank": blank,
        }

    def count_functions_and_classes(
        self, content: str, language: str
    ) -> Dict[str, int]:
        """Count functions and classes in code (simple regex heuristics)"""
        functions = 0
        classes = 0
        if not content:
            return {"functions": 0, "classes": 0}

        patterns = {
            "python": {
                "function": r"^\s*def\s+\w+\s*\(",
                "class": r"^\s*class\s+\w+",
            },
            "javascript": {
                "function": r"(^\s*function\s+\w+\s*\(|^\s*const\s+\w+\s*=\s*\(|^\s*\w+\s*:\s*function\s*\()",
                "class": r"^\s*class\s+\w+",
            },
            "typescript": {
                "function": r"(^\s*function\s+\w+\s*\(|^\s*const\s+\w+\s*=\s*\(|^\s*\w+\s*:\s*function\s*\()",
                "class": r"^\s*(export\s+)?(abstract\s+)?class\s+\w+",
            },
            "java": {
                "function": r"^\s*(public|private|protected)?\s*(static\s+)?\w+\s+\w+\s*\(",
                "class": r"^\s*(public|private|protected)?\s*class\s+\w+",
            },
            "cpp": {
                "function": r"^\s*\w+\s+\w+\s*\(",
                "class": r"^\s*class\s+\w+",
            },
            "go": {
                "function": r"^\s*func\s+(\w+\s*)?\(",
                "class": r"^\s*type\s+\w+\s+struct",
            },
            "rust": {
                "function": r"^\s*(pub\s+)?fn\s+\w+",
                "class": r"^\s*(pub\s+)?struct\s+\w+",
            },
        }

        lang_patterns = patterns.get(language, patterns.get("python"))

        for line in content.splitlines():
            if re.match(lang_patterns["function"], line):
                functions += 1
            if re.match(lang_patterns["class"], line):
                classes += 1

        return {"functions": functions, "classes": classes}

    def detect_frameworks(self, content: str) -> Set[str]:
        """Detect frameworks used in code (case-insensitive)"""
        detected = set()
        if not content:
            return detected

        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected.add(framework)
                    break

        return detected

    def analyze_file(self, filepath: str, content: str, size: int) -> Dict[str, Any]:
        """Comprehensive file analysis"""
        language = self.detect_language(filepath)

        analysis = {
            "path": filepath,
            "size": size,
            "language": language,
            "metrics": {},
            "frameworks": [],
            "complexity_score": 0,
        }

        if language and language not in ["json", "yaml", "xml", "markdown"]:
            # Line counting
            line_metrics = self.count_lines(content, language)
            analysis["metrics"] = line_metrics

            # Function/class counting
            func_class_metrics = self.count_functions_and_classes(content, language)
            analysis["metrics"].update(func_class_metrics)

            # Framework detection
            frameworks = self.detect_frameworks(content)
            analysis["frameworks"] = list(frameworks)

            # Simple complexity score based on:
            # - Lines of code
            # - Number of functions/classes
            # - Nesting levels (count of indentation)
            non_empty_lines = [line for line in content.splitlines() if line.strip()]
            if non_empty_lines:
                nesting_level = max(
                    len(line) - len(line.lstrip()) for line in non_empty_lines
                )
            else:
                nesting_level = 0

            complexity = (
                line_metrics["code"] * 0.1
                + func_class_metrics["functions"] * 2
                + func_class_metrics["classes"] * 3
                + nesting_level * 0.5
            )
            analysis["complexity_score"] = round(complexity, 2)

            # Update global metrics
            self.metrics["total_lines"] += line_metrics["total"]
            self.metrics["total_code_lines"] += line_metrics["code"]
            self.metrics["total_comment_lines"] += line_metrics["comments"]
            self.metrics["total_blank_lines"] += line_metrics["blank"]
            if language:
                self.metrics["languages"][language] += 1

            self.function_metrics["total_functions"] += func_class_metrics["functions"]
            self.function_metrics["total_classes"] += func_class_metrics["classes"]
            if language:
                self.function_metrics["functions_by_language"][
                    language
                ] += func_class_metrics["functions"]
                self.function_metrics["classes_by_language"][
                    language
                ] += func_class_metrics["classes"]

            for fw in frameworks:
                self.metrics["frameworks"][fw] += 1

        # Track largest files
        lf = self.metrics["largest_files"]
        if len(lf) < 10:
            lf.append((filepath, size))
            lf.sort(key=lambda x: x[1], reverse=True)
        elif size > lf[-1][1]:
            lf[-1] = (filepath, size)
            lf.sort(key=lambda x: x[1], reverse=True)

        # Track most complex files
        mcf = self.metrics["most_complex_files"]
        if language and analysis["complexity_score"] > 0:
            if len(mcf) < 10:
                mcf.append((filepath, analysis["complexity_score"]))
                mcf.sort(key=lambda x: x[1], reverse=True)
            elif analysis["complexity_score"] > mcf[-1][1]:
                mcf[-1] = (filepath, analysis["complexity_score"])
                mcf.sort(key=lambda x: x[1], reverse=True)

        # Increment total files counter (analyzed files)
        self.metrics["total_files"] += 1
        # Track file_types
        self.metrics["file_types"][language or "unknown"] += 1

        return analysis

    def analyze_structure(self, file_paths: List[str]) -> None:
        """Analyze repository structure"""
        directories = set()
        root_files = []
        src_paths = []
        test_paths = []
        config_paths = []
        doc_paths = []

        max_depth = 0

        for path in file_paths:
            if not path:
                continue
            parts = path.split("/")
            depth = len(parts) - 1
            max_depth = max(max_depth, depth)

            # Build directory tree
            for i in range(len(parts) - 1):
                dir_path = "/".join(parts[: i + 1])
                directories.add(dir_path)

            # Categorize files
            path_lower = path.lower()
            filename = os.path.basename(path_lower)

            if depth == 0:
                root_files.append(path)

            if any(x in path_lower for x in ["src/", "source/", "lib/", "app/"]):
                src_paths.append(path)

            if any(x in path_lower for x in ["test/", "tests/", "__tests__", "spec/"]):
                test_paths.append(path)

            if any(
                x in filename
                for x in [
                    ".json",
                    ".yml",
                    ".yaml",
                    ".toml",
                    ".ini",
                    ".cfg",
                    ".conf",
                    "config",
                ]
            ):
                config_paths.append(path)

            if any(
                x in path_lower
                for x in ["doc/", "docs/", "documentation/", ".md", "readme"]
            ):
                doc_paths.append(path)

        self.repo_structure = {
            "directories": sorted(directories),
            "directory_count": len(directories),
            "max_depth": max_depth,
            "root_files": root_files,
            "src_paths": src_paths,
            "test_paths": test_paths,
            "config_paths": config_paths,
            "doc_paths": doc_paths,
        }

    def detect_tools(self, file_paths: List[str]) -> None:
        """Detect development tools and build systems"""
        file_set = set(f.lower() for f in file_paths if f)

        for tool, indicators in self.TOOL_PATTERNS.items():
            for indicator in indicators:
                if any(indicator.lower() in fp for fp in file_set):
                    self.metrics["tools"][tool] += 1
                    break

    def get_tech_stack_summary(self) -> Dict[str, Any]:
        """Generate comprehensive tech stack summary"""
        # Calculate average function length
        if self.function_metrics["total_functions"] > 0:
            self.function_metrics["average_function_length"] = round(
                self.metrics["total_code_lines"]
                / self.function_metrics["total_functions"],
                2,
            )

        return {
            "languages": {
                "primary": (
                    self.metrics["languages"].most_common(1)[0][0]
                    if self.metrics["languages"]
                    else "unknown"
                ),
                "all": dict(self.metrics["languages"]),
                "count": len(self.metrics["languages"]),
            },
            "frameworks": {
                "detected": list(self.metrics["frameworks"].keys()),
                "count": len(self.metrics["frameworks"]),
                "usage": dict(self.metrics["frameworks"]),
            },
            "tools": {
                "detected": list(self.metrics["tools"].keys()),
                "count": len(self.metrics["tools"]),
                "categories": self._categorize_tools(),
            },
            "metrics": {
                "total_files": self.metrics["total_files"],
                "total_lines": self.metrics["total_lines"],
                "total_code_lines": self.metrics["total_code_lines"],
                "total_comment_lines": self.metrics["total_comment_lines"],
                "total_blank_lines": self.metrics["total_blank_lines"],
                "code_to_comment_ratio": round(
                    self.metrics["total_code_lines"]
                    / max(self.metrics["total_comment_lines"], 1),
                    2,
                ),
            },
            "functions_and_classes": {
                "total_functions": self.function_metrics["total_functions"],
                "total_classes": self.function_metrics["total_classes"],
                "average_function_length": self.function_metrics[
                    "average_function_length"
                ],
                "functions_by_language": dict(
                    self.function_metrics["functions_by_language"]
                ),
                "classes_by_language": dict(
                    self.function_metrics["classes_by_language"]
                ),
            },
            "structure": self.repo_structure,
            "quality_indicators": {
                "has_tests": len(self.repo_structure.get("test_paths", [])) > 0,
                "has_documentation": len(self.repo_structure.get("doc_paths", [])) > 0,
                "has_ci_cd": any(
                    tool in self.metrics["tools"]
                    for tool in [
                        "github-actions",
                        "gitlab-ci",
                        "jenkins",
                        "travis",
                        "circleci",
                    ]
                ),
                "has_containerization": "docker" in self.metrics["tools"],
                "largest_files": [
                    {"path": p, "size": s} for p, s in self.metrics["largest_files"][:5]
                ],
                "most_complex_files": [
                    {"path": p, "complexity": c}
                    for p, c in self.metrics["most_complex_files"][:5]
                ],
            },
        }

    def _categorize_tools(self) -> Dict[str, List[str]]:
        """Categorize detected tools"""
        categories = {
            "build": [],
            "testing": [],
            "ci_cd": [],
            "containerization": [],
            "package_management": [],
            "code_quality": [],
            "infrastructure": [],
        }

        tool_categories = {
            "build": ["webpack", "babel", "gradle", "maven", "make"],
            "testing": ["pytest", "jest"],
            "ci_cd": ["github-actions", "gitlab-ci", "jenkins", "travis", "circleci"],
            "containerization": ["docker", "kubernetes"],
            "package_management": ["npm", "yarn", "pip", "poetry"],
            "code_quality": ["eslint", "prettier"],
            "infrastructure": ["terraform", "ansible"],
        }

        for tool in self.metrics["tools"].keys():
            for category, tools in tool_categories.items():
                if tool in tools:
                    categories[category].append(tool)

        return {k: v for k, v in categories.items() if v}


class DataChunker:
    """
    Intelligent chunking with cross-reference tracking, edge case handling, and code analysis
    """

    def __init__(self, repo_name):
        self.chunk_registry = {}  # Track all chunks by ID for deduplication
        self.entity_map = defaultdict(set)  # Map entities to chunk IDs
        self.git_keywords = set()  # Global keywords for correlation
        self.code_analyzer = CodeAnalyzer()  # Initialize code analyzer
        self.graph_extractor = GraphExtractor(repo_name)

    def generate_chunk_id(
        self, data: Dict[str, Any], chunk_type: str, index: int
    ) -> str:
        """Generate deterministic, collision-resistant chunk IDs"""
        try:
            # Use stable serialization for hashing
            payload = json.dumps(data, sort_keys=True, default=str)
        except Exception:
            payload = str(data)
        content_hash = hashlib.md5(payload.encode("utf-8")).hexdigest()[:8]
        return f"{chunk_type}_{index}_{content_hash}"

    def extract_git_entities(self, data: Dict[str, Any]) -> Dict[str, Set[str]]:
        """
        Extract structured entities for precise cross-referencing
        Returns: Dictionary of entity types → entity values
        """
        entities = {
            "authors": set(),
            "issue_numbers": set(),
            "pr_numbers": set(),
            "commit_shas": set(),
            "file_paths": set(),
            "branches": set(),
            "labels": set(),
            "emails": set(),
            "keywords": set(),
        }

        try:
            # Extract from issues
            for issue in data.get("issues", []):
                if not isinstance(issue, dict):
                    continue

                if "number" in issue:
                    num = str(issue["number"])
                    entities["issue_numbers"].add(f"#{num}")
                    entities["issue_numbers"].add(num)

                if "user" in issue and isinstance(issue["user"], dict):
                    author = issue["user"].get("login", "")
                    if author:
                        entities["authors"].add(author.lower())

                # Extract from issue body
                body = issue.get("body", "")
                if isinstance(body, str):
                    mentions = re.findall(r"@([a-zA-Z0-9_-]+)", body)
                    entities["authors"].update(m.lower() for m in mentions)

                    refs = re.findall(r"#(\d+)", body)
                    entities["issue_numbers"].update(f"#{r}" for r in refs)

                # Extract labels
                for label in issue.get("labels", []):
                    if isinstance(label, dict) and "name" in label:
                        entities["labels"].add(label["name"].lower())

                # Extract keywords from title
                title = issue.get("title", "")
                if isinstance(title, str):
                    words = re.findall(r"\b[a-zA-Z]{3,}\b", title.lower())
                    entities["keywords"].update(words)

            # Extract from PRs
            for pr in data.get("prs", []):
                if not isinstance(pr, dict):
                    continue

                if "number" in pr:
                    num = str(pr["number"])
                    entities["pr_numbers"].add(f"#{num}")
                    entities["pr_numbers"].add(num)

                if "user" in pr and isinstance(pr["user"], dict):
                    author = pr["user"].get("login", "")
                    if author:
                        entities["authors"].add(author.lower())

                # Extract file paths
                for file in pr.get("files", []):
                    if isinstance(file, dict) and "filename" in file:
                        path = file["filename"]
                        entities["file_paths"].add(path)
                        # Also add directories
                        parts = path.split("/")
                        for i in range(1, len(parts) + 1):
                            entities["file_paths"].add("/".join(parts[:i]))

                # Extract from PR body
                body = pr.get("body", "")
                if isinstance(body, str):
                    mentions = re.findall(r"@([a-zA-Z0-9_-]+)", body)
                    entities["authors"].update(m.lower() for m in mentions)

                    refs = re.findall(r"#(\d+)", body)
                    entities["pr_numbers"].update(f"#{r}" for r in refs)

                # Extract branch names
                if "head" in pr and isinstance(pr["head"], dict):
                    branch = pr["head"].get("ref", "")
                    if branch:
                        entities["branches"].add(branch.lower())

            # Extract from commits
            for commit in data.get("commits", []):
                if not isinstance(commit, dict):
                    continue

                if "sha" in commit:
                    sha = commit["sha"]
                    if sha:
                        entities["commit_shas"].add(sha[:7])
                        entities["commit_shas"].add(sha)

                commit_data = commit.get("commit", {})
                if isinstance(commit_data, dict):
                    # Author info
                    author_info = commit_data.get("author", {})
                    if isinstance(author_info, dict):
                        author_name = author_info.get("name", "")
                        author_email = author_info.get("email", "")
                        if author_name:
                            entities["authors"].add(author_name.lower())
                        if author_email:
                            entities["emails"].add(author_email.lower())

                    # Extract from commit message
                    message = commit_data.get("message", "")
                    if isinstance(message, str):
                        refs = re.findall(r"#(\d+)", message)
                        entities["issue_numbers"].update(f"#{r}" for r in refs)
                        words = re.findall(r"\b[a-zA-Z]{3,}\b", message.lower())
                        entities["keywords"].update(words)

                # Extract modified files
                files = commit.get("files", [])
                if isinstance(files, list):
                    for file in files:
                        if isinstance(file, dict) and "filename" in file:
                            entities["file_paths"].add(file["filename"])

            # Extract from code files
            for code_file in data.get("code_files", []):
                if not isinstance(code_file, dict):
                    continue
                if "path" in code_file:
                    entities["file_paths"].add(code_file["path"])

            # Clean up stop words
            stop_words = {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "from",
                "up",
                "about",
                "into",
                "through",
                "during",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
            }
            entities["keywords"] = {
                k for k in entities["keywords"] if len(k) > 2 and k not in stop_words
            }

        except Exception as e:
            print(f"      ⚠️  Warning: Error extracting entities: {e}")

        return entities

    def analyze_repository_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive code analysis on repository
        """
        print(f"      🔍 Analyzing repository code...")

        # Collect all file paths for structure analysis
        all_file_paths = []

        # Analyze code files
        for code_file in data.get("code_files", []):
            if not isinstance(code_file, dict):
                continue

            path = code_file.get("path", "")
            content = code_file.get("content", "")
            size = code_file.get("size", 0)

            if path and content is not None:
                all_file_paths.append(path)
                # analyze_file increments metrics internally
                analysis = self.code_analyzer.analyze_file(path, content, size)
                code_file["analysis"] = analysis

        # Analyze PR files
        for pr in data.get("prs", []):
            if not isinstance(pr, dict):
                continue
            for file in pr.get("files", []):
                if isinstance(file, dict) and "filename" in file:
                    all_file_paths.append(file["filename"])

        # Analyze commit files
        for commit in data.get("commits", []):
            if not isinstance(commit, dict):
                continue
            files = commit.get("files", [])
            if isinstance(files, list):
                for file in files:
                    if isinstance(file, dict) and "filename" in file:
                        all_file_paths.append(file["filename"])

        # Analyze structure
        if all_file_paths:
            self.code_analyzer.analyze_structure(all_file_paths)

        # Detect tools
        self.code_analyzer.detect_tools(all_file_paths)

        # Get comprehensive tech stack summary
        tech_stack = self.code_analyzer.get_tech_stack_summary()

        print(f"         ✓ Analyzed {self.code_analyzer.metrics['total_files']} files")
        print(f"         ✓ Total lines: {self.code_analyzer.metrics['total_lines']:,}")
        print(
            f"         ✓ Code lines: {self.code_analyzer.metrics['total_code_lines']:,}"
        )
        print(
            f"         ✓ Functions: {self.code_analyzer.function_metrics['total_functions']}"
        )
        print(
            f"         ✓ Classes: {self.code_analyzer.function_metrics['total_classes']}"
        )
        print(f"         ✓ Languages: {len(tech_stack['languages']['all'])}")
        print(f"         ✓ Frameworks: {len(tech_stack['frameworks']['detected'])}")
        print(f"         ✓ Tools: {len(tech_stack['tools']['detected'])}")

        return tech_stack

    def create_raw_data_reference(
        self, data: Dict[str, Any], source: str, repo_name: str
    ) -> Dict[str, Any]:
        """
        Create comprehensive raw data reference for edge case fallback
        """
        data_summary = {}

        for key, value in data.items():
            if isinstance(value, list):
                data_summary[key] = {
                    "count": len(value),
                    "sample": value[:2] if value else [],
                }
            elif isinstance(value, dict):
                data_summary[key] = {"keys": list(value.keys())}
            else:
                data_summary[key] = str(value)[:100]

        return {
            "chunk_id": f"{repo_name}_raw_{source}_full",
            "type": "raw_data_reference",
            "source": source,
            "repo_name": repo_name,
            "retrieval_priority": 4,  # Lowest priority - fallback only
            "is_raw_data": True,
            "metadata": {
                "repo_name": repo_name,
                "source": source,
                "data_keys": list(data.keys()),
                "summary": data_summary,
                "created_at": datetime.now().isoformat(),
                "total_size_bytes": len(json.dumps(data).encode("utf-8")),
            },
            "raw_data": data,
            "search_hints": {"text": json.dumps(data_summary), "keywords": []},
        }

    def chunk_git_data(
        self, data: Dict[str, Any], reponame: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Set[str]], Dict[str, Any]]:
        """Chunk Git data with enhanced metadata, entity extraction, bidirectional linking, and code analysis"""

        chunks = []
        entities = self.extract_git_entities(data)
        techstack = self.analyze_repository_code(data)

        self.git_keywords.update(entities["keywords"])

        # Repository overview chunk
        repo_overview = {
            "chunk_id": f"{reponame}_overview",
            "type": "repository_overview",
            "source": "git",
            "repo_name": reponame,
            "retrieval_priority": 0,
            "techstack": techstack,
            "summary": {
                "total_issues": len(data.get("issues", [])),
                "total_prs": len(data.get("prs", [])),
                "total_commits": len(data.get("commits", [])),
                "total_code_files": len(data.get("code_files", [])),
                "total_documentation": len(data.get("documentation", [])),
                "total_workflows": len(data.get("workflows", [])),
                "entities_summary": {
                    "unique_authors": len(entities["authors"]),
                    "unique_issues": len(entities["issue_numbers"]),
                    "unique_prs": len(entities["pr_numbers"]),
                    "unique_commits": len(entities["commit_shas"]),
                    "unique_files": len(entities["file_paths"]),
                },
            },
            "search_hints": {
                "text": f"{reponame} repository overview tech stack languages frameworks tools structure metrics",
                "keywords": [
                    "overview",
                    "summary",
                    "tech",
                    "stack",
                    "structure",
                    "metrics",
                    "statistics",
                ],
            },
            "raw_data": {"repo_name": reponame, "techstack": techstack},
        }
        chunks.append(repo_overview)
        self.chunk_registry[repo_overview["chunk_id"]] = repo_overview

        # CHUNK ISSUES - ONE CHUNK PER ISSUE
        issues = data.get("issues", [])
        print(f"   Processing {len(issues)} issues...")

        for idx, issue in enumerate(issues):
            if not isinstance(issue, dict):
                continue

            chunk_id = self.generate_chunk_id(issue, f"{reponame}_issue", idx)

            # Extract comments
            comments = []
            if "comments" in issue and isinstance(issue["comments"], list):
                comments = [
                    {
                        "author": (
                            c.get("user", {}).get("login")
                            if isinstance(c.get("user"), dict)
                            else None
                        ),
                        "body": c.get("body", ""),
                        "created_at": c.get("created_at", ""),
                        "updated_at": c.get("updated_at", ""),
                    }
                    for c in issue["comments"]
                    if isinstance(c, dict)
                ]

            # Bidirectional linking
            linked_prs = issue.get("linked_prs", [])
            is_truly_resolved = issue.get("is_truly_resolved", False)
            resolution_status = issue.get("resolution_status", "unknown")
            body_text = issue.get("body", "") or ""

            # Extract labels properly
            labels = []
            if "labels" in issue:
                if isinstance(issue["labels"], list):
                    labels = [
                        l.get("name") if isinstance(l, dict) else str(l)
                        for l in issue["labels"]
                        if l
                    ]

            # Extract assignees properly
            assignees = []
            if "assignees" in issue:
                if isinstance(issue["assignees"], list):
                    assignees = [
                        a.get("login") if isinstance(a, dict) else str(a)
                        for a in issue["assignees"]
                        if a
                    ]

            chunk = {
                "chunk_id": chunk_id,
                "type": "issue",
                "source": "git",
                "repo_name": reponame,
                "retrieval_priority": 1,
                "entities": {
                    "issue_number": issue.get("number"),
                    "author": (
                        issue.get("user", {}).get("login")
                        if isinstance(issue.get("user"), dict)
                        else None
                    ),
                    "labels": labels,
                    "assignees": assignees,
                    "milestone": (
                        issue.get("milestone", {}).get("title")
                        if isinstance(issue.get("milestone"), dict)
                        else None
                    ),
                    "linked_prs": linked_prs,
                    "is_truly_resolved": is_truly_resolved,
                    "resolution_status": resolution_status,
                },
                "temporal": {
                    "created_at": issue.get("created_at"),
                    "updated_at": issue.get("updated_at"),
                    "closed_at": issue.get("closed_at"),
                },
                "content": {
                    "title": issue.get("title", ""),
                    "body": body_text,
                    "state": issue.get("state", ""),
                    "comments_count": len(comments),
                    "labels": labels,
                },
                "comments": comments,
                "search_hints": {
                    "text": f"{issue.get('title', '')} {body_text}",
                    "keywords": list(entities["keywords"]),
                    "linked_prs": [f"#{pr}" for pr in linked_prs],
                },
                "raw_data": issue,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

            if issue.get("number"):
                self.entity_map[f"issue_{issue['number']}"].add(chunk_id)

            self.graph_extractor.process_issue(issue, linked_prs)

        # CHUNK PRS - ONE CHUNK PER PR
        prs = data.get("prs", [])
        print(f"   Processing {len(prs)} PRs...")

        for idx, pr in enumerate(prs):
            if not isinstance(pr, dict):
                continue

            chunk_id = self.generate_chunk_id(pr, f"{reponame}_pr", idx)

            # Extract reviews
            reviews = []
            if "review_comments" in pr and isinstance(pr["review_comments"], list):
                reviews = [
                    {
                        "author": (
                            r.get("user", {}).get("login")
                            if isinstance(r.get("user"), dict)
                            else None
                        ),
                        "body": r.get("body", ""),
                        "state": r.get("state", ""),
                        "submitted_at": r.get("submitted_at", ""),
                        "commit_id": r.get("commit_id", ""),
                    }
                    for r in pr["review_comments"]
                    if isinstance(r, dict)
                ]
            # Also check for 'reviews' key (some APIs use this)
            elif "reviews" in pr and isinstance(pr["reviews"], list):
                reviews = [
                    {
                        "author": (
                            r.get("user", {}).get("login")
                            if isinstance(r.get("user"), dict)
                            else None
                        ),
                        "body": r.get("body", ""),
                        "state": r.get("state", ""),
                        "submitted_at": r.get("submitted_at", ""),
                        "commit_id": r.get("commit_id", ""),
                    }
                    for r in pr["reviews"]
                    if isinstance(r, dict)
                ]

            # Extract file changes with FULL details including patches
            file_changes = []

            # Check multiple possible keys for file changes
            files_data = pr.get("changed_files") or pr.get("files") or []

            if isinstance(files_data, list):
                for f in files_data:
                    if isinstance(f, dict):
                        file_change = {
                            "filename": f.get("filename", ""),
                            "status": f.get(
                                "status", ""
                            ),  # added, modified, removed, renamed
                            "additions": f.get("additions", 0),
                            "deletions": f.get("deletions", 0),
                            "changes": f.get("changes", 0),
                            "patch": f.get(
                                "patch", ""
                            ),  # The actual diff/patch content
                            "previous_filename": f.get(
                                "previous_filename", ""
                            ),  # For renamed files
                            "blob_url": f.get("blob_url", ""),
                            "raw_url": f.get("raw_url", ""),
                            "contents_url": f.get("contents_url", ""),
                        }

                        # Only add if we have a filename
                        if file_change["filename"]:
                            file_changes.append(file_change)

            # Bidirectional linking
            linked_issues = pr.get("linked_issues", [])

            # PROPERLY DETERMINE PR STATUS - merged vs closed
            is_merged = pr.get("merged", False) or pr.get("is_merged", False)
            state = pr.get("state", "unknown")

            # Determine the actual PR status
            if is_merged:
                pr_status = "merged"
            elif state == "closed" and not is_merged:
                pr_status = "closed"
            elif state == "open":
                pr_status = "open"
            else:
                pr_status = state or "unknown"

            body_text = pr.get("body", "") or ""

            # Extract reviewers list
            reviewers = []
            for r in reviews:
                if r.get("author"):
                    reviewers.append(r["author"])
            reviewers = list(set(reviewers))  # Remove duplicates

            # Get merge information
            merged_by = None
            if pr.get("merged_by"):
                if isinstance(pr["merged_by"], dict):
                    merged_by = pr["merged_by"].get("login")
                else:
                    merged_by = str(pr["merged_by"])

            chunk = {
                "chunk_id": chunk_id,
                "type": "pr",
                "source": "git",
                "repo_name": reponame,
                "retrieval_priority": 1,
                "entities": {
                    "pr_number": pr.get("number"),
                    "author": (
                        pr.get("user", {}).get("login")
                        if isinstance(pr.get("user"), dict)
                        else None
                    ),
                    "reviewers": reviewers,
                    "merged_by": merged_by,
                    "base_branch": (
                        pr.get("base", {}).get("ref")
                        if isinstance(pr.get("base"), dict)
                        else None
                    ),
                    "head_branch": (
                        pr.get("head", {}).get("ref")
                        if isinstance(pr.get("head"), dict)
                        else None
                    ),
                    "linked_issues": linked_issues,
                    "pr_status": pr_status,
                    "is_merged": is_merged,
                },
                "temporal": {
                    "created_at": pr.get("created_at"),
                    "updated_at": pr.get("updated_at"),
                    "merged_at": pr.get("merged_at"),
                    "closed_at": pr.get("closed_at"),
                },
                "content": {
                    "title": pr.get("title", ""),
                    "body": body_text,
                    "state": state,
                    "merged": is_merged,
                    "mergeable": pr.get("mergeable"),
                    "mergeable_state": pr.get("mergeable_state", ""),
                    "commits_count": (
                        pr.get("commits", 0)
                        if isinstance(pr.get("commits"), int)
                        else len(pr.get("commits", []))
                    ),
                    "changed_files_count": len(file_changes),
                    "additions": pr.get("additions", 0),
                    "deletions": pr.get("deletions", 0),
                    "review_comments_count": len(reviews),
                },
                "reviews": reviews,
                "file_changes": file_changes,
                "closes_issues": linked_issues,
                "search_hints": {
                    "text": f"{pr.get('title', '')} {body_text}",
                    "keywords": list(entities["keywords"]),
                    "files_modified": [f["filename"] for f in file_changes],
                },
                "raw_data": pr,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

            if pr.get("number"):
                self.entity_map[f"pr_{pr['number']}"].add(chunk_id)
            
            self.graph_extractor.process_pr(pr)

        # CHUNK COMMITS - ONE CHUNK PER COMMIT
        commits = data.get("commits", [])
        print(f"   Processing {len(commits)} commits...")

        for idx, commit in enumerate(commits):
            if not isinstance(commit, dict):
                continue

            chunk_id = self.generate_chunk_id(commit, f"{reponame}_commit", idx)

            commit_data = commit.get("commit", {}) or {}
            message = commit_data.get("message", "") or ""

            # Extract files with full details
            files_modified = []
            if "files" in commit and isinstance(commit["files"], list):
                for f in commit["files"]:
                    if isinstance(f, dict):
                        files_modified.append(
                            {
                                "filename": f.get("filename", ""),
                                "status": f.get("status", ""),
                                "additions": f.get("additions", 0),
                                "deletions": f.get("deletions", 0),
                                "changes": f.get("changes", 0),
                                "patch": f.get("patch", ""),
                            }
                        )

            # Extract author and committer info
            author_info = (
                commit_data.get("author", {})
                if isinstance(commit_data.get("author"), dict)
                else {}
            )
            committer_info = (
                commit_data.get("committer", {})
                if isinstance(commit_data.get("committer"), dict)
                else {}
            )

            chunk = {
                "chunk_id": chunk_id,
                "type": "commit",
                "source": "git",
                "repo_name": reponame,
                "retrieval_priority": 2,
                "entities": {
                    "sha": commit.get("sha"),
                    "sha_short": (commit.get("sha") or "")[:7],
                    "author": author_info.get("name"),
                    "author_email": author_info.get("email"),
                    "committer": committer_info.get("name"),
                    "committer_email": committer_info.get("email"),
                },
                "temporal": {
                    "date": author_info.get("date"),
                    "author_date": author_info.get("date"),
                    "committer_date": committer_info.get("date"),
                },
                "content": {
                    "message": message,
                    "files_modified": [
                        f["filename"] for f in files_modified if f.get("filename")
                    ],
                    "stats": {
                        "total_files": len(files_modified),
                        "additions": (
                            commit.get("stats", {}).get("additions", 0)
                            if isinstance(commit.get("stats"), dict)
                            else 0
                        ),
                        "deletions": (
                            commit.get("stats", {}).get("deletions", 0)
                            if isinstance(commit.get("stats"), dict)
                            else 0
                        ),
                    },
                },
                "files": files_modified,  # Full file details with patches
                "search_hints": {
                    "text": message,
                    "keywords": list(entities["keywords"]),
                },
                "raw_data": commit,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

            if commit.get("sha"):
                self.entity_map[f"commit_{commit['sha'][:7]}"].add(chunk_id)

        # CHUNK CODE FILES - ONE CHUNK PER FILE
        code_files = data.get("code_files", [])
        print(f"   Processing {len(code_files)} code files...")

        for idx, codefile in enumerate(code_files):
            if not isinstance(codefile, dict):
                continue

            chunk_id = self.generate_chunk_id(codefile, f"{reponame}_code", idx)

            path = codefile.get("path")
            language = codefile.get("language") or self.code_analyzer.detect_language(
                path
            )
            content = codefile.get("content", "") or ""
            size = codefile.get("size", 0)

            ast_analysis = codefile.get("analysis")
            if path:
                self.graph_extractor.process_analysis(path, ast_analysis, content)

            chunk = {
                "chunk_id": chunk_id,
                "type": "code",
                "source": "git",
                "repo_name": reponame,
                "retrieval_priority": 2,
                "entities": {
                    "path": path,
                    "language": language,
                    "directory": str(Path(path).parent) if path else "",
                    "filename": Path(path).name if path else "",
                },
                "content": {"content": content, "size": size, "analysis": ast_analysis},
                "search_hints": {
                    "text": content[:1000],
                    "keywords": list(entities["keywords"]),
                },
                "raw_data": codefile,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

            if path:
                self.entity_map[f"file_{path}"].add(chunk_id)

        # CHUNK DOCUMENTATION - ONE CHUNK PER DOC
        documentation = data.get("documentation", [])
        print(f"   Processing {len(documentation)} documentation files...")

        for idx, doc in enumerate(documentation):
            if not isinstance(doc, dict):
                continue

            chunk_id = self.generate_chunk_id(doc, f"{reponame}_doc", idx)

            content_text = doc.get("content", "") or ""

            chunk = {
                "chunk_id": chunk_id,
                "type": "documentation",
                "source": "git",
                "repo_name": reponame,
                "retrieval_priority": 1,
                "entities": {
                    "path": doc.get("path", ""),
                    "title": doc.get("title", ""),
                },
                "content": {
                    "content": content_text,
                    "headers": re.findall(r"^#+\s+(.+)$", content_text, re.MULTILINE),
                },
                "search_hints": {
                    "text": content_text,
                    "keywords": list(entities["keywords"]),
                },
                "raw_data": doc,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

        # CHUNK WORKFLOWS - ONE CHUNK PER WORKFLOW
        workflows = data.get("workflows", [])
        print(f"   Processing {len(workflows)} workflows...")

        for idx, workflow in enumerate(workflows):
            if not isinstance(workflow, dict):
                continue

            chunk_id = self.generate_chunk_id(workflow, f"{reponame}_workflow", idx)

            chunk = {
                "chunk_id": chunk_id,
                "type": "workflow",
                "source": "git",
                "repo_name": reponame,
                "retrieval_priority": 2,
                "entities": {
                    "name": workflow.get("name", ""),
                    "path": workflow.get("path", ""),
                },
                "content": workflow,
                "search_hints": {
                    "text": json.dumps(workflow),
                    "keywords": list(entities["keywords"]),
                },
                "raw_data": workflow,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

        # CHUNK ANALYZED FILES - ONE CHUNK PER ANALYZED FILE
        analyzed_files = data.get("analyzed_files", [])
        print(f"   Processing {len(analyzed_files)} analyzed files...")

        for idx, analyzed in enumerate(analyzed_files):
            if not isinstance(analyzed, dict):
                continue

            chunk_id = self.generate_chunk_id(analyzed, f"{reponame}_analyzed", idx)

            chunk = {
                "chunk_id": chunk_id,
                "type": "analyzed_file",
                "source": "git",
                "repo_name": reponame,
                "retrieval_priority": 2,
                "entities": {"path": analyzed.get("path", "")},
                "content": analyzed,
                "search_hints": {
                    "text": json.dumps(analyzed),
                    "keywords": list(entities["keywords"]),
                },
                "raw_data": analyzed,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

        # CHUNK ONBOARDING (single document)
        if "onboarding" in data and data["onboarding"]:
            chunk = {
                "chunk_id": f"{reponame}_onboarding_all",
                "type": "onboarding",
                "source": "git",
                "repo_name": reponame,
                "retrieval_priority": 1,
                "content": data["onboarding"],
                "search_hints": {
                    "text": json.dumps(data["onboarding"]),
                    "keywords": list(entities["keywords"]),
                },
                "raw_data": data["onboarding"],
            }
            chunks.append(chunk)
            self.chunk_registry[chunk["chunk_id"]] = chunk

        # CHUNK OFFBOARDING (single document)
        if "offboarding" in data and data["offboarding"]:
            chunk = {
                "chunk_id": f"{reponame}_offboarding_all",
                "type": "offboarding",
                "source": "git",
                "repo_name": reponame,
                "retrieval_priority": 1,
                "content": data["offboarding"],
                "search_hints": {
                    "text": json.dumps(data["offboarding"]),
                    "keywords": list(entities["keywords"]),
                },
                "raw_data": data["offboarding"],
            }
            chunks.append(chunk)
            self.chunk_registry[chunk["chunk_id"]] = chunk

        return chunks, entities, techstack

    def chunk_gmail_data(
        self, data: Dict[str, Any], repo_name: str, git_entities: Dict[str, Set[str]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk Gmail data with GitHub correlation analysis
        """
        chunks = []
        messages = data.get("messages", []) or []

        for idx, message in enumerate(messages):
            if not isinstance(message, dict):
                continue

            chunk_id = self.generate_chunk_id(message, f"{repo_name}_email", idx)

            # Extract email content
            subject = str(message.get("subject", "") or "").lower()
            snippet = str(message.get("snippet", "") or "").lower()
            payload_text = str(message.get("payload_text", "") or "").lower()
            payload_html = str(message.get("payload_html", "") or "").lower()

            full_text = f"{subject} {snippet} {payload_text} {payload_html}"

            # Correlation analysis with GitHub
            correlated = {
                "authors": [],
                "issue_numbers": [],
                "pr_numbers": [],
                "commit_shas": [],
                "file_paths": [],
                "branches": [],
                "labels": [],
                "emails": [],
                "keywords": [],
            }

            correlation_score = 0.0

            if git_entities:
                # Check author mentions (case-insensitive)
                for author in git_entities.get("authors", set()):
                    if author and author.lower() in full_text:
                        correlated["authors"].append(author)
                        correlation_score += 2

                # Check issue references
                for issue_num in git_entities.get("issue_numbers", set()):
                    if issue_num and issue_num.lower() in full_text:
                        correlated["issue_numbers"].append(issue_num)
                        correlation_score += 3

                # Check PR references
                for pr_num in git_entities.get("pr_numbers", set()):
                    if pr_num and pr_num.lower() in full_text:
                        correlated["pr_numbers"].append(pr_num)
                        correlation_score += 3

                # Check commit SHAs (short or full)
                for sha in git_entities.get("commit_shas", set()):
                    if sha and sha.lower() in full_text:
                        correlated["commit_shas"].append(sha)
                        correlation_score += 2

                # Check file paths (case-insensitive)
                for path in git_entities.get("file_paths", set()):
                    if path and path.lower() in full_text:
                        correlated["file_paths"].append(path)
                        correlation_score += 1

                # Check branch names
                for branch in git_entities.get("branches", set()):
                    if branch and branch.lower() in full_text:
                        correlated["branches"].append(branch)
                        correlation_score += 1

                # Check keywords (small contribution)
                for keyword in git_entities.get("keywords", set()):
                    if keyword and keyword.lower() in full_text:
                        correlated["keywords"].append(keyword)
                        correlation_score += 0.1

                # Check emails
                for email in git_entities.get("emails", set()):
                    if email and email.lower() in full_text:
                        correlated["emails"].append(email)
                        correlation_score += 2

            # Determine if GitHub-related (heuristic)
            is_git_related = correlation_score > 0 or any(
                marker in full_text
                for marker in [
                    "github",
                    "pull request",
                    "pr #",
                    "issue #",
                    "commit",
                    "merge",
                    "branch",
                    "repository",
                    "repo",
                ]
            )

            # Extract structured data
            from_email = message.get("from", "")
            to_emails = message.get("to", "")

            attachments = message.get("attachments", []) or []

            chunk = {
                "chunk_id": chunk_id,
                "type": "email",
                "source": "gmail",
                "repo_name": repo_name,
                "retrieval_priority": (
                    1 if correlation_score > 3 else (2 if is_git_related else 3)
                ),
                # Correlation data
                "is_git_related": is_git_related,
                "correlation_score": correlation_score,
                "correlated_entities": correlated,
                # Entity linking
                "entities": {
                    "message_id": message.get("id"),
                    "from": from_email,
                    "to": to_emails,
                    "subject": message.get("subject", ""),
                },
                "temporal": {
                    "date": message.get("date"),
                },
                # Content
                "content": {
                    "subject": message.get("subject", ""),
                    "snippet": message.get("snippet", ""),
                    "body_text": message.get("payload_text", ""),
                    "body_html": message.get("payload_html", ""),
                    "has_attachments": message.get("has_attachments", False),
                    "attachment_count": len(attachments),
                },
                # Search hints
                "search_hints": {
                    "text": full_text,
                    "keywords": list(set(correlated["keywords"])),
                },
                "raw_data": {
                    "id": message.get("id"),
                    "subject": message.get("subject"),
                    "from": from_email,
                    "to": to_emails,
                    "date": message.get("date"),
                    "snippet": message.get("snippet"),
                    "payload_text": message.get("payload_text"),
                    "payload_html": message.get("payload_html"),
                    "has_attachments": message.get("has_attachments", False),
                    "attachments": attachments,
                },
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

            # Chunk attachments separately
            if isinstance(attachments, list) and attachments:
                for att_idx, attachment in enumerate(attachments):
                    if not isinstance(attachment, dict):
                        continue

                    att_chunk_id = f"{chunk_id}_attachment_{att_idx}"

                    # Check if attachment name correlates with GitHub
                    att_filename = str(attachment.get("filename", "") or "").lower()
                    att_correlation_score = 0.0

                    if git_entities:
                        for path in git_entities.get("file_paths", set()):
                            if path and path.lower() in att_filename:
                                att_correlation_score += 2

                    att_chunk = {
                        "chunk_id": att_chunk_id,
                        "type": "email_attachment",
                        "source": "gmail",
                        "repo_name": repo_name,
                        "retrieval_priority": 3,
                        "parent_message_id": message.get("id"),
                        "parent_chunk_id": chunk_id,
                        "is_git_related": is_git_related or att_correlation_score > 0,
                        "correlation_score": att_correlation_score,
                        "entities": {
                            "filename": attachment.get("filename"),
                            "mime_type": attachment.get("mime_type"),
                            "size": attachment.get("size"),
                        },
                        "content": attachment,
                        "search_hints": {"text": att_filename, "keywords": []},
                        "raw_data": attachment,
                    }

                    chunks.append(att_chunk)
                    self.chunk_registry[att_chunk_id] = att_chunk

        return chunks


def process_multi_source_data(
    data: Dict[str, Any],
    repo_name: str,
    chunker: DataChunker,
    git_entities: Optional[Dict[str, Set[str]]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Set[str]], Optional[Dict[str, Any]]]:
    """
    Process data with intelligent chunking, correlation, and code analysis
    """
    all_chunks = []
    source = data.get("source", "unknown")
    entities = {}
    tech_stack = None

    if source == "git":
        print(f"   📂 Processing Git data...")

        processed_chunks, entities, tech_stack = chunker.chunk_git_data(data, repo_name)
        all_chunks.extend(processed_chunks)

        raw_reference = chunker.create_raw_data_reference(data, source, repo_name)
        all_chunks.append(raw_reference)

        print(f"      ✓ Processed: {len(processed_chunks)} chunks")
        print(
            f"      ✓ Extracted entities: {sum(len(v) for v in entities.values())} total"
        )
        print(f"      ✓ Raw reference: 1 chunk")

    elif source == "gmail":
        print(f"   📧 Processing Gmail data...")

        if git_entities:
            print(
                f"      ℹ️  Using {sum(len(v) for v in git_entities.values())} GitHub entities for correlation"
            )

        processed_chunks = chunker.chunk_gmail_data(data, repo_name, git_entities or {})
        all_chunks.extend(processed_chunks)

        raw_reference = chunker.create_raw_data_reference(data, source, repo_name)
        all_chunks.append(raw_reference)

        git_related = [c for c in processed_chunks if c.get("is_git_related", False)]
        high_correlation = [
            c for c in processed_chunks if c.get("correlation_score", 0) > 3
        ]

        print(f"      ✓ Processed: {len(processed_chunks)} chunks")
        print(f"      ✓ Git-related emails: {len(git_related)}")
        print(f"      ✓ High correlation (score>3): {len(high_correlation)}")
        print(f"      ✓ Raw reference: 1 chunk")

    else:
        # Auto-detect
        if "issues" in data or "prs" in data or "commits" in data:
            print(f"   📂 Processing Git data (auto-detected)...")
            chunks, entities, tech_stack = chunker.chunk_git_data(data, repo_name)
            all_chunks.extend(chunks)
            all_chunks.append(chunker.create_raw_data_reference(data, "git", repo_name))

        if "messages" in data:
            print(f"   📧 Processing Gmail data (auto-detected)...")
            chunks = chunker.chunk_gmail_data(data, repo_name, git_entities or {})
            all_chunks.extend(chunks)
            all_chunks.append(
                chunker.create_raw_data_reference(data, "gmail", repo_name)
            )

    return all_chunks, entities, tech_stack


def process_file(
    input_file: str,
    output_dir: str,
    chunker: "DataChunker",
    git_entities: Optional[Dict[str, Set[str]]] = None,
) -> Dict[str, Any]:
    """
    Load JSON, Chunk with dual indexing, Save SPLIT BY TYPE + GRAPH DATA
    """
    print("=" * 70)
    print("ENTERPRISE-GRADE MULTI-SOURCE PROCESSING WITH GRAPH EXTRACTION")
    print("=" * 70)

    print(f"Loading {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    repo_name = REPO_NAME
    repo_owner = REPO_OWNER
    source = data.get("source", "unknown")

    print(f"Source: {source}")
    print(f"File: {repo_name}")

    if source == "git":
        print(f"Issues: {len(data.get('issues', []))}")
        print(f"PRs: {len(data.get('prs', []))}")
        print(f"Commits: {len(data.get('commits', []))}")
        print(f"Code files: {len(data.get('code_files', []))}")
        print(f"Docs: {len(data.get('documentation', []))}")
    elif source == "gmail":
        total_messages = data.get("total_messages", len(data.get("messages", [])))
        messages_with_attachments = sum(
            1 for m in data.get("messages", []) if m.get("has_attachments")
        )
        print(f"Total messages: {total_messages}")
        print(f"Messages with attachments: {messages_with_attachments}")

    print("Processing...")
    chunks, entities, tech_stack = process_multi_source_data(
        data, repo_name, chunker, git_entities
    )

    processed_chunks = [c for c in chunks if not c.get("is_raw_data", False)]
    raw_chunks = [c for c in chunks if c.get("is_raw_data", False)]

    print(f"Total chunks: {len(chunks)}")
    print(f" - Processed chunks: {len(processed_chunks)}")
    print(f" - Raw data references: {len(raw_chunks)}")

    print("\nSaving chunks split by type...")

    # Create repo-specific directory
    repo_output_dir = Path(output_dir) / repo_owner / repo_name
    repo_output_dir.mkdir(parents=True, exist_ok=True)

    # Optional subfolders
    chunks_dir = repo_output_dir / "chunks"
    chunks_dir.mkdir(exist_ok=True)

    # GROUP CHUNKS BY TYPE
    from collections import defaultdict

    chunks_by_type = defaultdict(list)

    for chunk in chunks:
        chunk_type = chunk.get("type", "unknown")
        chunks_by_type[chunk_type].append(chunk)

    saved_files = []

    # SAVE EACH TYPE TO ITS OWN FILE
    for chunk_type, type_chunks in chunks_by_type.items():
        if not type_chunks:
            continue

        output_file = chunks_dir / f"{chunk_type}_chunks.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(type_chunks, f, indent=2, ensure_ascii=False)

        print(
            f"   Saved {len(type_chunks)} {chunk_type} chunks -> {Path(output_file).name}"
        )
        saved_files.append(output_file)

    # ALSO SAVE COMBINED FILE (optional, for backward compatibility)
    combined_file = chunks_dir / "combined_chunks.json"
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"   Saved {len(chunks)} combined chunks -> {Path(combined_file).name}")
    saved_files.append(combined_file)

    # --- NEW: SAVE GRAPH DATA ---
    graph_has_data = len(chunker.graph_extractor.nodes) > 0

    if source == "git" or graph_has_data:
        # Extract graph data from the chunker's state
        graph_data = chunker.graph_extractor.get_graph_data()
        graph_file = repo_output_dir / "graph_data.json"

        with open(graph_file, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

        print(
            f"   🕸️  Graph Data Saved: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges -> {graph_file.name}"
        )
        saved_files.append(graph_file)
    # ----------------------------

    # Save entities
    if entities and source == "git":
        entities_file = repo_output_dir / "entities.json"
        entities_serializable = {k: list(v) for k, v in entities.items()}
        with open(entities_file, "w", encoding="utf-8") as f:
            json.dump(entities_serializable, f, indent=2, ensure_ascii=False)
        print(f"   Entities saved: {entities_file}")

    # Save tech stack
    if tech_stack and source == "git":
        techstack_file = repo_output_dir / "techstack.json"
        with open(techstack_file, "w", encoding="utf-8") as f:
            json.dump(tech_stack, f, indent=2, ensure_ascii=False)
        print(f"   Tech stack analysis saved: {techstack_file}")

    # Save retrieval strategy
    strategy = {
        "repository": {
            "owner": REPO_OWNER,
            "name": REPO_NAME,
            "full_name": f"{REPO_OWNER}/{REPO_NAME}",
            "url": f"https://github.com/{REPO_OWNER}/{REPO_NAME}",
        },
        "source": source,
        "chatbot_flow": [
            "1. User query received",
            "2. Search repository overview for tech stack/metrics queries",
            "3. Search GitHub chunks (priority 0-2) using hybrid search (semantic + keyword)",
            "4. Extract entities from GitHub results (issues, PRs, authors, etc.)",
            "5. Search Gmail chunks using GitHub entities as correlation hints",
            "6. Merge and rank results based on relevance and correlation",
            "7. If insufficient results, fallback to raw data references (priority 4)",
            "8. Generate response using combined context with tech stack awareness",
        ],
        "retrieval_priorities": {
            "0": "Repository overview (tech stack, metrics, structure)",
            "1": "GitHub issues, PRs, docs, high-correlation emails",
            "2": "GitHub commits, code, Git-related emails",
            "3": "General emails, attachments",
            "4": "Raw data (fallback for edge cases)",
        },
        "chunk_counts": {
            "total": len(chunks),
            "processed": len(processed_chunks),
            "raw_references": len(raw_chunks),
            "by_type": {k: len(v) for k, v in chunks_by_type.items()},
        },
        "graph_stats": {
            "nodes_count": len(chunker.graph_extractor.nodes) if source == "git" else 0,
            "edges_count": len(chunker.graph_extractor.edges) if source == "git" else 0,
        },
        "correlation_strategy": "Entity-based linking (authors, issue/PR numbers, commits, file paths)",
        "edge_case_handling": "Raw data preserved for queries requiring full context or missing from processed chunks",
        "techstack_integration": "Overview chunk contains comprehensive tech stack, code metrics, and structure analysis",
    }

    if tech_stack:
        strategy["techstack_summary"] = {
            "primary_language": tech_stack["languages"]["primary"],
            "total_languages": tech_stack["languages"]["count"],
            "frameworks_detected": len(tech_stack["frameworks"]["detected"]),
            "tools_detected": len(tech_stack["tools"]["detected"]),
            "total_files": tech_stack["metrics"]["total_files"],
            "total_code_lines": tech_stack["metrics"]["total_code_lines"],
            "total_functions": tech_stack["functions_and_classes"]["total_functions"],
            "total_classes": tech_stack["functions_and_classes"]["total_classes"],
        }

    if source == "gmail":
        git_related = [c for c in processed_chunks if c.get("is_git_related", False)]
        high_correlation = [
            c for c in processed_chunks if c.get("correlation_score", 0) >= 3
        ]
        strategy["chunk_counts"]["git_related_emails"] = len(git_related)
        strategy["chunk_counts"]["high_correlation_emails"] = len(high_correlation)

    strategy_file = repo_output_dir / "retrieval_strategy.json"
    with open(strategy_file, "w", encoding="utf-8") as f:
        json.dump(strategy, f, indent=2, ensure_ascii=False)
    print(f"   Retrieval strategy: {strategy_file}")

    print("=" * 70)
    print("DONE")
    print("=" * 70)

    return {
        "output_files": saved_files,
        "chunk_count": len(chunks),
        "processed_count": len(processed_chunks),
        "raw_count": len(raw_chunks),
        "repo_name": repo_name,
        "source": source,
        "entities": entities,
        "techstack": tech_stack,
    }


def batch_process():
    """
    Batch process with Git-first → Gmail correlation strategy
    """
    git_dir = "../../data/DataCollectionFromGit"
    gmail_dir = "../../data/DataCollectionFromGmail"
    output_dir = "../../data/DataProcessing"

    # Initialize shared chunker
    chunker = DataChunker(REPO_NAME)

    git_files = []
    if os.path.exists(git_dir):
        git_files = list(Path(git_dir).glob("*/*/*.json"))
        print(f"📂 Found {len(git_files)} Git files")

    gmail_files = []
    if os.path.exists(gmail_dir):
        gmail_files = list(Path(gmail_dir).glob("*_data.json"))
        print(f"📧 Found {len(gmail_files)} Gmail files")

    if not git_files and not gmail_files:
        print(f"❌ No JSON files found")
        return

    print(f"\n📦 Total files to process: {len(git_files) + len(gmail_files)}")
    print(
        f"   Strategy: Git first → Code analysis → Extract entities → Gmail with correlation\n"
    )

    results = []
    all_git_entities = {}
    all_tech_stacks = {}

    # Phase 1: Process all Git files first
    print(f"\n{'=' * 70}")
    print("PHASE 1: Processing GitHub Data with Code Analysis")
    print(f"{'=' * 70}\n")

    for json_file in git_files:
        try:
            result = process_file(str(json_file), output_dir, chunker)
            results.append((json_file.name, "Success", result))

            # Collect entities
            if result.get("entities"):
                all_git_entities[result["repo_name"]] = result["entities"]

            # Collect tech stacks
            if result.get("tech_stack"):
                all_tech_stacks[result["repo_name"]] = result["tech_stack"]

        except Exception as e:
            print(f"❌ Failed {json_file.name}: {e}")
            import traceback

            traceback.print_exc()
            results.append((json_file.name, "Failed", str(e)))

    # Phase 2: Process Gmail files with Git correlation
    if gmail_files:
        print(f"\n{'=' * 70}")
        print("PHASE 2: Processing Gmail Data (with GitHub correlation)")
        print(f"{'=' * 70}\n")

        # Merge all Git entities for comprehensive correlation
        merged_entities = {
            "authors": set(),
            "issue_numbers": set(),
            "pr_numbers": set(),
            "commit_shas": set(),
            "file_paths": set(),
            "branches": set(),
            "labels": set(),
            "emails": set(),
            "keywords": set(),
        }

        for entities in all_git_entities.values():
            for key, values in entities.items():
                if key in merged_entities:
                    merged_entities[key].update(values)

        print(f"   📊 Merged GitHub entities:")
        for key, values in merged_entities.items():
            print(f"      • {key}: {len(values)}")
        print()

        for json_file in gmail_files:
            try:
                result = process_file(
                    str(json_file), output_dir, chunker, merged_entities
                )
                results.append((json_file.name, "Success", result))
            except Exception as e:
                print(f"❌ Failed {json_file.name}: {e}")
                import traceback

                traceback.print_exc()
                results.append((json_file.name, "Failed", str(e)))

    # Summary
    print(f"\n{'=' * 70}")
    print("BATCH PROCESSING SUMMARY")
    print(f"{'=' * 70}\n")

    successful = [r for r in results if r[1] == "Success"]
    failed = [r for r in results if r[1] == "Failed"]

    print(f"✅ Success: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")

    if successful:
        total_chunks = sum(r[2]["chunk_count"] for r in successful)
        total_processed = sum(r[2]["processed_count"] for r in successful)
        total_raw = sum(r[2]["raw_count"] for r in successful)

        print(f"\n📊 Statistics:")
        print(f"   Total chunks: {total_chunks}")
        print(f"   Processed chunks: {total_processed}")
        print(f"   Raw data references: {total_raw}")
        print(f"   Average chunks per file: {total_chunks // len(successful)}")

        # Entity statistics
        print(f"\n   GitHub entities extracted:")
        for key in [
            "authors",
            "issue_numbers",
            "pr_numbers",
            "commit_shas",
            "file_paths",
        ]:
            total = sum(
                len(r[2].get("entities", {}).get(key, []))
                for r in successful
                if r[2].get("entities")
            )
            if total > 0:
                print(f"      • {key}: {total}")

        # Tech stack summary
        if all_tech_stacks:
            print(f"\n   Tech Stack Summary:")
            all_languages = Counter()
            all_frameworks = Counter()
            all_tools = Counter()
            total_code_lines = 0
            total_functions = 0
            total_classes = 0

            for tech_stack in all_tech_stacks.values():
                for lang, count in tech_stack["languages"]["all"].items():
                    all_languages[lang] += count
                for fw in tech_stack["frameworks"]["detected"]:
                    all_frameworks[fw] += 1
                for tool in tech_stack["tools"]["detected"]:
                    all_tools[tool] += 1
                total_code_lines += tech_stack["metrics"]["total_code_lines"]
                total_functions += tech_stack["functions_and_classes"][
                    "total_functions"
                ]
                total_classes += tech_stack["functions_and_classes"]["total_classes"]

            print(f"      • Total code lines: {total_code_lines:,}")
            print(f"      • Total functions: {total_functions:,}")
            print(f"      • Total classes: {total_classes:,}")
            print(f"      • Languages detected: {len(all_languages)}")
            print(
                f"        Top 5: {', '.join([f'{l}({c})' for l, c in all_languages.most_common(5)])}"
            )
            print(f"      • Frameworks detected: {len(all_frameworks)}")
            print(f"        {', '.join(all_frameworks.keys())}")
            print(f"      • Tools detected: {len(all_tools)}")
            print(f"        {', '.join(all_tools.keys())}")

    if failed:
        print(f"\n❌ Failed files:")
        for name, _, error in failed:
            print(f"   • {name}: {error}")

    # Save aggregated tech stack summary
    if all_tech_stacks:
        aggregated_summary_file = os.path.join(
            output_dir, "aggregated_tech_stack_summary.json"
        )
        with open(aggregated_summary_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "repositories": all_tech_stacks,
                    "summary": {
                        "total_repositories": len(all_tech_stacks),
                        "languages": dict(all_languages),
                        "frameworks": dict(all_frameworks),
                        "tools": dict(all_tools),
                        "total_code_lines": total_code_lines,
                        "total_functions": total_functions,
                        "total_classes": total_classes,
                    },
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"\n💾 Aggregated tech stack summary saved: {aggregated_summary_file}")

    print(f"\n💡 Next Steps:")
    print(
        f"   1. Review generated retrieval strategies in {output_dir}/*_retrieval_strategy.json"
    )
    print(f"   2. Review tech stack analysis in {output_dir}/*_tech_stack.json")
    print(
        f"   3. Review aggregated summary in {output_dir}/aggregated_tech_stack_summary.json"
    )
    print(f"   4. Use chunks for vector embedding and indexing")
    print(f"   5. Implement chatbot with GitHub-first → Gmail correlation logic")
    print(f"   6. Set up hybrid search (semantic + keyword) for optimal retrieval")
    print(f"   7. Integrate tech stack awareness in chatbot responses")


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise-grade multi-source RAG data processing with code analysis"
    )
    parser.add_argument(
        "input_file", nargs="?", help="Path to JSON from data collection"
    )
    parser.add_argument("--output-dir", default="./processed", help="Output directory")
    parser.add_argument("--batch", action="store_true", help="Batch process all files")

    args = parser.parse_args()

    if args.batch or not args.input_file:
        batch_process()
    else:
        if not os.path.exists(args.input_file):
            print(f"❌ Error: File not found: {args.input_file}")
            sys.exit(1)

        try:
            chunker = DataChunker(REPO_NAME)
            process_file(args.input_file, args.output_dir, chunker)
            print("✅ Success!")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
