from collections import Counter
import os
from typing import Optional, List
import re
from typing import Dict, Any, Set




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
        "objective-c": [".mm"],
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
        self.reset()
    
    def reset(self):
        """Reset all metrics and state for a new repository analysis"""
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
