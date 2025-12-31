"""
Code Structure Collector
Maps code architecture, entry points, and system components
"""

from typing import Dict, List, Any, Set
import re
from pathlib import Path


class CodeStructureCollector:
    """Analyzes code structure for architecture understanding"""
    
    def __init__(self):
        self.entry_point_files = [
            'main.py', 'app.py', 'index.js', 'server.js', 
            'index.ts', 'main.ts', 'main.go', 'main.rs',
            'Program.cs', 'Main.java', '__init__.py'
        ]
        
        self.framework_indicators = {
            'flask': ['from flask import', '@app.route'],
            'django': ['from django', 'django.conf'],
            'fastapi': ['from fastapi import', 'FastAPI('],
            'express': ['express()', 'app.use(', 'app.get('],
            'react': ['import React', 'from \'react\''],
            'vue': ['new Vue', 'createApp'],
            'angular': ['@Component', '@NgModule'],
            'spring': ['@SpringBootApplication', '@RestController'],
            'gin': ['gin.Default()', 'gin.New()']
        }
    
    def collect_structure_data(self, code_files: List[Dict], analyzed_files: List[Dict]) -> Dict[str, Any]:
        """Extract code structure and architecture information"""
        
        structure_data = {
            'entry_points': [],
            'module_structure': {},
            'api_endpoints': [],
            'database_models': [],
            'authentication': {},
            'middleware': [],
            'route_mappings': [],
            'service_layer': [],
            'utility_functions': [],
            'frameworks_detected': {},
            'component_hierarchy': {}
        }
        
        # Detect entry points
        structure_data['entry_points'] = self._find_entry_points(code_files)
        
        # Build module structure
        structure_data['module_structure'] = self._build_module_tree(code_files)
        
        # Extract API endpoints and routes
        structure_data['api_endpoints'] = self._extract_api_endpoints(code_files, analyzed_files)
        
        # Find database models
        structure_data['database_models'] = self._find_database_models(code_files, analyzed_files)
        
        # Detect authentication mechanisms
        structure_data['authentication'] = self._detect_authentication(code_files)
        
        # Find middleware
        structure_data['middleware'] = self._find_middleware(code_files)
        
        # Detect frameworks
        structure_data['frameworks_detected'] = self._detect_frameworks(code_files)
        
        # Build component hierarchy
        structure_data['component_hierarchy'] = self._build_component_hierarchy(code_files)
        
        return structure_data
    
    def _find_entry_points(self, code_files: List[Dict]) -> List[Dict]:
        """Identify application entry points"""
        entry_points = []
        
        for file_data in code_files:
            file_name = file_data.get('name', '')
            file_path = file_data.get('path', '')
            content = file_data.get('content', '')
            
            # Check if it's a known entry point file
            if file_name.lower() in self.entry_point_files:
                entry_points.append({
                    'file': file_path,
                    'type': 'primary_entry',
                    'description': f'Main entry point: {file_name}'
                })
            
            # Check for main function/block
            if 'if __name__ == "__main__"' in content:
                entry_points.append({
                    'file': file_path,
                    'type': 'python_main',
                    'description': 'Python executable entry point'
                })
            
            # Check for server initialization
            if any(pattern in content for pattern in ['app.listen(', 'app.run(', 'uvicorn.run(']):
                entry_points.append({
                    'file': file_path,
                    'type': 'server_start',
                    'description': 'Server initialization'
                })
        
        return entry_points
    
    def _build_module_tree(self, code_files: List[Dict]) -> Dict[str, Any]:
        """Build hierarchical module structure"""
        module_tree = {}
        
        for file_data in code_files:
            path = file_data.get('path', '')
            parts = path.split('/')
            
            current_level = module_tree
            for part in parts[:-1]:  # Exclude filename
                if part not in current_level:
                    current_level[part] = {'_files': [], '_subdirs': {}}
                current_level = current_level[part]['_subdirs']
            
            # Add file to current level
            if parts:
                parent = parts[-2] if len(parts) > 1 else 'root'
                if parent not in module_tree:
                    module_tree[parent] = {'_files': [], '_subdirs': {}}
                module_tree[parent]['_files'].append({
                    'name': parts[-1],
                    'path': path,
                    'size': file_data.get('size', 0),
                    'lines': file_data.get('lines', 0)
                })
        
        return module_tree
    
    def _extract_api_endpoints(self, code_files: List[Dict], analyzed_files: List[Dict]) -> List[Dict]:
        """Extract API endpoints and routes"""
        endpoints = []
        
        for file_data in code_files:
            content = file_data.get('content', '')
            file_path = file_data.get('path', '')
            
            # Flask/FastAPI routes
            flask_routes = re.findall(
                r'@(?:app|router|api)\.(?:route|get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
                content
            )
            for route in flask_routes:
                endpoints.append({
                    'path': route,
                    'file': file_path,
                    'framework': 'flask/fastapi',
                    'type': 'route_decorator'
                })
            
            # Express.js routes
            express_routes = re.findall(
                r'app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
                content
            )
            for method, route in express_routes:
                endpoints.append({
                    'path': route,
                    'method': method.upper(),
                    'file': file_path,
                    'framework': 'express',
                    'type': 'route_method'
                })
            
            # Spring REST endpoints
            spring_routes = re.findall(
                r'@(?:Get|Post|Put|Delete|Patch)Mapping\([\'"]([^\'"]+)[\'"]',
                content
            )
            for route in spring_routes:
                endpoints.append({
                    'path': route,
                    'file': file_path,
                    'framework': 'spring',
                    'type': 'annotation'
                })
        
        # Also check analyzed files for more detailed info
        for analyzed in analyzed_files:
            if 'functions' in analyzed:
                for func in analyzed['functions']:
                    if func.get('decorators'):
                        for dec in func['decorators']:
                            if any(x in dec for x in ['route', 'get', 'post', 'put', 'delete']):
                                endpoints.append({
                                    'path': func.get('name'),
                                    'file': analyzed.get('file_path'),
                                    'function': func.get('name'),
                                    'decorators': func.get('decorators')
                                })
        
        return endpoints
    
    def _find_database_models(self, code_files: List[Dict], analyzed_files: List[Dict]) -> List[Dict]:
        """Find database model definitions"""
        models = []
        
        for file_data in code_files:
            content = file_data.get('content', '')
            file_path = file_data.get('path', '')
            
            # SQLAlchemy models (Python)
            sqlalchemy_models = re.findall(
                r'class\s+(\w+)\([^)]*(?:Base|Model|db\.Model)[^)]*\):',
                content
            )
            for model_name in sqlalchemy_models:
                fields = self._extract_model_fields(content, model_name)
                models.append({
                    'name': model_name,
                    'file': file_path,
                    'type': 'sqlalchemy',
                    'fields': fields
                })
            
            # Django models
            django_models = re.findall(
                r'class\s+(\w+)\(models\.Model\):',
                content
            )
            for model_name in django_models:
                fields = self._extract_model_fields(content, model_name)
                models.append({
                    'name': model_name,
                    'file': file_path,
                    'type': 'django',
                    'fields': fields
                })
            
            # Mongoose models (Node.js)
            mongoose_models = re.findall(
                r'const\s+(\w+Schema)\s*=\s*new\s+Schema\(',
                content
            )
            for schema_name in mongoose_models:
                models.append({
                    'name': schema_name,
                    'file': file_path,
                    'type': 'mongoose'
                })
            
            # Sequelize models
            sequelize_models = re.findall(
                r'sequelize\.define\([\'"](\w+)[\'"]',
                content
            )
            for model_name in sequelize_models:
                models.append({
                    'name': model_name,
                    'file': file_path,
                    'type': 'sequelize'
                })
        
        return models
    
    def _extract_model_fields(self, content: str, model_name: str) -> List[str]:
        """Extract fields from a model definition"""
        fields = []
        
        # Find the class definition
        class_pattern = f'class\\s+{model_name}\\([^)]+\\):(.*?)(?=\\nclass|\\Z)'
        match = re.search(class_pattern, content, re.DOTALL)
        
        if match:
            class_body = match.group(1)
            # Find field definitions (simplified)
            field_pattern = r'(\w+)\s*=\s*(?:Column|models\.\w+Field)'
            fields = re.findall(field_pattern, class_body)
        
        return fields
    
    def _detect_authentication(self, code_files: List[Dict]) -> Dict[str, Any]:
        """Detect authentication mechanisms"""
        auth_info = {
            'mechanisms': [],
            'files': [],
            'middleware': [],
            'jwt_detected': False,
            'oauth_detected': False,
            'session_detected': False
        }
        
        for file_data in code_files:
            content = file_data.get('content', '')
            file_path = file_data.get('path', '')
            
            # JWT detection
            if any(x in content for x in ['jwt', 'JWT', 'jsonwebtoken', 'pyjwt']):
                auth_info['jwt_detected'] = True
                auth_info['mechanisms'].append('JWT')
                if file_path not in auth_info['files']:
                    auth_info['files'].append(file_path)
            
            # OAuth detection
            if any(x in content for x in ['oauth', 'OAuth', 'passport']):
                auth_info['oauth_detected'] = True
                auth_info['mechanisms'].append('OAuth')
                if file_path not in auth_info['files']:
                    auth_info['files'].append(file_path)
            
            # Session detection
            if any(x in content for x in ['session', 'Session', 'flask_session']):
                auth_info['session_detected'] = True
                auth_info['mechanisms'].append('Session-based')
                if file_path not in auth_info['files']:
                    auth_info['files'].append(file_path)
            
            # Auth middleware detection
            if any(x in content for x in ['@login_required', '@authenticated', 'requireAuth', 'isAuthenticated']):
                auth_info['middleware'].append(file_path)
        
        auth_info['mechanisms'] = list(set(auth_info['mechanisms']))
        return auth_info
    
    def _find_middleware(self, code_files: List[Dict]) -> List[Dict]:
        """Find middleware definitions"""
        middleware = []
        
        for file_data in code_files:
            content = file_data.get('content', '')
            file_path = file_data.get('path', '')
            
            # Express middleware
            if 'app.use(' in content:
                middleware_matches = re.findall(r'app\.use\(([^)]+)\)', content)
                for match in middleware_matches:
                    middleware.append({
                        'type': 'express',
                        'definition': match.strip(),
                        'file': file_path
                    })
            
            # Flask before_request
            if '@app.before_request' in content or '@before_request' in content:
                middleware.append({
                    'type': 'flask_before_request',
                    'file': file_path
                })
            
            # Django middleware
            if 'MIDDLEWARE' in content and 'django' in content.lower():
                middleware.append({
                    'type': 'django_middleware',
                    'file': file_path
                })
        
        return middleware
    
    def _detect_frameworks(self, code_files: List[Dict]) -> Dict[str, List[str]]:
        """Detect frameworks used in the codebase"""
        frameworks = {}
        
        for file_data in code_files:
            content = file_data.get('content', '')
            file_path = file_data.get('path', '')
            
            for framework, indicators in self.framework_indicators.items():
                if any(indicator in content for indicator in indicators):
                    if framework not in frameworks:
                        frameworks[framework] = []
                    frameworks[framework].append(file_path)
        
        return frameworks
    
    def _build_component_hierarchy(self, code_files: List[Dict]) -> Dict[str, Any]:
        """Build component/class hierarchy"""
        hierarchy = {
            'classes': [],
            'inheritance': {},
            'imports': {}
        }
        
        for file_data in code_files:
            content = file_data.get('content', '')
            file_path = file_data.get('path', '')
            
            # Find class definitions
            class_matches = re.findall(
                r'class\s+(\w+)(?:\(([^)]+)\))?:',
                content
            )
            
            for class_name, parent_classes in class_matches:
                hierarchy['classes'].append({
                    'name': class_name,
                    'file': file_path
                })
                
                if parent_classes:
                    parents = [p.strip() for p in parent_classes.split(',')]
                    hierarchy['inheritance'][class_name] = parents
            
            # Extract imports
            import_matches = re.findall(
                r'(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))',
                content
            )
            
            if import_matches:
                hierarchy['imports'][file_path] = [
                    m[0] or m[1] for m in import_matches
                ]
        
        return hierarchy