import os
import re


class CppClassGraph:

    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.class_inheritance = {}
        self.reverse_inheritance = {}

    def build(self, cpp_files):

        inheritance_pattern = re.compile(
            r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*public\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        )

        for file_path in cpp_files:

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            for match in inheritance_pattern.finditer(content):
                child = match.group(1)
                parent = match.group(2)

                self.class_inheritance.setdefault(child, []).append(parent)
                self.reverse_inheritance.setdefault(parent, []).append(child)

        return {
            "class_inheritance": self.class_inheritance,
            "reverse_class_inheritance": self.reverse_inheritance,
        }