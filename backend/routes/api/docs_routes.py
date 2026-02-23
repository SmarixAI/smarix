"""
Auto Documentation API Routes
Generates documentation for code, APIs, README, changelogs, and more.
Fetches live content directly from GitHub API — 100% reliable.
"""

import json
import asyncio
import re
import os
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Literal
from concurrent.futures import ThreadPoolExecutor

from routes.api import shared

router = APIRouter()


# ==================== PYDANTIC MODELS ====================

DocType = Literal[
    "system_e2e",
    "function_docs", "class_docs", "module_docs", "api_docs",
    "readme", "changelog", "architecture", "db_schema",
    "env_docs", "onboarding"
]

FormatType = Literal["markdown", "jsdoc", "docstring", "openapi"]


class GenerateDocsRequest(BaseModel):
    doc_type: DocType
    target: Optional[str] = None
    format: FormatType = "markdown"
    username: Optional[str] = None
    options: Optional[dict] = {}


def get_user_schema_name(username: str) -> str:
    if not username:
        return "public"
    sanitized = re.sub(r"[^a-z0-9_]", "_", username.lower())
    return f"user_{sanitized}"


# ==================== GITHUB CLIENT ====================

class GitHubClient:
    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo  = repo
        self.base  = f"https://api.github.com/repos/{owner}/{repo}"
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_ACCESS_TOKEN")
        self.headers = {"User-Agent": "smarix-docs", "Accept": "application/vnd.github+json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def _get(self, url: str, params: dict = None, raw: bool = False):
        try:
            h = dict(self.headers)
            if raw:
                h["Accept"] = "application/vnd.github.v3.raw"
            resp = requests.get(url, headers=h, params=params, timeout=20)
            if resp.status_code == 200:
                return resp.text if raw else resp.json()
            print(f"[github] GET {url} → {resp.status_code}: {resp.text[:100]}")
            return None
        except Exception as e:
            print(f"[github] GET error {url}: {e}")
            return None

    def get_default_branch(self) -> str:
        data = self._get(self.base)
        return (data or {}).get("default_branch", "main")

    def get_file(self, path: str) -> Optional[str]:
        return self._get(f"{self.base}/contents/{path}", raw=True)

    def get_tree(self, branch: str = None) -> list:
        if not branch:
            branch = self.get_default_branch()
        data = self._get(f"{self.base}/git/trees/{branch}?recursive=1")
        if not data:
            return []
        if data.get("truncated"):
            print(f"[github] Tree truncated for {self.owner}/{self.repo}")
        return [i for i in data.get("tree", []) if i.get("type") == "blob"]

    def get_commits(self, per_page: int = 100) -> list:
        data = self._get(f"{self.base}/commits", params={"per_page": per_page})
        return data if isinstance(data, list) else []

    def get_pulls(self, state: str = "all", per_page: int = 100) -> list:
        data = self._get(f"{self.base}/pulls", params={"state": state, "per_page": per_page})
        return data if isinstance(data, list) else []

    def get_releases(self) -> list:
        data = self._get(f"{self.base}/releases", params={"per_page": 30})
        return data if isinstance(data, list) else []

    def fetch_files_by_extensions(
        self,
        extensions: list,
        max_files: int = 80,
        exclude_dirs: list = None,
    ) -> list:
        exclude_dirs = exclude_dirs or [
            "node_modules", ".dart_tool", "build", "dist",
            ".gradle", ".idea", ".vscode", "vendor", "__pycache__",
            ".pub-cache", "ios/Pods", "android/.gradle",
        ]
        tree = self.get_tree()
        if not tree:
            return []

        def should_include(path: str) -> bool:
            if not any(path.endswith(ext) for ext in extensions):
                return False
            parts = path.split("/")
            return not any(ex in parts for ex in exclude_dirs)

        matching = [item["path"] for item in tree if should_include(item["path"])][:max_files]
        print(f"[github] Fetching {len(matching)}/{len(tree)} files from {self.owner}/{self.repo}")

        results = []
        for fp in matching:
            content = self.get_file(fp)
            if content and content.strip():
                results.append({"file_path": fp, "content": content})

        print(f"[github] Fetched {len(results)} non-empty files")
        return results

    def fetch_config_and_infra_files(self) -> list:
        config_names = [
            "pubspec.yaml", "package.json", "requirements.txt", "Pipfile",
            "pyproject.toml", "go.mod", "Cargo.toml", "pom.xml", "build.gradle",
            ".env.example", ".env.sample", ".env.template",
            "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
            "Makefile", ".github/workflows",
            "README.md", "CONTRIBUTING.md", "CHANGELOG.md",
        ]
        results = []
        for name in config_names:
            content = self.get_file(name)
            if content and content.strip():
                results.append({"file_path": name, "content": content})
        return results


def _get_github_client() -> Optional[GitHubClient]:
    if shared.chatbot_instance is None:
        return None
    owner = getattr(shared.chatbot_instance, "repo_owner", None)
    repo  = getattr(shared.chatbot_instance, "repo_name", None)
    if not owner or not repo:
        return None
    return GitHubClient(owner, repo)


# ==================== FILE TREE (from index) ====================

def get_all_indexed_files() -> list:
    if shared.chatbot_instance is None:
        return []
    store = shared.chatbot_instance.multi_index_store
    chunks = store.find(where={"chunk_type": "code"}, top_k=50000, index="code")
    seen, files = set(), []
    for c in chunks:
        fp = c.get("metadata", {}).get("file_path")
        if fp and fp not in seen:
            seen.add(fp)
            files.append(fp)
    return sorted(files)


# ==================== CONTENT BUILDERS ====================

def _build_code_content(
    gh: GitHubClient,
    target: Optional[str],
    extensions: list,
    max_files: int,
) -> list:
    if target:
        content = gh.get_file(target)
        return [{"file_path": target, "content": content}] if content else []
    return gh.fetch_files_by_extensions(extensions, max_files=max_files)


def _build_changelog_content(gh: GitHubClient) -> list:
    results = []

    releases = gh.get_releases()
    if releases:
        lines = ["# Releases\n"]
        for r in releases[:20]:
            lines.append(
                f"## {r.get('tag_name', '?')} — {r.get('name', '')}\n"
                f"Published: {r.get('published_at', '?')}\n"
                f"{r.get('body', '(no notes)')}\n"
            )
        results.append({"file_path": "releases", "content": "\n".join(lines)})

    pulls = gh.get_pulls(state="closed", per_page=100)
    if pulls:
        lines = ["# Pull Requests\n"]
        for pr in pulls:
            merged = pr.get("merged_at")
            lines.append(
                f"- PR #{pr.get('number')}: {pr.get('title', '?')} "
                f"[{pr.get('state')}{'✓merged' if merged else ''}] "
                f"by {pr.get('user', {}).get('login', '?')} "
                f"({(merged or pr.get('closed_at') or '')[:10]})"
            )
        results.append({"file_path": "pull_requests", "content": "\n".join(lines)})

    commits = gh.get_commits(per_page=100)
    if commits:
        lines = ["# Commits\n"]
        for c in commits:
            msg    = (c.get("commit", {}).get("message") or "").split("\n")[0]
            author = c.get("commit", {}).get("author", {}).get("name", "?")
            date   = (c.get("commit", {}).get("author", {}).get("date") or "")[:10]
            sha    = (c.get("sha") or "")[:7]
            lines.append(f"- [{sha}] {date} {author}: {msg}")
        results.append({"file_path": "commits", "content": "\n".join(lines)})

    return results


def get_content_for_doc_type(
    gh: GitHubClient,
    doc_type: str,
    target: Optional[str],
    options: dict,
) -> list:

    CODE_EXTS = [
        ".py", ".ts", ".tsx", ".js", ".jsx", ".dart",
        ".go", ".rs", ".java", ".kt", ".swift", ".rb",
        ".cpp", ".c", ".cs", ".php",
    ]

    if doc_type == "system_e2e":
        if not target:
            entry_names = {
                "main.dart", "main.py", "main.ts", "main.tsx",
                "index.ts", "index.tsx", "index.js",
                "app.py", "server.py", "app.ts",
            }
            tree = gh.get_tree()
            results = []
            for item in tree:
                name = item["path"].split("/")[-1]
                if name in entry_names:
                    content = gh.get_file(item["path"])
                    if content:
                        results.append({"file_path": item["path"], "content": content})
            return results[:3]
        content = gh.get_file(target)
        if not content:
            return []
        return [{"file_path": target, "content": content}]

    if doc_type == "changelog":
        return _build_changelog_content(gh)

    if doc_type == "readme":
        config = gh.fetch_config_and_infra_files()
        code   = gh.fetch_files_by_extensions(CODE_EXTS, max_files=30)
        return config + code

    if doc_type == "onboarding":
        config = gh.fetch_config_and_infra_files()
        code   = gh.fetch_files_by_extensions(CODE_EXTS, max_files=30)
        return config + code

    if doc_type == "architecture":
        if target:
            # File-scoped: fetch target + sibling files in the same directory
            content = gh.get_file(target)
            if not content:
                return []
            results = [{"file_path": target, "content": content}]
            target_dir = "/".join(target.split("/")[:-1])
            if target_dir:
                tree = gh.get_tree()
                siblings = [
                    item["path"] for item in tree
                    if item["path"].startswith(target_dir + "/")
                    and item["path"] != target
                    and any(item["path"].endswith(ext) for ext in CODE_EXTS)
                ][:10]
                for fp in siblings:
                    c = gh.get_file(fp)
                    if c:
                        results.append({"file_path": fp, "content": c})
            return results
        # Full system
        return gh.fetch_files_by_extensions(CODE_EXTS, max_files=60)

    if doc_type == "function_docs":
        return _build_code_content(gh, target, CODE_EXTS, max_files=20)

    if doc_type == "class_docs":
        return _build_code_content(gh, target, CODE_EXTS, max_files=20)

    if doc_type == "module_docs":
        return _build_code_content(gh, target, CODE_EXTS, max_files=20)

    if doc_type == "api_docs":
        api_exts = [".py", ".ts", ".js", ".go", ".rb", ".java", ".dart"]
        return _build_code_content(gh, target, api_exts, max_files=30)

    if doc_type == "db_schema":
        schema_exts = [".py", ".ts", ".js", ".dart", ".kt", ".java", ".sql"]
        return _build_code_content(gh, target, schema_exts, max_files=20)

    if doc_type == "env_docs":
        config = gh.fetch_config_and_infra_files()
        env_keywords = [".env", "config", "settings", "docker", "compose", "makefile"]
        return [
            f for f in config
            if any(kw in f["file_path"].lower() for kw in env_keywords)
        ] or config

    return gh.fetch_files_by_extensions(CODE_EXTS, max_files=40)


# ==================== PROMPTS ====================

def build_content_block(chunks: list, max_chars: int = 80000) -> str:
    parts, total = [], 0
    for chunk in chunks:
        content   = chunk.get("content") or ""
        file_path = chunk.get("file_path") or ""
        if not content:
            continue
        entry = f"// {file_path}\n{content}\n" if file_path else content
        if total + len(entry) > max_chars:
            break
        parts.append(entry)
        total += len(entry)
    return "\n---\n".join(parts)


def build_prompt(doc_type: str, chunks: list, target: Optional[str], fmt: str, options: dict) -> str:
    content_block = build_content_block(chunks)
    target_label  = target or "the codebase"

    if doc_type == "system_e2e":
        file_label = target or "the entry point"
        return f"""You are a senior software architect. Analyze the following file and generate a complete **execution flow document** for `{file_label}`.

Include ALL of these sections:

1. **Purpose** — What this file does and where it fits in the app
2. **Execution Entry Point** — Where execution begins (main(), constructor, route handler, widget build, etc.)
3. **Step-by-Step Execution Flow** — Number each step, describe exactly what happens, which functions/methods are called in order
4. **Data Flow** — What data enters, how it transforms, what is returned or emitted
5. **State Changes** — Any state mutations, side effects, or async operations triggered
6. **External Dependencies** — Packages, services, APIs, database calls, network requests
7. **Error Handling** — How exceptions, null checks, and failure cases are handled
8. **Mermaid.js Flowchart** — Detailed flowchart of the complete execution path (```mermaid block using flowchart TD)

Be precise and technical. Reference actual function names, class names, variables, and line-level logic from the code.

FILE:
{content_block}"""

    if doc_type == "function_docs":
        fmt_instruction = (
            "JSDoc comments" if fmt == "jsdoc"
            else "Python docstrings (Google style)" if fmt == "docstring"
            else "Markdown"
        )
        return f"""You are a documentation expert. Generate complete documentation for all functions/methods in `{target_label}`.

For EACH function write:
- Clear one-line summary
- Parameters with types and descriptions
- Return value with type
- Raises/throws if applicable
- A short usage example

Format: {fmt_instruction}

CODE:
{content_block}

Generate documentation for EVERY function. Be concise but complete."""

    elif doc_type == "class_docs":
        return f"""Generate class documentation for all classes in `{target_label}`.
For each class include: purpose, constructor params, all public methods, inheritance/interfaces.

CODE:
{content_block}"""

    elif doc_type == "module_docs":
        return f"""Generate a module-level overview document for `{target_label}`.
Include: purpose, key exports/functions, dependencies it uses, and where it fits in the overall architecture.

CODE:
{content_block}"""

    elif doc_type == "api_docs":
        return f"""Generate API documentation for all route handlers in `{target_label}`.
For each endpoint include: HTTP method, path, description, request body schema, response schema, auth required, example.
Format as clean Markdown. Group endpoints by resource type.

CODE:
{content_block}"""

    elif doc_type == "readme":
        return f"""Generate a comprehensive, professional README.md for this repository.

Include these sections:
1. Project title and description
2. Key features
3. Tech stack (detected from config files)
4. Folder structure (inferred from code)
5. Prerequisites
6. Installation & setup steps
7. Environment variables (list all .env keys found)
8. How to run (dev + production)
9. API overview
10. Contributing guide

CODEBASE CONTEXT:
{content_block}"""

    elif doc_type == "changelog":
        date_range = f"Date range: {options.get('date_from', 'beginning')} to present\n" if options.get("date_from") else ""
        return f"""Generate a structured CHANGELOG.md from these commits, PRs, and releases.
{date_range}
Rules:
- Group by release tag if releases exist, otherwise group by month
- Categorize as: ✨ Features | 🐛 Bug Fixes | ♻️ Refactors | 💥 Breaking Changes | 📦 Dependencies | 🔒 Security
- Skip merge commits and trivial changes
- Write human-readable descriptions, not raw commit messages
- Format: Keep a Changelog standard (https://keepachangelog.com)

DATA:
{content_block}"""

    elif doc_type == "architecture":
        if target:
            return f"""Generate a focused architecture document for the module `{target}` and its immediate context.

Include:
1. **Module Purpose** — What this file/module is responsible for
2. **Internal Structure** — Classes, functions, key data structures
3. **Dependencies** — What it imports and why
4. **Interfaces** — What it exposes to the rest of the system
5. **Data Flow** — How data enters and exits this module
6. **Sibling Context** — How it relates to other files in the same directory
7. **Mermaid.js component diagram** (```mermaid block)

CONTEXT FILES:
{content_block}"""
        else:
            return f"""Generate a complete system architecture overview for this codebase.

Include:
1. High-level system description (2-3 paragraphs)
2. Key components and their responsibilities
3. Data flow between components
4. External dependencies/services
5. Folder structure breakdown
6. A Mermaid.js diagram of the full architecture (```mermaid block)

CODEBASE:
{content_block}"""

    elif doc_type == "db_schema":
        return f"""Generate database schema documentation from these model/schema files.

For each model/table:
- Purpose and description
- All fields with types, constraints, and descriptions
- Relationships (foreign keys, references)
- Indexes if visible

End with a Mermaid.js ER diagram (```mermaid block).

SCHEMA FILES:
{content_block}"""

    elif doc_type == "env_docs":
        return f"""Generate environment variable documentation from these config files.

Format as a Markdown table: Variable | Description | Required | Default | Example
Then add a complete `.env.example` file block.

CONFIG FILES:
{content_block}"""

    elif doc_type == "onboarding":
        return f"""Generate a comprehensive onboarding guide for new developers joining this project.

Include:
1. Project overview (what it does, why it exists)
2. Local setup (step by step)
3. Folder structure explained
4. Key concepts to understand before coding
5. Coding conventions and patterns used
6. How to run tests
7. How to submit a PR
8. Who to contact / where to ask questions

CODEBASE:
{content_block}"""

    return f"Generate documentation for:\n\n{content_block}"


# ==================== SSE STREAMING ====================

async def stream_llm_response(prompt: str):
    if shared.chatbot_instance is None:
        yield f"data: {json.dumps({'type': 'error', 'content': 'Chatbot not initialized'})}\n\n"
        return

    loop  = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def run_stream():
        try:
            stream = shared.chatbot_instance.client.chat.completions.create(
                model=shared.chatbot_instance.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical writer. Generate clean, accurate, developer-friendly documentation.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=True,
                max_tokens=4096,
                temperature=0.2,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    loop.call_soon_threadsafe(
                        queue.put_nowait, {"type": "token", "content": delta}
                    )
        except Exception as e:
            import traceback
            traceback.print_exc()
            loop.call_soon_threadsafe(
                queue.put_nowait, {"type": "error", "content": str(e)}
            )
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    ThreadPoolExecutor(max_workers=1).submit(run_stream)

    while True:
        chunk = await queue.get()
        if chunk is None:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            break
        yield f"data: {json.dumps(chunk)}\n\n"


# ==================== ENDPOINTS ====================

@router.post("/docs/generate")
async def generate_docs(request: GenerateDocsRequest):
    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    gh = _get_github_client()
    if not gh:
        raise HTTPException(
            status_code=503,
            detail="GitHub client could not be initialized. "
                   "repo_owner/repo_name not set on chatbot instance."
        )

    chunks = get_content_for_doc_type(gh, request.doc_type, request.target, request.options or {})

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Could not fetch content from {gh.owner}/{gh.repo}. "
                f"Check that GITHUB_TOKEN is set and the repo is accessible."
            )
        )

    prompt = build_prompt(
        request.doc_type,
        chunks,
        request.target,
        request.format,
        request.options or {}
    )

    print(f"[docs] {request.doc_type} | target={request.target or 'global'} | {len(chunks)} files | ~{len(prompt):,} chars")

    return StreamingResponse(
        stream_llm_response(prompt),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/docs/files")
async def list_files(username: Optional[str] = None):
    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    files = get_all_indexed_files()

    if len(files) < 10:
        gh = _get_github_client()
        if gh:
            CODE_EXTS = [
                ".py", ".ts", ".tsx", ".js", ".jsx", ".dart",
                ".go", ".rs", ".java", ".kt", ".swift", ".rb",
                ".cpp", ".c", ".cs", ".php",
            ]
            tree = gh.get_tree()
            gh_files = [
                item["path"] for item in tree
                if any(item["path"].endswith(ext) for ext in CODE_EXTS)
            ]
            all_files = sorted(set(files) | set(gh_files))
            return {"files": all_files, "total": len(all_files), "source": "github"}

    return {"files": files, "total": len(files), "source": "index"}


@router.get("/docs/coverage")
async def get_coverage(username: Optional[str] = None):
    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    total = len(get_all_indexed_files())
    return {
        "function_coverage": {
            "total":        total,
            "documented":   0,
            "undocumented": total,
            "coverage_pct": 0.0,
        }
    }


@router.get("/docs/debug")
async def debug_chunks(file_path: str):
    if shared.chatbot_instance is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    gh = _get_github_client()
    if not gh:
        return {"error": "No GitHub client — repo_owner/repo_name not set"}

    content = gh.get_file(file_path)
    branch  = gh.get_default_branch()
    tree    = gh.get_tree(branch)

    return {
        "repo":            f"{gh.owner}/{gh.repo}",
        "default_branch":  branch,
        "tree_file_count": len(tree),
        "file_fetch_test": {
            "file_path":       file_path,
            "fetched":         content is not None,
            "content_length":  len(content) if content else 0,
            "content_preview": (content or "")[:300],
        },
        "sample_tree_paths": [i["path"] for i in tree[:20]],
    }
