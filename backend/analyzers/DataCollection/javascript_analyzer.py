"""JavaScript/TypeScript code analyzer."""

import re
from typing import Dict, Any, List
from analyzers.base_analyzer import BaseAnalyzer


class JavaScriptAnalyzer(BaseAnalyzer):
    """Analyzes JavaScript/TypeScript source code"""

    def __init__(self):
        super().__init__()
        # 1. Regex for DEFINITIONS (Nodes)
        self.function_patterns = [
            r"function\s+(\w+)\s*\(",  # function name()
            r"(?:const|let|var)\s+(\w+)\s*=\s*function",  # const name = function
            r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[^=]+)\s*=>",  # const name = () =>
            r"(?:async\s+)?(\w+)\s*\([^)]*\)\s*{",  # method() {
        ]

        # 2. Regex for CALLS (Edges) - Simple heuristic to find "func()" patterns
        self.call_pattern = r"(\w+)\s*\("

        # 3. Regex for IMPORTS (Dependencies)
        self.import_patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',  # standard import
            r'require\([\'"]([^\'"]+)[\'"]\)',  # require
            r'import\s+[\'"]([^\'"]+)[\'"]',  # side-effect import
        ]

        # 4. Regex for JSX Components (React Edges)
        # Finds <Button ... /> or <Button>
        self.jsx_pattern = r"<([A-Z][a-zA-Z0-9]*)"

        # 5. Class Pattern
        self.class_pattern = r"class\s+(\w+)(?:\s+extends\s+(\w+))?"

        # 6. Regex for EXPORTS
        self.export_patterns = [
            r"export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)",
            r"export\s*{\s*([^}]+)\s*}",
            r"module\.exports\s*=\s*(\w+)",
        ]

    def analyze(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract Nodes and Edges from JS/TS files"""

        # Initialize basic stats (optional, but good for compatibility)
        base_analysis = self.basic_analysis(content, file_path)

        analysis = {
            **base_analysis,
            "file_path": file_path,
            "language": (
                "typescript" if file_path.endswith(("ts", "tsx")) else "javascript"
            ),
            # -- Graph Nodes --
            "functions": [],  # {name, type, args, calls, jsx_calls}
            "classes": [],  # {name, methods}
            "imports": [],  # {module, alias}
            # -- Graph Edges --
            "dependencies": set(),
            "exports": [],
        }

        # A. Extract Imports (File -> Module Edges)
        self._extract_imports(content, analysis)

        # B. Extract Functions & Calls (Function -> Function Edges)
        self._extract_functions_and_calls(content, analysis)

        # C. Extract Classes (Class -> Method Edges)
        self._extract_classes(content, analysis)

        # Clean up sets for JSON serialization
        analysis["dependencies"] = list(analysis["dependencies"])

        return analysis

    def _extract_imports(self, content: str, analysis: Dict[str, Any]):
        """Populate imports and dependencies"""
        for pattern in self.import_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                module = match.group(1)
                analysis["imports"].append({"module": module})
                analysis["dependencies"].add(
                    module.split("/")[-1]
                )  # Simplify 'utils/auth' -> 'auth'

    def _extract_functions_and_calls(self, content: str, analysis: Dict[str, Any]):
        """Find functions and what they call (including JSX components)"""

        # We need to slice the content to find the "body" of the function.
        # Since we don't have a real AST parser, we use a heuristic:
        # We assume indentation or braces define the body roughly.

        for pattern in self.function_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                name = match.group(1)
                start_idx = match.end()

                # Heuristic: Extract next 50 lines or up to next function definition as "body"
                # This is imperfect but better than nothing for GraphRAG
                body_snippet = content[start_idx : start_idx + 2000]

                # Find outgoing edges (Calls)
                calls = set(re.findall(self.call_pattern, body_snippet))

                # Find UI edges (JSX Components)
                jsx_calls = set(re.findall(self.jsx_pattern, body_snippet))

                # Filter out standard language keywords from "calls"
                keywords = {
                    "if",
                    "for",
                    "while",
                    "switch",
                    "catch",
                    "function",
                    "return",
                    "await",
                }
                calls = list(calls - keywords)

                analysis["functions"].append(
                    {
                        "name": name,
                        "lineno": content[: match.start()].count("\n") + 1,
                        "calls": calls,  # Edge: Function -> Calls -> Function
                        "components_used": list(
                            jsx_calls
                        ),  # Edge: Component -> Renders -> Component
                    }
                )

    def _extract_classes(self, content: str, analysis: Dict[str, Any]):
        """Extract classes"""
        matches = re.finditer(self.class_pattern, content)

        for match in matches:
            name = match.group(1)
            base = match.group(2)
            analysis["classes"].append(
                {
                    "name": name,
                    "bases": [base] if base else [],
                    "lineno": content[: match.start()].count("\n") + 1,
                }
            )
