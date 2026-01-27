from typing import Dict, Any, List
from pathlib import Path


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
        "typescript": {
            "function": r"(?:export\s+)?(?:async\s+)?function\s+(\w+)|const\s+(\w+)\s*=\s*\(",
            "class": r"(?:export\s+)?class\s+(\w+)",
            "import": r"import\s+(?:\{[^}]*\}\s+from\s+)?['\"]([^'\"]+)['\"]",
        },
        "javascript": {
            "function": r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*\(|(\w+)\s*:\s*function\s*\()",
            "class": r"class\s+(\w+)",
            "import": r"(?:import\s+.*from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))",
        },
        "swift": {
            "function": r"func\s+(\w+)\s*\(",
            "class": r"(?:class|struct|enum|protocol)\s+(\w+)",
            "import": r"import\s+([\w\.]+)",
        },
        "python": {
            "function": r"def\s+(\w+)\s*\(",
            "class": r"class\s+(\w+)",
            "import": r"(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))",
        },
        "kotlin": {
            "function": r"fun\s+(\w+)\s*\(",
            "class": r"(?:class|interface|object|sealed\s+class)\s+(\w+)",
            "import": r"import\s+([\w\.]+)",
        },
        "scala": {
            "function": r"def\s+(\w+)\s*\(",
            "class": r"(?:class|trait|object)\s+(\w+)",
            "import": r"import\s+([\w\.]+)",
        },
        "objective-c": {
            "function": r"-\s*\(.*?\)\s*(\w+)",
            "class": r"@interface\s+(\w+)",
            "import": r"#import\s+[<\"]([^>\"]+)[>\"]",
        },
        "perl": {
            "function": r"sub\s+(\w+)",
            "class": r"package\s+(\w+)",
            "import": r"use\s+([\w:]+);",
        },
        "r": {
            "function": r"(\w+)\s*<-\s*function\s*\(",
            "class": None,
            "import": r"library\((\w+)\)",
        },
        "powershell": {
            "function": r"function\s+(\w+)",
            "class": None,
            "import": r"Import-Module\s+([\w\-\.]+)",
        },
        "groovy": {
            "function": r"def\s+(\w+)\s*\(",
            "class": r"class\s+(\w+)",
            "import": r"import\s+([\w\.]+)",
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
