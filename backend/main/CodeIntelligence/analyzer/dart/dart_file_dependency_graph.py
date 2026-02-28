import os
import re


class DartFileDependencyGraph:

    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.graph = {}
        self.reverse_graph = {}

    def build_graph(self, dart_files):

        import_pattern = re.compile(r'import\s+[\'"](.+?)[\'"];')

        for file_path in dart_files:
            relative_path = os.path.relpath(file_path, self.repo_root)
            self.graph[relative_path] = []

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            imports = import_pattern.findall(content)

            for imp in imports:

                resolved = self._resolve_import(imp)

                if resolved and resolved != relative_path:
                    if resolved not in self.graph[relative_path]:
                        self.graph[relative_path].append(resolved)

        return self.graph

    def _resolve_import(self, import_path):

        # Skip SDK imports
        if import_path.startswith("dart:"):
            return None

        # Handle package imports
        if import_path.startswith("package:"):
            package_path = import_path.replace("package:", "")
            parts = package_path.split("/", 1)

            if len(parts) == 2:
                # Assume lib/ as root for package imports
                resolved = os.path.join("lib", parts[1])
                return resolved

        # Handle relative imports
        if import_path.endswith(".dart"):
            return import_path

        return None

    def build_reverse_graph(self):

        for file, deps in self.graph.items():
            for dep in deps:
                self.reverse_graph.setdefault(dep, []).append(file)

        return self.reverse_graph