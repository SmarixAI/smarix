from fastapi import APIRouter, HTTPException, Query
import json
import os

router = APIRouter()

BASE_METADATA_PATH = "/Users/vishalkeshari/Desktop/smarix/backend/data"


# ---------------------------------------------------------
# Helper: Load Metadata + Repo Path
# ---------------------------------------------------------
def load_metadata(repo_id: str, commit_hash: str):

    metadata_path = os.path.join(
        BASE_METADATA_PATH,
        repo_id,
        commit_hash,
        "metadata.json"
    )

    if not os.path.exists(metadata_path):
        raise HTTPException(status_code=404, detail="Metadata not found")

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    repo_path = metadata["snapshot"]["repo_path"]

    if not os.path.exists(repo_path):
        raise HTTPException(status_code=404, detail="Cloned repo not found")

    return metadata, repo_path


# ---------------------------------------------------------
# 1️⃣ Project Structure
# ---------------------------------------------------------
@router.get("/impact/project-structure/{repo_id}/{commit_hash}")
def get_project_structure(repo_id: str, commit_hash: str):

    metadata, repo_path = load_metadata(repo_id, commit_hash)

    def build_tree(path):
        tree = []

        for item in sorted(os.listdir(path)):

            if item.startswith("."):
                continue

            full_path = os.path.join(path, item)

            if os.path.isdir(full_path):
                tree.append({
                    "type": "folder",
                    "name": item,
                    "path": os.path.relpath(full_path, repo_path),
                    "children": build_tree(full_path)
                })
            else:
                tree.append({
                    "type": "file",
                    "name": item,
                    "path": os.path.relpath(full_path, repo_path)
                })

        return tree

    return {
        "tree": build_tree(repo_path)
    }


