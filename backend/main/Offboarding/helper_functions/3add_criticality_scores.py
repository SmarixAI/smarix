
import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# ================= PATHS =================

# Find the data directory relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "DataCollectionFromGit"
OUTPUT_DIR = BASE_DIR / "data" / "Offboarding"
if not OUTPUT_DIR.exists():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Find any JSON file in DataCollectionFromGit folder
def find_data_file():
    """Find any JSON file in the DataCollectionFromGit directory"""
    if not DATA_DIR.exists():
        # Try alternative paths
        possible_paths = [
            Path(r"C:\Users\vishalke\Desktop\AI007\super-employee\backend\data\DataCollectionFromGit"),
            BASE_DIR / "backend" / "data" / "DataCollectionFromGit",
            Path("data/DataCollectionFromGit"),
            Path("../data/DataCollectionFromGit"),
        ]
        for path in possible_paths:
            if path.exists():
                data_dir = path
                break
        else:
            raise FileNotFoundError(f"DataCollectionFromGit directory not found. Tried: {DATA_DIR}")
    else:
        data_dir = DATA_DIR
    
    # Find any JSON file in the directory
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {data_dir}")
    
    # Use the first JSON file found
    return json_files[0]

EMPLOYEES_FILE = OUTPUT_DIR / "1employees_with_ids.json"
PRS_FILE = find_data_file()
INPUT_FILE = OUTPUT_DIR / "2employee_changed_files.json"
OUTPUT_FILE = OUTPUT_DIR / "3employee_prs_with_criticality.json"

# ================= HELPERS =================

def parse_date(date_str):
    """Parse date and return ISO format"""
    if not date_str:
        return None
    try:
        if isinstance(date_str, str):
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
    except:
        pass
    return date_str

def categorize_file(path: str) -> str:
    """Categorize file by path"""
    p = path.lower()
    if p.startswith(("frontend/", "lib/", "web/", "src/screens", "src/components", "ui/")):
        return "frontend"
    if p.startswith(("backend/", "server/", "api/", "service/")):
        return "backend"
    if p.startswith(("android/", "ios/", ".github/", "infra/", "docker", "pubspec", ".gitignore", "workflow", "ci/", "cd/")):
        return "infra"
    if p.endswith((".md", ".txt")) or "readme" in p or "doc" in p:
        return "docs"
    if "test" in p or p.endswith(("_test.dart", ".test.js", "test.py")):
        return "test"
    return "other"

def is_critical_file(path: str) -> bool:
    """Check if file is critical"""
    keywords = ["auth", "notification", "config", "security", "permission", "api", "database", "payment", "billing"]
    return any(k in path.lower() for k in keywords)

def detect_file_status(file_path, commits_data):
    """Detect if file is NEW, MODIFIED, or DELETED"""
    appearances = sum(1 for c in commits_data if file_path in c.get('changed_files', []))

    for commit in commits_data:
        if file_path in commit.get('changed_files', []):
            msg = commit.get('message', '').lower()
            if 'delet' in msg or 'remov' in msg:
                return "DELETED"

    if appearances == 1 and commits_data and file_path in commits_data[0].get('changed_files', []):
        msg = commits_data[0].get('message', '').lower()
        if 'add' in msg or 'creat' in msg or 'new' in msg or 'initial' in msg:
            return "NEW"

    return "MODIFIED"

def calculate_criticality_score(work_data, commits_timeline, files_detail):
    """
    Calculate criticality score 0-100
    Higher score = more critical for handover
    """
    score = 0

    # Factor 1: Number of commits
    commit_count = len(commits_timeline)
    if commit_count > 10:
        score += 20
    elif commit_count > 5:
        score += 10
    elif commit_count > 2:
        score += 5

    # Factor 2: Duration
    duration = work_data.get('duration_days', 0)
    if duration > 14:
        score += 15
    elif duration > 7:
        score += 8
    elif duration > 3:
        score += 4

    # Factor 3: Critical files
    critical_count = sum(1 for f in files_detail if f.get('critical'))
    score += critical_count * 10

    # Factor 4: Single owner files
    single_owner_count = sum(1 for f in files_detail if f.get('single_owner'))
    score += single_owner_count * 8

    # Factor 5: Files modified multiple times
    rework_count = sum(1 for f in files_detail if f.get('changes_count', 0) > 2)
    score += rework_count * 5

    # Factor 6: Backend files
    backend_count = sum(1 for f in files_detail if f.get('category') == 'backend')
    if backend_count > 3:
        score += 15
    elif backend_count > 0:
        score += 8

    # Factor 7: New files
    new_files_count = sum(1 for f in files_detail if f.get('status') == 'NEW')
    if new_files_count > 5:
        score += 15
    elif new_files_count > 2:
        score += 10
    elif new_files_count > 0:
        score += 5

    # Factor 8: Total files touched
    total_files = len(files_detail)
    if total_files > 15:
        score += 10
    elif total_files > 8:
        score += 5

    return min(score, 100)

