"""Base analyzer class for code analysis."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path
from utils.file_utils import FileUtils

class BaseAnalyzer(ABC):
    """Base class for code analyzers"""
    
    def __init__(self):
        self.file_utils = FileUtils()
    
    @abstractmethod
    def analyze(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze file content and return structured data"""
        pass
    
    def basic_analysis(self, content: str, file_path: str) -> Dict[str, Any]:
        """Perform basic file analysis"""
        lines = content.splitlines()
        line_stats = self.file_utils.count_lines_of_code(content)
        # Infer language from file extension when possible so basic analysis
        # can produce a reasonable `language` value for files like .html
        ext = Path(file_path).suffix.lower() if file_path else ''
        extension_language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.json': 'json',
            '.md': 'markdown',
            '.xml': 'xml',
        }

        language = extension_language_map.get(ext, 'unknown')

        return {
            'file_path': file_path,
            'language': language,
            'analysis_type': 'basic',
            'line_stats': line_stats,
            'file_size': len(content.encode('utf-8')),
            'has_comments': line_stats['comments'] > 0,
            'complexity_score': self._calculate_basic_complexity(content),
            'encoding': 'utf-8'
        }
    
    def _calculate_basic_complexity(self, content: str) -> int:
        """Calculate basic complexity score based on common patterns"""
        complexity = 0
        
        # Count control flow statements
        control_patterns = ['if ', 'else', 'elif', 'for ', 'while ', 'switch', 'case']
        for pattern in control_patterns:
            complexity += content.lower().count(pattern)
        
        # Count function-like patterns
        function_patterns = ['function', 'def ', 'class ', 'method']
        for pattern in function_patterns:
            complexity += content.lower().count(pattern)
        
        return min(complexity, 100)  # Cap at 100
    
    def extract_imports_generic(self, content: str, import_patterns: list) -> list:
        """Generic method to extract imports using regex patterns"""
        import re
        imports = []
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if isinstance(matches[0], tuple) if matches else False:
                # Handle tuple results from groups
                imports.extend([match[0] if match[0] else match[1] for match in matches])
            else:
                imports.extend(matches)
        
        return list(set(imports))  # Remove duplicates
    
    def count_indentation_levels(self, content: str) -> Dict[str, int]:
        """Count indentation levels in the file"""
        lines = content.splitlines()
        indentation_counts = {}
        
        for line in lines:
            if line.strip():  # Skip empty lines
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    level = leading_spaces // 4  # Assuming 4-space indentation
                    indentation_counts[level] = indentation_counts.get(level, 0) + 1
        
        return indentation_counts


# Concrete implementation for basic analysis
class BasicAnalyzer(BaseAnalyzer):
    """Concrete implementation of BaseAnalyzer for unsupported file types"""
    
    def analyze(self, content: str, file_path: str) -> Dict[str, Any]:
        """Perform basic analysis for unsupported file types"""
        return self.basic_analysis(content, file_path)
