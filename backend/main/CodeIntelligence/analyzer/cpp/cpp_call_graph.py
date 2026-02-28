import os
import re


CPP_KEYWORDS = {
    "if", "for", "while", "switch", "catch",
    "return", "sizeof", "delete", "new"
}


class CppCallGraph:

    def __init__(self, repo_root, symbols):
        self.repo_root = repo_root
        self.symbols = symbols
        self.call_graph = {}
        self.reverse_call_graph = {}

    def build(self, cpp_files):

        valid_symbols = set(self.symbols.keys())

        for file_path in cpp_files:
            relative_path = os.path.relpath(file_path, self.repo_root)

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            self._process_file(content, relative_path, valid_symbols)

        return {
            "call_graph": self.call_graph,
            "reverse_call_graph": self.reverse_call_graph,
        }

    # --------------------------------------------
    # Process File
    # --------------------------------------------
    def _process_file(self, content, relative_path, valid_symbols):

        function_pattern = re.compile(
            r'^[a-zA-Z_][\w:<>\s*&]*\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*\{',
            re.MULTILINE
        )

        call_pattern = re.compile(r'([A-Za-z_]\w*)\s*\(')

        for match in function_pattern.finditer(content):

            function_name = match.group(1)

            if function_name in CPP_KEYWORDS:
                continue

            caller = f"{relative_path}::{function_name}"

            if caller not in valid_symbols:
                continue

            self.call_graph.setdefault(caller, [])

            # Extract body (basic block detection)
            start = match.end()
            body = content[start:start + 2000]  # limited scan window

            for call_match in call_pattern.finditer(body):

                callee_name = call_match.group(1)

                if callee_name in CPP_KEYWORDS:
                    continue

                resolved = self._resolve_symbol(
                    callee_name,
                    relative_path,
                    valid_symbols
                )

                if resolved:
                    self.call_graph[caller].append(resolved)
                    self.reverse_call_graph.setdefault(resolved, []).append(caller)

            # Deduplicate
            self.call_graph[caller] = list(set(self.call_graph[caller]))

    # --------------------------------------------
    # Symbol Resolution
    # --------------------------------------------
    def _resolve_symbol(self, callee_name, relative_path, valid_symbols):

        candidate = f"{relative_path}::{callee_name}"
        if candidate in valid_symbols:
            return candidate

        for symbol in valid_symbols:
            if symbol.endswith(f"::{callee_name}"):
                return symbol

        return None