"""JavaScript/TypeScript code analyzer."""

import re
from typing import Dict, Any, List
from analyzers.base_analyzer import BaseAnalyzer

class JavaScriptAnalyzer(BaseAnalyzer):
    """Analyzes JavaScript/TypeScript source code"""
    
    def __init__(self):
        super().__init__()
        self.function_patterns = [
            r'function\s+(\w+)\s*\(',                           # function name()
            r'(?:const|let|var)\s+(\w+)\s*=\s*function',        # const name = function
            r'(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>', # const name = () =>
            r'(\w+):\s*function\s*\(',                          # name: function()
            r'(\w+)\s*\([^)]*\)\s*{',                          # name() { (method)
            r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*=>',            # async name() =>
        ]
        self.class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?'
        self.import_patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',       # import ... from 'module'
            r'import\s+[\'"]([^\'"]+)[\'"]',                    # import 'module'
            r'require\([\'"]([^\'"]+)[\'"]\)',                  # require('module')
            r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',         # dynamic import()
        ]
        self.export_patterns = [
            r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)',
            r'export\s*{\s*([^}]+)\s*}',
            r'module\.exports\s*=\s*(\w+)',
        ]
    
    def analyze(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract JavaScript/TypeScript information"""
        base_analysis = self.basic_analysis(content, file_path)
        
        # Update language detection
        language = 'typescript' if file_path.endswith(('.ts', '.tsx')) else 'javascript'
        is_react = file_path.endswith(('.jsx', '.tsx'))
        
        js_analysis = {
            **base_analysis,
            'language': language,
            'is_react': is_react,
            'analysis_type': 'javascript',
            'functions': self._extract_functions(content),
            'classes': self._extract_classes(content),
            'imports': self._extract_imports(content),
            'exports': self._extract_exports(content),
            'react_components': self._extract_react_components(content) if is_react else [],
            'async_functions': self._count_async_functions(content),
            'promises': self._count_promises(content),
            'dom_usage': self._detect_dom_usage(content),
            'frameworks': self._detect_frameworks(content),
        }
        
        return js_analysis
    
    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function information with more details"""
        functions = []
        
        for pattern in self.function_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                func_name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                # Check if it's async
                is_async = 'async' in content[max(0, match.start()-20):match.start()]
                
                functions.append({
                    'name': func_name,
                    'line': line_number,
                    'is_async': is_async,
                    'type': self._determine_function_type(match.group(0))
                })
        
        return functions
    
    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract class information"""
        classes = []
        matches = re.finditer(self.class_pattern, content, re.MULTILINE)
        
        for match in matches:
            class_name = match.group(1)
            extends_class = match.group(2) if match.lastindex > 1 else None
            line_number = content[:match.start()].count('\n') + 1
            
            classes.append({
                'name': class_name,
                'line': line_number,
                'extends': extends_class,
                'methods': self._extract_class_methods(content, match.end())
            })
        
        return classes
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements"""
        return self.extract_imports_generic(content, self.import_patterns)
    
    def _extract_exports(self, content: str) -> List[str]:
        """Extract export statements"""
        exports = []
        
        for pattern in self.export_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            exports.extend(matches)
        
        # Handle export lists like "export { a, b, c }"
        export_list_pattern = r'export\s*{\s*([^}]+)\s*}'
        export_lists = re.findall(export_list_pattern, content)
        for export_list in export_lists:
            items = [item.strip() for item in export_list.split(',')]
            exports.extend(items)
        
        return list(set(exports))
    
    def _extract_react_components(self, content: str) -> List[Dict[str, Any]]:
        """Extract React component information"""
        components = []
        
        # Function components
        func_component_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*{[^}]*return\s*\('
        matches = re.finditer(func_component_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            component_name = match.group(1)
            # Check if it starts with uppercase (React component convention)
            if component_name[0].isupper():
                line_number = content[:match.start()].count('\n') + 1
                components.append({
                    'name': component_name,
                    'type': 'functional',
                    'line': line_number
                })
        
        # Class components
        class_component_pattern = r'class\s+(\w+)\s+extends\s+(?:React\.)?Component'
        matches = re.finditer(class_component_pattern, content)
        
        for match in matches:
            component_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            components.append({
                'name': component_name,
                'type': 'class',
                'line': line_number
            })
        
        return components
    
    def _count_async_functions(self, content: str) -> int:
        """Count async functions in the code"""
        return len(re.findall(r'async\s+(?:function|\w+\s*=>)', content))
    
    def _count_promises(self, content: str) -> int:
        """Count Promise usage"""
        promise_patterns = [
            r'new\s+Promise\s*\(',
            r'\.then\s*\(',
            r'\.catch\s*\(',
            r'\.finally\s*\(',
            r'Promise\.(?:all|race|resolve|reject)',
            r'await\s+',
        ]
        
        count = 0
        for pattern in promise_patterns:
            count += len(re.findall(pattern, content))
        
        return count
    
    def _detect_dom_usage(self, content: str) -> bool:
        """Detect if code uses DOM APIs"""
        dom_patterns = [
            r'document\.',
            r'window\.',
            r'getElementById',
            r'querySelector',
            r'addEventListener',
            r'createElement',
        ]
        
        return any(re.search(pattern, content) for pattern in dom_patterns)
    
    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect JavaScript frameworks being used"""
        frameworks = []
        
        framework_patterns = {
            'React': [r'import.*React', r'from\s+[\'"]react[\'"]', r'JSX'],
            'Vue': [r'import.*Vue', r'from\s+[\'"]vue[\'"]', r'\.vue[\'"]'],
            'Angular': [r'@Component', r'@Injectable', r'from\s+[\'"]@angular'],
            'Express': [r'express\(\)', r'from\s+[\'"]express[\'"]'],
            'jQuery': [r'\$\(', r'jQuery', r'from\s+[\'"]jquery[\'"]'],
            'Lodash': [r'from\s+[\'"]lodash[\'"]', r'_\.'],
            'Axios': [r'from\s+[\'"]axios[\'"]', r'axios\.'],
        }
        
        for framework, patterns in framework_patterns.items():
            if any(re.search(pattern, content) for pattern in patterns):
                frameworks.append(framework)
        
        return frameworks
    
    def _determine_function_type(self, function_declaration: str) -> str:
        """Determine the type of function declaration"""
        if 'function' in function_declaration:
            return 'function_declaration'
        elif '=>' in function_declaration:
            return 'arrow_function'
        elif ':' in function_declaration:
            return 'method'
        else:
            return 'unknown'
    
    def _extract_class_methods(self, content: str, class_start: int) -> List[str]:
        """Extract method names from a class (simplified)"""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated parsing
        class_content = content[class_start:class_start+1000]  # Look ahead 1000 chars
        method_pattern = r'(\w+)\s*\([^)]*\)\s*{'
        methods = re.findall(method_pattern, class_content)
        return methods[:10]  # Limit to first 10 methods found
