##/Users/vishalkeshari/Desktop/smarix/backend/routes/api/impact_routes.py 

from fastapi import APIRouter, HTTPException, Query
import json
import os

from main.CodeIntelligence.repo_registry import RepoRegistry

router = APIRouter()
registry = RepoRegistry()


def load_intelligence(extractor_id: str, repo_id: str):

    metadata_path = registry.get_intelligence_path(
        extractor_id,
        repo_id
    )

    if not os.path.exists(metadata_path):
        raise HTTPException(status_code=404, detail="Intelligence file not found")

    with open(metadata_path, "r") as f:
        return json.load(f)




# ---------------------------------------------------------
# 1️⃣ Project Structure (Use file_tree directly)
# ---------------------------------------------------------
@router.get("/impact/{extractor_id}/repos/{repo_id}/project-structure")
def get_project_structure(extractor_id: str, repo_id: str):

    metadata = load_intelligence(extractor_id, repo_id)

    file_tree = metadata.get("file_tree", [])

    return {
        "tree": file_tree
    }


# ---------------------------------------------------------
# 2️⃣ File Content
# ---------------------------------------------------------


from urllib.parse import unquote

@router.get("/impact/{extractor_id}/repos/{repo_id}/file-content")
def get_file_content(extractor_id: str, repo_id: str, path: str = Query(...)):

    repo_json_path = registry.get_repo_json_path(
        extractor_id,
        repo_id
    )

    if not os.path.exists(repo_json_path):
        raise HTTPException(status_code=404, detail="Repository data not found")

    with open(repo_json_path, "r") as f:
        repo_data = json.load(f)

    # 🔥 Correct level: code_files
    files = repo_data.get("code_files", [])

    for file_obj in files:
        if file_obj.get("path") == path:
            return {
                "file": path,
                "content": file_obj.get("content", "")
            }

    raise HTTPException(status_code=404, detail="File not found")
        


# ---------------------------------------------------------
# 3️⃣ File Impact (Advanced Right Panel Data)
# ---------------------------------------------------------
@router.get("/impact/{extractor_id}/repos/{repo_id}/file-impact")
def get_file_impact(extractor_id: str, repo_id: str, path: str = Query(...)):

    metadata = load_intelligence(extractor_id, repo_id)

    relationships = metadata.get("relationships", {})
    reverse_relationships = metadata.get("reverse_relationships", {})
    risk_data = metadata.get("risk", {})

    file_dependencies = relationships.get("file_dependencies", {})
    reverse_dependencies = reverse_relationships.get("file_dependencies", {})
    file_risk = risk_data.get("files", {})

    calls = file_dependencies.get(path, [])
    called_by = reverse_dependencies.get(path, [])

    blast_radius = file_risk.get(path, 0)

    outgoing = len(calls)
    incoming = len(called_by)

    instability = (
        0 if (incoming + outgoing == 0)
        else round(outgoing / (incoming + outgoing), 2)
    )

    if incoming == 0 and outgoing > 0:
        role = "Leaf Module"
    elif incoming > 5 and blast_radius > 20:
        role = "Core Module"
    elif "tests" in path:
        role = "Test File"
    else:
        role = "Service/Utility"

    prod_impact = 0
    test_impact = 0

    for f in called_by:
        if "tests" in f:
            test_impact += 1
        else:
            prod_impact += 1

    if blast_radius > 50:
        severity = "HIGH"
    elif blast_radius > 15:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return {
        "file": path,
        "blast_radius": blast_radius,
        "direct_dependents": incoming,
        "depends_on": outgoing,
        "calls": calls,
        "called_by": called_by,
        "instability": instability,
        "role": role,
        "severity": severity,
        "production_impact": prod_impact,
        "test_impact": test_impact
    }



