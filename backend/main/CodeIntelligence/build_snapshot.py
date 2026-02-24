import os

from git.git_service import GitService
from scanner.project_structure import ProjectStructureScanner
from storage.metadata_store import MetadataStore

from analyzer.python.python_file_dependency_graph import PythonFileDependencyGraph
from analyzer.python.python_symbol_graph import PythonSymbolGraph
from analyzer.python.python_call_graph import PythonCallGraph
from analyzer.impact_analyzer import ImpactAnalyzer


REPO_URL = "https://github.com/pallets/flask.git"
BRANCH = "main"


def main():

    # --------------------------------------------------
    # 1️⃣ Prepare Snapshot
    # --------------------------------------------------
    git_service = GitService(base_repo_dir="/tmp/codeintel_repos")
    snapshot = git_service.prepare_snapshot(REPO_URL, BRANCH)

    repo_path = snapshot["repo_path"]

    print("\n✅ Snapshot Ready")
    print(f"Local Path  : {repo_path}")
    print(f"Commit Hash : {snapshot['commit_hash']}")

    # --------------------------------------------------
    # 2️⃣ Scan Project Structure
    # --------------------------------------------------
    print("\n🔍 Scanning project structure...")

    scanner = ProjectStructureScanner(repo_path)
    structure_data = scanner.scan()

    print("\n📊 Structure Summary:")
    print(f"Total Files: {structure_data['total_files']}")

    python_files = structure_data.get("languages", {}).get("python", [])

    # --------------------------------------------------
    # 3️⃣ File-Level Dependency Graph
    # --------------------------------------------------
    print("\n🔗 Building file dependency graph...")

    file_graph_builder = PythonFileDependencyGraph(repo_path)
    file_dependency_graph = file_graph_builder.build_graph(python_files)
    reverse_file_dependency_graph = file_graph_builder.build_reverse_graph()

    print(f"File Dependency Graph Nodes: {len(file_dependency_graph)}")

    # --------------------------------------------------
    # 4️⃣ Symbol Graph (Unified Model)
    # --------------------------------------------------
    print("\n🧠 Building symbol graph...")

    symbol_graph_builder = PythonSymbolGraph(repo_path)
    symbol_data = symbol_graph_builder.build(python_files)

    # --------------------------------------------------
    # 5️⃣ Call Graph (Symbol-Level Dependency)
    # --------------------------------------------------
    print("\n📞 Building call graph...")

    call_graph_builder = PythonCallGraph(repo_path, symbol_data)
    call_graph_data = call_graph_builder.build(python_files)

    # --------------------------------------------------
    # 6️⃣ Derive Inheritance From Symbols
    # --------------------------------------------------
    print("\n🏛 Building inheritance relationships...")

    inheritance = {}
    reverse_inheritance = {}

    for symbol_id, symbol_info in symbol_data.items():

        if symbol_info["type"] != "class":
            continue

        bases = symbol_info["structure"].get("bases", [])

        for base in bases:
            # Try resolving base to fully-qualified symbol
            for candidate in symbol_data:
                if candidate.endswith(f"::{base}"):

                    inheritance.setdefault(symbol_id, []).append(candidate)
                    reverse_inheritance.setdefault(candidate, []).append(symbol_id)

    # --------------------------------------------------
    # 7️⃣ Impact Analyzer
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

    # ----------------------------
    # File Risk Scores
    # ----------------------------
    file_risk_scores = {
        file: len(impact_analyzer.get_impacted_files(file))
        for file in file_dependency_graph
    }

    sorted_file_risk = dict(
        sorted(file_risk_scores.items(), key=lambda x: x[1], reverse=True)
    )

    # ----------------------------
    # Symbol Risk Scores
    # ----------------------------
    symbol_risk_scores = {
        symbol: len(impact_analyzer.get_impacted_methods(symbol))
        for symbol in call_graph_data["call_graph"]
    }

    sorted_symbol_risk = dict(
        sorted(symbol_risk_scores.items(), key=lambda x: x[1], reverse=True)
    )

    # --------------------------------------------------
    # 8️⃣ Prepare Metadata Payload (Language Neutral)
    # --------------------------------------------------
    metadata = {

        # Snapshot Info
        "snapshot": {
            "repo_path": repo_path,
            "branch": snapshot["branch"],
            "commit_hash": snapshot["commit_hash"],
        },

        # Structure Intelligence
        "structure": {
            "total_files": structure_data["total_files"],
            "file_count_by_extension": structure_data["file_count_by_extension"],
            "languages": structure_data.get("languages", {}),
            "templates": structure_data.get("templates", []),
            "static_assets": structure_data.get("static_assets", []),
            "config_files": structure_data.get("config_files", []),
            "test_files": structure_data.get("test_files", []),
        },

        # Unified Symbol Model
        "symbols": symbol_data,

        # Relationships (Language Neutral)
        "relationships": {
            "file_dependencies": file_dependency_graph,
            "symbol_dependencies": call_graph_data["call_graph"],
            "inheritance": inheritance,
        },

        # Reverse Relationships
        "reverse_relationships": {
            "file_dependencies": reverse_file_dependency_graph,
            "symbol_dependencies": call_graph_data["reverse_call_graph"],
            "inheritance": reverse_inheritance,
        },

        # Risk Intelligence
        "risk": {
            "files": sorted_file_risk,
            "symbols": sorted_symbol_risk,
        },
    }

    # --------------------------------------------------
    # 9️⃣ Store Metadata
    # --------------------------------------------------
    print("\n💾 Storing metadata...")

    store = MetadataStore(
        repo_url=REPO_URL,
        commit_hash=snapshot["commit_hash"],
    )

    store.save(metadata)

    print("\n📁 Metadata stored successfully.")
    print(f"Metadata file: {store.get_metadata_path()}")


if __name__ == "__main__":
    main()