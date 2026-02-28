import os
import re


CPP_KEYWORDS = {
    "if", "for", "while", "switch", "catch",
    "return", "sizeof", "delete", "new"
}


class CppSymbolGraph:

    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.symbols = {}

    def build(self, cpp_files):

        for file_path in cpp_files:
            relative_path = os.path.relpath(file_path, self.repo_root)

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            self._extract_classes(content, relative_path)
            self._extract_functions(content, relative_path)

        return self.symbols

    # --------------------------------------------------
    # Class Extraction
    # --------------------------------------------------
    def _extract_classes(self, content, relative_path):

        class_pattern = re.compile(
            r'^\s*class\s+([A-Za-z_]\w*)',
            re.MULTILINE
        )

        for match in class_pattern.finditer(content):
            class_name = match.group(1)

            self.symbols[f"{relative_path}::{class_name}"] = {
                "type": "class",
                "language": "cpp",
                "file": relative_path,
                "structure": {
                    "bases": [],
                    "attributes": [],
                    "methods": []
                },
                "behavior": {},
                "documentation": {}
            }

    # --------------------------------------------------
    # Function + Method Extraction
    # --------------------------------------------------
    def _extract_functions(self, content, relative_path):

        function_pattern = re.compile(
            r'([A-Za-z_][\w:\<\>\s*&~]*)\s+'   # return type
            r'([A-Za-z_]\w*(?:::\w+)?)\s*'     # function or Class::method
            r'\(([^)]*)\)\s*'                  # parameters
            r'\{',
            re.MULTILINE
        )

        for match in function_pattern.finditer(content):

            return_type = match.group(1).strip()
            full_name = match.group(2).strip()
            params_raw = match.group(3).strip()

            # Skip keywords
            simple_name = full_name.split("::")[-1]
            if simple_name in CPP_KEYWORDS:
                continue

            parameters = []
            if params_raw and params_raw != "void":
                for p in params_raw.split(","):
                    parameters.append(p.strip())

            # --------------------------------------------------
            # Detect class method
            # --------------------------------------------------
            if "::" in full_name:

                class_name, method_name = full_name.split("::", 1)

                class_symbol = f"{relative_path}::{class_name}"
                method_symbol = f"{relative_path}::{class_name}::{method_name}"

                self.symbols[method_symbol] = {
                    "type": "method",
                    "language": "cpp",
                    "file": relative_path,
                    "structure": {
                        "parameters": parameters,
                        "return_type": return_type
                    },
                    "behavior": {},
                    "documentation": {}
                }

                # Attach method to class if class exists
                if class_symbol in self.symbols:
                    self.symbols[class_symbol]["structure"]["methods"].append(method_symbol)

            else:
                # --------------------------------------------------
                # Free function
                # --------------------------------------------------
                symbol_id = f"{relative_path}::{full_name}"

                self.symbols[symbol_id] = {
                    "type": "function",
                    "language": "cpp",
                    "file": relative_path,
                    "structure": {
                        "parameters": parameters,
                        "return_type": return_type
                    },
                    "behavior": {},
                    "documentation": {}
                }