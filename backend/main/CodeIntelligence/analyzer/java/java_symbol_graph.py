# java_symbol_graph.py

import os
import re


class JavaSymbolGraph:

    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.symbols = {}

    # --------------------------------------------------
    # Public Build Method
    # --------------------------------------------------
    def build(self, java_files):
        for file_path in java_files:
            relative_path = os.path.relpath(file_path, self.repo_root)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            self._extract_classes(content, relative_path)

        return self.symbols

    # --------------------------------------------------
    # Extract Classes
    # --------------------------------------------------
    def _extract_classes(self, content, relative_path):

        class_pattern = re.compile(
            r'class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?',
            re.MULTILINE
        )

        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            parent = match.group(2)
            interfaces = match.group(3)

            class_symbol = f"{relative_path}::{class_name}"

            methods = self._extract_methods(content, relative_path, class_name)

            self.symbols[class_symbol] = {
                "type": "class",
                "language": "java",
                "file": relative_path,
                "structure": {
                    "extends": parent,
                    "implements": interfaces.split(",") if interfaces else [],
                    "methods": methods,
                },
                "behavior": {},
                "documentation": {},
            }

    # --------------------------------------------------
    # Extract Methods
    # --------------------------------------------------
    def _extract_methods(self, content, relative_path, class_name):

        methods = []

        method_pattern = re.compile(
            r'(public|private|protected)?\s+[\w<>\[\]]+\s+(\w+)\s*\((.*?)\)',
            re.MULTILINE
        )

        for match in method_pattern.finditer(content):
            method_name = match.group(2)
            parameters = match.group(3)

            method_symbol = f"{relative_path}::{class_name}::{method_name}"

            methods.append(method_symbol)

            self.symbols[method_symbol] = {
                "type": "method",
                "language": "java",
                "file": relative_path,
                "structure": {
                    "parameters": parameters,
                },
                "behavior": {},
                "documentation": {},
            }

        return methods