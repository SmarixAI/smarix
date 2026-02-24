import ast
import os


class PythonSymbolGraph:

    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.symbols = {}

    # --------------------------------------------------
    # Public Build Method
    # --------------------------------------------------
    def build(self, python_files):
        for file_path in python_files:
            relative_path = os.path.relpath(file_path, self.repo_root)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())
            except Exception:
                continue

            for node in tree.body:

                # ----------------------------
                # Class Extraction
                # ----------------------------
                if isinstance(node, ast.ClassDef):
                    self._extract_class(node, relative_path)

                # ----------------------------
                # Function Extraction
                # ----------------------------
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._extract_function(node, relative_path)

        return self.symbols

    # --------------------------------------------------
    # Class Extraction
    # --------------------------------------------------
    def _extract_class(self, node, relative_path):

        class_symbol = f"{relative_path}::{node.name}"

        bases = [self._get_name(base) for base in node.bases]

        attributes = []
        methods = []

        constructor_signature = None

        for child in node.body:

            # Class attributes
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

            # Methods
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_symbol = f"{relative_path}::{node.name}::{child.name}"
                methods.append(method_symbol)

                if child.name == "__init__":
                    constructor_signature = self._extract_signature(child)

                self._extract_method(child, relative_path, node.name)

        self.symbols[class_symbol] = {
            "type": "class",
            "language": "python",
            "file": relative_path,
            "structure": {
                "bases": bases,
                "attributes": attributes,
                "methods": methods,
                "constructor": constructor_signature,
            },
            "behavior": {},
            "documentation": {
                "docstring": ast.get_docstring(node)
            },
        }

    # --------------------------------------------------
    # Function Extraction
    # --------------------------------------------------
    def _extract_function(self, node, relative_path):

        symbol = f"{relative_path}::{node.name}"

        self.symbols[symbol] = {
            "type": "function",
            "language": "python",
            "file": relative_path,
            "structure": self._extract_signature(node),
            "behavior": {
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "decorators": [self._get_name(d) for d in node.decorator_list],
            },
            "documentation": {
                "docstring": ast.get_docstring(node)
            },
        }

    # --------------------------------------------------
    # Method Extraction
    # --------------------------------------------------
    def _extract_method(self, node, relative_path, class_name):

        symbol = f"{relative_path}::{class_name}::{node.name}"

        self.symbols[symbol] = {
            "type": "method",
            "language": "python",
            "file": relative_path,
            "structure": self._extract_signature(node),
            "behavior": {
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "decorators": [self._get_name(d) for d in node.decorator_list],
            },
            "documentation": {
                "docstring": ast.get_docstring(node)
            },
        }

    # --------------------------------------------------
    # Extract Function Signature
    # --------------------------------------------------
    def _extract_signature(self, node):

        parameters = []

        for arg in node.args.args:
            parameters.append({
                "name": arg.arg,
                "type": self._get_name(arg.annotation) if arg.annotation else None
            })

        return {
            "parameters": parameters,
            "return_type": self._get_name(node.returns) if node.returns else None,
        }

    # --------------------------------------------------
    # Helper: Extract Name
    # --------------------------------------------------
    def _get_name(self, node):
        if node is None:
            return None

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            return node.attr

        if isinstance(node, ast.Subscript):
            return self._get_name(node.value)

        return None