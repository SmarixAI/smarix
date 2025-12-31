"""
Enhanced Mermaid Diagram Generator with Dynamic Support
Creates both static and query-driven diagrams
"""

from typing import Dict, List, Any, Set, Optional, Tuple
import re
import json
from collections import defaultdict


class MermaidGenerator:
    """
    Generates Mermaid diagrams for:
    - Static diagrams (architecture, onboarding, technical debt)
    - Dynamic diagrams (issue timelines, PR impacts, feature flows)
    """

    def __init__(
        self, processed_data: Dict[str, Any], raw_data: Optional[Dict[str, Any]] = None
    ):
        self.data = processed_data
        self.raw_data = raw_data or {}
        self.chunks = processed_data.get("chunks", [])
        self.graph = processed_data.get("knowledge_graph", {})
        self.relationships = processed_data.get("relationships", {})

        # Cache for raw data lookups
        if self.raw_data:
            self._issues_cache = {
                i.get("number"): i for i in self.raw_data.get("issues", [])
            }
            self._prs_cache = {p.get("number"): p for p in self.raw_data.get("prs", [])}
            self._commits_cache = {
                c.get("sha"): c for c in self.raw_data.get("commits", [])
            }
        else:
            self._issues_cache = {}
            self._prs_cache = {}
            self._commits_cache = {}

    def generate_all_diagrams(self) -> Dict[str, str]:
        """Generate all static diagrams"""
        diagrams = {
            "architecture": self.generate_architecture_diagram(),
            "onboarding_flow": self.generate_onboarding_flow(),
            "file_dependencies": self.generate_file_dependencies_diagram(),
            "developer_ownership": self.generate_ownership_diagram(),
            "layer_architecture": self.generate_layer_architecture(),
            "technical_debt": self.generate_technical_debt_map(),
            "api_routes": self.generate_api_routes_diagram(),
            "diagram_index": self._create_diagram_index(),
        }

        diagrams["combined"] = self._create_combined_diagram(diagrams)
        return diagrams

    def generate_layer_architecture(self) -> str:
        """Generate layered architecture diagram"""
        lines = ["```mermaid", "graph TB", "    %% Layered Architecture", ""]

        layers = self._classify_by_layer()
        layer_order = ["presentation", "api", "service", "data", "utility"]

        for layer in layer_order:
            if layer not in layers or not layers[layer]:
                continue

            layer_label = layer.replace("_", " ").title()
            layer_id = f"layer_{layer}"

            lines.append(f'    subgraph {layer_id}["{layer_label} Layer"]')

            for file_path in layers[layer][:5]:
                file_id = self._sanitize_id(file_path)
                file_name = file_path.split("/")[-1]
                lines.append(f"        {file_id}[{file_name}]")

            lines.append("    end")
            lines.append("")

        prev_layer = None
        for layer in layer_order:
            if layer in layers and layers[layer]:
                layer_id = f"layer_{layer}"
                if prev_layer:
                    lines.append(f"    {prev_layer} -.->|depends on| {layer_id}")
                prev_layer = layer_id

        lines.append("```")
        return "\n".join(lines)

    def generate_technical_debt_map(self) -> str:
        """Generate technical debt and workaround map"""
        lines = ["```mermaid", "mindmap", "  root((Technical Debt))", ""]

        workarounds = [
            c for c in self.chunks if "workaround" in c.get("semantic_tags", [])
        ]
        complex_areas = [
            c
            for c in self.chunks
            if c.get("metadata", {}).get("complexity_score", 0) > 7
        ]
        todos = [c for c in self.chunks if "todo" in c.get("content", "").lower()]

        if workarounds:
            lines.append("    Workarounds & Hacks")
            for w in workarounds[:3]:
                file = w.get("file_path", "unknown").split("/")[-1]
                lines.append(f"      {file}")

        if complex_areas:
            lines.append("    Complex Areas")
            for c in complex_areas[:3]:
                file = c.get("file_path", "unknown").split("/")[-1]
                score = c.get("metadata", {}).get("complexity_score", 0)
                lines.append(f"      {file} (score: {score})")

        if todos:
            lines.append("    TODOs & FIXMEs")
            for t in todos[:3]:
                file = t.get("file_path", "unknown").split("/")[-1]
                lines.append(f"      {file}")

        lines.append("    Architectural Issues")
        lines.append("      Circular dependencies")
        lines.append("      Missing tests")
        lines.append("      Code duplication")

        lines.append("```")
        return "\n".join(lines)

    def generate_api_routes_diagram(self) -> str:
        """Generate API routes diagram"""
        lines = ["```mermaid", "graph LR", "    %% API Routes & Endpoints", ""]

        api_chunks = [c for c in self.chunks if c.get("chunk_type") == "api_endpoint"]

        if not api_chunks:
            api_chunks = [
                c
                for c in self.chunks
                if any(
                    kw in c.get("content", "").lower()
                    for kw in ["@route", "@get", "@post", "endpoint", "api"]
                )
            ][:10]

        by_method = defaultdict(list)
        for chunk in api_chunks:
            content = chunk.get("content", "").lower()
            if "post" in content or "@post" in content:
                by_method["POST"].append(chunk)
            elif "get" in content or "@get" in content:
                by_method["GET"].append(chunk)
            elif "put" in content or "@put" in content:
                by_method["PUT"].append(chunk)
            elif "delete" in content or "@delete" in content:
                by_method["DELETE"].append(chunk)
            else:
                by_method["OTHER"].append(chunk)

        lines.append("    Client[📱 Client]")

        for method, chunks in by_method.items():
            if not chunks:
                continue

            method_node = f"Method_{method}"
            lines.append(f"    {method_node}[{method}]")
            lines.append(f"    Client --> {method_node}")

            for chunk in chunks[:3]:
                file_path = chunk.get("file_path", "unknown")
                file_id = self._sanitize_id(file_path)
                file_name = file_path.split("/")[-1]

                lines.append(f"    {file_id}[📄 {file_name}]")
                lines.append(f"    {method_node} --> {file_id}")

        lines.append("```")
        return "\n".join(lines)

    def generate_issue_timeline(self, issue_number: int) -> Optional[str]:
        """Generate timeline for a specific issue"""
        issue = self._issues_cache.get(issue_number)
        if not issue:
            return None

        lines = [
            "```mermaid",
            "timeline",
            f"    title Issue #{issue_number}: {self._truncate(issue.get('title', ''), 40)}",
            "",
        ]

        created_date = (
            issue.get("created_at", "").split("T")[0] if issue.get("created_at") else ""
        )
        lines.append(f"    {created_date} : Issue Created")
        lines.append(
            f"               : Reporter: {issue.get('user', {}).get('login', 'unknown')}"
        )

        comments = issue.get("comments_data", [])[:5]
        for comment in comments:
            date = (
                comment.get("created_at", "").split("T")[0]
                if comment.get("created_at")
                else ""
            )
            author = comment.get("user", {}).get("login", "unknown")
            lines.append(f"    {date} : Comment by {author}")

        linked_prs = issue.get("referenced_prs", [])
        for pr_num in linked_prs[:3]:
            pr = self._prs_cache.get(pr_num)
            if pr:
                date = (
                    pr.get("created_at", "").split("T")[0]
                    if pr.get("created_at")
                    else ""
                )
                merged = "✅ Merged" if pr.get("is_merged") else "🔄 Open"
                lines.append(f"    {date} : PR #{pr_num} ({merged})")

        if issue.get("state") == "closed":
            closed_date = (
                issue.get("closed_at", "").split("T")[0]
                if issue.get("closed_at")
                else ""
            )
            lines.append(f"    {closed_date} : Issue Closed")

        lines.append("```")
        return "\n".join(lines)

    def generate_pr_impact_diagram(self, pr_number: int) -> Optional[str]:
        """Generate impact diagram for a PR"""
        pr = self._prs_cache.get(pr_number)
        if not pr:
            return None

        lines = [
            "```mermaid",
            "graph TB",
            f"    %% PR #{pr_number} Impact Analysis",
            "",
        ]

        pr_id = f"PR{pr_number}"
        pr_title = self._truncate(pr.get("title", ""), 30)
        merged = "✅ Merged" if pr.get("is_merged") else "🔄 Open"

        lines.append(f"    {pr_id}[{merged} PR #{pr_number}<br/>{pr_title}]")
        lines.append("")

        changed_files = pr.get("changed_files", [])[:10]
        if changed_files:
            lines.append(
                f'    subgraph ChangedFiles["📝 Changed Files ({len(changed_files)})"]'
            )
            for file in changed_files[:5]:
                file_id = self._sanitize_id(file)
                file_name = file.split("/")[-1]
                lines.append(f"        {file_id}[{file_name}]")
            lines.append("    end")
            lines.append(f"    {pr_id} --> ChangedFiles")
            lines.append("")

        linked_issues = pr.get("linked_issues", [])
        if linked_issues:
            lines.append(f'    subgraph LinkedIssues["🐛 Fixes Issues"]')
            for issue_num in linked_issues[:3]:
                issue = self._issues_cache.get(issue_num)
                if issue:
                    issue_id = f"Issue{issue_num}"
                    issue_title = self._truncate(issue.get("title", ""), 25)
                    lines.append(
                        f"        {issue_id}[Issue #{issue_num}<br/>{issue_title}]"
                    )
            lines.append("    end")
            lines.append(f"    {pr_id} --> LinkedIssues")
            lines.append("")

        commits = pr.get("commits", [])[:5]
        if commits:
            lines.append(f'    subgraph Commits["📝 Commits ({len(commits)})"]')
            for commit_sha in commits[:3]:
                commit = self._commits_cache.get(commit_sha)
                if commit:
                    commit_id = self._sanitize_id(commit_sha[:7])
                    msg = self._truncate(commit.get("message", ""), 20)
                    lines.append(f"        {commit_id}[{commit_sha[:7]}<br/>{msg}]")
            lines.append("    end")
            lines.append(f"    {pr_id} --> Commits")

        lines.append("```")
        return "\n".join(lines)

        return "\n".join(lines)

    def generate_feature_flow_diagram(self, feature_keywords: List[str]) -> str:
        """Generate flow diagram for a feature"""
        lines = [
            "```mermaid",
            "flowchart TD",
            f"    %% Feature Flow: {', '.join(feature_keywords)}",
            "",
        ]

        relevant_chunks = []
        for chunk in self.chunks:
            content = chunk.get("content", "").lower()
            keywords_str = " ".join(chunk.get("keywords", [])).lower()

            if any(
                kw.lower() in content or kw.lower() in keywords_str
                for kw in feature_keywords
            ):
                relevant_chunks.append(chunk)

        relevant_chunks.sort(key=lambda x: x.get("importance_score", 0), reverse=True)
        relevant_chunks = relevant_chunks[:10]

        if not relevant_chunks:
            lines.append("    NoData[No data found for this feature]")
            lines.append("```")
            return "\n".join(lines)

        lines.append("    Start([User Action]) --> Entry")

        prev_node = "Entry"
        for idx, chunk in enumerate(relevant_chunks):
            node_id = f"Step{idx}"

            if chunk.get("chunk_type") == "function":
                label = f"⚙️ {chunk.get('function_name', 'Function')}"
            elif chunk.get("chunk_type") == "class":
                label = f"🏗️ {chunk.get('class_name', 'Class')}"
            else:
                label = chunk.get("file_path", "unknown").split("/")[-1]

            lines.append(f'    {node_id}["{label}"]')
            lines.append(f"    {prev_node} --> {node_id}")
            prev_node = node_id

        lines.append(f"    {prev_node} --> End([Response])")
        lines.append("```")
        return "\n".join(lines)

    def generate_bug_investigation_diagram(self, keywords: List[str]) -> str:
        """Generate bug investigation diagram"""
        lines = [
            "```mermaid",
            "graph TB",
            f"    %% Bug Investigation: {', '.join(keywords)}",
            "",
        ]

        related_issues = []
        for issue_num, issue in self._issues_cache.items():
            title = issue.get("title", "").lower()
            body = issue.get("body", "").lower()

            if any(kw.lower() in title or kw.lower() in body for kw in keywords):
                related_issues.append(issue)

        if not related_issues:
            lines.append("    NoIssues[No related issues found]")
            lines.append("```")
            return "\n".join(lines)

        open_issues = [i for i in related_issues if i.get("state") == "open"]
        closed_issues = [i for i in related_issues if i.get("state") == "closed"]

        lines.append("    Bug[🐛 Bug Investigation]")
        lines.append("")

        if open_issues:
            lines.append('    subgraph OpenIssues["🔴 Open Issues"]')
            for issue in open_issues[:3]:
                issue_id = f"Open{issue.get('number')}"
                title = self._truncate(issue.get("title", ""), 25)
                lines.append(f"        {issue_id}[#{issue.get('number')}: {title}]")
            lines.append("    end")
            lines.append("    Bug --> OpenIssues")
            lines.append("")

        if closed_issues:
            lines.append('    subgraph ClosedIssues["✅ Resolved"]')
            for issue in closed_issues[:3]:
                issue_id = f"Closed{issue.get('number')}"
                title = self._truncate(issue.get("title", ""), 25)
                lines.append(f"        {issue_id}[#{issue.get('number')}: {title}]")

                for pr_num in issue.get("referenced_prs", [])[:1]:
                    pr_id = f"PR{pr_num}"
                    lines.append(f"        {pr_id}[PR #{pr_num}]")
                    lines.append(f"        {issue_id} -.->|fixed by| {pr_id}")

            lines.append("    end")
            lines.append("    Bug --> ClosedIssues")

        lines.append("```")
        return "\n".join(lines)

    def _classify_by_layer(self) -> Dict[str, List[str]]:
        """Classify files by architectural layer"""
        layers = defaultdict(list)

        for chunk in self.chunks:
            file_path = chunk.get("file_path", "")
            if not file_path:
                continue

            path_lower = file_path.lower()

            if any(
                x in path_lower for x in ["view", "ui", "component", "widget", "screen"]
            ):
                layers["presentation"].append(file_path)
            elif any(
                x in path_lower for x in ["api", "endpoint", "route", "controller"]
            ):
                layers["api"].append(file_path)
            elif any(x in path_lower for x in ["service", "business", "logic"]):
                layers["service"].append(file_path)
            elif any(
                x in path_lower for x in ["model", "entity", "database", "repository"]
            ):
                layers["data"].append(file_path)
            elif any(x in path_lower for x in ["util", "helper", "common", "shared"]):
                layers["utility"].append(file_path)
            else:
                layers["utility"].append(file_path)

        for layer in layers:
            layers[layer] = list(set(layers[layer]))

        return dict(layers)

    def _create_diagram_index(self) -> str:
        """Create searchable index of available diagrams"""
        index = {
            "static_diagrams": [
                {
                    "type": "architecture",
                    "description": "Overall architecture overview",
                },
                {
                    "type": "layer_architecture",
                    "description": "Layered architecture diagram",
                },
                {
                    "type": "technical_debt",
                    "description": "Technical debt and workarounds",
                },
                {"type": "api_routes", "description": "API endpoints and routes"},
                {"type": "onboarding_flow", "description": "Developer onboarding flow"},
                {"type": "file_dependencies", "description": "File dependency graph"},
                {
                    "type": "developer_ownership",
                    "description": "Code ownership by developers",
                },
            ],
            "dynamic_diagrams": [
                {
                    "type": "issue_timeline",
                    "description": "Timeline for a specific issue",
                    "query_patterns": [
                        "show timeline for issue",
                        "issue history",
                        "what happened with issue",
                    ],
                },
                {
                    "type": "pr_impact",
                    "description": "Impact analysis for a pull request",
                    "query_patterns": ["what did pr change", "pr impact", "show pr"],
                },
                {
                    "type": "feature_flow",
                    "description": "Code flow for a feature",
                    "query_patterns": [
                        "how does .* work",
                        "explain .* flow",
                        "trace .*",
                    ],
                },
                {
                    "type": "bug_investigation",
                    "description": "Related bugs and fixes",
                    "query_patterns": ["bugs related to", "show bugs", "issues with"],
                },
            ],
            "available_issues": list(self._issues_cache.keys())[:20],
            "available_prs": list(self._prs_cache.keys())[:20],
        }

        return json.dumps(index, indent=2)

    def _sanitize_id(self, text: str) -> str:
        """Sanitize text for Mermaid node ID"""
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", text)
        sanitized = re.sub(r"_+", "_", sanitized)
        if sanitized and not sanitized.isalpha():
            sanitized = "n" + sanitized
        return sanitized[:50]

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis"""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."


    def generate_architecture_diagram(self) -> str:
        """Generate architecture overview from knowledge graph"""
        lines = [
            "```mermaid",
            "graph TB",
            "    %% Architecture Overview - Key Components",
            "",
        ]

        # Get high-importance chunks (entry points, APIs, core components)
        important_chunks = [c for c in self.chunks if c.get("importance_score", 0) >= 2.0][
            :30
        ]

        if not important_chunks:
            # Fallback to any chunks
            important_chunks = self.chunks[:30]

        if not important_chunks:
            lines.append("    EmptyState[No architecture data detected]")
            lines.append("```")
            return "\n".join(lines)

        # Group by category
        by_category = defaultdict(list)
        for chunk in important_chunks:
            category = chunk.get("category", "general")
            by_category[category].append(chunk)

        # Create subgraphs by category
        for category, chunks in list(by_category.items())[:6]:
            if not chunks:
                continue

            cat_id = self._sanitize_id(category)
            cat_label = category.replace("_", " ").title()

            lines.append(f'    subgraph {cat_id}["{cat_label}"]')

            for chunk in chunks[:5]:
                chunk_id = self._sanitize_id(chunk.get("chunk_id", "unknown"))

                if chunk.get("file_path"):
                    label = chunk["file_path"].split("/")[-1]
                elif chunk.get("title"):
                    label = self._truncate(chunk["title"], 20)
                else:
                    label = chunk.get("chunk_id", "unknown").split("_")[-1]

                chunk_type = chunk.get("chunk_type", "unknown")
                icon = {
                    "code": "💻",
                    "function": "⚙️",
                    "class": "🏗️",
                    "documentation": "📚",
                    "api_endpoint": "🌐",
                    "config": "⚙️",
                }.get(chunk_type, "📄")

                score = chunk.get("importance_score", 0)
                lines.append(f"        {chunk_id}[{icon} {label}<br/>⭐{score:.1f}]")

            lines.append("    end")
            lines.append("")

        # Add relationships between chunks
        edges_added = set()
        for chunk in important_chunks[:15]:
            chunk_id = self._sanitize_id(chunk.get("chunk_id", ""))
            related = chunk.get("related_chunks", [])

            for related_id in related[:2]:
                related_chunk = next(
                    (c for c in important_chunks if c.get("chunk_id") == related_id), None
                )
                if related_chunk:
                    related_chunk_id = self._sanitize_id(related_id)
                    edge_key = tuple(sorted([chunk_id, related_chunk_id]))

                    if edge_key not in edges_added:
                        lines.append(f"    {chunk_id} -.-> {related_chunk_id}")
                        edges_added.add(edge_key)

        lines.append("```")
        return "\n".join(lines)


    def generate_onboarding_flow(self) -> str:
        """Generate onboarding flow diagram"""
        lines = [
            "```mermaid",
            "flowchart TD",
            "    %% Developer Onboarding Flow",
            "    Start([🚀 New Developer]) --> Setup",
            "",
        ]

        # Get onboarding chunks
        onboarding_chunks = [
            c for c in self.chunks if "onboarding" in c.get("semantic_tags", [])
        ]

        if not onboarding_chunks:
            # Fallback: use documentation and setup chunks
            onboarding_chunks = [
                c
                for c in self.chunks
                if c.get("category") in ["setup_configuration", "documentation"]
            ][:20]

        # Categorize by category
        categories = defaultdict(list)
        for chunk in onboarding_chunks:
            cat = chunk.get("category", "general")
            categories[cat].append(chunk)

        # Create flow
        step_map = {
            "setup_configuration": ("Setup", "⚙️ Setup Environment", "setupColor"),
            "documentation": ("Docs", "📚 Read Documentation", "docsColor"),
            "code_implementation": ("Code", "💻 Understand Code", "codeColor"),
            "api_documentation": ("API", "📡 Learn APIs", "apiColor"),
            "architecture": ("Arch", "🏗️ Study Architecture", "archColor"),
            "troubleshooting": ("Debug", "🐛 Debug Issues", "debugColor"),
        }

        prev_step = "Start"
        created_steps = []

        for cat, (step_id, label, color_class) in step_map.items():
            if cat in categories:
                count = len(categories[cat])
                lines.append(
                    f'    {prev_step} --> {step_id}["{label}<br/>({count} resources)"]'
                )
                lines.append(f"    class {step_id} {color_class}")
                created_steps.append(step_id)
                prev_step = step_id

        # If no steps created, add generic steps
        if not created_steps:
            lines.append("    Start --> ReadDocs[📚 Read Documentation]")
            lines.append("    ReadDocs --> ExploreCode[💻 Explore Codebase]")
            lines.append("    ExploreCode --> FirstTask[🎯 Pick First Task]")
            lines.append("    FirstTask --> Ready")
            prev_step = "FirstTask"

        lines.append(f"    {prev_step} --> Ready([✅ Ready to Contribute])")

        # Add sub-steps for setup if available
        if "setup_configuration" in categories:
            setup_chunks = categories["setup_configuration"][:3]
            lines.append("")
            for idx, chunk in enumerate(setup_chunks):
                title = chunk.get("title") or chunk.get("section_header", "Setup Step")
                title = self._truncate(title, 25)
                step_id = f"SetupSub{idx}"
                lines.append(f"    Setup -.-> {step_id}[{title}]")

        lines.append("```")
        return "\n".join(lines)


    def generate_file_dependencies_diagram(self) -> str:
        """Generate file dependency diagram"""
        lines = ["```mermaid", "graph TD", "    %% File Dependencies", ""]

        dependencies = self.relationships.get("file_dependencies", [])

        if not dependencies:
            # Try to extract from chunks
            file_imports = defaultdict(set)
            for chunk in self.chunks:
                if chunk.get("file_path"):
                    source = chunk["file_path"]
                    mentioned = chunk.get("mentioned_files", [])
                    for target in mentioned:
                        if target != source:
                            file_imports[source].add(target)

            # Convert to dependency list
            dependencies = []
            for source, targets in file_imports.items():
                for target in targets:
                    dependencies.append(
                        {
                            "source_file": source,
                            "target_file": target,
                            "dependency_type": "import",
                        }
                    )

        if not dependencies:
            lines.append("    NoData[No file dependencies detected]")
            lines.append("```")
            return "\n".join(lines)

        # Limit to top 20 dependencies
        dependencies = dependencies[:20]

        # Count dependencies per file to find most connected
        dep_count = defaultdict(int)
        for dep in dependencies:
            src = dep.get("source_file", "")
            tgt = dep.get("target_file", "")
            dep_count[src] += 1
            dep_count[tgt] += 1

        # Get most connected files
        top_files = sorted(dep_count.items(), key=lambda x: x[1], reverse=True)[:15]
        included_files = set(f for f, _ in top_files)

        # Add nodes with connection counts
        for file_path, count in top_files:
            file_id = self._sanitize_id(file_path)
            file_name = file_path.split("/")[-1]

            # Color by connection count
            if count > 5:
                lines.append(f"    {file_id}[{file_name}<br/>{count} deps]:::highDep")
            elif count > 3:
                lines.append(f"    {file_id}[{file_name}<br/>{count} deps]:::medDep")
            else:
                lines.append(f"    {file_id}[{file_name}<br/>{count} deps]")

        lines.append("")

        # Add edges
        added_edges = set()
        for dep in dependencies:
            src = dep.get("source_file", "")
            tgt = dep.get("target_file", "")

            if src in included_files and tgt in included_files:
                src_id = self._sanitize_id(src)
                tgt_id = self._sanitize_id(tgt)
                edge_key = (src_id, tgt_id)

                if edge_key not in added_edges:
                    dep_type = dep.get("dependency_type", "depends")
                    lines.append(f"    {src_id} -->|{dep_type}| {tgt_id}")
                    added_edges.add(edge_key)

        lines.append("```")
        return "\n".join(lines)


    def generate_ownership_diagram(self) -> str:
        """Generate developer ownership diagram"""
        lines = ["```mermaid", "graph LR", "    %% Developer Ownership Map", ""]

        ownership = self.relationships.get("developer_ownership", {}) or {}
        file_owners = ownership.get("file_owners", {}) or {}
        top_contributors = ownership.get("top_contributors", []) or []

        if not top_contributors and self.raw_data:
            # Extract from commits
            commit_authors = defaultdict(int)
            for commit in self.raw_data.get("commits", [])[:200]:
                author = commit.get("author", {}).get("name", "unknown")
                if author and author != "unknown":
                    commit_authors[author] += 1

            top_contributors = [
                {"author": a, "commits": c}
                for a, c in sorted(
                    commit_authors.items(), key=lambda x: x[1], reverse=True
                )[:5]
            ]

        if not top_contributors:
            lines.append("    NoData[No developer data available]")
            lines.append("```")
            return "\n".join(lines)

        # Add developer nodes
        for contrib in top_contributors[:5]:
            author = contrib.get("author", "unknown")
            commits = contrib.get("commits", 0)
            dev_id = self._sanitize_id(author)
            lines.append(f"    {dev_id}[👤 {author}<br/>{commits} commits]:::devNode")

        lines.append("")

        # Add file ownership
        added_files = set()
        if file_owners:
            for file_path, owner in list(file_owners.items())[:15]:
                # Only show files owned by top contributors
                if any(c.get("author") == owner for c in top_contributors):
                    file_id = self._sanitize_id(file_path)
                    file_name = file_path.split("/")[-1]
                    owner_id = self._sanitize_id(owner)

                    if file_path not in added_files:
                        lines.append(f"    {file_id}[📄 {file_name}]:::fileNode")
                        lines.append(f"    {owner_id} -->|owns| {file_id}")
                        added_files.add(file_path)
        else:
            # Fallback: show relationship with top files from chunks
            top_files = defaultdict(list)
            for chunk in self.chunks[:50]:
                author = chunk.get("metadata", {}).get("last_modified_by")
                file_path = chunk.get("file_path")
                if author and file_path:
                    top_files[author].append(file_path)

            for contrib in top_contributors[:3]:
                author = contrib.get("author")
                if author in top_files:
                    owner_id = self._sanitize_id(author)
                    for file_path in list(dict.fromkeys(top_files[author]))[:3]:
                        file_id = self._sanitize_id(file_path)
                        file_name = file_path.split("/")[-1]

                        if file_path not in added_files:
                            lines.append(f"    {file_id}[📄 {file_name}]:::fileNode")
                            lines.append(f"    {owner_id} --> {file_id}")
                            added_files.add(file_path)

        lines.append("```")
        return "\n".join(lines)

    def _create_combined_diagram(self, diagrams: Dict[str, str]) -> str:
        """Create combined markdown file"""
        lines = [
            "# Repository Analysis Diagrams",
            "",
            "## 1. Layered Architecture",
            diagrams.get("layer_architecture", ""),
            "",
            "## 2. Architecture Overview",
            diagrams.get("architecture", ""),
            "",
            "## 3. Technical Debt Map",
            diagrams.get("technical_debt", ""),
            "",
            "## 4. API Routes",
            diagrams.get("api_routes", ""),
            "",
            "## 5. Developer Onboarding Flow",
            diagrams.get("onboarding_flow", ""),
            "",
            "## 6. File Dependencies",
            diagrams.get("file_dependencies", ""),
            "",
            "## 7. Developer Ownership",
            diagrams.get("developer_ownership", ""),
        ]

        return "\n".join(lines)

    def save_diagrams(self, output_dir: str = "./processed") -> Dict[str, str]:
        """Save all diagrams to files"""
        import os

        diagrams = self.generate_all_diagrams()
        saved_files = {}

        diagrams_dir = os.path.join(output_dir, "diagrams")
        os.makedirs(diagrams_dir, exist_ok=True)

        for name, content in diagrams.items():
            if name == "combined":
                file_path = os.path.join(output_dir, "DIAGRAMS.md")
            elif name == "diagram_index":
                file_path = os.path.join(diagrams_dir, "index.json")
            else:
                file_path = os.path.join(diagrams_dir, f"{name}.mmd")

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            saved_files[name] = file_path

        return saved_files
