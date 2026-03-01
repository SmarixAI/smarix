from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

from main.CodeIntelligence.repo_registry import RepoRegistry

# =========================================================
# Environment
# =========================================================

load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

router = APIRouter()
registry = RepoRegistry()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in environment")

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================================================
# Request Models
# =========================================================

class ContextBuildRequest(BaseModel):
    file_path: str
    user_instruction: str
    max_depth: int = 1
    max_files: int = 10


class PromptGenerationRequest(BaseModel):
    user_instruction: str
    architecture_payload: Dict[str, Any]


# =========================================================
# Load Intelligence
# =========================================================

def load_intelligence(extractor_id: str, repo_id: str):
    path = registry.get_intelligence_path(extractor_id, repo_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Intelligence file not found")
    with open(path, "r") as f:
        return json.load(f)


def load_repo_json(extractor_id: str, repo_id: str):
    path = registry.get_repo_json_path(extractor_id, repo_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Repository data not found")
    with open(path, "r") as f:
        return json.load(f)


# =========================================================
# Classification
# =========================================================

def classify_instruction(user_instruction: str, file_list: List[str]):

    system_prompt = """
Determine:
1. intent: bugfix | refactor | optimization | feature | new_feature
2. scope: existing_feature | new_feature
3. related_files: list of relevant files from provided list
Return JSON only.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({
                "instruction": user_instruction,
                "available_files": file_list[:200]
            })}
        ]
    )

    try:
        return json.loads(response.choices[0].message.content)
    except:
        return {
            "intent": "feature",
            "scope": "existing_feature",
            "related_files": []
        }


# =========================================================
# Utilities
# =========================================================

def count_loc(content: str):
    return len(content.splitlines())


def extract_imports(content: str):
    imports = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#include") or stripped.startswith("import"):
            imports.append(stripped)
    return imports[:15]


def slice_code(content: str, max_lines=60):
    lines = content.splitlines()
    if len(lines) <= max_lines:
        return content
    return "\n".join(lines[:30]) + "\n...\n" + "\n".join(lines[-20:])


def classify_role(fan_in, fan_out):
    if fan_in == 0 and fan_out > 0:
        return "ENTRY_POINT"
    if fan_in > 5:
        return "CORE_MODULE"
    if fan_out > 5:
        return "COORDINATOR"
    return "UTILITY"


# =========================================================
# Graph + Context Builders
# =========================================================

def expand_impact(root_files, relationships, reverse_relationships, depth):

    file_deps = relationships.get("file_dependencies", {})
    reverse_deps = reverse_relationships.get("file_dependencies", {})

    visited = set(root_files)
    current = set(root_files)

    for _ in range(depth):
        next_level = set()
        for f in current:
            next_level.update(file_deps.get(f, []))
            next_level.update(reverse_deps.get(f, []))
        next_level -= visited
        visited.update(next_level)
        current = next_level

    return list(visited)


def build_file_graph(files, relationships):
    file_deps = relationships.get("file_dependencies", {})
    nodes = [{"id": f} for f in files]
    edges = []

    for f in files:
        for dep in file_deps.get(f, []):
            if dep in files:
                edges.append({"from": f, "to": dep})

    return {"nodes": nodes, "edges": edges}


def build_structured_context(files, metadata, repo_data, relationships, reverse_relationships, risk_data):

    repo_files_map = {f["path"]: f["content"] for f in repo_data.get("code_files", [])}
    file_deps = relationships.get("file_dependencies", {})
    reverse_deps = reverse_relationships.get("file_dependencies", {})
    file_risk = risk_data.get("files", {})

    structured = []

    for path in files:
        content = repo_files_map.get(path)
        if not content:
            continue

        fan_in = len(reverse_deps.get(path, []))
        fan_out = len(file_deps.get(path, []))
        blast = file_risk.get(path, 0)

        structured.append({
            "file_path": path,
            "role": classify_role(fan_in, fan_out),
            "metrics": {
                "loc": count_loc(content),
                "fan_in": fan_in,
                "fan_out": fan_out,
                "blast_radius": blast,
                "sensitivity_score": fan_in * blast
            },
            "imports": extract_imports(content),
            "code_slice": slice_code(content)
        })

    structured.sort(key=lambda x: x["metrics"]["sensitivity_score"], reverse=True)
    return structured


def build_architecture_summary(structured_files):

    entry_points = [f["file_path"] for f in structured_files if f["role"] == "ENTRY_POINT"]
    core_modules = [f["file_path"] for f in structured_files if f["role"] == "CORE_MODULE"]

    return {
        "entry_points": entry_points,
        "core_modules": core_modules,
        "total_files": len(structured_files)
    }


# =========================================================
# Prompt Generation Only
# =========================================================

def refine_prompt_with_llm(payload, instruction):

    system_prompt = """
You are a senior software architect.

Analyze architecture and produce a precise engineering prompt.
Avoid generic advice.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({
                "architecture": payload,
                "task": instruction
            }, indent=2)}
        ]
    )

    return response.choices[0].message.content


# =========================================================
# 1️⃣ CONTEXT ENDPOINT (RIGHT SIDEBAR)
# =========================================================

@router.post("/prompt-builder/{extractor_id}/repos/{repo_id}/context")
def build_context(extractor_id: str, repo_id: str, request: ContextBuildRequest):

    metadata = load_intelligence(extractor_id, repo_id)
    repo_data = load_repo_json(extractor_id, repo_id)

    relationships = metadata.get("relationships", {})
    reverse_relationships = metadata.get("reverse_relationships", {})
    risk_data = metadata.get("risk", {})

    all_files = [f["path"] for f in repo_data.get("code_files", [])]

    classification = classify_instruction(request.user_instruction, all_files)

    if classification.get("scope") == "new_feature":
        root_files = all_files[:request.max_files]
    else:
        root_files = classification.get("related_files") or [request.file_path]

    expanded_files = expand_impact(
        root_files,
        relationships,
        reverse_relationships,
        request.max_depth
    )[:request.max_files]

    structured_context = build_structured_context(
        expanded_files,
        metadata,
        repo_data,
        relationships,
        reverse_relationships,
        risk_data
    )

    file_graph = build_file_graph(expanded_files, relationships)
    architecture_summary = build_architecture_summary(structured_context)

    total_loc = sum(f["metrics"]["loc"] for f in structured_context)

    return {
        "classification": classification,
        "file_graph": file_graph,
        "architecture_summary": architecture_summary,
        "structured_context": structured_context,
        "impact_summary": {
            "total_files": len(structured_context),
            "total_loc": total_loc
        }
    }


# =========================================================
# 2️⃣ PROMPT GENERATION ENDPOINT (CENTER)
# =========================================================

@router.post("/prompt-builder/{extractor_id}/repos/{repo_id}/generate-prompt")
def generate_prompt(extractor_id: str, repo_id: str, request: PromptGenerationRequest):

    refined_prompt = refine_prompt_with_llm(
        request.architecture_payload,
        request.user_instruction
    )

    return {
        "llm_refined_prompt": refined_prompt
    }