"""Code analysis modules for different programming languages."""

from .base_analyzer import BaseAnalyzer
from .python_analyzer import PythonAnalyzer
from .javascript_analyzer import JavaScriptAnalyzer

# Factory function to get appropriate analyzer
def get_analyzer(file_extension: str) -> BaseAnalyzer:
    """Get appropriate analyzer for file extension."""
    analyzers = {
        '.py': PythonAnalyzer(),
        '.js': JavaScriptAnalyzer(),
        '.ts': JavaScriptAnalyzer(),
        '.jsx': JavaScriptAnalyzer(),
        '.tsx': JavaScriptAnalyzer()
    }
    return analyzers.get(file_extension, BaseAnalyzer())

__all__ = ["BaseAnalyzer", "PythonAnalyzer", "JavaScriptAnalyzer", "get_analyzer"]
