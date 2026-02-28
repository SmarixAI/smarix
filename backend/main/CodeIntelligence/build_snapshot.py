import os
import json
import tempfile
from typing import List, Dict, Any

from scanner.project_structure import ProjectStructureScanner
from analyzer.impact_analyzer import ImpactAnalyzer
from repo_registry import RepoRegistry

# 🐍 Python analyzers
from analyzer.python.python_file_dependency_graph import PythonFileDependencyGraph
from analyzer.python.python_symbol_graph import PythonSymbolGraph
from analyzer.python.python_call_graph import PythonCallGraph

# 💻 C++ analyzers
from analyzer.cpp.cpp_file_dependency_graph import CppFileDependencyGraph
from analyzer.cpp.cpp_symbol_graph import CppSymbolGraph
from analyzer.cpp.cpp_call_graph import CppCallGraph
from analyzer.cpp.cpp_class_graph import CppClassGraph

# ☕ Java analyzers
from analyzer.java.java_file_dependency_graph import JavaFileDependencyGraph
from analyzer.java.java_symbol_graph import JavaSymbolGraph
from analyzer.java.java_call_graph import JavaCallGraph
from analyzer.java.java_class_graph import JavaClassGraph

# 🎯 Dart analyzers
from analyzer.dart.dart_file_dependency_graph import DartFileDependencyGraph
from analyzer.dart.dart_symbol_graph import DartSymbolGraph
from analyzer.dart.dart_call_graph import DartCallGraph
from analyzer.dart.dart_class_graph import DartClassGraph




# ==========================================================
# FILE TREE BUILDER (Embedded)
# ==========================================================

class FileTreeBuilder:

    def __init__(self, code_files: List[Dict[str, Any]]):
        self.code_files = code_files

    def build(self) -> List[Dict[str, Any]]:
        tree = {}

        for file in self.code_files:
            path = file.get("path")
            if not path:
                continue

            parts = path.split("/")
            current = tree

            for part in parts[:-1]:
                current = current.setdefault(part, {})

            current[parts[-1]] = file

        return self._convert(tree)

    def _convert(self, node):
        result = []

        for name in sorted(node.keys()):
            value = node[name]

            if isinstance(value, dict) and "content" not in value:
                result.append({
                    "name": name,
                    "type": "folder",
                    "children": self._convert(value)
                })
            else:
                result.append({
                    "name": name,
                    "type": "file",
                    "path": value.get("path"),
                    "extension": value.get("extension"),
                    "lines": value.get("lines"),
                    "size": value.get("size"),
                    "sha": value.get("sha")
                })

        return result


# ==========================================================
# RECONSTRUCT REPO
# ==========================================================

def reconstruct_repo(repo_data, base_dir):
    code_files = repo_data.get("code_files", [])

    for file in code_files:

        if file.get("is_binary"):
            continue

        file_path = os.path.join(base_dir, file["path"])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(file["content"])


def merge_dict_of_lists(base, new_data):
    for key, values in new_data.items():
        base.setdefault(key, [])
        for v in values:
            if v not in base[key]:
                base[key].append(v)


def merge_simple_dict(base, new_data):
    base.update(new_data)


# ==========================================================
# MAIN
# ==========================================================

