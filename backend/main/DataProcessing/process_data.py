import os
import sys
import argparse
from pathlib import Path

# Handle both script execution and module import
# When run as script, add parent directories to path for absolute imports
try:
    from .state.repo_state import load_current_repo_from_state
    from .chunking.base_chunker import DataChunker
    from .pipeline.file_processor import process_file
    from .batch.batch_runner import batch_process
except ImportError:
    # If relative imports fail, we're running as a script
    # Add parent directories to path
    current_dir = Path(__file__).resolve().parent
    backend_dir = current_dir.parent.parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    from backend.main.DataProcessing.state.repo_state import load_current_repo_from_state
    from backend.main.DataProcessing.chunking.base_chunker import DataChunker
    from backend.main.DataProcessing.pipeline.file_processor import process_file
    from backend.main.DataProcessing.batch.batch_runner import batch_process


REPO_OWNER, REPO_NAME = load_current_repo_from_state()
FULL_REPO_NAME = f"{REPO_OWNER}/{REPO_NAME}"


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise-grade multi-source RAG data processing with code analysis"
    )
    parser.add_argument("input_file", nargs="?", help="Path to JSON from data collection")
    parser.add_argument("--output-dir", default="./processed")
    parser.add_argument("--batch", action="store_true")

    args = parser.parse_args()

    if args.batch or not args.input_file:
        batch_process()
    else:
        if not os.path.exists(args.input_file):
            print(f"❌ Error: File not found: {args.input_file}")
            sys.exit(1)

        try:
            chunker = DataChunker(REPO_NAME, REPO_OWNER)
            process_file(args.input_file, args.output_dir, chunker)
            print("✅ Success!")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
