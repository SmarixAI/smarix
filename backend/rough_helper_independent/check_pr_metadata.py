# import pickle
# from pathlib import Path

# OWNER = "CCExtractor"
# REPO  = "taskwarrior-flutter"

# path = Path("data/VectorDB") / OWNER / REPO / "pr" / "metadata.pkl"

# print("📂 Reading:", path)

# with open(path, "rb") as f:
#     data = pickle.load(f)

# print("🔎 Total PR chunks:", len(data.get("metadata", [])))

# found = False
# for m in data["metadata"]:
#     if m.get("pr_number") == 499:
#         found = True
#         print("\n✅ PR #499 FOUND")
#         print("Keys:", list(m.keys()))
#         print("merged_by =", m.get("merged_by"))

# if not found:
#     print("\n❌ PR #499 NOT FOUND in metadata")



# debug_vectordb_pr.py
import pickle

path = "data/VectorDB/CCExtractor/taskwarrior-flutter/pr/metadata.pkl"

with open(path, "rb") as f:
    data = pickle.load(f)

found = False
for m in data["metadata"]:
    if m.get("pr_number") == 499:
        found = True
        print("FOUND PR 499")
        print("merged_by:", m.get("merged_by"))
        print("keys:", sorted(m.keys()))

if not found:
    print("PR 499 NOT FOUND")
