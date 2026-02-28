# java_class_graph.py

import os
import re


class JavaClassGraph:

    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.class_inheritance = {}
        self.reverse_inheritance = {}

    def build(self, java_files):

        class_pattern = re.compile(
            r'class\s+(\w+)(?:\s+extends\s+(\w+))?',
            re.MULTILINE
        )

        for file_path in java_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            for match in class_pattern.finditer(content):
                class_name = match.group(1)
                parent = match.group(2)

                if parent:
                    self.class_inheritance.setdefault(class_name, []).append(parent)
                    self.reverse_inheritance.setdefault(parent, []).append(class_name)

        return {
            "class_inheritance": self.class_inheritance,
            "reverse_class_inheritance": self.reverse_inheritance,
        }