"""
Enhanced Intelligent Chunker with AST-Based Code Understanding
Splits content into optimal chunks with context preservation and smart boundaries
"""

import re
import ast
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ChunkType(Enum):
    """Types of chunks for different content"""

    CODE = "code"
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    DOCUMENTATION = "documentation"
    COMMIT = "commit"
    ISSUE = "issue"
    PR = "pull_request"
    CONFIG = "config"
    COMMENT = "comment"
    API_ENDPOINT = "api_endpoint"
    FILE_OVERVIEW = "file_overview"


@dataclass
class Chunk:
    """Represents a processed chunk with metadata"""

    content: str
    chunk_type: ChunkType
    metadata: Dict[str, Any]
    chunk_id: str
    parent_id: Optional[str] = None
    importance_score: float = 1.0
    tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "type": self.chunk_type.value,
            "metadata": self.metadata,
            "parent_id": self.parent_id,
            "importance_score": self.importance_score,
            "tokens": self.tokens,
        }


class IntelligentChunker:
    """
    Enhanced chunker with:
    - AST-based code chunking (preserves semantic boundaries)
    - Smart boundary detection (functions, classes, logical sections)
    - Context preservation (hierarchical overlapping chunks)
    - Language-aware splitting
    - Importance scoring
    - Execution context extraction
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        min_chunk_size: int = 100,
        max_chunk_size: int = 1024,
    ):
        """
        Args:
            chunk_size: Target chunk size in tokens
            overlap: Overlap between chunks for context
            min_chunk_size: Minimum chunk size
            max_chunk_size: Maximum chunk size
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

        self.code_boundaries = {
            "function": [
                r"^def\s+\w+",  # Python
                r"^async\s+def\s+\w+",  # Python async
                r"^function\s+\w+",  # JavaScript
                r"^async\s+function\s+\w+",  # JavaScript async
                r"^const\s+\w+\s*=\s*async\s*\(",  # Arrow functions
                r"^func\s+\w+",  # Go
                r"^\w+\s+\w+\s*\([^)]*\)\s*{",  # C/Java/etc
                r"^export\s+(?:default\s+)?(?:function|const)",  # ES6
            ],
            "class": [
                r"^class\s+\w+",  # Most languages
                r"^interface\s+\w+",  # TypeScript/Java
                r"^struct\s+\w+",  # C/Go
                r"^type\s+\w+\s+struct",  # Go
                r"^@dataclass",  # Python dataclass
            ],
            "import": [
                r"^import\s+",
                r"^from\s+\w+\s+import",
                r"^require\(",
                r"^#include\s+",
            ],
            "comment_block": [
                r"^\/\*\*",  # JavaDoc style
                r"^\/\*",  # Block comment
                r"^##+",  # Markdown headers
                r'^""".+"""$',  # Python docstring
                r"^'''.+'''$",  # Python docstring
            ],
        }

    def chunk_code_file(self, file_data: Dict[str, Any]) -> List[Chunk]:
        """Chunk a code file intelligently using AST when possible"""
        content = file_data.get("content", "")
        file_path = file_data.get("path", "unknown")
        language = self._detect_language(file_path)

        chunks = []

        # Use AST-based chunking for Python
        if language == "python":
            try:
                chunks = self._chunk_python_ast(content, file_path, file_data)
                if chunks:  # If AST parsing succeeded
                    return chunks
            except SyntaxError as e:
                print(
                    f"   ⚠️  AST parsing failed for {file_path}, falling back to regex: {e}"
                )

        # Fallback to regex-based chunking
        logical_chunks = self._split_by_boundaries(content, language)

        if logical_chunks:
            # Process each logical section
            for idx, section in enumerate(logical_chunks):
                if len(section.strip()) < self.min_chunk_size:
                    continue

                if self._estimate_tokens(section) > self.max_chunk_size:
                    sub_chunks = self._split_large_section(section, language)
                    for sub_idx, sub_chunk in enumerate(sub_chunks):
                        chunk = self._create_code_chunk(
                            sub_chunk, file_path, language, idx, sub_idx, file_data
                        )
                        chunks.append(chunk)
                else:
                    chunk = self._create_code_chunk(
                        section, file_path, language, idx, None, file_data
                    )
                    chunks.append(chunk)
        else:
            # Final fallback: size-based chunking
            chunks = self._chunk_by_size(
                content,
                file_path,
                ChunkType.CODE,
                {"language": language, "file_path": file_path},
            )

        return chunks

    def _chunk_python_ast(
        self, code: str, file_path: str, file_data: Dict
    ) -> List[Chunk]:
        """Chunk Python code using AST for semantic understanding"""
        chunks = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []  # Fall back to regex-based chunking

        # Extract imports
        imports = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.unparse(node))

        import_block = "\n".join(imports) if imports else ""

        # Extract module-level docstring
        module_docstring = ast.get_docstring(tree) or ""

        # Create file overview chunk (NEW: architectural context)
        overview_content = self._create_file_overview(
            file_path, tree, module_docstring, import_block, file_data
        )
        if overview_content:
            overview_chunk = Chunk(
                content=overview_content,
                chunk_type=ChunkType.FILE_OVERVIEW,
                metadata={
                    "file_path": file_path,
                    "chunk_role": "file_overview",
                    "language": "python",
                    "contains": self._get_file_structure_summary(tree),
                    "imports": imports,
                    "has_docstring": bool(module_docstring),
                },
                chunk_id=f"{file_path}_overview",
                importance_score=2.5,
                tokens=self._estimate_tokens(overview_content),
            )
            chunks.append(overview_chunk)

        # Process each top-level node
        for idx, node in enumerate(tree.body):
            if isinstance(node, ast.FunctionDef):
                chunk = self._create_function_chunk(
                    node, import_block, file_path, idx, file_data
                )
                chunks.append(chunk)

            elif isinstance(node, ast.ClassDef):
                class_chunks = self._create_class_chunks(
                    node, import_block, file_path, idx, file_data
                )
                chunks.extend(class_chunks)

            elif isinstance(node, ast.Assign):
                # Module-level constants/variables
                chunk = self._create_variable_chunk(node, file_path, idx)
                if chunk:
                    chunks.append(chunk)

        return chunks

    def _create_file_overview(
        self,
        file_path: str,
        tree: ast.AST,
        docstring: str,
        imports: str,
        file_data: Dict,
    ) -> str:
        """Create comprehensive file overview with architectural context"""
        overview = f"# File Overview: {file_path}\n\n"

        # Module documentation
        if docstring:
            overview += f"## Purpose\n{docstring}\n\n"

        # Dependencies
        if imports:
            overview += f"## Dependencies\n``````\n\n"

        # Architectural information (NEW)
        overview += "## Architecture\n"

        # Extract structure
        classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
        functions = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]

        if classes:
            overview += f"**Classes**: {', '.join(classes)}\n"
        if functions:
            overview += f"**Functions**: {', '.join(functions)}\n"

        # Detect patterns and roles
        file_role = self._infer_file_role(file_path, tree)
        if file_role:
            overview += f"**File Role**: {file_role}\n"

        # API endpoints detection
        endpoints = self._extract_api_endpoints(tree)
        if endpoints:
            overview += f"**API Endpoints**:\n"
            for endpoint in endpoints:
                overview += f"- {endpoint}\n"

        # Entry points
        entry_points = self._find_entry_points_in_tree(tree)
        if entry_points:
            overview += f"**Entry Points**: {', '.join(entry_points)}\n"

        return overview

    def _create_function_chunk(
        self,
        node: ast.FunctionDef,
        imports: str,
        file_path: str,
        idx: int,
        file_data: Dict,
    ) -> Chunk:
        """Create a complete, executable function chunk with rich context"""
        func_code = ast.unparse(node)
        docstring = ast.get_docstring(node) or ""

        # Build contextual content (NEW: both code AND explanation)
        content = f"# Function: `{node.name}`\n"
        content += (
            f"**File**: `{file_path}` (lines {node.lineno}-{node.end_lineno})\n\n"
        )

        # Architectural context (NEW)
        content += "## Purpose\n"
        purpose = self._infer_function_purpose(node, docstring)
        content += f"{purpose}\n\n"

        # Documentation
        if docstring:
            content += f"## Documentation\n``````\n\n"

        # Signature and parameters
        params = [arg.arg for arg in node.args.args]
        content += f"## Signature\n"
        content += f"``````\n"

        if params:
            content += f"\n**Parameters**: {', '.join(params)}\n"

        # Returns (NEW)
        returns = self._extract_return_info(node)
        if returns:
            content += f"**Returns**: {returns}\n"

        content += "\n"

        # Full implementation with imports
        content += "## Implementation\n"
        content += f"``````\n\n"

        # Execution context (NEW)
        content += "## Execution Context\n"
        calls = self._extract_function_calls(node)
        if calls:
            content += f"**Calls**: {', '.join(calls[:10])}\n"

        dependencies = self._extract_dependencies_from_node(node)
        if dependencies:
            content += f"**Dependencies**: {', '.join(dependencies)}\n"

        # Complexity indicator
        complexity = self._calculate_complexity(node)
        content += f"**Complexity**: {complexity} (cyclomatic)\n"

        return Chunk(
            content=content,
            chunk_type=ChunkType.FUNCTION,
            metadata={
                "file_path": file_path,
                "function_name": node.name,
                "language": "python",
                "has_docstring": bool(docstring),
                "params": params,
                "param_count": len(params),
                "decorators": [ast.unparse(d) for d in node.decorator_list],
                "calls_functions": calls,
                "dependencies": dependencies,
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "complexity": complexity,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "is_private": node.name.startswith("_"),
                "is_entry_point": node.name in ["main", "run", "execute", "__main__"],
                "purpose": purpose,
            },
            chunk_id=f"{file_path}_func_{node.name}_{idx}",
            parent_id=f"{file_path}_overview",
            importance_score=self._score_function_importance(node, docstring),
            tokens=self._estimate_tokens(content),
        )

    def _create_class_chunks(
        self,
        node: ast.ClassDef,
        imports: str,
        file_path: str,
        idx: int,
        file_data: Dict,
    ) -> List[Chunk]:
        """Create hierarchical chunks for a class (overview + methods)"""
        chunks = []
        class_docstring = ast.get_docstring(node) or ""

        # Class overview chunk (NEW: architectural view)
        overview = f"# Class: `{node.name}`\n"
        overview += (
            f"**File**: `{file_path}` (lines {node.lineno}-{node.end_lineno})\n\n"
        )

        # Purpose
        overview += "## Purpose\n"
        purpose = self._infer_class_purpose(node, class_docstring)
        overview += f"{purpose}\n\n"

        # Documentation
        if class_docstring:
            overview += f"## Documentation\n``````\n\n"

        # Inheritance
        bases = [ast.unparse(base) for base in node.bases]
        if bases:
            overview += f"## Inheritance\n"
            overview += f"**Inherits from**: {', '.join(bases)}\n\n"

        # Structure
        methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
        attributes = self._extract_class_attributes(node)

        overview += "## Structure\n"
        if methods:
            overview += f"**Methods** ({len(methods)}): {', '.join(methods[:10])}\n"
        if attributes:
            overview += f"**Attributes**: {', '.join(attributes[:10])}\n"

        # Class signature
        class_signature = f"class {node.name}"
        if bases:
            class_signature += f"({', '.join(bases)})"

        overview += f"\n## Signature\n``````\n"

        overview_chunk = Chunk(
            content=overview,
            chunk_type=ChunkType.CLASS,
            metadata={
                "file_path": file_path,
                "class_name": node.name,
                "language": "python",
                "bases": bases,
                "methods": methods,
                "method_count": len(methods),
                "attributes": attributes,
                "chunk_role": "class_overview",
                "has_docstring": bool(class_docstring),
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "purpose": purpose,
            },
            chunk_id=f"{file_path}_class_{node.name}_overview",
            parent_id=f"{file_path}_overview",
            importance_score=2.5,
            tokens=self._estimate_tokens(overview),
        )
        chunks.append(overview_chunk)

        # Individual method chunks
        for method_idx, method in enumerate(node.body):
            if isinstance(method, ast.FunctionDef):
                method_chunk = self._create_method_chunk(
                    method, node.name, imports, file_path, method_idx, file_data
                )
                chunks.append(method_chunk)

        return chunks

    def _create_method_chunk(
        self,
        node: ast.FunctionDef,
        class_name: str,
        imports: str,
        file_path: str,
        idx: int,
        file_data: Dict,
    ) -> Chunk:
        """Create chunk for a class method"""
        method_code = ast.unparse(node)
        docstring = ast.get_docstring(node) or ""

        content = f"# Method: `{class_name}.{node.name}`\n"
        content += f"**Class**: `{class_name}` | **File**: `{file_path}`\n\n"

        # Purpose
        purpose = self._infer_function_purpose(node, docstring, is_method=True)
        content += f"## Purpose\n{purpose}\n\n"

        if docstring:
            content += f"## Documentation\n``````\n\n"

        # Method type detection
        method_type = self._classify_method(node)
        content += f"**Type**: {method_type}\n\n"

        # Implementation
        content += f"## Implementation\n``````\n"

        return Chunk(
            content=content,
            chunk_type=ChunkType.METHOD,
            metadata={
                "file_path": file_path,
                "class_name": class_name,
                "method_name": node.name,
                "full_name": f"{class_name}.{node.name}",
                "language": "python",
                "method_type": method_type,
                "has_docstring": bool(docstring),
                "decorators": [ast.unparse(d) for d in node.decorator_list],
                "is_private": node.name.startswith("_"),
                "is_magic": node.name.startswith("__") and node.name.endswith("__"),
                "purpose": purpose,
            },
            chunk_id=f"{file_path}_method_{class_name}_{node.name}_{idx}",
            parent_id=f"{file_path}_class_{class_name}_overview",
            importance_score=self._score_function_importance(node, docstring),
            tokens=self._estimate_tokens(content),
        )

    def _create_variable_chunk(
        self, node: ast.Assign, file_path: str, idx: int
    ) -> Optional[Chunk]:
        """Create chunk for important module-level variables/constants"""
        # Only chunk important constants (uppercase names)
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if not targets or not any(t.isupper() for t in targets):
            return None

        var_code = ast.unparse(node)
        content = f"# Module Constants\n**File**: `{file_path}`\n\n"
        content += f"``````\n"

        return Chunk(
            content=content,
            chunk_type=ChunkType.CONFIG,
            metadata={
                "file_path": file_path,
                "variables": targets,
                "language": "python",
            },
            chunk_id=f"{file_path}_const_{idx}",
            parent_id=f"{file_path}_overview",
            importance_score=1.5,
            tokens=self._estimate_tokens(content),
        )

    def _create_code_chunk(
        self,
        section: str,
        file_path: str,
        language: str,
        idx: int,
        sub_idx: Optional[int],
        file_data: Dict,
    ) -> Chunk:
        """Create a generic code chunk (fallback for non-Python or unparseable code)"""
        chunk_id_suffix = f"{idx}_{sub_idx}" if sub_idx is not None else str(idx)

        return Chunk(
            content=section,
            chunk_type=ChunkType.CODE,
            metadata={
                "file_path": file_path,
                "language": language,
                "section_index": idx,
                "has_function": self._has_function_def(section),
                "has_class": self._has_class_def(section),
                "line_count": len(section.split("\n")),
            },
            chunk_id=f"code_{file_path}_{chunk_id_suffix}",
            parent_id=file_path,
            importance_score=self._calculate_code_importance(section),
            tokens=self._estimate_tokens(section),
        )

    # ========== HELPER METHODS (NEW) ==========

    def _get_file_structure_summary(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Extract high-level file structure"""
        return {
            "classes": [n.name for n in tree.body if isinstance(n, ast.ClassDef)],
            "functions": [n.name for n in tree.body if isinstance(n, ast.FunctionDef)],
            "imports": len(
                [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
            ),
        }

    def _infer_file_role(self, file_path: str, tree: ast.AST) -> str:
        """Infer the architectural role of a file"""
        path_lower = file_path.lower()

        # Check file path patterns
        if "test" in path_lower:
            return "Testing"
        elif "config" in path_lower or "settings" in path_lower:
            return "Configuration"
        elif "model" in path_lower:
            return "Data Model"
        elif "view" in path_lower or "template" in path_lower:
            return "View/Presentation"
        elif "controller" in path_lower or "handler" in path_lower:
            return "Controller/Handler"
        elif "util" in path_lower or "helper" in path_lower:
            return "Utility"
        elif "api" in path_lower or "endpoint" in path_lower:
            return "API Layer"

        # Check content patterns
        has_routes = any(
            self._is_route_decorator(n)
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)
        )
        if has_routes:
            return "API Routes"

        return "General"

    def _is_route_decorator(self, node: ast.FunctionDef) -> bool:
        """Check if function has route decorator"""
        route_patterns = ["route", "get", "post", "put", "delete", "patch"]
        for dec in node.decorator_list:
            dec_str = ast.unparse(dec).lower()
            if any(pattern in dec_str for pattern in route_patterns):
                return True
        return False

    def _extract_api_endpoints(self, tree: ast.AST) -> List[str]:
        """Extract API endpoints from decorators"""
        endpoints = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for dec in node.decorator_list:
                    dec_str = ast.unparse(dec)
                    # Match @app.route('/path'), @api.get('/path'), etc.
                    match = re.search(r'["\']([/\w{}:-]+)["\']', dec_str)
                    if match:
                        endpoints.append(match.group(1))

        return endpoints

    def _find_entry_points_in_tree(self, tree: ast.AST) -> List[str]:
        """Find entry point functions"""
        entry_points = []
        entry_names = ["main", "run", "execute", "start", "init"]

        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in entry_names:
                entry_points.append(node.name)

        # Check for if __name__ == '__main__'
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if isinstance(node.test, ast.Compare):
                    test_str = ast.unparse(node.test)
                    if "__name__" in test_str and "__main__" in test_str:
                        entry_points.append("__main__")
                        break

        return entry_points

    def _infer_function_purpose(
        self, node: ast.FunctionDef, docstring: str, is_method: bool = False
    ) -> str:
        """Infer the purpose of a function from its name and docstring"""
        if docstring:
            # Use first line of docstring
            first_line = docstring.split("\n")[0].strip()
            if first_line:
                return first_line

        # Infer from name
        name = node.name

        if name.startswith("get_"):
            return f"Retrieves {name[4:].replace('_', ' ')}"
        elif name.startswith("set_"):
            return f"Sets {name[4:].replace('_', ' ')}"
        elif name.startswith("create_"):
            return f"Creates {name[7:].replace('_', ' ')}"
        elif name.startswith("delete_"):
            return f"Deletes {name[7:].replace('_', ' ')}"
        elif name.startswith("update_"):
            return f"Updates {name[7:].replace('_', ' ')}"
        elif name.startswith("is_") or name.startswith("has_"):
            return f"Checks if {name[3:].replace('_', ' ')}"
        elif name == "__init__" and is_method:
            return "Initializes a new instance of the class"
        elif name == "__str__" and is_method:
            return "Returns string representation of the object"
        elif name == "__repr__" and is_method:
            return "Returns developer-friendly string representation"

        return f"Function: {name.replace('_', ' ')}"

    def _infer_class_purpose(self, node: ast.ClassDef, docstring: str) -> str:
        """Infer the purpose of a class"""
        if docstring:
            first_line = docstring.split("\n")[0].strip()
            if first_line:
                return first_line

        name = node.name

        # Common patterns
        if name.endswith("Error") or name.endswith("Exception"):
            return f"Custom exception for {name[:-5]}"
        elif name.endswith("Handler"):
            return f"Handles {name[:-7].replace('_', ' ')}"
        elif name.endswith("Manager"):
            return f"Manages {name[:-7].replace('_', ' ')}"
        elif name.endswith("Controller"):
            return f"Controls {name[:-10].replace('_', ' ')}"
        elif name.endswith("Service"):
            return f"Service for {name[:-7].replace('_', ' ')}"
        elif name.endswith("Model"):
            return f"Data model for {name[:-5].replace('_', ' ')}"

        return f"Class: {name}"

    def _extract_function_calls(self, node: ast.AST) -> List[str]:
        """Extract all function calls within a node"""
        calls = []
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Call):
                if isinstance(subnode.func, ast.Name):
                    calls.append(subnode.func.id)
                elif isinstance(subnode.func, ast.Attribute):
                    calls.append(subnode.func.attr)
        return list(set(calls))[:15]

    def _extract_dependencies_from_node(self, node: ast.AST) -> List[str]:
        """Extract imported modules used in this node"""
        deps = []
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Call):
                if isinstance(subnode.func, ast.Attribute):
                    # e.g., os.path.join -> os
                    if isinstance(subnode.func.value, ast.Name):
                        deps.append(subnode.func.value.id)
        return list(set(deps))[:10]

    def _extract_return_info(self, node: ast.FunctionDef) -> str:
        """Extract return type information"""
        # Check return annotation
        if node.returns:
            return ast.unparse(node.returns)

        # Check docstring
        docstring = ast.get_docstring(node) or ""
        returns_match = re.search(r"[Rr]eturns?:\s*(.+)", docstring)
        if returns_match:
            return returns_match.group(1).strip()

        # Check for return statements
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Return) and subnode.value:
                return "value"

        return ""

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        for subnode in ast.walk(node):
            if isinstance(subnode, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(subnode, ast.BoolOp):
                complexity += len(subnode.values) - 1
        return complexity

    def _extract_class_attributes(self, node: ast.ClassDef) -> List[str]:
        """Extract class attributes"""
        attributes = []

        # Look in __init__ method
        for method in node.body:
            if isinstance(method, ast.FunctionDef) and method.name == "__init__":
                for subnode in ast.walk(method):
                    if isinstance(subnode, ast.Assign):
                        for target in subnode.targets:
                            if isinstance(target, ast.Attribute):
                                if (
                                    isinstance(target.value, ast.Name)
                                    and target.value.id == "self"
                                ):
                                    attributes.append(target.attr)

        # Class-level attributes
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        return list(set(attributes))

    def _classify_method(self, node: ast.FunctionDef) -> str:
        """Classify method type"""
        name = node.name

        if name == "__init__":
            return "Constructor"
        elif name.startswith("__") and name.endswith("__"):
            return "Magic Method"
        elif name.startswith("_"):
            return "Private Method"
        elif any(ast.unparse(d) == "property" for d in node.decorator_list):
            return "Property"
        elif any(ast.unparse(d) == "staticmethod" for d in node.decorator_list):
            return "Static Method"
        elif any(ast.unparse(d) == "classmethod" for d in node.decorator_list):
            return "Class Method"
        else:
            return "Public Method"

    def _score_function_importance(
        self, node: ast.FunctionDef, docstring: str
    ) -> float:
        """Score function importance"""
        score = 1.0

        # Has docstring
        if docstring:
            score += 0.5

        # Public API (no leading underscore)
        if not node.name.startswith("_"):
            score += 0.5

        # Has decorators (likely API endpoints or important)
        if node.decorator_list:
            score += 0.5
            # Extra for route decorators
            if any(self._is_route_decorator(node) for _ in [None]):
                score += 0.5

        # High complexity
        if self._calculate_complexity(node) > 5:
            score += 0.3

        # Main entry point
        if node.name in ["main", "__init__", "run", "execute"]:
            score += 0.7

        return min(score, 3.0)

    # ========== EXISTING METHODS (Keep as fallback) ==========

    def chunk_documentation(self, doc_data: Dict[str, Any]) -> List[Chunk]:
        """Chunk documentation with section awareness"""
        content = doc_data.get("content", "")
        file_path = doc_data.get("path", "unknown")

        chunks = []

        # Split by markdown headers or logical sections
        sections = self._split_markdown(content)

        for idx, (header, section_content) in enumerate(sections):
            if len(section_content.strip()) < self.min_chunk_size:
                continue

            importance = self._calculate_doc_importance(header, section_content)

            chunk = Chunk(
                content=section_content,
                chunk_type=ChunkType.DOCUMENTATION,
                metadata={
                    "file_path": file_path,
                    "section_header": header,
                    "section_index": idx,
                    "is_setup": self._is_setup_section(header, section_content),
                    "is_api_doc": self._is_api_doc(section_content),
                    "has_code_examples": "```",
                },
                chunk_id=f"doc_{file_path}_{idx}",
                parent_id=file_path,
                importance_score=importance,
                tokens=self._estimate_tokens(section_content),
            )
            chunks.append(chunk)

        return chunks

    def chunk_issue(self, issue_data: Dict[str, Any]) -> List[Chunk]:
        """Chunk issue with EXACT metadata for retrieval"""
        issue_number = issue_data.get("number", "unknown")
        title = issue_data.get("title", "")
        body = issue_data.get("body", "")

        # CRITICAL: Format with explicit issue number for search
        full_content = f"""# Issue #{issue_number}: {title}

    **Issue Number**: #{issue_number}
    **State**: {issue_data.get('state', 'unknown')}
    **Created**: {issue_data.get('created_at', 'N/A')}
    **URL**: {issue_data.get('url', 'N/A')}

    {body}

    ---
    *This is Issue #{issue_number} in the repository*
    """

        # If short enough, keep as single chunk
        if self._estimate_tokens(full_content) <= self.chunk_size:
            chunk = Chunk(
                content=full_content,
                chunk_type=ChunkType.ISSUE,
                metadata={
                    "source": "issue",                   
                    "number": int(issue_number), 
                    "issue_number": int(issue_number),  # Store as int for sorting
                    "issue_id": f"#{issue_number}",  # Store with # for search
                    "title": title,
                    "state": issue_data.get("state", "unknown"),
                    "labels": issue_data.get("labels", []),
                    "is_solved": issue_data.get("is_solved", False),
                    "created_at": issue_data.get("created_at"),
                    "url": issue_data.get("url", ""),  # NEW: Add URL
                    "html_url": issue_data.get("html_url", ""),  # NEW: GitHub link
                    "referenced_issues": issue_data.get("referenced_issues", []),
                    "referenced_prs": issue_data.get("referenced_prs", []),
                    "author": issue_data.get("user", {}).get("login", "unknown"),
                    # NEW: Add searchable fields
                    "search_terms": [
                        f"issue {issue_number}",
                        f"#{issue_number}",
                        f"issue #{issue_number}",
                        title.lower(),
                    ],
                    "content_type": "issue",
                },
                chunk_id=f"issue_{issue_number}",
                importance_score=self._calculate_issue_importance(issue_data),
                tokens=self._estimate_tokens(full_content),
            )
            return [chunk]

        # Split long issue body
        return self._chunk_by_size(
            full_content,
            f"issue_{issue_number}",
            ChunkType.ISSUE,
            {
                "issue_number": int(issue_number),
                "issue_id": f"#{issue_number}",
                "title": title,
                "url": issue_data.get("url", ""),
                "html_url": issue_data.get("html_url", ""),
                "content_type": "issue",
            },
        )

    def chunk_pr(self, pr_data: Dict[str, Any]) -> List[Chunk]:
        """Chunk pull request with EXACT metadata"""
        pr_number = pr_data.get("number", "unknown")
        title = pr_data.get("title", "")
        body = pr_data.get("body_preview", pr_data.get("body", ""))

        full_content = f"""# Pull Request #{pr_number}: {title}

    **PR Number**: #{pr_number}
    **State**: {pr_data.get('state', 'unknown')}
    **Merged**: {pr_data.get('is_merged', False)}
    **Author**: {pr_data.get('user', {}).get('login', 'unknown')}
    **URL**: {pr_data.get('url', 'N/A')}

    {body}

    **Linked Issues**: {', '.join([f"#{i}" for i in pr_data.get('linked_issues', [])])}
    **Changed Files**: {len(pr_data.get('changed_files', []))} files

    ---
    *This is Pull Request #{pr_number} in the repository*
    """

        chunk = Chunk(
            content=full_content,
            chunk_type=ChunkType.PR,
            metadata={
                "source": "pr",                   
                "number": int(pr_number),  
                "pr_number": int(pr_number),  # Store as int
                "pr_id": f"#{pr_number}",  # Store with # for search
                "title": title,
                "state": pr_data.get("state", "unknown"),
                "is_merged": pr_data.get("is_merged", False),
                "author": pr_data.get("user", {}).get("login", "unknown"),
                "url": pr_data.get("url", ""),  # NEW
                "html_url": pr_data.get("html_url", ""),  # NEW: GitHub link
                "linked_issues": pr_data.get("linked_issues", []),
                "changed_files": pr_data.get("changed_files", []),
                # NEW: Searchable fields
                "search_terms": [
                    f"pr {pr_number}",
                    f"#{pr_number}",
                    f"pull request {pr_number}",
                    f"pr #{pr_number}",
                    title.lower(),
                ],
                "content_type": "pull_request",
            },
            chunk_id=f"pr_{pr_number}",
            importance_score=self._calculate_pr_importance(pr_data),
            tokens=self._estimate_tokens(full_content),
        )

        return [chunk]

    def chunk_commit(self, commit_data: Dict[str, Any]) -> Chunk:
        """Create chunk from commit with exact metadata"""
        sha = commit_data.get("sha", "unknown")[:7]
        full_sha = commit_data.get("sha", "unknown")
        message = commit_data.get("message", "")

        content = f"""Commit {sha}: {message}

    **Full SHA**: {full_sha}
    **Author**: {commit_data.get('author', {}).get('name', 'unknown')}
    **Date**: {commit_data.get('date', 'N/A')}
    **URL**: {commit_data.get('url', 'N/A')}

    **Changed Files**: {', '.join(commit_data.get('changed_files', [])[:10])}

    ---
    *Commit {sha} in the repository*
    """

        chunk = Chunk(
            content=content,
            chunk_type=ChunkType.COMMIT,
            metadata={
                "sha": full_sha,
                "short_sha": sha,
                "author": commit_data.get("author", {}).get("name", "unknown"),
                "date": commit_data.get("date"),
                "url": commit_data.get("url", ""),  # NEW
                "html_url": commit_data.get("html_url", ""),  # NEW
                "changed_files": commit_data.get("changed_files", []),
                "linked_issues": commit_data.get("linked_issues", []),
                "linked_prs": commit_data.get("linked_prs", []),
                "search_terms": [
                    f"commit {sha}",
                    f"commit {full_sha}",
                    message.lower()[:100],
                ],
                "content_type": "commit",
            },
            chunk_id=f"commit_{sha}",
            importance_score=self._calculate_commit_importance(commit_data),
            tokens=self._estimate_tokens(content),
        )

        return chunk

    def _split_by_boundaries(self, content: str, language: str) -> List[str]:
        """Split code by logical boundaries (functions, classes)"""
        lines = content.split("\n")
        chunks = []
        current_chunk = []

        for line in lines:
            is_boundary = False
            for boundary_type, patterns in self.code_boundaries.items():
                for pattern in patterns:
                    if re.match(pattern, line.strip()):
                        is_boundary = True
                        break
                if is_boundary:
                    break

            if is_boundary and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _split_large_section(self, content: str, language: str) -> List[str]:
        """Split a large section into smaller chunks with overlap"""
        lines = content.split("\n")
        chunks = []

        lines_per_chunk = self.chunk_size // 4
        overlap_lines = self.overlap // 4

        i = 0
        while i < len(lines):
            chunk_lines = lines[i : i + lines_per_chunk]
            chunks.append("\n".join(chunk_lines))
            i += lines_per_chunk - overlap_lines

        return chunks

    def _split_markdown(self, content: str) -> List[Tuple[str, str]]:
        """Split markdown by headers"""
        sections = []
        lines = content.split("\n")

        current_header = "Introduction"
        current_content = []

        for line in lines:
            if line.startswith("#"):
                if current_content:
                    sections.append((current_header, "\n".join(current_content)))
                current_header = line.strip("#").strip()
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections.append((current_header, "\n".join(current_content)))

        return sections

    def _chunk_by_size(
        self, content: str, parent_id: str, chunk_type: ChunkType, metadata: Dict
    ) -> List[Chunk]:
        """Fallback: chunk by size with overlap"""
        words = content.split()
        chunks = []

        words_per_chunk = self.chunk_size * 3 // 4
        overlap_words = self.overlap * 3 // 4

        i = 0
        chunk_idx = 0
        while i < len(words):
            chunk_words = words[i : i + words_per_chunk]
            chunk_content = " ".join(chunk_words)

            chunk = Chunk(
                content=chunk_content,
                chunk_type=chunk_type,
                metadata={**metadata, "chunk_index": chunk_idx},
                chunk_id=f"{chunk_type.value}_{parent_id}_{chunk_idx}",
                parent_id=parent_id,
                tokens=self._estimate_tokens(chunk_content),
            )
            chunks.append(chunk)

            i += words_per_chunk - overlap_words
            chunk_idx += 1

        return chunks

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".dart": "dart",
        }

        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        return "unknown"

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (words * 1.3)"""
        return int(len(text.split()) * 1.3)

    def _has_function_def(self, content: str) -> bool:
        """Check if content contains function definition"""
        patterns = self.code_boundaries["function"]
        return any(re.search(pattern, content, re.MULTILINE) for pattern in patterns)

    def _has_class_def(self, content: str) -> bool:
        """Check if content contains class definition"""
        patterns = self.code_boundaries["class"]
        return any(re.search(pattern, content, re.MULTILINE) for pattern in patterns)

    def _calculate_code_importance(self, content: str) -> float:
        """Calculate importance score for code chunk"""
        score = 1.0

        # Higher importance for entry points
        if any(word in content.lower() for word in ["main", "init", "setup"]):
            score += 0.5

        if self._has_class_def(content):
            score += 0.3
        if self._has_function_def(content):
            score += 0.2

        if any(
            word in content for word in ["@app.route", "@api", "app.get", "app.post"]
        ):
            score += 0.4

        return min(score, 3.0)

    def _calculate_doc_importance(self, header: str, content: str) -> float:
        """Calculate importance for documentation"""
        score = 1.0

        header_lower = header.lower()

        # Critical sections
        if any(
            word in header_lower
            for word in ["setup", "install", "getting started", "quick start"]
        ):
            score += 1.0

        if any(
            word in header_lower for word in ["api", "configuration", "environment"]
        ):
            score += 0.7

        if any(word in header_lower for word in ["architecture", "design", "overview"]):
            score += 0.5

        return min(score, 3.0)

    def _calculate_issue_importance(self, issue_data: Dict) -> float:
        """Calculate importance for issues"""
        score = 1.0

        if issue_data.get("is_solved"):
            score *= 0.7

        if issue_data.get("referenced_prs") or issue_data.get("referenced_issues"):
            score += 0.3

        labels = [l.lower() for l in issue_data.get("labels", [])]
        if any(word in " ".join(labels) for word in ["bug", "critical", "urgent"]):
            score += 0.5

        return min(score, 3.0)

    def _calculate_pr_importance(self, pr_data: Dict) -> float:
        """Calculate importance for PRs"""
        score = 1.0

        if pr_data.get("is_merged"):
            score += 0.5

        changed_files = len(pr_data.get("changed_files", []))
        if changed_files > 10:
            score += 0.3

        return min(score, 3.0)

    def _calculate_commit_importance(self, commit_data: Dict) -> float:
        """Calculate importance for commits"""
        score = 0.5

        message = commit_data.get("message", "").lower()

        if any(word in message for word in ["fix", "bug", "feature", "add"]):
            score += 0.3

        if commit_data.get("linked_issues") or commit_data.get("linked_prs"):
            score += 0.2

        return min(score, 2.0)

    def _is_setup_section(self, header: str, content: str) -> bool:
        """Check if section is about setup/installation"""
        keywords = [
            "setup",
            "install",
            "getting started",
            "quick start",
            "configuration",
        ]
        return any(
            kw in header.lower() or kw in content.lower()[:200] for kw in keywords
        )

    def _is_api_doc(self, content: str) -> bool:
        """Check if content is API documentation"""
        api_indicators = [
            "endpoint",
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "request",
            "response",
        ]
        return sum(1 for indicator in api_indicators if indicator in content[:500]) >= 2