# ---------------------------------------------------------
# 5️⃣ File-Specific Symbol Intelligence
# ---------------------------------------------------------
@router.get("/impact/{extractor_id}/repos/{repo_id}/file-symbols")
def get_file_symbols(extractor_id: str, repo_id: str, path: str = Query(...)):

    metadata = load_intelligence(extractor_id, repo_id)

    symbols = metadata.get("symbols", {})
    relationships = metadata.get("relationships", {})
    reverse_relationships = metadata.get("reverse_relationships", {})

    symbol_dependencies = relationships.get("symbol_dependencies", {})
    reverse_symbol_dependencies = reverse_relationships.get("symbol_dependencies", {})
    inheritance = relationships.get("inheritance", {})
    reverse_inheritance = reverse_relationships.get("inheritance", {})

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

        # Transitive blast radius
        visited = set()
        stack = list(called_by)

        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                stack.extend(reverse_symbol_dependencies.get(current, []))

        blast_radius = len(visited)

        # Impact depth
        depth = 0
        frontier = list(called_by)
        visited_depth = set()

        while frontier:
            next_frontier = []
            for node in frontier:
                if node not in visited_depth:
                    visited_depth.add(node)
                    next_frontier.extend(reverse_symbol_dependencies.get(node, []))
            frontier = next_frontier
            depth += 1

        instability = (
            0 if (fan_in + fan_out == 0)
            else round(fan_out / (fan_in + fan_out), 2)
        )

        if blast_radius > 75:
            severity = "CRITICAL"
        elif blast_radius > 30:
            severity = "HIGH"
        elif blast_radius > 10:
            severity = "MEDIUM"
        else:
            severity = "LOW"

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
            "parameters": structure.get("parameters", []),
            "return_type": structure.get("return_type"),
            "is_async": behavior.get("is_async"),
            "decorators": behavior.get("decorators", []),
            "docstring": documentation.get("docstring"),
            "input": {
                "fan_in": fan_in,
                "inherits_from": inheritance.get(symbol_id, [])
            },
            "output": {
                "fan_out": fan_out,
                "calls": calls,
                "inherited_by": reverse_inheritance.get(symbol_id, [])
            },
            "fan_in": fan_in,
            "fan_out": fan_out,
            "blast_radius": blast_radius,
            "impact_depth": depth,
            "instability": instability,
            "severity": severity,
            "role": role
        })

    file_symbols.sort(key=lambda x: x["blast_radius"], reverse=True)

    return {
        "file": path,
        "total_symbols": len(file_symbols),
        "symbols": file_symbols
    }


# ---------------------------------------------------------
# 7️⃣ Symbol Details
# ---------------------------------------------------------
@router.get("/impact/symbol-details/{extractor_id}/repos/{repo_id}")
def get_symbol_details(extractor_id: str, repo_id: str, symbol_id: str = Query(...)):

    metadata = load_intelligence(extractor_id, repo_id)

    symbols = metadata.get("symbols", {})
    relationships = metadata.get("relationships", {})
    reverse_relationships = metadata.get("reverse_relationships", {})
    risk_data = metadata.get("risk", {})

    symbol_dependencies = relationships.get("symbol_dependencies", {})
    reverse_symbol_dependencies = reverse_relationships.get("symbol_dependencies", {})
    symbol_risk = risk_data.get("symbols", {})

    if symbol_id not in symbols:
        raise HTTPException(status_code=404, detail="Symbol not found")

    symbol_info = symbols[symbol_id]

    calls = symbol_dependencies.get(symbol_id, [])
    called_by = reverse_symbol_dependencies.get(symbol_id, [])

    fan_out = len(calls)
    fan_in = len(called_by)

    visited = set()
    stack = list(called_by)

    while stack:
        current = stack.pop()
        if current not in visited:
            visited.add(current)
            stack.extend(reverse_symbol_dependencies.get(current, []))

    blast_radius = len(visited)

    instability = (
        0 if (fan_in + fan_out == 0)
        else round(fan_out / (fan_in + fan_out), 2)
    )

    if blast_radius > 75:
        severity = "CRITICAL"
    elif blast_radius > 30:
        severity = "HIGH"
    elif blast_radius > 10:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return {
        "symbol": symbol_id,
        "name": symbol_id.split("::")[-1],
        "file": symbol_info["file"],
        "type": symbol_info["type"],
        "fan_in": fan_in,
        "fan_out": fan_out,
        "blast_radius": blast_radius,
        "instability": instability,
        "severity": severity,
        "calls": calls,
        "called_by": called_by
    }



