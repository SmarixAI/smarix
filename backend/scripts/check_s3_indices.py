"""
Diagnostic script to check S3 index availability and loading status.
This helps diagnose issues when indices fail to load from S3.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from utils.s3 import s3_manager
from utils.repo_context import get_runtime_state_from_s3

S3_BUCKET = "smarix-data-apsouth1"
S3_VECTORDB_PATH = "VectorDB"


def check_s3_index(index_s3_prefix: str, index_type: str) -> dict:
    """Check if an index exists in S3 and has required files."""
    result = {
        "index_type": index_type,
        "exists": False,
        "has_faiss": False,
        "has_metadata": False,
        "has_config": False,
        "error": None
    }
    
    try:
        # Check for required files
        faiss_key = f"{index_s3_prefix}/faiss.index"
        metadata_key = f"{index_s3_prefix}/metadata.pkl"
        config_key = f"{index_s3_prefix}/config.json"
        
        result["has_faiss"] = s3_manager.key_exists(faiss_key)
        result["has_metadata"] = s3_manager.key_exists(metadata_key)
        result["has_config"] = s3_manager.key_exists(config_key)
        
        result["exists"] = result["has_faiss"] or result["has_metadata"] or result["has_config"]
        
        if result["exists"]:
            # Get file sizes
            try:
                if result["has_faiss"]:
                    response = s3_manager.s3.head_object(Bucket=S3_BUCKET, Key=faiss_key)
                    result["faiss_size_mb"] = response.get("ContentLength", 0) / (1024 * 1024)
                if result["has_metadata"]:
                    response = s3_manager.s3.head_object(Bucket=S3_BUCKET, Key=metadata_key)
                    result["metadata_size_mb"] = response.get("ContentLength", 0) / (1024 * 1024)
            except Exception as e:
                result["error"] = f"Error getting file sizes: {e}"
        
    except Exception as e:
        result["error"] = str(e)
        result["exists"] = False
    
    return result


def main():
    """Main diagnostic function."""
    print("=" * 80)
    print("S3 INDEX DIAGNOSTIC TOOL")
    print("=" * 80)
    print()
    
    # Get repo context from S3
    try:
        print("📥 Loading runtime state from S3...")
        state = get_runtime_state_from_s3()
        
        repo_config = state.get("curr_repo", {}) or state.get("user_default_repo", {})
        owner = repo_config.get("owner")
        repo_name = repo_config.get("name")
        
        if not owner or not repo_name:
            print("❌ ERROR: Could not determine repo from runtime_state.json")
            print(f"   curr_repo: {state.get('curr_repo')}")
            print(f"   user_default_repo: {state.get('user_default_repo')}")
            return
        
        print(f"✅ Found repo: {owner}/{repo_name}")
        print()
        
    except Exception as e:
        print(f"❌ ERROR: Failed to load runtime state: {e}")
        return
    
    # Check S3 prefix
    s3_vectordb_prefix = f"{S3_VECTORDB_PATH}/{owner}/{repo_name}"
    print(f"🔍 Checking S3 prefix: s3://{S3_BUCKET}/{s3_vectordb_prefix}/")
    print()
    
    # List all subdirectories (index types)
    try:
        response = s3_manager.s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=s3_vectordb_prefix + "/",
            Delimiter="/"
        )
        
        index_types = []
        if "CommonPrefixes" in response:
            for prefix_info in response["CommonPrefixes"]:
                prefix = prefix_info["Prefix"]
                # Extract index type from prefix
                parts = prefix.rstrip("/").split("/")
                if len(parts) > 0:
                    index_type = parts[-1]
                    # Special handling for graph/graph_nodes
                    if index_type == "graph":
                        index_types.append(("graph_nodes", f"{prefix}graph_nodes"))
                    else:
                        index_types.append((index_type, prefix.rstrip("/")))
        
        print(f"📊 Found {len(index_types)} potential index types:")
        print()
        
        # Check each index
        all_checks = []
        for index_type, index_prefix in index_types:
            print(f"Checking '{index_type}' index...")
            check_result = check_s3_index(index_prefix, index_type)
            all_checks.append(check_result)
            
            if check_result["exists"]:
                status = "✅" if (check_result["has_faiss"] and check_result["has_metadata"]) else "⚠️"
                print(f"  {status} Index exists")
                print(f"     - faiss.index: {'✅' if check_result['has_faiss'] else '❌'}", end="")
                if check_result.get("faiss_size_mb"):
                    print(f" ({check_result['faiss_size_mb']:.2f} MB)")
                else:
                    print()
                print(f"     - metadata.pkl: {'✅' if check_result['has_metadata'] else '❌'}", end="")
                if check_result.get("metadata_size_mb"):
                    print(f" ({check_result['metadata_size_mb']:.2f} MB)")
                else:
                    print()
                print(f"     - config.json: {'✅' if check_result['has_config'] else '❌'}")
            else:
                print(f"  ❌ Index not found")
                if check_result["error"]:
                    print(f"     Error: {check_result['error']}")
            print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        complete_indices = [c for c in all_checks if c["has_faiss"] and c["has_metadata"]]
        incomplete_indices = [c for c in all_checks if c["exists"] and not (c["has_faiss"] and c["has_metadata"])]
        missing_indices = [c for c in all_checks if not c["exists"]]
        
        print(f"✅ Complete indices: {len(complete_indices)}")
        for c in complete_indices:
            print(f"   - {c['index_type']}")
        
        if incomplete_indices:
            print(f"\n⚠️  Incomplete indices: {len(incomplete_indices)}")
            for c in incomplete_indices:
                print(f"   - {c['index_type']} (missing: ", end="")
                missing = []
                if not c["has_faiss"]:
                    missing.append("faiss.index")
                if not c["has_metadata"]:
                    missing.append("metadata.pkl")
                print(", ".join(missing) + ")")
        
        if missing_indices:
            print(f"\n❌ Missing indices: {len(missing_indices)}")
            for c in missing_indices:
                print(f"   - {c['index_type']}")
        
        print()
        print("=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        if incomplete_indices or missing_indices:
            print("⚠️  Some indices are missing or incomplete. This may cause:")
            print("   - Empty retrieval results for certain query types")
            print("   - Chatbot not responding to some questions")
            print()
            print("To fix:")
            print("   1. Rebuild indices: python backend/core/VectorDB/build_indices.py")
            print("   2. Ensure all required files are uploaded to S3")
            print("   3. Check S3 permissions and network connectivity")
        else:
            print("✅ All indices appear to be complete!")
            print("   If you're still experiencing issues, check:")
            print("   - Application logs for index loading errors")
            print("   - S3 access permissions")
            print("   - Network connectivity to S3")
        
    except Exception as e:
        print(f"❌ ERROR: Failed to list S3 objects: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

