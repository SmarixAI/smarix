from typing import Dict, List, Any
from pathlib import Path
from config.DataCollection.settings import Config
from analyzers.DataCollection.python_analyzer import PythonAnalyzer
from analyzers.DataCollection.javascript_analyzer import JavaScriptAnalyzer
from analyzers.DataCollection.base_analyzer import BasicAnalyzer
import hashlib
import mimetypes

class FileProcessor:
    """Processes and categorizes files (enhanced for consistent metadata tracking)"""

    def __init__(self):
        self.config = Config()
        self.analyzers = {
            '.py': PythonAnalyzer(),
            '.js': JavaScriptAnalyzer(),
            '.ts': JavaScriptAnalyzer(),
            '.jsx': JavaScriptAnalyzer(),
            '.tsx': JavaScriptAnalyzer()
        }
        self.base_analyzer = BasicAnalyzer()

    def should_skip_directory(self, dir_name: str) -> bool:
        return dir_name.lower() in self.config.SKIP_DIRECTORIES

    def should_skip_file(self, file_item: Dict) -> bool:
        # skip extremely large files or binary files beyond a size threshold
        size = file_item.get('size', 0)
        if size and size > self.config.MAX_FILE_SIZE:
            return True
        name = file_item.get('name', '')
        ext = Path(name).suffix.lower()
        if ext in self.config.SKIP_EXTENSIONS:
            return True
        return False

    def categorize_file(self, file_item: Dict) -> str:
        file_name = file_item.get('name', '')
        file_ext = Path(file_name).suffix.lower()

        if file_ext in self.config.SUPPORTED_CODE_EXTENSIONS:
            return 'code'
        elif self._is_documentation_file(file_name):
            return 'documentation'
        elif self._is_dependency_file(file_name):
            return 'dependencies'
        else:
            return 'other'

    def process_file_content(self, file_item: Dict, content: str) -> Dict[str, Any]:
        """Process file and create normalized record"""
        file_path = file_item.get('path', '')
        file_name = file_item.get('name', '')
        file_ext = Path(file_name).suffix.lower()
        # calculate hash for duplicate detection
        sha256 = hashlib.sha256(content.encode('utf-8', errors='ignore')).hexdigest()
        # detect MIME type (best effort)
        mtype, _ = mimetypes.guess_type(file_name)
        is_binary = False
        try:
            # basic binary detection heuristic
            if "\0" in content[:1024]:
                is_binary = True
        except Exception:
            is_binary = False

        record = {
            'path': file_path,
            'name': file_name,
            'extension': file_ext,
            'size': file_item.get('size', len(content)),
            'content': content,
            'lines': len(content.splitlines()),
            'sha': file_item.get('sha'),
            'download_url': file_item.get('download_url'),
            'sha256': sha256,
            'mimetype': mtype,
            'is_binary': is_binary
        }

        return record

    def analyze_code_files(self, code_files: List[Dict]) -> List[Dict]:
        """Analyze code files using appropriate analyzers"""
        analyzed = []
        for code_file in code_files[:self.config.MAX_FILES_TO_ANALYZE]:
            extension = code_file.get('extension', '')
            analyzer = self.analyzers.get(extension)
            if analyzer:
                try:
                    analysis = analyzer.analyze(code_file.get('content', ''), code_file.get('path', ''))
                except Exception as e:
                    print(f"Analyzer error for {code_file.get('path')}: {e}")
                    analysis = self.base_analyzer.basic_analysis(code_file.get('content', ''), code_file.get('path', ''))
            else:
                analysis = self.base_analyzer.basic_analysis(code_file.get('content', ''), code_file.get('path', ''))
            if analysis:
                # attach source metadata
                analysis['_source_path'] = code_file.get('path', '')
                analysis['_lines'] = code_file.get('lines', 0)
                analyzed.append(analysis)
        return analyzed

    def _is_documentation_file(self, filename: str) -> bool:
        f = filename.lower()
        return (
            f in self.config.DOCUMENTATION_FILES
            or f.startswith('readme')
            or any(f.endswith(ext) for ext in self.config.DOCUMENTATION_EXTENSIONS)
            or f in self.config.IMPORTANT_INFRA_FILES  # include Dockerfile, docker-compose, env samples etc.
        )

    def _is_dependency_file(self, filename: str) -> bool:
        return filename.lower() in self.config.DEPENDENCY_FILES

    def detect_annotations(self, content: str) -> List[Dict]:
        patterns = ['TODO', 'FIXME', 'HACK', 'NOTE']
        lines = content.splitlines()
        results = []
        for i, line in enumerate(lines, start=1):
            for p in patterns:
                if p in line:
                    results.append({'type': p, 'line': i, 'context': line.strip()})
        return results
