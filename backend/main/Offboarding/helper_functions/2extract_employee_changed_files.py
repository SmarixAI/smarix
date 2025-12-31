import json
from collections import defaultdict
from pathlib import Path

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
OUTPUT_FILE = OUTPUT_DIR / "2employee_changed_files.json"

# ================= HELPERS =================

def categorize_file(path: str) -> str:
    p = path.lower()
    if p.startswith(("frontend/", "lib/", "web/")):
        return "frontend"
    if p.startswith(("backend/", "server/", "api/")):
        return "backend"
    if p.startswith((
        "android/", "ios/", ".github/", "infra/",
        "docker", "pubspec.yaml", ".gitignore"
    )):
        return "infra"
    return "other"


def is_critical_file(path: str) -> bool:
    keywords = ["auth", "notification", "config", "security", "permission"]
    return any(k in path.lower() for k in keywords)


def compute_risk(files):
    risk = 0
    categories = set()

    for f in files:
        categories.add(f["category"])

        if f["category"] == "infra":
            risk += 25
        elif f["category"] == "backend":
            risk += 15
        elif f["category"] == "frontend":
            risk += 8

        if f["single_owner"]:
            risk += 20

        if is_critical_file(f["path"]):
            risk += 10

    if len(files) > 10:
        risk += 15

    return min(risk, 100)


def main():
    """Main execution function"""
    print("📂 Loading data files...")
    
    employees = json.loads(EMPLOYEES_FILE.read_text(encoding="utf-8"))["employees"]
    prs = json.loads(PRS_FILE.read_text(encoding="utf-8"))["prs"]
    
    print(f"✓ Loaded {len(employees)} employees")
    print(f"✓ Loaded {len(prs)} PRs")
    
    # Map name (formerly login) to employee data
    name_to_employee = {e.get("name", e.get("login", "")).lower(): e for e in employees}
    
    # ================= GLOBAL FILE OWNERSHIP =================
    
    file_owners = defaultdict(set)
    
    for pr in prs:
        login = pr.get("user", {}).get("login", "").lower()
        if login not in name_to_employee:
            continue
    
        emp_name = name_to_employee[login].get("name", login)
    
        for f in pr.get("changed_files", []):
            if "filename" in f:
                file_owners[f["filename"]].add(emp_name)
    
    single_owner_files = {
        f for f, owners in file_owners.items() if len(owners) == 1
    }
    
    # ================= EMPLOYEE → PR AGG =================
    
    employees_out = defaultdict(lambda: {
        "name": "",
        "html_url": "",
        "risk": "medium",
        "employeeId": None,
        "tasks": {}
    })
    
    for pr in prs:
        user = pr.get("user", {})
        login = user.get("login", "").lower()
        if login not in name_to_employee:
            continue
    
        emp = name_to_employee[login]
        emp_name = emp.get("name", login)
    
        bucket = employees_out[emp_name]
        bucket["name"] = emp.get("name", emp.get("login", ""))
        bucket["html_url"] = emp.get("html_url", "")
        bucket["risk"] = emp.get("risk", "medium")
        bucket["employeeId"] = emp.get("employeeId") or emp.get("employee_id")  # Get employeeId from input file (support both formats)
    
        pr_number = pr["number"]
    
        if pr_number not in bucket["tasks"]:
            bucket["tasks"][pr_number] = {
                "pr_number": pr_number,
                "title": pr.get("title", ""),
                "files": [],
            }
    
        for f in pr.get("changed_files", []):
            filename = f.get("filename")
            if not filename:
                continue
    
            bucket["tasks"][pr_number]["files"].append({
                "path": filename,
                "category": categorize_file(filename),
                "single_owner": filename in single_owner_files
            })
    
    # ================= BUILD OUTPUT =================
    
    print("\n🔧 Processing employee changed files...")
    
    output = {
        "total_employees": len(employees_out),
        "employees": []
    }
    
    for emp in employees_out.values():
        emp_name = emp["name"]
        
        # Initialize tasks object with "ai" category
        ai_tasks = []
        ai_task_counter = 1
        
        for w in emp["tasks"].values():
            files = w["files"]
            # Generate task ID: "{name}-a{number}" format (e.g., "john-a1", "john-a2")
            task_id = f"{emp_name}-a{ai_task_counter}"
            task = {
                "id": task_id,
                "pr_number": w["pr_number"],
                "title": w["title"],
                "risk_score": compute_risk(files),
                "single_owner_files": [
                    f["path"] for f in files if f["single_owner"]
                ],
                "changed_files": [f["path"] for f in files]
            }
            ai_tasks.append(task)
            ai_task_counter += 1
        
        # Sort tasks by risk score (highest first)
        ai_tasks.sort(key=lambda x: -x["risk_score"])
        
        # Add employee with their tasks organized by category - name, html_url, risk, employeeId, tasks
        output["employees"].append({
            "name": emp.get("name", "Unknown"),
            "html_url": emp.get("html_url", ""),
            "risk": emp.get("risk", "medium"),
            "employeeId": emp.get("employeeId"),  # Include employeeId in output
            "tasks": {
                "ai": ai_tasks
            }
        })
    
    # ================= WRITE =================
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8"
    )
    
    print(f"\n✅ Enriched offboarding data generated")
    print(f"   Output: {OUTPUT_FILE}")
    print(f"   Total employees: {len(output['employees'])}")


if __name__ == "__main__":
    main()