# ---------------------------------------------------------
# 2️⃣ File Content
# ---------------------------------------------------------
@router.get("/impact/file-content/{repo_id}/{commit_hash}")
def get_file_content(
    repo_id: str,
    commit_hash: str,
    path: str = Query(...)
):

    metadata, repo_path = load_metadata(repo_id, commit_hash)

    file_full_path = os.path.join(repo_path, path)

    if not os.path.exists(file_full_path):
        raise HTTPException(status_code=404, detail="File not found")

    if not os.path.isfile(file_full_path):
        raise HTTPException(status_code=400, detail="Not a file")

    with open(file_full_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    return {
        "file": path,
        "content": content
    }


# ---------------------------------------------------------
# 3️⃣ File Impact (Advanced Right Panel Data)
# ---------------------------------------------------------
@router.get("/impact/file-impact/{repo_id}/{commit_hash}")
def get_file_impact(
    repo_id: str,
    commit_hash: str,
    path: str = Query(...)
):

    metadata, _ = load_metadata(repo_id, commit_hash)

    file_dependencies = metadata["relationships"]["file_dependencies"]
    reverse_dependencies = metadata["reverse_relationships"]["file_dependencies"]
    file_risk = metadata["risk"]["files"]

    calls = file_dependencies.get(path, [])
    called_by = reverse_dependencies.get(path, [])

    blast_radius = file_risk.get(path, 0)

    total_files = len(file_dependencies)

    # -------------------------------
    # Instability Metric
    # I = outgoing / (incoming + outgoing)
    # -------------------------------
    outgoing = len(calls)
    incoming = len(called_by)

    if incoming + outgoing == 0:
        instability = 0
    else:
        instability = round(outgoing / (incoming + outgoing), 2)

    # -------------------------------
    # Role Classification
    # -------------------------------
    if incoming == 0 and outgoing > 0:
        role = "Leaf Module"
    elif incoming > 5 and blast_radius > 20:
        role = "Core Module"
    elif "tests" in path:
        role = "Test File"
    else:
        role = "Service/Utility"

    # -------------------------------
    # Production vs Test Impact Split
    # -------------------------------
    impacted_files = reverse_dependencies.get(path, [])

    prod_impact = 0
    test_impact = 0

    for f in impacted_files:
        if "tests" in f:
            test_impact += 1
        else:
            prod_impact += 1

    # -------------------------------
    # Severity Level
    # -------------------------------
    if blast_radius > 50:
        severity = "HIGH"
    elif blast_radius > 15:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return {
        "file": path,

        # Core Metrics
        "blast_radius": blast_radius,
        "direct_dependents": incoming,
        "depends_on": outgoing,

        # Dependency Lists
        "calls": calls,
        "called_by": called_by,

        # Advanced Metrics
        "instability": instability,
        "role": role,
        "severity": severity,

        # Impact Breakdown
        "production_impact": prod_impact,
        "test_impact": test_impact
    }


# ---------------------------------------------------------
# 5️⃣ File-Specific Symbol Intelligence (Enhanced + Transitive)
# ---------------------------------------------------------
@router.get("/impact/file-symbols/{repo_id}/{commit_hash}")
def get_file_symbols(
    repo_id: str,
    commit_hash: str,
    path: str = Query(...)
):

    metadata, _ = load_metadata(repo_id, commit_hash)

    symbols = metadata["symbols"]
    symbol_dependencies = metadata["relationships"]["symbol_dependencies"]
    reverse_symbol_dependencies = metadata["reverse_relationships"]["symbol_dependencies"]
    inheritance = metadata["relationships"]["inheritance"]
    reverse_inheritance = metadata["reverse_relationships"]["inheritance"]

    file_symbols = []

    for symbol_id, symbol_info in symbols.items():

        if symbol_info["file"] != path:
            continue

        structure = symbol_info.get("structure", {})
        behavior = symbol_info.get("behavior", {})
        documentation = symbol_info.get("documentation", {})

        calls = symbol_dependencies.get(symbol_id, [])
        called_by = reverse_symbol_dependencies.get(symbol_id, [])

        fan_out = len(calls)
        fan_in = len(called_by)

        # -------------------------------------------------
        # 🔥 Transitive Blast Radius Calculation
        # -------------------------------------------------
        visited = set()
        stack = list(called_by)

        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                stack.extend(
                    reverse_symbol_dependencies.get(current, [])
                )

        blast_radius = len(visited)

        # -------------------------------------------------
        # 🔥 Impact Depth Calculation
        # -------------------------------------------------
        depth = 0
        frontier = list(called_by)
        visited_depth = set()

        while frontier:
            next_frontier = []
            for node in frontier:
                if node not in visited_depth:
                    visited_depth.add(node)
                    next_frontier.extend(
                        reverse_symbol_dependencies.get(node, [])
                    )
            frontier = next_frontier
            depth += 1

        # -------------------------------------------------
        # Severity Classification
        # -------------------------------------------------
        if blast_radius > 75:
            severity = "CRITICAL"
        elif blast_radius > 30:
            severity = "HIGH"
        elif blast_radius > 10:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # -------------------------------------------------
        # Instability Metric
        # I = outgoing / (incoming + outgoing)
        # -------------------------------------------------
        instability = (
            0 if (fan_in + fan_out == 0)
            else round(fan_out / (fan_in + fan_out), 2)
        )

        # -------------------------------------------------
        # Architectural Role Detection
        # -------------------------------------------------
        if fan_in > 15 and blast_radius > 40:
            role = "Core Symbol"
        elif fan_out > 15 and fan_in < 3:
            role = "Unstable Symbol"
        elif fan_in == 0 and fan_out > 0:
            role = "Leaf Symbol"
        elif fan_in == 0 and fan_out == 0:
            role = "Isolated"
        else:
            role = "Utility"

        file_symbols.append({
            "symbol": symbol_id,
            "name": symbol_id.split("::")[-1],
            "type": symbol_info["type"],
            "language": symbol_info.get("language"),

            # Signature
            "parameters": structure.get("parameters", []),
            "return_type": structure.get("return_type"),

            # Behavior
            "is_async": behavior.get("is_async"),
            "decorators": behavior.get("decorators", []),

            # Documentation
            "docstring": documentation.get("docstring"),

            # Input / Output Model
            "input": {
                "fan_in": fan_in,
                "inherits_from": inheritance.get(symbol_id, [])
            },
            "output": {
                "fan_out": fan_out,
                "calls": calls,
                "inherited_by": reverse_inheritance.get(symbol_id, [])
            },

            # Advanced Metrics
            "fan_in": fan_in,
            "fan_out": fan_out,
            "blast_radius": blast_radius,
            "impact_depth": depth,
            "instability": instability,
            "severity": severity,
            "role": role
        })

    # Sort by highest blast radius first
    file_symbols.sort(key=lambda x: x["blast_radius"], reverse=True)

    return {
        "file": path,
        "total_symbols": len(file_symbols),
        "symbols": file_symbols
    }

# ---------------------------------------------------------
# 7️⃣ Universal Symbol Intelligence (For Project Click)
# ---------------------------------------------------------
@router.get("/impact/symbol-details/{repo_id}/{commit_hash}")
def get_symbol_details(
    repo_id: str,
    commit_hash: str,
    symbol_id: str = Query(...)
):

    metadata, _ = load_metadata(repo_id, commit_hash)

    symbols = metadata["symbols"]
    symbol_dependencies = metadata["relationships"]["symbol_dependencies"]
    reverse_symbol_dependencies = metadata["reverse_relationships"]["symbol_dependencies"]
    inheritance = metadata["relationships"]["inheritance"]
    reverse_inheritance = metadata["reverse_relationships"]["inheritance"]

    if symbol_id not in symbols:
        raise HTTPException(status_code=404, detail="Symbol not found")

    symbol_info = symbols[symbol_id]

    structure = symbol_info.get("structure", {})
    behavior = symbol_info.get("behavior", {})
    documentation = symbol_info.get("documentation", {})

    calls = symbol_dependencies.get(symbol_id, [])
    called_by = reverse_symbol_dependencies.get(symbol_id, [])

    fan_out = len(calls)
    fan_in = len(called_by)

    # -----------------------------
    # 🔥 Transitive Blast Radius
    # -----------------------------
    visited = set()
    stack = list(called_by)

    while stack:
        current = stack.pop()
        if current not in visited:
            visited.add(current)
            stack.extend(
                reverse_symbol_dependencies.get(current, [])
            )

    blast_radius = len(visited)

    # -----------------------------
    # 🔥 Impact Depth
    # -----------------------------
    depth = 0
    frontier = list(called_by)
    visited_depth = set()

    while frontier:
        next_frontier = []
        for node in frontier:
            if node not in visited_depth:
                visited_depth.add(node)
                next_frontier.extend(
                    reverse_symbol_dependencies.get(node, [])
                )
        frontier = next_frontier
        depth += 1

    # -----------------------------
    # Instability
    # -----------------------------
    instability = (
        0 if (fan_in + fan_out == 0)
        else round(fan_out / (fan_in + fan_out), 2)
    )

    # -----------------------------
    # Severity
    # -----------------------------
    if blast_radius > 75:
        severity = "CRITICAL"
    elif blast_radius > 30:
        severity = "HIGH"
    elif blast_radius > 10:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # -----------------------------
    # Architectural Role
    # -----------------------------
    if fan_in > 15 and blast_radius > 40:
        role = "Core Symbol"
    elif fan_out > 15 and fan_in < 3:
        role = "Unstable Symbol"
    elif fan_in == 0 and fan_out > 0:
        role = "Leaf Symbol"
    elif fan_in == 0 and fan_out == 0:
        role = "Isolated"
    else:
        role = "Utility"

    return {
        "symbol": symbol_id,
        "name": symbol_id.split("::")[-1],
        "file": symbol_info["file"],
        "type": symbol_info["type"],
        "language": symbol_info.get("language"),

        # Signature
        "parameters": structure.get("parameters", []),
        "return_type": structure.get("return_type"),

        # Behavior
        "is_async": behavior.get("is_async"),
        "decorators": behavior.get("decorators", []),

        # Documentation
        "docstring": documentation.get("docstring"),

        # Input / Output
        "input": {
            "fan_in": fan_in,
            "inherits_from": inheritance.get(symbol_id, [])
        },
        "output": {
            "fan_out": fan_out,
            "calls": calls,
            "inherited_by": reverse_inheritance.get(symbol_id, [])
        },

        # Advanced Metrics
        "fan_in": fan_in,
        "fan_out": fan_out,
        "blast_radius": blast_radius,
        "impact_depth": depth,
        "instability": instability,
        "severity": severity,
        "role": role
    }


# ---------------------------------------------------------
# 6️⃣ Project-Level Symbol Intelligence (Enhanced)
# ---------------------------------------------------------
@router.get("/impact/project-symbols/{repo_id}/{commit_hash}")
def get_project_symbols(repo_id: str, commit_hash: str):

    metadata, _ = load_metadata(repo_id, commit_hash)

    symbols = metadata["symbols"]
    symbol_dependencies = metadata["relationships"]["symbol_dependencies"]
    reverse_symbol_dependencies = metadata["reverse_relationships"]["symbol_dependencies"]
    symbol_risk = metadata["risk"]["symbols"]

    result = []

    total_fan_in = 0
    total_fan_out = 0

    for symbol_id, symbol_info in symbols.items():

        calls = symbol_dependencies.get(symbol_id, [])
        called_by = reverse_symbol_dependencies.get(symbol_id, [])

        fan_out = len(calls)
        fan_in = len(called_by)

        total_fan_in += fan_in
        total_fan_out += fan_out

        blast_radius = symbol_risk.get(symbol_id, 0)

        # Instability
        instability = (
            0 if (fan_in + fan_out == 0)
            else round(fan_out / (fan_in + fan_out), 2)
        )

        # Severity
        if blast_radius > 50:
            severity = "HIGH"
        elif blast_radius > 15:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # Architectural Role
        if fan_in > 10 and blast_radius > 30:
            role = "Core Symbol"
        elif fan_out > 10 and fan_in < 2:
            role = "Unstable Symbol"
        elif fan_in == 0 and fan_out > 0:
            role = "Leaf Symbol"
        else:
            role = "Utility"

        result.append({
            "symbol": symbol_id,
            "name": symbol_id.split("::")[-1],
            "file": symbol_info["file"],
            "type": symbol_info["type"],
            "fan_in": fan_in,
            "fan_out": fan_out,
            "blast_radius": blast_radius,
            "instability": instability,
            "severity": severity,
            "role": role
        })

    total_symbols = len(result)

    avg_fan_in = round(total_fan_in / total_symbols, 2) if total_symbols else 0
    avg_fan_out = round(total_fan_out / total_symbols, 2) if total_symbols else 0

    severity_breakdown = {
        "HIGH": len([r for r in result if r["severity"] == "HIGH"]),
        "MEDIUM": len([r for r in result if r["severity"] == "MEDIUM"]),
        "LOW": len([r for r in result if r["severity"] == "LOW"])
    }

    return {
        "total_symbols": total_symbols,
        "average_fan_in": avg_fan_in,
        "average_fan_out": avg_fan_out,
        "severity_breakdown": severity_breakdown,

        "top_risky_symbols": sorted(result, key=lambda x: x["blast_radius"], reverse=True)[:20],
        "most_depended_symbols": sorted(result, key=lambda x: x["fan_in"], reverse=True)[:20],
        "most_outgoing_symbols": sorted(result, key=lambda x: x["fan_out"], reverse=True)[:20]
    }







# ---------------------------------------------------------
# 8️⃣ File Dependency Graph (Depth = 1)
# ---------------------------------------------------------
@router.get("/impact/file-graph/{repo_id}/{commit_hash}")
def get_file_graph(
    repo_id: str,
    commit_hash: str,
    path: str = Query(...)
):

    metadata, _ = load_metadata(repo_id, commit_hash)

    file_dependencies = metadata["relationships"]["file_dependencies"]
    reverse_dependencies = metadata["reverse_relationships"]["file_dependencies"]
    file_risk = metadata["risk"]["files"]

    if path not in file_dependencies:
        raise HTTPException(status_code=404, detail="File not found in metadata")

    outgoing_list = file_dependencies.get(path, [])
    incoming_list = reverse_dependencies.get(path, [])

    nodes = []
    edges = []
    visited_nodes = set()
    visited_edges = set()

    # -------------------------------------------------
    # Helper: Add Node
    # -------------------------------------------------
    def add_node(file_path: str, category: str):

        if file_path in visited_nodes:
            return

        visited_nodes.add(file_path)

        blast = file_risk.get(file_path, 0)

        # Severity classification
        if blast > 75:
            severity = "CRITICAL"
        elif blast > 30:
            severity = "HIGH"
        elif blast > 10:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        nodes.append({
            "id": file_path,
            "label": file_path.split("/")[-1],
            "full_path": file_path,
            "severity": severity,
            "category": category,     # center / incoming / outgoing
            "is_center": file_path == path
        })

    # -------------------------------------------------
    # Helper: Add Edge
    # -------------------------------------------------
    def add_edge(source: str, target: str, edge_type: str):

        key = (source, target, edge_type)

        if key in visited_edges:
            return

        visited_edges.add(key)

        edges.append({
            "source": source,
            "target": target,
            "type": edge_type
        })

    # -------------------------------------------------
    # Add Center Node
    # -------------------------------------------------
    add_node(path, "center")

    # Outgoing (path → dependency)
    for dep in outgoing_list:
        add_node(dep, "outgoing")
        add_edge(path, dep, "outgoing")

    # Incoming (dependency → path)
    for dep in incoming_list:
        add_node(dep, "incoming")
        add_edge(dep, path, "incoming")

    return {
        "center": path,
        "fan_in": len(incoming_list),
        "fan_out": len(outgoing_list),
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": nodes,
        "edges": edges
    }




# ---------------------------------------------------------
# 7️⃣ Symbol Call Graph (Depth = 1, Clean + Deduplicated)
# ---------------------------------------------------------
@router.get("/impact/symbol-graph/{repo_id}/{commit_hash}")
def get_symbol_graph(
    repo_id: str,
    commit_hash: str,
    symbol_id: str = Query(...)
):

    metadata, _ = load_metadata(repo_id, commit_hash)

    symbols = metadata.get("symbols", {})
    relationships = metadata.get("relationships", {})
    reverse_relationships = metadata.get("reverse_relationships", {})
    risk_data = metadata.get("risk", {}).get("symbols", {})

    symbol_dependencies = relationships.get("symbol_dependencies", {})
    reverse_symbol_dependencies = reverse_relationships.get("symbol_dependencies", {})

    if symbol_id not in symbols:
        raise HTTPException(status_code=404, detail="Symbol not found")

    nodes = []
    edges = []
    visited_nodes = set()
    visited_edges = set()

    outgoing_list = symbol_dependencies.get(symbol_id, [])
    incoming_list = reverse_symbol_dependencies.get(symbol_id, [])

    # -------------------------------------------------
    # Helper: Add Node
    # -------------------------------------------------
    def add_node(sid: str, category: str):
        if sid in visited_nodes:
            return

        visited_nodes.add(sid)

        symbol_info = symbols.get(sid, {})
        blast = risk_data.get(sid, 0)

        # Severity classification
        if blast > 75:
            severity = "CRITICAL"
        elif blast > 30:
            severity = "HIGH"
        elif blast > 10:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        nodes.append({
            "id": sid,
            "label": sid.split("::")[-1],
            "file": symbol_info.get("file"),
            "type": symbol_info.get("type"),
            "severity": severity,
            "category": category,   # center / incoming / outgoing
            "is_center": sid == symbol_id
        })

    # -------------------------------------------------
    # Helper: Add Edge (Deduplicated)
    # -------------------------------------------------
    def add_edge(source: str, target: str, edge_type: str):
        key = (source, target, edge_type)

        if key in visited_edges:
            return

        visited_edges.add(key)

        edges.append({
            "source": source,
            "target": target,
            "type": edge_type  # incoming / outgoing
        })

    # -------------------------------------------------
    # Add Center Node
    # -------------------------------------------------
    add_node(symbol_id, "center")

    # -------------------------------------------------
    # Add Outgoing Nodes + Edges
    # symbol_id → callee
    # -------------------------------------------------
    for callee in outgoing_list:
        add_node(callee, "outgoing")
        add_edge(symbol_id, callee, "outgoing")

    # -------------------------------------------------
    # Add Incoming Nodes + Edges
    # caller → symbol_id
    # -------------------------------------------------
    for caller in incoming_list:
        add_node(caller, "incoming")
        add_edge(caller, symbol_id, "incoming")

    # -------------------------------------------------
    # Final Response
    # -------------------------------------------------
    return {
        "center": symbol_id,
        "fan_in": len(incoming_list),
        "fan_out": len(outgoing_list),
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": nodes,
        "edges": edges
    }


# ---------------------------------------------------------
# 9️⃣ Project Symbol Graph (All Symbols - Depth 1)
# ---------------------------------------------------------
@router.get("/impact/project-graph/{repo_id}/{commit_hash}")
def get_project_graph(repo_id: str, commit_hash: str):

    metadata, _ = load_metadata(repo_id, commit_hash)

    symbols = metadata.get("symbols", {})
    relationships = metadata.get("relationships", {})
    reverse_relationships = metadata.get("reverse_relationships", {})
    risk_data = metadata.get("risk", {}).get("symbols", {})

    symbol_dependencies = relationships.get("symbol_dependencies", {})
    reverse_symbol_dependencies = reverse_relationships.get("symbol_dependencies", {})

    nodes = []
    edges = []
    visited_nodes = set()
    visited_edges = set()

    # -------------------------------
    # Add Node Helper
    # -------------------------------
    def add_node(sid: str):
        if sid in visited_nodes:
            return

        visited_nodes.add(sid)

        symbol_info = symbols.get(sid, {})
        blast = risk_data.get(sid, 0)

        if blast > 75:
            severity = "CRITICAL"
        elif blast > 30:
            severity = "HIGH"
        elif blast > 10:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        nodes.append({
            "id": sid,
            "label": sid.split("::")[-1],
            "file": symbol_info.get("file"),
            "type": symbol_info.get("type"),
            "severity": severity
        })

    # -------------------------------
    # Add Edge Helper
    # -------------------------------
    def add_edge(source: str, target: str):
        key = (source, target)
        if key in visited_edges:
            return

        visited_edges.add(key)

        edges.append({
            "source": source,
            "target": target
        })

    # -------------------------------
    # Build Full Graph
    # -------------------------------
    for symbol_id in symbols.keys():
        add_node(symbol_id)

        for callee in symbol_dependencies.get(symbol_id, []):
            add_node(callee)
            add_edge(symbol_id, callee)

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": nodes,
        "edges": edges
    }