# ---------------------------------------------------------
# 6️⃣ Project-Level Symbol Intelligence
# ---------------------------------------------------------
@router.get("/impact/project-symbols/{extractor_id}/repos/{repo_id}")
def get_project_symbols(extractor_id: str, repo_id: str):

    metadata = load_intelligence(extractor_id, repo_id)

    symbols = metadata.get("symbols", {})
    relationships = metadata.get("relationships", {})
    reverse_relationships = metadata.get("reverse_relationships", {})
    risk_data = metadata.get("risk", {})

    symbol_dependencies = relationships.get("symbol_dependencies", {})
    reverse_symbol_dependencies = reverse_relationships.get("symbol_dependencies", {})
    symbol_risk = risk_data.get("symbols", {})

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

        instability = (
            0 if (fan_in + fan_out == 0)
            else round(fan_out / (fan_in + fan_out), 2)
        )

        if blast_radius > 50:
            severity = "HIGH"
        elif blast_radius > 15:
            severity = "MEDIUM"
        else:
            severity = "LOW"

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
@router.get("/impact/{extractor_id}/repos/{repo_id}/file-graph")
def get_file_graph(extractor_id: str, repo_id: str, path: str = Query(...)):

    metadata = load_intelligence(extractor_id, repo_id)

    relationships = metadata.get("relationships", {})
    reverse_relationships = metadata.get("reverse_relationships", {})
    risk_data = metadata.get("risk", {})

    file_dependencies = relationships.get("file_dependencies", {})
    reverse_dependencies = reverse_relationships.get("file_dependencies", {})
    file_risk = risk_data.get("files", {})

    outgoing_list = file_dependencies.get(path, [])
    incoming_list = reverse_dependencies.get(path, [])

    nodes = []
    edges = []

    def severity_of(file_path):
        blast = file_risk.get(file_path, 0)
        if blast > 75:
            return "CRITICAL"
        elif blast > 30:
            return "HIGH"
        elif blast > 10:
            return "MEDIUM"
        return "LOW"

    def add_node(fp, category):
        nodes.append({
            "id": fp,
            "label": fp.split("/")[-1],
            "full_path": fp,
            "severity": severity_of(fp),
            "category": category,
            "is_center": fp == path
        })

    add_node(path, "center")

    for dep in outgoing_list:
        add_node(dep, "outgoing")
        edges.append({"source": path, "target": dep})

    for dep in incoming_list:
        add_node(dep, "incoming")
        edges.append({"source": dep, "target": path})

    return {
        "center": path,
        "fan_in": len(incoming_list),
        "fan_out": len(outgoing_list),
        "nodes": nodes,
        "edges": edges
    }



# ---------------------------------------------------------
# 7️⃣ Symbol Call Graph
# ---------------------------------------------------------
@router.get("/impact/symbol-graph/{extractor_id}/repos/{repo_id}")
def get_symbol_graph(extractor_id: str, repo_id: str, symbol_id: str = Query(...)):

    metadata = load_intelligence(extractor_id, repo_id)

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

    outgoing_list = symbol_dependencies.get(symbol_id, [])
    incoming_list = reverse_symbol_dependencies.get(symbol_id, [])

    def severity_of(sid):
        blast = risk_data.get(sid, 0)
        if blast > 75:
            return "CRITICAL"
        elif blast > 30:
            return "HIGH"
        elif blast > 10:
            return "MEDIUM"
        return "LOW"

    def add_node(sid, category):
        symbol_info = symbols.get(sid, {})
        nodes.append({
            "id": sid,
            "label": sid.split("::")[-1],
            "file": symbol_info.get("file"),
            "type": symbol_info.get("type"),
            "severity": severity_of(sid),
            "category": category,
            "is_center": sid == symbol_id
        })

    add_node(symbol_id, "center")

    for callee in outgoing_list:
        add_node(callee, "outgoing")
        edges.append({"source": symbol_id, "target": callee})

    for caller in incoming_list:
        add_node(caller, "incoming")
        edges.append({"source": caller, "target": symbol_id})

    return {
        "center": symbol_id,
        "fan_in": len(incoming_list),
        "fan_out": len(outgoing_list),
        "nodes": nodes,
        "edges": edges
    }

