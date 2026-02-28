# java_call_graph.py

import os
import re


class JavaCallGraph:

    def __init__(self, repo_root, symbols):
        self.repo_root = repo_root
        self.symbols = symbols
        self.call_graph = {}
        self.reverse_call_graph = {}

    # --------------------------------------------------
    # Build Call Graph
    # --------------------------------------------------
    def build(self, java_files):

        valid_symbols = set(self.symbols.keys())

        method_pattern = re.compile(
            r'(public|private|protected)?\s+[\w<>\[\]]+\s+(\w+)\s*\((.*?)\)\s*\{',
            re.MULTILINE
        )

        call_pattern = re.compile(r'(\w+)\s*\(')

        for file_path in java_files:
            relative_path = os.path.relpath(file_path, self.repo_root)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            for method_match in method_pattern.finditer(content):
                method_name = method_match.group(2)
                caller_symbol = self._resolve_caller(
                    relative_path, method_name, valid_symbols
                )

                if not caller_symbol:
                    continue

                self.call_graph.setdefault(caller_symbol, [])

                method_body_start = method_match.end()
                method_body = content[method_body_start:]

                for call in call_pattern.findall(method_body):
                    resolved = self._resolve_symbol(
                        call,
                        relative_path,
                        valid_symbols
                    )

                    if resolved:
                        self.call_graph[caller_symbol].append(resolved)
                        self.reverse_call_graph.setdefault(
                            resolved, []
                        ).append(caller_symbol)

        return {
            "call_graph": self.call_graph,
            "reverse_call_graph": self.reverse_call_graph,
        }

    # --------------------------------------------------
    # Resolve Caller
    # --------------------------------------------------
    def _resolve_caller(self, relative_path, method_name, valid_symbols):

        for symbol in valid_symbols:
            if symbol.endswith(f"::{method_name}") and symbol.startswith(relative_path):
                return symbol

        return None

    # --------------------------------------------------
    # Resolve Callee
    # --------------------------------------------------
    def _resolve_symbol(self, callee_name, relative_path, valid_symbols):

        # Same file
        candidate = f"{relative_path}::{callee_name}"
        if candidate in valid_symbols:
            return candidate

        # Method in same class
        for symbol in valid_symbols:
            if symbol.endswith(f"::{callee_name}") and symbol.startswith(relative_path):
                return symbol

        # Global fallback
        for symbol in valid_symbols:
            if symbol.endswith(f"::{callee_name}"):
                return symbol

        return None