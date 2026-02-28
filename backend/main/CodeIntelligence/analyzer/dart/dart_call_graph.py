import os
import re


DART_KEYWORDS = {
    "if", "for", "while", "switch", "return",
    "await", "print", "super", "this",
    "new", "throw", "catch", "assert"
}


class DartCallGraph:

    def __init__(self, repo_root, symbols):
        self.repo_root = repo_root
        self.symbols = symbols
        self.call_graph = {}
        self.reverse_call_graph = {}

    # --------------------------------------------------
    # Build Call Graph
    # --------------------------------------------------
    def build(self, dart_files):

        valid_symbols = set(self.symbols.keys())

        method_pattern = re.compile(
            r'(?:static\s+)?'
            r'(?:Future<.*?>|[\w<>\[\]\?]+)\s+'
            r'(\w+)\s*'
            r'\(([^)]*)\)\s*'
            r'(?:async\s*)?\{',
            re.MULTILINE
        )

        call_pattern = re.compile(r'(\w+)\s*\(')

        for file_path in dart_files:
            relative_path = os.path.relpath(file_path, self.repo_root)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            for method_match in method_pattern.finditer(content):
                method_name = method_match.group(1)

                caller_symbol = self._resolve_caller(
                    relative_path,
                    method_name,
                    valid_symbols
                )

                if not caller_symbol:
                    continue

                self.call_graph.setdefault(caller_symbol, [])

                method_body = self._extract_method_body(
                    content,
                    method_match.end()
                )

                for call in call_pattern.findall(method_body):

                    # Skip Dart keywords
                    if call in DART_KEYWORDS:
                        continue

                    resolved = self._resolve_symbol(
                        call,
                        relative_path,
                        valid_symbols
                    )

                    # Only link project symbols
                    if resolved and resolved in valid_symbols:

                        if resolved not in self.call_graph[caller_symbol]:
                            self.call_graph[caller_symbol].append(resolved)

                        self.reverse_call_graph.setdefault(
                            resolved, []
                        )

                        if caller_symbol not in self.reverse_call_graph[resolved]:
                            self.reverse_call_graph[resolved].append(caller_symbol)

        return {
            "call_graph": self.call_graph,
            "reverse_call_graph": self.reverse_call_graph,
        }

    # --------------------------------------------------
    # Extract Proper Method Body Using Brace Matching
    # --------------------------------------------------
    def _extract_method_body(self, content, start_index):

        brace_count = 1
        i = start_index
        body = []

        while i < len(content) and brace_count > 0:
            char = content[i]

            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1

            body.append(char)
            i += 1

        return "".join(body)

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

        # Same file top-level
        candidate = f"{relative_path}::{callee_name}"
        if candidate in valid_symbols:
            return candidate

        # Same file class method
        for symbol in valid_symbols:
            if symbol.endswith(f"::{callee_name}") and symbol.startswith(relative_path):
                return symbol

        # Global fallback (optional, can remove if too noisy)
        for symbol in valid_symbols:
            if symbol.endswith(f"::{callee_name}"):
                return symbol

        return None