# ---------------------------------------------------------
# 9️⃣ Project Core Architecture Graph (Filtered)
# ---------------------------------------------------------
@router.get("/impact/{extractor_id}/repos/{repo_id}/project-graph")
def get_project_graph(extractor_id: str, repo_id: str):

    metadata = load_intelligence(extractor_id, repo_id)

    symbols = metadata.get("symbols", {})
    relationships = metadata.get("relationships", {})
    reverse_relationships = metadata.get("reverse_relationships", {})
    risk_all = metadata.get("risk", {})

    symbol_dependencies = relationships.get("symbol_dependencies", {})
    reverse_symbol_dependencies = reverse_relationships.get("symbol_dependencies", {})
    risk_data = risk_all.get("symbols", {})

    nodes = []
    edges = []

    # ---------------------------------------------------------
    # 🔥 Adaptive Filtering
    # ---------------------------------------------------------
    total_symbols = len(symbols)

    if total_symbols < 50:
        MIN_BLAST = 1
        MIN_FAN_IN = 0
    elif total_symbols < 200:
        MIN_BLAST = 3
        MIN_FAN_IN = 1
    else:
        MIN_BLAST = 25
        MIN_FAN_IN = 8

    important = set()

    for sid in symbols:
        fan_in = len(reverse_symbol_dependencies.get(sid, []))
        blast = risk_data.get(sid, 0)

        if blast >= MIN_BLAST or fan_in >= MIN_FAN_IN:
            important.add(sid)

    for sid in important:
        symbol_info = symbols[sid]

        nodes.append({
            "id": sid,
            "label": sid.split("::")[-1],
            "file": symbol_info.get("file"),
            "type": symbol_info.get("type"),
            "blast_radius": risk_data.get(sid, 0)
        })

        for callee in symbol_dependencies.get(sid, []):
            if callee in important:
                edges.append({
                    "source": sid,
                    "target": callee
                })

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": nodes,
        "edges": edges
    }


# ---------------------------------------------------------
# 📦 List All Extractors + Repos
# ---------------------------------------------------------
@router.get("/projects")
def get_all_projects():

    result = []

    extractors = registry.list_extractors()

    for extractor in extractors:
        repos = registry.list_repos(extractor)

        result.append({
            "extractor": extractor,
            "repos": repos
        })

    return result

# ---------------------------------------------------------
# 🔟 High Risk Files (Project-Level)
# ---------------------------------------------------------
@router.get("/impact/{extractor_id}/repos/{repo_id}/high-risk-files")
def get_high_risk_files(extractor_id: str, repo_id: str):

    metadata = load_intelligence(extractor_id, repo_id)

    relationships = metadata.get("relationships", {})
    reverse_relationships = metadata.get("reverse_relationships", {})
    risk_data = metadata.get("risk", {})

    file_dependencies = relationships.get("file_dependencies", {})
    reverse_dependencies = reverse_relationships.get("file_dependencies", {})
    file_risk = risk_data.get("files", {})

    result = []

    for file_path, blast_radius in file_risk.items():

        incoming = len(reverse_dependencies.get(file_path, []))
        outgoing = len(file_dependencies.get(file_path, []))

        if blast_radius > 50:
            severity = "HIGH"
        elif blast_radius > 15:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        result.append({
            "file": file_path,
            "name": file_path.split("/")[-1],
            "blast_radius": blast_radius,
            "fan_in": incoming,
            "fan_out": outgoing,
            "severity": severity
        })

    result.sort(key=lambda x: x["blast_radius"], reverse=True)

    return {
        "total_files": len(result),
        "high_risk_files": result[:50]
    }


