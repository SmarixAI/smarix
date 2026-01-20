"""
Graph-Ready Python Analyzer
Extracts Entities (Nodes) and Relationships (Edges) for GraphRAG
"""

import ast
from typing import Dict, Any, List, Set
from analyzers.base_analyzer import BaseAnalyzer

class PythonAnalyzer(BaseAnalyzer):
    """
    Advanced Python Analyzer that extracts Graph Nodes and Edges.
    """
    
    def analyze(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze Python code to extract graph structure (Nodes & Edges).
        """
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"❌ Syntax Error in {file_path}: {e}")
            return self.basic_analysis(content, file_path)
            
        # 1. Initialize Graph Data Containers
        analysis = {
            'file_path': file_path,
            'language': 'python',
            'classes': [],      # {name, lineno, docstring, methods}
            'functions': [],    # {name, lineno, args, docstring, calls}
            'imports': [],      # {module, alias}
            'global_calls': [], # Calls made at module level
            'dependencies': set()
        }

        # 2. Walk the Tree with State
        visitor = GraphVisitor(analysis)
        visitor.visit(tree)
        
        # 3. Clean up Sets to Lists for JSON serialization
        analysis['dependencies'] = list(analysis['dependencies'])
        
        return analysis


class GraphVisitor(ast.NodeVisitor):
    """
    AST Visitor that tracks scope and relationships.
    """
    def __init__(self, data_container):
        self.data = data_container
        self.current_scope = None # 'function', 'class', or None (Module)
        self.current_parent = None # Name of the class/function we are inside
    
    def visit_Import(self, node):
        """Edge: File -> IMPORTS -> Module"""
        for alias in node.names:
            self.data['imports'].append({'module': alias.name, 'alias': alias.asname})
            self.data['dependencies'].add(alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Edge: File -> IMPORTS -> Module"""
        module = node.module or ''
        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            self.data['imports'].append({'module': full_name, 'alias': alias.asname})
            self.data['dependencies'].add(module.split('.')[0])
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Node: Class | Edge: Class -> INHERITS -> Class"""
        # Capture Inheritance
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else "Unknown")

        class_info = {
            'name': node.name,
            'type': 'class',
            'lineno': node.lineno,
            'end_lineno': getattr(node, 'end_lineno', node.lineno),
            'docstring': ast.get_docstring(node),
            'bases': bases, # Inheritance edges
            'methods': []
        }
        
        # Enter Class Scope
        prev_scope = self.current_scope
        prev_parent = self.current_parent
        self.current_scope = 'class'
        self.current_parent = node.name
        
        # Walk children (methods)
        self.generic_visit(node)
        
        # Exit Scope
        self.current_scope = prev_scope
        self.current_parent = prev_parent
        
        self.data['classes'].append(class_info)

    def visit_FunctionDef(self, node):
        self._handle_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node):
        self._handle_function(node, is_async=True)

    def _handle_function(self, node, is_async):
        """Node: Function | Edge: Function -> CALLS -> Function"""
        
        call_visitor = CallCollector()
        call_visitor.visit(node)
        
        func_info = {
            'name': node.name,
            'type': 'method' if self.current_scope == 'class' else 'function',
            'parent': self.current_parent, 
            'lineno': node.lineno,
            'end_lineno': getattr(node, 'end_lineno', node.lineno),
            'docstring': ast.get_docstring(node),
            'args': [a.arg for a in node.args.args],
            'is_async': is_async,
            'calls': call_visitor.calls,
            'code_hash': None 
        }

        if self.current_scope == 'class':
            if self.data['classes']:
                self.data['classes'][-1]['methods'].append(func_info)
        else:
            self.data['functions'].append(func_info)
            

class CallCollector(ast.NodeVisitor):
    """Helper to find all function calls inside a function body"""
    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        """Found a call: obj.method() or func()"""
        try:
            if isinstance(node.func, ast.Name):
                self.calls.append(node.func.id) # func()
            elif isinstance(node.func, ast.Attribute):
                self.calls.append(node.func.attr) 
        except Exception:
            pass
        self.generic_visit(node)