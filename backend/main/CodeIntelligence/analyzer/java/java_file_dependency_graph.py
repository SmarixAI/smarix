# java_file_dependency_graph.py

import os
import re


class JavaFileDependencyGraph:

    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.graph = {}
        self.reverse_graph = {}

    def build_graph(self, java_files):

        import_pattern = re.compile(r'import\s+([\w\.]+);')

        for file_path in java_files:
            relative_path = os.path.relpath(file_path, self.repo_root)
            self.graph[relative_path] = []

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            imports = import_pattern.findall(content)

            for imp in imports:
                target_file = imp.replace(".", "/") + ".java"
                self.graph[relative_path].append(target_file)

        return self.graph

    def build_reverse_graph(self):

        for file, deps in self.graph.items():
            for dep in deps:
                self.reverse_graph.setdefault(dep, []).append(file)

        return self.reverse_graph