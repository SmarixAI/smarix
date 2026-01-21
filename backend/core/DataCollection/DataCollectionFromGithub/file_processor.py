"""
File Processor - OPTIMIZED VERSION
Processes and categorizes files with enhanced performance
Compatible with async data collection pipeline
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from config.DataCollection.settings import Config
from analyzers.DataCollection.python_analyzer import PythonAnalyzer
from analyzers.DataCollection.javascript_analyzer import JavaScriptAnalyzer
from analyzers.DataCollection.base_analyzer import BasicAnalyzer
import hashlib
import mimetypes
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


class FileProcessor:
    """
    Processes and categorizes files (OPTIMIZED)

    Enhancements:
    - Parallel code analysis
    - Optimized annotation detection
    - Better error handling
    - Progress indicators
    """

    def __init__(self):
        self.config = Config()
        self.analyzers = {
            ".py": PythonAnalyzer(),
            ".js": JavaScriptAnalyzer(),
            ".ts": JavaScriptAnalyzer(),
            ".jsx": JavaScriptAnalyzer(),
            ".tsx": JavaScriptAnalyzer(),
        }
        self.base_analyzer = BasicAnalyzer()

        # Cache for file categorization (small performance boost)
        self._doc_file_cache = set(f.lower() for f in self.config.DOCUMENTATION_FILES)
        self._dep_file_cache = set(f.lower() for f in self.config.DEPENDENCY_FILES)
        self._infra_file_cache = set(
            f.lower() for f in self.config.IMPORTANT_INFRA_FILES
        )

    def should_skip_directory(self, dir_name: str) -> bool:
        """Check if directory should be skipped"""
        return dir_name.lower() in self.config.SKIP_DIRECTORIES

    def should_skip_file(self, file_item: Dict) -> bool:
        """
        Check if file should be skipped (OPTIMIZED)

        Returns True if file is too large or has skipped extension
        """
        # Check size first (fastest check)
        size = file_item.get("size", 0)
        if size and size > self.config.MAX_FILE_SIZE:
            return True

        # Check extension
        name = file_item.get("name", "")
        if not name:
            return True

        ext = Path(name).suffix.lower()
        if ext in self.config.SKIP_EXTENSIONS:
            return True

        return False

    def categorize_file(self, file_item: Dict) -> str:
        file_name_lower = file_item.get("name", "").lower()
        ext = Path(file_name_lower).suffix
        
        # CODE FIRST - expanded config covers everything
        if ext in self.config.SUPPORTED_CODE_EXTENSIONS:
            return "code"
        
        # Docs second
        if self._is_documentation_file_optimized(file_name_lower):
            return "documentation"
        
        # Dependencies last
        if file_name_lower in self._dep_file_cache:
            return "dependencies"
        
        return "code" 


    def process_file_content(self, file_item: Dict, content: str) -> Dict[str, Any]:
        """
        Process file and create normalized record (OPTIMIZED)

        Improvements:
        - Faster binary detection
        - Optimized hash calculation
        - Better error handling
        """
        file_path = file_item.get("path", "")
        file_name = file_item.get("name", "")
        file_ext = Path(file_name).suffix.lower()

        # Calculate hash for duplicate detection (optimized encoding)
        try:
            sha256 = hashlib.sha256(
                content.encode("utf-8", errors="ignore")
            ).hexdigest()
        except Exception:
            sha256 = "error"

        # Detect MIME type
        mtype, _ = mimetypes.guess_type(file_name)

        # Binary detection (optimized - check first 512 bytes only)
        is_binary = False
        try:
            # Check for null bytes in first 512 chars
            if content and "\0" in content[:512]:
                is_binary = True
        except Exception:
            is_binary = False

        # Count lines efficiently
        try:
            lines = content.count("\n") + 1 if content else 0
        except Exception:
            lines = 0

        record = {
            "path": file_path,
            "name": file_name,
            "extension": file_ext,
            "size": file_item.get(
                "size", len(content.encode("utf-8", errors="ignore")) if content else 0
            ),
            "content": content,
            "lines": lines,
            "sha": file_item.get("sha"),
            "download_url": file_item.get("download_url"),
            "sha256": sha256,
            "mimetype": mtype,
            "is_binary": is_binary,
        }

        return record

    def analyze_code_files(
        self, code_files: List[Dict], parallel: bool = True
    ) -> List[Dict]:
        """
        Analyze code files using appropriate analyzers (OPTIMIZED)

        NEW Features:
        - Parallel analysis for faster processing
        - Progress bar
        - Better error handling
        - Respects MAX_FILES_TO_ANALYZE=None (all files)

        Args:
            code_files: List of code file dictionaries
            parallel: Whether to use parallel processing (default: True)

        Returns:
            List of analyzed file dictionaries
        """
        # Determine how many files to analyze
        max_files = self.config.MAX_FILES_TO_ANALYZE

        if max_files is None:
            # Analyze all files
            files_to_analyze = code_files
        else:
            # Limit to max_files
            files_to_analyze = code_files[:max_files]

        if not files_to_analyze:
            return []

        print(f"   Analyzing {len(files_to_analyze)} code files...")

        # Choose analysis method based on file count and parallel flag
        if parallel and len(files_to_analyze) > 10:
            return self._analyze_parallel(files_to_analyze)
        else:
            return self._analyze_sequential(files_to_analyze)

    def _analyze_sequential(self, code_files: List[Dict]) -> List[Dict]:
        """Sequential analysis with progress bar"""
        analyzed = []

        for code_file in tqdm(code_files, desc="Analyzing files", unit="file"):
            try:
                result = self._analyze_single_file(code_file)
                if result:
                    analyzed.append(result)
            except Exception as e:
                print(
                    f"      ⚠️  Error analyzing {code_file.get('path', 'unknown')}: {e}"
                )
                continue

        return analyzed

    def _analyze_parallel(self, code_files: List[Dict]) -> List[Dict]:
        """
        Parallel analysis using ThreadPoolExecutor (OPTIMIZED)

        Uses threads since analysis is mostly CPU-bound but with I/O for AST parsing
        """
        analyzed = []
        max_workers = min(4, len(code_files))  # Limit to 4 workers to avoid overhead

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all analysis tasks
            future_to_file = {
                executor.submit(self._analyze_single_file, code_file): code_file
                for code_file in code_files
            }

            # Collect results with progress bar
            for future in tqdm(
                as_completed(future_to_file),
                total=len(code_files),
                desc="Analyzing files",
                unit="file",
            ):
                try:
                    result = future.result()
                    if result:
                        analyzed.append(result)
                except Exception as e:
                    code_file = future_to_file[future]
                    print(
                        f"      ⚠️  Error analyzing {code_file.get('path', 'unknown')}: {e}"
                    )
                    continue

        return analyzed

    def _analyze_single_file(self, code_file: Dict) -> Optional[Dict]:
        """
        Analyze a single code file

        Returns None if analysis fails
        """
        extension = code_file.get("extension", "")
        file_path = code_file.get("path", "")
        content = code_file.get("content", "")

        if not content:
            return None

        # Get appropriate analyzer
        analyzer = self.analyzers.get(extension)

        # Perform analysis
        try:
            if analyzer:
                analysis = analyzer.analyze(content, file_path)
            else:
                analysis = self.base_analyzer.basic_analysis(content, file_path)

            if analysis:
                # Attach source metadata
                analysis["_source_path"] = file_path
                analysis["_lines"] = code_file.get("lines", 0)
                analysis["_extension"] = extension
                return analysis

        except Exception as e:
            # Fallback to basic analysis
            try:
                analysis = self.base_analyzer.basic_analysis(content, file_path)
                if analysis:
                    analysis["_source_path"] = file_path
                    analysis["_lines"] = code_file.get("lines", 0)
                    analysis["_extension"] = extension
                    analysis["_analysis_fallback"] = True
                    return analysis
            except Exception:
                return None

        return None

    def _is_documentation_file(self, filename: str) -> bool:
        """
        Check if file is a documentation file (LEGACY METHOD)

        Kept for backwards compatibility
        """
        return self._is_documentation_file_optimized(filename.lower())

    def _is_documentation_file_optimized(self, filename_lower: str) -> bool:
        """
        Check if file is a documentation file (OPTIMIZED)

        Args:
            filename_lower: Lowercase filename
        """
        # Check cached documentation files
        if filename_lower in self._doc_file_cache:
            return True

        # Check if starts with readme
        if filename_lower.startswith("readme"):
            return True

        # Check documentation extensions
        if any(
            filename_lower.endswith(ext) for ext in self.config.DOCUMENTATION_EXTENSIONS
        ):
            return True

        # Check infrastructure files
        if filename_lower in self._infra_file_cache:
            return True

        return False

    def _is_dependency_file(self, filename: str) -> bool:
        """Check if file is a dependency file"""
        return filename.lower() in self._dep_file_cache

    def detect_annotations(self, content: str) -> List[Dict]:
        """
        Detect code annotations (TODO, FIXME, etc.) (OPTIMIZED)

        Improvements:
        - Uses compiled regex for better performance
        - Handles multiple patterns in one pass
        - Limits context length
        """
        if not content:
            return []

        patterns = {
            "TODO": r"TODO:?\s*(.{0,100})",
            "FIXME": r"FIXME:?\s*(.{0,100})",
            "HACK": r"HACK:?\s*(.{0,100})",
            "NOTE": r"NOTE:?\s*(.{0,100})",
            "XXX": r"XXX:?\s*(.{0,100})",
            "BUG": r"BUG:?\s*(.{0,100})",
            "OPTIMIZE": r"OPTIMIZE:?\s*(.{0,100})",
        }

        results = []
        lines = content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            line_upper = line.upper()

            for annotation_type, pattern in patterns.items():
                if annotation_type in line_upper:
                    # Extract context using regex
                    match = re.search(pattern, line_upper)
                    context = line.strip()[:150]  # Limit context length

                    results.append(
                        {"type": annotation_type, "line": line_num, "context": context}
                    )
                    break  # Only one annotation per line

        return results

    def get_file_statistics(self, code_files: List[Dict]) -> Dict[str, Any]:
        """
        Generate statistics about processed files (NEW)

        Useful for debugging and reporting
        """
        stats = {
            "total_files": len(code_files),
            "total_size_bytes": 0,
            "total_lines": 0,
            "by_extension": {},
            "largest_file": None,
            "most_lines": None,
            "binary_files": 0,
            "average_size": 0,
            "average_lines": 0,
        }

        if not code_files:
            return stats

        max_size = 0
        max_lines = 0

        for file_data in code_files:
            size = file_data.get("size", 0)
            lines = file_data.get("lines", 0)
            ext = file_data.get("extension", "unknown")
            is_binary = file_data.get("is_binary", False)

            stats["total_size_bytes"] += size
            stats["total_lines"] += lines

            # Count by extension
            stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1

            # Track largest file
            if size > max_size:
                max_size = size
                stats["largest_file"] = {
                    "path": file_data.get("path"),
                    "size": size,
                    "lines": lines,
                }

            # Track most lines
            if lines > max_lines:
                max_lines = lines
                stats["most_lines"] = {
                    "path": file_data.get("path"),
                    "lines": lines,
                    "size": size,
                }

            # Count binary files
            if is_binary:
                stats["binary_files"] += 1

        # Calculate averages
        if code_files:
            stats["average_size"] = stats["total_size_bytes"] // len(code_files)
            stats["average_lines"] = stats["total_lines"] // len(code_files)

        return stats

    def batch_categorize(self, file_items: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Batch categorize multiple files (NEW)

        Returns dict with categories as keys and file lists as values
        """
        categorized = {"code": [], "documentation": [], "dependencies": [], "other": []}

        for file_item in file_items:
            try:
                category = self.categorize_file(file_item)
                categorized[category].append(file_item)
            except Exception:
                categorized["other"].append(file_item)

        return categorized
