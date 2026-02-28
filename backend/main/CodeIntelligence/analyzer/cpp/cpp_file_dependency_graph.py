import os
import re


class CppFileDependencyGraph:

    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.graph = {}
        self.reverse_graph = {}

    # --------------------------------------------------
    # Extract local includes only
    # --------------------------------------------------
    def extract_includes(self, file_path):

        includes = []
        include_pattern = re.compile(r'#include\s+"([^"]+)"')

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    match = include_pattern.search(line)
                    if match:
                        includes.append(match.group(1))
        except Exception:
            pass

        return includes

    # --------------------------------------------------
    # Build Graph
    # --------------------------------------------------
    def build_graph(self, cpp_files):

        # Build lookup: filename -> relative path
        repo_files = {
            os.path.basename(f): os.path.relpath(f, self.repo_root)
            for f in cpp_files
        }

        for file_path in cpp_files:

            relative_path = os.path.relpath(file_path, self.repo_root)
            self.graph[relative_path] = []

            includes = self.extract_includes(file_path)

            for inc in includes:

                filename = os.path.basename(inc)

                if filename in repo_files:
                    target = repo_files[filename]

                    if target != relative_path:
                        if target not in self.graph[relative_path]:
                            self.graph[relative_path].append(target)

        # --------------------------------------------------
        # 🔥 NEW PART — LINK .cpp <-> .h PAIRS
        # --------------------------------------------------

        for file in list(self.graph.keys()):

            if file.endswith(".cpp"):

                header = file.replace(".cpp", ".h")

                if header in self.graph:
                    if header not in self.graph[file]:
                        self.graph[file].append(header)

            elif file.endswith(".h"):

                source = file.replace(".h", ".cpp")

                if source in self.graph:
                    if source not in self.graph[file]:
                        self.graph[file].append(source)

        return self.graph

    # --------------------------------------------------
    # Reverse Graph
    # --------------------------------------------------
    def build_reverse_graph(self):

        for file, deps in self.graph.items():
            for dep in deps:
                self.reverse_graph.setdefault(dep, []).append(file)

        return self.reverse_graph