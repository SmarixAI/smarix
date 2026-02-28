##/Users/vishalkeshari/Desktop/smarix/backend/main/CodeIntelligence/analyzer/python/python_call_graph.py

import ast
import os


class PythonCallGraph:

    def __init__(self, repo_root, symbols):
        self.repo_root = repo_root
        self.symbols = symbols  # unified symbol table
        self.call_graph = {}
        self.reverse_call_graph = {}

    # --------------------------------------------------
    # Build Call Graph
    # --------------------------------------------------
    def build(self, python_files):

        valid_symbols = set(self.symbols.keys())

        for file_path in python_files:
            relative_path = os.path.relpath(file_path, self.repo_root)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())
            except Exception:
                continue

            for node in ast.walk(tree):

                # Handle both normal and async functions
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

                    caller = self._build_caller_symbol(node, relative_path)

                    if caller not in valid_symbols:
                        continue

                    self.call_graph.setdefault(caller, [])

                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):

                            callee_name = self._resolve_call(child)

                            if not callee_name:
                                continue

                            # Try resolving to fully qualified symbol
                            resolved = self._resolve_symbol(
                                callee_name,
                                relative_path,
                                valid_symbols
                            )

                            if resolved:
                                self.call_graph[caller].append(resolved)
                                self.reverse_call_graph.setdefault(
                                    resolved, []
                                ).append(caller)

        return {
            "call_graph": self.call_graph,
            "reverse_call_graph": self.reverse_call_graph,
        }

    # --------------------------------------------------
    # Build Caller Symbol ID
    # --------------------------------------------------
    def _build_caller_symbol(self, node, relative_path):

        parent_class = self._get_parent_class(node)

        if parent_class:
            return f"{relative_path}::{parent_class}::{node.name}"

        return f"{relative_path}::{node.name}"

    # --------------------------------------------------
    # Resolve Callee Name (simple)
    # --------------------------------------------------
    def _resolve_call(self, node):

        if isinstance(node.func, ast.Name):
            return node.func.id

        if isinstance(node.func, ast.Attribute):
            return node.func.attr

        return None

    # --------------------------------------------------
    # Try resolving to valid symbol
    # --------------------------------------------------
    def _resolve_symbol(self, callee_name, relative_path, valid_symbols):

        # 1️⃣ Try same-file function
        candidate = f"{relative_path}::{callee_name}"
        if candidate in valid_symbols:
            return candidate

        # 2️⃣ Try class method in same file
        for symbol in valid_symbols:
            if symbol.endswith(f"::{callee_name}") and symbol.startswith(relative_path):
                return symbol

        # 3️⃣ Global search (rare but safe fallback)
        for symbol in valid_symbols:
            if symbol.endswith(f"::{callee_name}"):
                return symbol

        return None

    # --------------------------------------------------
    # Get Parent Class (safe)
    # --------------------------------------------------
    def _get_parent_class(self, node):

        while hasattr(node, "parent"):
            node = node.parent
            if isinstance(node, ast.ClassDef):
                return node.name

        return None