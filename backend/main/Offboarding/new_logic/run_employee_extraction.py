import json
import os
from backend.main.Offboarding.new_logic.finalcall_old1.json_loader import RepoJsonLoader
from backend.main.Offboarding.new_logic.finalcall_old.employee_aggregator import EmployeeAggregator


INPUT_FILE = "/Users/vishalkeshari/Desktop/smarix/backend/main/Offboarding/new_logic/taskwarrior-flutter.json"
OUTPUT_DIR = "/Users/vishalkeshari/Desktop/smarix/backend/main/Offboarding/new_logic/output"
EMPLOYEE_NAME = "inderjeet20"   # Change dynamically if needed


def main():

    print("Loading repository data...")
    repo_data = RepoJsonLoader.load(INPUT_FILE)

    print("Extracting employee data...")
    employee_data = EmployeeAggregator.extract(repo_data, EMPLOYEE_NAME)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_path = os.path.join(
        OUTPUT_DIR,
        f"{EMPLOYEE_NAME}_offboarding_data.json"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(employee_data, f, indent=4)

    print("Done.")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