def main():
    """Main execution function"""
    # ================= LOAD DATA =================
    
    print("📂 Loading data files...")
    
    employees = json.loads(EMPLOYEES_FILE.read_text(encoding="utf-8"))["employees"]
    prs_data = json.loads(PRS_FILE.read_text(encoding="utf-8"))
    input_data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    
    prs = prs_data.get("prs", prs_data.get("pull_requests", []))
    all_commits = prs_data.get("commits", [])
    
    print(f"✓ Loaded {len(employees)} employees")
    print(f"✓ Loaded {len(prs)} PRs with commits")
    print(f"✓ Loaded {len(all_commits)} total commits")
    print(f"✓ Loaded previous stage output with {input_data.get('total_employees', 0)} employees")
    
    # Create mappings
    # Support both "name" and "login" for backward compatibility
    name_to_employee = {e.get("name", e.get("login", "")).lower(): e for e in employees}
    pr_number_to_data = {pr["number"]: pr for pr in prs}
    # Map commit SHA to full commit object
    commit_sha_to_data = {commit.get("sha", ""): commit for commit in all_commits if commit.get("sha")}
    
    # ================= ENRICH WITH CRITICALITY SCORES =================
    
    print("\n🔧 Adding criticality scores and commit details...")
    
    enriched_employees = []
    
    for emp_data in input_data.get("employees", []):
        # Use name as the identifier (no longer using employeeId)
        name = emp_data.get("name", "Unknown")
        if not name or name == "Unknown":
            continue

        enriched_tasks = []
        total_commits = 0
        total_files_touched = set()

        # Tasks are now nested under "tasks": { "ai": [...] }
        tasks_data = emp_data.get("tasks", {})
        ai_tasks = tasks_data.get("ai", []) if isinstance(tasks_data, dict) else []
        
        for work in ai_tasks:
            pr_number = work["pr_number"]
            pr_full_data = pr_number_to_data.get(pr_number)

            if not pr_full_data:
                # No PR data found, keep original with minimal score
                enriched_tasks.append({
                    **work,
                    "criticality_score": 0,
                    "state": "UNKNOWN",
                    "commit_summary": {
                        "total_commits": 0,
                        "commits_timeline": []
                    },
                    "files_aggregated": {
                        "total_unique_files": len(work.get("changed_files", [])),
                        "files_detail": []
                    }
                })
                continue

            # PRs have commits as array of SHA strings, need to map to full commit objects
            commit_shas = pr_full_data.get("commits", [])
            
            if not commit_shas:
                # No commits data, keep original with low score
                enriched_tasks.append({
                    **work,
                    "criticality_score": 5,
                    "state": pr_full_data.get("state", "UNKNOWN"),
                    "commit_summary": {
                        "total_commits": 0,
                        "commits_timeline": []
                    },
                    "files_aggregated": {
                        "total_unique_files": len(work.get("changed_files", [])),
                        "files_detail": []
                    }
                })
                continue

            # Map commit SHAs to full commit objects
            commits_raw = []
            for sha in commit_shas:
                if isinstance(sha, str) and sha in commit_sha_to_data:
                    commits_raw.append(commit_sha_to_data[sha])
                elif isinstance(sha, dict) and sha.get("sha"):
                    # Already a commit object
                    commits_raw.append(sha)

            if not commits_raw:
                # No valid commit objects found
                enriched_tasks.append({
                    **work,
                    "criticality_score": 5,
                    "state": pr_full_data.get("state", "UNKNOWN"),
                    "commit_summary": {
                        "total_commits": 0,
                        "commits_timeline": []
                    },
                    "files_aggregated": {
                        "total_unique_files": len(work.get("changed_files", [])),
                        "files_detail": []
                    }
                })
                continue

            # Process commits
            commits_timeline = []
            all_files_in_pr = defaultdict(lambda: {
                "commits_touching": [],
                "change_count": 0
            })

            # Use PR created_at as fallback date if commits don't have dates
            pr_created_date = parse_date(pr_full_data.get("created_at"))

            for commit in commits_raw:
                # Commits don't have date field, use PR date or None
                commit_date = pr_created_date  # Fallback to PR creation date
                author_info = commit.get("author", {})
                author_name = author_info.get("name", "Unknown") if isinstance(author_info, dict) else "Unknown"
                changed_files = commit.get("changed_files", [])

                commits_timeline.append({
                    "sha": commit.get("sha", "")[:8],
                    "message": commit.get("message", ""),
                    "date": commit_date,
                    "author": author_name,
                    "files_count": len(changed_files)
                })

                for file_path in changed_files:
                    all_files_in_pr[file_path]["commits_touching"].append(commit.get("sha", "")[:8])
                    all_files_in_pr[file_path]["change_count"] += 1
                    total_files_touched.add(file_path)

            # Sort commits by date if available, otherwise keep original order
            commits_timeline.sort(key=lambda x: (x.get("date") or "") if x.get("date") else "9999-99-99")

            # Build files detail
            files_detail = []
            for file_path, file_info in all_files_in_pr.items():
                status = detect_file_status(file_path, commits_raw)

                # Check if single owner from original data
                is_single_owner = file_path in work.get("single_owner_files", [])

                files_detail.append({
                    "path": file_path,
                    "status": status,
                    "changes_count": file_info["change_count"],
                    "category": categorize_file(file_path),
                    "single_owner": is_single_owner,
                    "critical": is_critical_file(file_path),
                    "commits": file_info["commits_touching"]
                })

            # Sort: critical first, then by change count
            files_detail.sort(key=lambda x: (not x["critical"], -x["changes_count"]))

            # Calculate dates and duration
            # Use PR dates if commit dates are not available
            first_commit_date = commits_timeline[0].get("date") if commits_timeline and commits_timeline[0].get("date") else pr_created_date
            last_commit_date = commits_timeline[-1].get("date") if commits_timeline and commits_timeline[-1].get("date") else parse_date(pr_full_data.get("updated_at") or pr_full_data.get("closed_at"))

            duration_days = 0
            if first_commit_date and last_commit_date:
                try:
                    d1 = datetime.strptime(first_commit_date, "%Y-%m-%d")
                    d2 = datetime.strptime(last_commit_date, "%Y-%m-%d")
                    duration_days = (d2 - d1).days
                    if duration_days < 0:
                        duration_days = 0
                except:
                    # If parsing fails, try to calculate from PR dates
                    pr_created = parse_date(pr_full_data.get("created_at"))
                    pr_updated = parse_date(pr_full_data.get("updated_at") or pr_full_data.get("closed_at"))
                    if pr_created and pr_updated:
                        try:
                            d1 = datetime.strptime(pr_created, "%Y-%m-%d")
                            d2 = datetime.strptime(pr_updated, "%Y-%m-%d")
                            duration_days = (d2 - d1).days
                            if duration_days < 0:
                                duration_days = 0
                        except:
                            pass

            pr_state = pr_full_data.get("state", "UNKNOWN")

            # Build work with duration for scoring
            work_with_duration = {
                **work,
                "state": pr_state,
                "duration_days": duration_days
            }

            # CALCULATE CRITICALITY SCORE
            criticality_score = calculate_criticality_score(
                work_with_duration, commits_timeline, files_detail
            )

            # Skip declined PRs
            if pr_state == "DECLINED":
                criticality_score = 0

            # Build enriched work entry
            enriched_work = {
                # Keep all existing fields from previous stage
                "pr_number": work["pr_number"],
                "title": work.get("title", ""),
                "risk_score": work.get("risk_score", 0),
                "single_owner_files": work.get("single_owner_files", []),
                "changed_files": work.get("changed_files", []),

                # NEW: Add criticality score
                "criticality_score": criticality_score,

                # NEW: Add PR metadata
                "state": pr_state,
                "created_date": parse_date(pr_full_data.get("created_at")),
                "merged_date": parse_date(pr_full_data.get("merged_at")),
                "duration_days": duration_days,

                # NEW: Add commit summary
                "commit_summary": {
                    "total_commits": len(commits_timeline),
                    "first_commit_date": first_commit_date,
                    "last_commit_date": last_commit_date,
                    "commits_timeline": commits_timeline
                },

                # NEW: Add files aggregation
                "files_aggregated": {
                    "total_unique_files": len(all_files_in_pr),
                    "new_files": sum(1 for f in files_detail if f['status'] == 'NEW'),
                    "modified_files": sum(1 for f in files_detail if f['status'] == 'MODIFIED'),
                    "deleted_files": sum(1 for f in files_detail if f['status'] == 'DELETED'),
                    "critical_files": [f['path'] for f in files_detail if f['critical']],
                    "files_detail": files_detail
                }
            }

            enriched_tasks.append(enriched_work)
            total_commits += len(commits_timeline)

        # Sort tasks by criticality score (highest first)
        enriched_tasks.sort(key=lambda x: -x.get('criticality_score', 0))

        # Add employee-level summary - keep name, html_url, risk, employeeId, tasks
        enriched_emp = {
            "name": name,
            "html_url": emp_data.get("html_url", ""),
            "risk": emp_data.get("risk", "medium"),
            "employeeId": emp_data.get("employeeId") or emp_data.get("employee_id"),  # Get employeeId from input file (support both formats)
            "tasks": enriched_tasks
        }

        enriched_employees.append(enriched_emp)

        # Show stats
        critical_prs = [w for w in enriched_tasks if w.get('criticality_score', 0) >= 70]
        high_prs = [w for w in enriched_tasks if 50 <= w.get('criticality_score', 0) < 70]

        print(f"  ✓ {name}: {len(enriched_tasks)} PRs | Critical: {len(critical_prs)} | High: {len(high_prs)} | Commits: {total_commits}")
    
    # ================= BUILD FINAL OUTPUT =================
    
    final_output = {
        "generated_at": datetime.now().isoformat(),
        "total_employees": len(enriched_employees),
        "employees": []
    }
    
    for emp in enriched_employees:
        emp_name = emp["name"]
        
        # Initialize tasks object with "ai" category
        ai_tasks = []
        ai_task_counter = 1
        
        for task in emp["tasks"]:
            # Generate task ID: "{name}-a{number}" format (e.g., "john-a1", "john-a2")
            task_id = f"{emp_name}-a{ai_task_counter}"
            task_with_id = {
                "id": task_id,
                **task
            }
            ai_tasks.append(task_with_id)
            ai_task_counter += 1
        
        # Sort tasks by criticality score (highest first)
        ai_tasks.sort(key=lambda x: -x.get('criticality_score', 0))
        
        # Add employee with their tasks organized by category - name, html_url, risk, employeeId, tasks
        final_output["employees"].append({
            "name": emp.get("name", "Unknown"),
            "html_url": emp.get("html_url", ""),
            "risk": emp.get("risk", "medium"),
            "employeeId": emp.get("employeeId"),  # Include employeeId in output
            "tasks": {
                "ai": ai_tasks
            }
        })
    
    # ================= WRITE OUTPUT =================
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(final_output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    print(f"\n✅ Enriched data with criticality scores written to:")
    print(f"   {OUTPUT_FILE}")
    print(f"\n📊 Summary:")
    print(f"   Total employees: {len(enriched_employees)}")
    
    # Calculate overall stats
    all_scores = [w['criticality_score'] for emp in enriched_employees for w in emp['tasks']]
    if all_scores:
        critical_count = sum(1 for s in all_scores if s >= 70)
        high_count = sum(1 for s in all_scores if 50 <= s < 70)
        medium_count = sum(1 for s in all_scores if 30 <= s < 50)
        low_count = sum(1 for s in all_scores if s < 30)
    
        print(f"   Total PRs: {len(all_scores)}")
        print(f"   Critical (70-100): {critical_count}")
        print(f"   High (50-69): {high_count}")
        print(f"   Medium (30-49): {medium_count}")
        print(f"   Low (0-29): {low_count}")
    
        print(f"\n💡 Next step: Use this data for LLM analysis")
        print(f"   Filter: criticality_score >= 50 for important handovers")


if __name__ == "__main__":
    main()