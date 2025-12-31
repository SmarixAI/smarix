import json
import uuid
import random
from pathlib import Path

# ---------------- CONFIG ---------------- #

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

INPUT_FILE = find_data_file()
EMPLOYEES_FILE = OUTPUT_DIR / "1employees_with_ids.json"
USERS_FILE = BASE_DIR / "data" / "Admin" / "users.json"
if not USERS_FILE.exists():
    # Try alternative paths
    possible_paths = [
        BASE_DIR / "backend" / "data" / "Admin" / "users.json",
        Path(r"C:\Users\vishalke\Desktop\AI007\super-employee\backend\data\Admin\users.json"),
    ]
    for path in possible_paths:
        if path.exists():
            USERS_FILE = path
            break

# --------------------------------------- #


def generate_employee_id(existing_ids: set) -> str:
    """Generate a unique employee ID"""
    while True:
        raw = uuid.uuid4().int
        emp_id = f"EMP-{str(raw)[-6:]}"
        if emp_id not in existing_ids:
            return emp_id


def generate_dummy_employee_data():
    """Generate dummy data for employee"""
    roles = [
        "Frontend Engineer",
        "Backend Engineer",
        "Full Stack Engineer",
        "DevOps Engineer",
        "QA Engineer",
        "Mobile Developer",
        "Data Engineer",
        "Security Engineer",
        "Product Manager",
        "Technical Lead"
    ]
    
    risks = ["low", "medium", "high"]
    statuses = ["active"]  # Mostly active
    
    return {
        "role": random.choice(roles),
        "risk": random.choice(risks),
        "status": random.choice(statuses),
        "lastDay": None  # Most employees don't have a last day set
    }


def get_random_designation():
    """Get a random designation for new employees"""
    designations = [
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Engineer",
        "DevOps Engineer",
        "QA Engineer",
        "Mobile Developer",
        "Data Engineer",
        "Security Engineer",
        "Product Manager",
        "Technical Lead",
        "Software Engineer",
        "Senior Software Engineer"
    ]
    return random.choice(designations)


def load_users_json():
    """Load users.json file"""
    if not USERS_FILE.exists():
        return {"users": []}
    
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Warning: Could not load users.json: {e}")
        return {"users": []}


def user_exists_in_users_json(users_data, name):
    """Check if a user with the given name exists in users.json"""
    for user in users_data.get("users", []):
        if user.get("name", "").lower() == name.lower() or user.get("username", "").lower() == name.lower():
            return True
    return False


def add_missing_users_to_users_json(unique_users):
    """Add missing users to users.json"""
    users_data = load_users_json()
    existing_names = {user.get("name", "").lower() or user.get("username", "").lower() for user in users_data.get("users", [])}
    
    # Get all existing employee IDs to avoid duplicates
    existing_employee_ids = {user.get("employeeId") for user in users_data.get("users", []) if user.get("employeeId")}
    
    new_users_added = 0
    
    for user_name, user_data in unique_users.items():
        name = user_data.get("name", user_name)
        
        # Check if user already exists (by name or username)
        if name.lower() in existing_names:
            continue
        
        # Generate employee ID
        emp_id = generate_employee_id(existing_employee_ids)
        existing_employee_ids.add(emp_id)
        
        # Generate random designation
        designation = get_random_designation()
        
        # Create new user entry
        new_user = {
            "username": name,
            "password": name,  # Password same as username (following existing pattern)
            "role": "employee",
            "status": "general",
            "employeeId": emp_id,
            "name": name,
            "designation": designation,
            "managers": []  # Empty managers list for new employees
        }
        
        users_data["users"].append(new_user)
        existing_names.add(name.lower())
        new_users_added += 1
        print(f"  ➕ Added new user: {name} ({designation})")
    
    if new_users_added > 0:
        # Ensure directory exists
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write back to file
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Added {new_users_added} new user(s) to {USERS_FILE}")
    else:
        print(f"✅ All users already exist in {USERS_FILE}")
    
    return new_users_added


def extract_unique_users(input_path: Path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    prs = data.get("prs", [])

    unique_users = {}
    for pr in prs:
        user = pr.get("user")
        if not user:
            continue

        login = user.get("login")
        if not login:
            continue

        if login not in unique_users:
            unique_users[login] = {
                "name": login, 
                "html_url": user.get("html_url")
            }

    return unique_users


def get_employee_id_from_users_json(users_data, name):
    """Get employeeId from users.json for a given name"""
    for user in users_data.get("users", []):
        user_name = user.get("name", "") or user.get("username", "")
        if user_name.lower() == name.lower():
            return user.get("employeeId")
    return None


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: extract unique users
    print("📂 Extracting unique users from PRs...")
    unique_users = extract_unique_users(INPUT_FILE)
    print(f"✓ Found {len(unique_users)} unique users")

    # Step 2: Add missing users to users.json
    print(f"\n🔍 Checking users.json for missing employees...")
    add_missing_users_to_users_json(unique_users)

    # Step 3: Reload users.json to get all employeeIds (including newly added ones)
    users_data = load_users_json()

    # Step 4: Create employees list with employee_id
    print(f"\n📝 Creating employees list with employee IDs...")
    employees = []

    for user_name, user_data in unique_users.items():
        name = user_data.get("name", user_name)
        
        # Get employeeId from users.json
        employee_id = get_employee_id_from_users_json(users_data, name)
        
        if not employee_id:
            print(f"⚠️  Warning: Could not find employeeId for {name} in users.json")
            # Generate a temporary ID if not found (shouldn't happen after adding to users.json)
            existing_ids = {user.get("employeeId") for user in users_data.get("users", []) if user.get("employeeId")}
            employee_id = generate_employee_id(existing_ids)
            print(f"  Generated temporary ID: {employee_id}")
        
        # Generate dummy employee data
        dummy_data = generate_dummy_employee_data()

        employees.append({
            "name": name,
            "html_url": user_data.get("html_url", ""),
            "risk": dummy_data["risk"],
            "employeeId": employee_id  # Add employeeId to output
        })

    employees_output = {
        "total_employees": len(employees),
        "employees": employees
    }

    with open(EMPLOYEES_FILE, "w", encoding="utf-8") as f:
        json.dump(employees_output, f, indent=2)

    print(f"✅ Employees with IDs saved to: {EMPLOYEES_FILE}")
    print(f"   Total employees: {len(employees)}")


if __name__ == "__main__":
    main()
