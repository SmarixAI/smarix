import ast
from typing import Dict, Any
from analyzers.base_analyzer import BaseAnalyzer

class PythonAnalyzer(BaseAnalyzer):
    """Analyzes Python source code"""
    
    def analyze(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract Python-specific information"""
        try:
            tree = ast.parse(content)
            analysis = {
                'file_path': file_path,
                'language': 'python',
                'functions': [],
                'classes': [],
                'imports': [],
                'docstrings': []
            }
            
            for node in ast.walk(tree):
                self._process_node(node, analysis)
            
            return analysis
        except Exception as e:
            print(f"❌ Error analyzing Python file {file_path}: {e}")
            return self.basic_analysis(content, file_path)
    
    def _process_node(self, node: ast.AST, analysis: Dict[str, Any]) -> None:
        """Process individual AST nodes"""
        if isinstance(node, ast.FunctionDef):
            self._process_function(node, analysis)
        elif isinstance(node, ast.ClassDef):
            self._process_class(node, analysis)
        elif isinstance(node, ast.Import):
            self._process_import(node, analysis)
        elif isinstance(node, ast.ImportFrom):
            self._process_import_from(node, analysis)
    
    def _process_function(self, node: ast.FunctionDef, analysis: Dict[str, Any]) -> None:
        """Process function definition"""
        func_info = {
            'name': node.name,
            'line': node.lineno,
            'args': [arg.arg for arg in node.args.args],
            'docstring': ast.get_docstring(node) or ''
        }
        analysis['functions'].append(func_info)
    
    def _process_class(self, node: ast.ClassDef, analysis: Dict[str, Any]) -> None:
        """Process class definition"""
        class_info = {
            'name': node.name,
            'line': node.lineno,
            'docstring': ast.get_docstring(node) or ''
        }
        analysis['classes'].append(class_info)
    
    def _process_import(self, node: ast.Import, analysis: Dict[str, Any]) -> None:
        """Process import statement"""
        for alias in node.names:
            analysis['imports'].append(alias.name)
    
    def _process_import_from(self, node: ast.ImportFrom, analysis: Dict[str, Any]) -> None:
        """Process from-import statement"""
        if node.module:
            for alias in node.names:
                analysis['imports'].append(f"{node.module}.{alias.name}")
