import os
import re


class DartSymbolGraph:

    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.symbols = {}

    # --------------------------------------------------
    # Public Build Method
    # --------------------------------------------------
    def build(self, dart_files):
        for file_path in dart_files:
            relative_path = os.path.relpath(file_path, self.repo_root)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            self._extract_classes(content, relative_path)
            self._extract_top_level_functions(content, relative_path)

        return self.symbols

    # --------------------------------------------------
    # Extract Classes
    # --------------------------------------------------
    def _extract_classes(self, content, relative_path):

        class_pattern = re.compile(
            r'(?:abstract\s+)?class\s+(\w+)'
            r'(?:\s+extends\s+(\w+))?'
            r'(?:\s+implements\s+([\w<>,\s]+))?'
            r'\s*\{',
            re.MULTILINE
        )

        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            parent = match.group(2)
            interfaces = match.group(3)

            class_symbol = f"{relative_path}::{class_name}"

            self.symbols[class_symbol] = {
                "type": "class",
                "language": "dart",
                "file": relative_path,
                "structure": {
                    "extends": parent,
                    "implements": (
                        [i.strip() for i in interfaces.split(",")]
                        if interfaces else []
                    ),
                    "methods": []
                },
                "behavior": {},
                "documentation": {},
            }

            # Extract methods for this class
            self._extract_methods(content, relative_path, class_name)

    # --------------------------------------------------
    # Extract Methods (Scoped)
    # --------------------------------------------------
    def _extract_methods(self, content, relative_path, class_name):

        method_pattern = re.compile(
            r'(static\s+)?'
            r'(Future<.*?>|[\w<>\[\]\?]+)?\s+'
            r'(\w+)\s*'
            r'\(([^)]*)\)\s*'
            r'(async\s*)?\{',
            re.MULTILINE
        )

        constructor_pattern = re.compile(
            rf'\b{class_name}\s*\(([^)]*)\)\s*\{{',
            re.MULTILINE
        )

        # -------- Normal Methods --------
        for match in method_pattern.finditer(content):

            is_static = bool(match.group(1))
            return_type = match.group(2)
            method_name = match.group(3)
            params_raw = match.group(4)
            is_async = bool(match.group(5))

            # Skip constructor detection here
            if method_name == class_name:
                continue

            parameters = self._parse_parameters(params_raw)

            method_symbol = f"{relative_path}::{class_name}::{method_name}"

            if method_symbol not in self.symbols:

                self.symbols[method_symbol] = {
                    "type": "method",
                    "language": "dart",
                    "file": relative_path,
                    "structure": {
                        "parameters": parameters,
                        "return_type": return_type
                    },
                    "behavior": {
                        "static": is_static,
                        "async": is_async
                    },
                    "documentation": {},
                }

                self.symbols[f"{relative_path}::{class_name}"]["structure"]["methods"].append(method_symbol)

        # -------- Constructors --------
        for match in constructor_pattern.finditer(content):

            params_raw = match.group(1)
            parameters = self._parse_parameters(params_raw)

            constructor_symbol = f"{relative_path}::{class_name}::{class_name}"

            if constructor_symbol not in self.symbols:

                self.symbols[constructor_symbol] = {
                    "type": "constructor",
                    "language": "dart",
                    "file": relative_path,
                    "structure": {
                        "parameters": parameters,
                        "return_type": None
                    },
                    "behavior": {},
                    "documentation": {},
                }

                self.symbols[f"{relative_path}::{class_name}"]["structure"]["methods"].append(constructor_symbol)

    # --------------------------------------------------
    # Extract Top-Level Functions
    # --------------------------------------------------
    def _extract_top_level_functions(self, content, relative_path):

        function_pattern = re.compile(
            r'(Future<.*?>|[\w<>\[\]\?]+)\s+'
            r'(\w+)\s*'
            r'\(([^)]*)\)\s*'
            r'(async\s*)?\{',
            re.MULTILINE
        )

        for match in function_pattern.finditer(content):

            return_type = match.group(1)
            func_name = match.group(2)
            params_raw = match.group(3)
            is_async = bool(match.group(4))

            parameters = self._parse_parameters(params_raw)

            symbol = f"{relative_path}::{func_name}"

            if symbol not in self.symbols:

                self.symbols[symbol] = {
                    "type": "function",
                    "language": "dart",
                    "file": relative_path,
                    "structure": {
                        "parameters": parameters,
                        "return_type": return_type
                    },
                    "behavior": {
                        "async": is_async
                    },
                    "documentation": {},
                }

    # --------------------------------------------------
    # Parameter Parser
    # --------------------------------------------------
    def _parse_parameters(self, params_raw):

        parameters = []

        if not params_raw or params_raw.strip() == "":
            return parameters

        for p in params_raw.split(","):
            parameters.append(p.strip())

        return parameters