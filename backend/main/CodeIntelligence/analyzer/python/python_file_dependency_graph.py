import ast
import os


class PythonFileDependencyGraph:

    def __init__(self, repo_root):
        self.repo_root = repo_root
        self.graph = {}
        self.reverse_graph = {}
        self.module_map = {}
        self.package_root = self.detect_package_root()

    # --------------------------------------------------
    # Detect package root (supports src layout)
    # --------------------------------------------------
    def detect_package_root(self):
        src_path = os.path.join(self.repo_root, "src")
        if os.path.isdir(src_path):
            return src_path
        return self.repo_root

    # --------------------------------------------------
    # Build module map (module → file path)
    # --------------------------------------------------
    def build_module_map(self, python_files):
        for file_path in python_files:
            relative_to_pkg = os.path.relpath(file_path, self.package_root)

            # Skip files outside package root (like tests if src layout)
            if relative_to_pkg.startswith(".."):
                continue

            module_name = relative_to_pkg.replace(os.sep, ".").replace(".py", "")

            # Remove trailing __init__
            if module_name.endswith(".__init__"):
                module_name = module_name.replace(".__init__", "")

            self.module_map[module_name] = os.path.relpath(file_path, self.repo_root)

    # --------------------------------------------------
    # Extract imports (absolute + relative)
    # --------------------------------------------------
    def extract_imports(self, file_path):
        imports = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):

                # import flask.helpers
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)

                # from flask.helpers import X
                elif isinstance(node, ast.ImportFrom):
                    module = node.module

                    # Handle relative imports
                    if node.level > 0:
                        current_module = os.path.relpath(
                            file_path, self.package_root
                        ).replace(os.sep, ".").replace(".py", "")

                        parent_parts = current_module.split(".")[:-node.level]

                        if module:
                            resolved = ".".join(parent_parts + [module])
                        else:
                            resolved = ".".join(parent_parts)

                        imports.append(resolved)

                    # Absolute import
                    elif module:
                        imports.append(module)

        except Exception:
            pass

        return imports

    # --------------------------------------------------
    # Resolve module to actual file
    # Supports partial match (flask.helpers → flask.helpers.utils)
    # --------------------------------------------------
    def resolve_module(self, module_name):
        if module_name in self.module_map:
            return self.module_map[module_name]

        # Try prefix matching
        for mod in self.module_map:
            if module_name.startswith(mod):
                return self.module_map[mod]

        return None

    # --------------------------------------------------
    # Build dependency graph
    # --------------------------------------------------
    def build_graph(self, python_files):
        self.build_module_map(python_files)

        for file_path in python_files:
            relative_path = os.path.relpath(file_path, self.repo_root)
            self.graph[relative_path] = set()

            imports = self.extract_imports(file_path)

            for imp in imports:
                target_file = self.resolve_module(imp)

                # ✅ Add this check HERE
                if target_file and target_file != relative_path:
                    self.graph[relative_path].add(target_file)

        # Convert sets to lists for JSON serialization
        for k in self.graph:
            self.graph[k] = list(self.graph[k])

        return self.graph

    # --------------------------------------------------
    # Build reverse dependency graph
    # --------------------------------------------------
    def build_reverse_graph(self):
        for file, deps in self.graph.items():
            for dep in deps:
                self.reverse_graph.setdefault(dep, set()).add(file)

        # Convert sets to lists
        for k in self.reverse_graph:
            self.reverse_graph[k] = list(self.reverse_graph[k])

        return self.reverse_graph