def build_snapshot(extractor_id: str, repo_id: str):

    registry = RepoRegistry()

    input_json_path = registry.get_repo_json_path(
        extractor_id,
        repo_id
    )

    if not os.path.exists(input_json_path):
        raise FileNotFoundError("Repo JSON not found")

    print(f"📂 Loading repository: {input_json_path}")

    with open(input_json_path, "r", encoding="utf-8") as f:
        repo_data = json.load(f)

    metadata = repo_data.get("metadata", {})
    code_files = repo_data.get("code_files", [])

    # --------------------------------------------------
    # Reconstruct repo
    # --------------------------------------------------

    temp_dir = tempfile.mkdtemp(prefix="codeintel_repo_")
    print(f"📁 Reconstructing repository at: {temp_dir}")

    reconstruct_repo(repo_data, temp_dir)
    repo_path = temp_dir

    print("✅ Repository reconstructed successfully")

    # --------------------------------------------------
    # Scan structure
    # --------------------------------------------------

    print("\n🔍 Scanning project structure...")
    scanner = ProjectStructureScanner(repo_path)
    structure_data = scanner.scan()

    print(f"📊 Total Files: {structure_data['total_files']}")
    languages = structure_data.get("languages", {})


    # --------------------------------------------------
    # Initialize graphs
    # --------------------------------------------------

    symbol_data = {}
    file_dependency_graph = {}
    reverse_file_dependency_graph = {}
    call_graph_data = {"call_graph": {}, "reverse_call_graph": {}}
    inheritance = {}
    reverse_inheritance = {}

    # ==================================================
    # PYTHON ANALYZER
    # ==================================================

    python_files = languages.get("python", [])

    if python_files:
        print("🐍 Running Python analyzer...")

        file_builder = PythonFileDependencyGraph(repo_path)
        python_file_graph = file_builder.build_graph(python_files)
        python_reverse_file_graph = file_builder.build_reverse_graph()

        merge_dict_of_lists(file_dependency_graph, python_file_graph)
        merge_dict_of_lists(reverse_file_dependency_graph, python_reverse_file_graph)

        symbol_builder = PythonSymbolGraph(repo_path)
        python_symbols = symbol_builder.build(python_files)
        merge_simple_dict(symbol_data, python_symbols)

        call_builder = PythonCallGraph(repo_path, symbol_data)
        python_call_data = call_builder.build(python_files)

        merge_dict_of_lists(call_graph_data["call_graph"], python_call_data["call_graph"])
        merge_dict_of_lists(call_graph_data["reverse_call_graph"], python_call_data["reverse_call_graph"])

        # inheritance from symbol data
        for symbol_id, symbol_info in python_symbols.items():
            if symbol_info["type"] != "class":
                continue

            bases = symbol_info["structure"].get("bases", [])

            for base in bases:
                for candidate in symbol_data:
                    if candidate.endswith(f"::{base}"):
                        inheritance.setdefault(symbol_id, []).append(candidate)
                        reverse_inheritance.setdefault(candidate, []).append(symbol_id)

    # ==================================================
    # C++ ANALYZER
    # ==================================================

    cpp_files = languages.get("cpp", [])

    if cpp_files:
        print("💻 Running C++ analyzer...")

        file_builder = CppFileDependencyGraph(repo_path)
        cpp_file_graph = file_builder.build_graph(cpp_files)
        cpp_reverse_file_graph = file_builder.build_reverse_graph()

        merge_dict_of_lists(file_dependency_graph, cpp_file_graph)
        merge_dict_of_lists(reverse_file_dependency_graph, cpp_reverse_file_graph)

        symbol_builder = CppSymbolGraph(repo_path)
        cpp_symbols = symbol_builder.build(cpp_files)
        merge_simple_dict(symbol_data, cpp_symbols)

        call_builder = CppCallGraph(repo_path, symbol_data)
        cpp_call_data = call_builder.build(cpp_files)

        merge_dict_of_lists(call_graph_data["call_graph"], cpp_call_data["call_graph"])
        merge_dict_of_lists(call_graph_data["reverse_call_graph"], cpp_call_data["reverse_call_graph"])

        class_builder = CppClassGraph(repo_path)
        cpp_class_data = class_builder.build(cpp_files)

        merge_dict_of_lists(inheritance, cpp_class_data["class_inheritance"])
        merge_dict_of_lists(reverse_inheritance, cpp_class_data["reverse_class_inheritance"])

    # ==================================================
    # JAVA ANALYZER
    # ==================================================

    java_files = languages.get("java", [])

    if java_files:
        print("☕ Running Java analyzer...")

        file_builder = JavaFileDependencyGraph(repo_path)
        java_file_graph = file_builder.build_graph(java_files)
        java_reverse_file_graph = file_builder.build_reverse_graph()

        merge_dict_of_lists(file_dependency_graph, java_file_graph)
        merge_dict_of_lists(reverse_file_dependency_graph, java_reverse_file_graph)

        symbol_builder = JavaSymbolGraph(repo_path)
        java_symbols = symbol_builder.build(java_files)
        merge_simple_dict(symbol_data, java_symbols)

        call_builder = JavaCallGraph(repo_path, symbol_data)
        java_call_data = call_builder.build(java_files)

        merge_dict_of_lists(call_graph_data["call_graph"], java_call_data["call_graph"])
        merge_dict_of_lists(call_graph_data["reverse_call_graph"], java_call_data["reverse_call_graph"])

        class_builder = JavaClassGraph(repo_path)
        java_class_data = class_builder.build(java_files)

        merge_dict_of_lists(inheritance, java_class_data["class_inheritance"])
        merge_dict_of_lists(reverse_inheritance, java_class_data["reverse_class_inheritance"])

    # ==================================================
    # DART ANALYZER
    # ==================================================

    dart_files = languages.get("dart", [])

    if dart_files:
        print("🎯 Running Dart analyzer...")

        file_builder = DartFileDependencyGraph(repo_path)
        dart_file_graph = file_builder.build_graph(dart_files)
        dart_reverse_file_graph = file_builder.build_reverse_graph()

        merge_dict_of_lists(file_dependency_graph, dart_file_graph)
        merge_dict_of_lists(reverse_file_dependency_graph, dart_reverse_file_graph)

        symbol_builder = DartSymbolGraph(repo_path)
        dart_symbols = symbol_builder.build(dart_files)
        merge_simple_dict(symbol_data, dart_symbols)

        call_builder = DartCallGraph(repo_path, symbol_data)
        dart_call_data = call_builder.build(dart_files)

        merge_dict_of_lists(call_graph_data["call_graph"], dart_call_data["call_graph"])
        merge_dict_of_lists(call_graph_data["reverse_call_graph"], dart_call_data["reverse_call_graph"])

        class_builder = DartClassGraph(repo_path)
        dart_class_data = class_builder.build(dart_files)

        merge_dict_of_lists(inheritance, dart_class_data["class_inheritance"])
        merge_dict_of_lists(reverse_inheritance, dart_class_data["reverse_class_inheritance"])

    # --------------------------------------------------
    # Impact Analysis
    # --------------------------------------------------

    print("\n🔥 Running impact analysis...")

    impact_analyzer = ImpactAnalyzer(
        file_dependency_graph,
        reverse_file_dependency_graph,
        call_graph_data["call_graph"],
        call_graph_data["reverse_call_graph"],
        inheritance,
        reverse_inheritance,
    )

    file_risk_scores = {
        file: len(impact_analyzer.get_impacted_files(file))
        for file in file_dependency_graph
    }

    sorted_file_risk = dict(
        sorted(file_risk_scores.items(), key=lambda x: x[1], reverse=True)
    )

    symbol_risk_scores = {
        symbol: len(impact_analyzer.get_impacted_methods(symbol))
        for symbol in call_graph_data["call_graph"]
    }

    sorted_symbol_risk = dict(
        sorted(symbol_risk_scores.items(), key=lambda x: x[1], reverse=True)
    )

    # --------------------------------------------------
    # Build File Tree
    # --------------------------------------------------

    print("🌳 Building file tree...")
    tree_builder = FileTreeBuilder(code_files)
    file_tree = tree_builder.build()

    # --------------------------------------------------
    # Final Intelligence JSON
    # --------------------------------------------------

    intelligence_output = {
        "repo_info": metadata,
        "file_count": structure_data["total_files"],
        "file_tree": file_tree,
        "symbols": symbol_data,
        "relationships": {
            "file_dependencies": file_dependency_graph,
            "symbol_dependencies": call_graph_data["call_graph"],
            "inheritance": inheritance,
        },
        "reverse_relationships": {
            "file_dependencies": reverse_file_dependency_graph,
            "symbol_dependencies": call_graph_data["reverse_call_graph"],
            "inheritance": reverse_inheritance,
        },
        "risk": {
            "files": sorted_file_risk,
            "symbols": sorted_symbol_risk,
        },
    }

    registry = RepoRegistry()

    # --------------------------------------------------
    # Save to CodeIntelligence Folder (API Compatible)
    # --------------------------------------------------

    repo_output_dir = os.path.join(
        registry.BASE_INTEL_DIR,
        extractor_id,
        repo_id
    )

    repo_output_dir = os.path.abspath(repo_output_dir)
    os.makedirs(repo_output_dir, exist_ok=True)

    output_path = os.path.join(repo_output_dir, "intelligence.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(intelligence_output, f, indent=2)

    print("✅ Intelligence built successfully")
    print(f"📁 Saved at: {output_path}")

    return output_path


if __name__ == "__main__":
    import sys

    extractor = sys.argv[1]
    repo = sys.argv[2]

    build_snapshot(extractor, repo)