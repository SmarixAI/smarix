##/Users/vishalkeshari/Desktop/smarix/backend/main/CodeIntelligence/analyzer/python/python_class_graph.py

import ast
import os


class PythonClassGraph:

    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.class_inheritance = {}
        self.reverse_inheritance = {}

    def build(self, python_files):
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    parents = []

                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            parents.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            parents.append(base.attr)

                    self.class_inheritance[class_name] = parents

                    for parent in parents:
                        self.reverse_inheritance.setdefault(parent, []).append(class_name)

        return {
            "class_inheritance": self.class_inheritance,
            "reverse_class_inheritance": self.reverse_inheritance,
        }