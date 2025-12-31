"""
Configuration Files Collector
Extracts setup and environment configuration from various config files
"""

from typing import Dict, List, Any
import json
import re


class ConfigCollector:
    """Collects and parses configuration files for environment setup"""
    
    def __init__(self):
        self.config_file_patterns = {
            'package.json': self._parse_package_json,
            'requirements.txt': self._parse_requirements,
            'Pipfile': self._parse_pipfile,
            'pyproject.toml': self._parse_pyproject,
            'Cargo.toml': self._parse_cargo,
            'pom.xml': self._parse_maven,
            'build.gradle': self._parse_gradle,
            'docker-compose.yml': self._parse_docker_compose,
            'Dockerfile': self._parse_dockerfile,
            '.env.example': self._parse_env_example,
            'config.json': self._parse_config_json,
            'settings.json': self._parse_config_json,
            'tsconfig.json': self._parse_tsconfig,
            'webpack.config.js': self._parse_webpack,
            '.gitignore': self._parse_gitignore
        }
    
    def collect_config_data(self, dependency_files: List[Dict], code_files: List[Dict]) -> Dict[str, Any]:
        """Extract configuration and setup data from various config files"""
        
        config_data = {
            'dependencies': {
                'runtime': [],
                'development': [],
                'peer': [],
                'optional': []
            },
            'scripts': [],
            'environment_setup': {
                'required_env_vars': [],
                'optional_env_vars': [],
                'default_values': {}
            },
            'build_config': {},
            'docker_config': {},
            'database_config': {},
            'api_config': {},
            'testing_config': {},
            'ports_and_services': []
        }
        
        all_files = dependency_files + [f for f in code_files if self._is_config_file(f)]
        
        for file_data in all_files:
            file_name = file_data.get('name', '').lower()
            content = file_data.get('content', '')
            
            # Match and parse using appropriate parser
            for pattern, parser in self.config_file_patterns.items():
                if pattern.lower() in file_name:
                    parsed_data = parser(content, file_name)
                    self._merge_config_data(config_data, parsed_data, file_name)
                    break
        
        return config_data
    
    def _is_config_file(self, file_data: Dict) -> bool:
        """Check if file is a configuration file"""
        file_name = file_data.get('name', '').lower()
        config_patterns = [
            'config', 'settings', '.env', 'docker', 
            'webpack', 'babel', 'eslint', 'tsconfig'
        ]
        return any(pattern in file_name for pattern in config_patterns)
    
    def _parse_package_json(self, content: str, file_name: str) -> Dict:
        """Parse Node.js package.json"""
        try:
            data = json.loads(content)
            return {
                'dependencies': {
                    'runtime': list(data.get('dependencies', {}).keys()),
                    'development': list(data.get('devDependencies', {}).keys()),
                    'peer': list(data.get('peerDependencies', {}).keys()),
                    'optional': list(data.get('optionalDependencies', {}).keys())
                },
                'scripts': [
                    {'name': k, 'command': v} 
                    for k, v in data.get('scripts', {}).items()
                ],
                'engines': data.get('engines', {}),
                'metadata': {
                    'name': data.get('name'),
                    'version': data.get('version'),
                    'description': data.get('description')
                }
            }
        except json.JSONDecodeError:
            return {}
    
    def _parse_requirements(self, content: str, file_name: str) -> Dict:
        """Parse Python requirements.txt"""
        dependencies = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name and version
                match = re.match(r'^([a-zA-Z0-9\-_]+)([><=!]+.*)?$', line)
                if match:
                    dependencies.append({
                        'name': match.group(1),
                        'version': match.group(2).strip() if match.group(2) else 'latest'
                    })
        
        return {
            'dependencies': {
                'runtime': [d['name'] for d in dependencies]
            },
            'python_packages': dependencies
        }
    
    def _parse_pipfile(self, content: str, file_name: str) -> Dict:
        """Parse Python Pipfile"""
        runtime_deps = []
        dev_deps = []
        python_version = None
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line == '[packages]':
                current_section = 'runtime'
            elif line == '[dev-packages]':
                current_section = 'dev'
            elif line.startswith('python_version'):
                python_version = line.split('=')[1].strip().strip('"\'')
            elif current_section and '=' in line and not line.startswith('['):
                pkg_name = line.split('=')[0].strip()
                if current_section == 'runtime':
                    runtime_deps.append(pkg_name)
                elif current_section == 'dev':
                    dev_deps.append(pkg_name)
        
        return {
            'dependencies': {
                'runtime': runtime_deps,
                'development': dev_deps
            },
            'python_version': python_version
        }
    
    def _parse_pyproject(self, content: str, file_name: str) -> Dict:
        """Parse Python pyproject.toml"""
        dependencies = []
        dev_dependencies = []
        
        # Simple TOML parsing for dependencies
        in_deps = False
        in_dev_deps = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            if '[tool.poetry.dependencies]' in line:
                in_deps = True
                in_dev_deps = False
            elif '[tool.poetry.dev-dependencies]' in line:
                in_dev_deps = True
                in_deps = False
            elif line.startswith('['):
                in_deps = False
                in_dev_deps = False
            elif in_deps and '=' in line:
                pkg = line.split('=')[0].strip()
                if pkg != 'python':
                    dependencies.append(pkg)
            elif in_dev_deps and '=' in line:
                dev_dependencies.append(line.split('=')[0].strip())
        
        return {
            'dependencies': {
                'runtime': dependencies,
                'development': dev_dependencies
            }
        }
    
    def _parse_cargo(self, content: str, file_name: str) -> Dict:
        """Parse Rust Cargo.toml"""
        dependencies = []
        dev_dependencies = []
        
        in_deps = False
        in_dev_deps = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line == '[dependencies]':
                in_deps = True
                in_dev_deps = False
            elif line == '[dev-dependencies]':
                in_dev_deps = True
                in_deps = False
            elif line.startswith('['):
                in_deps = False
                in_dev_deps = False
            elif in_deps and '=' in line:
                dependencies.append(line.split('=')[0].strip())
            elif in_dev_deps and '=' in line:
                dev_dependencies.append(line.split('=')[0].strip())
        
        return {
            'dependencies': {
                'runtime': dependencies,
                'development': dev_dependencies
            }
        }
    
    def _parse_maven(self, content: str, file_name: str) -> Dict:
        """Parse Maven pom.xml"""
        dependencies = []
        
        # Simple XML parsing for dependencies
        dep_pattern = r'<artifactId>(.*?)</artifactId>'
        matches = re.findall(dep_pattern, content)
        
        return {
            'dependencies': {
                'runtime': matches
            }
        }
    
    def _parse_gradle(self, content: str, file_name: str) -> Dict:
        """Parse Gradle build file"""
        dependencies = []
        
        for line in content.split('\n'):
            if 'implementation' in line or 'compile' in line:
                match = re.search(r"['\"](.+?)['\"]", line)
                if match:
                    dependencies.append(match.group(1))
        
        return {
            'dependencies': {
                'runtime': dependencies
            }
        }
    
    def _parse_docker_compose(self, content: str, file_name: str) -> Dict:
        """Parse docker-compose.yml"""
        services = []
        ports = []
        volumes = []
        env_vars = []
        
        lines = content.split('\n')
        current_service = None
        
        for line in lines:
            stripped = line.strip()
            
            # Detect service definitions
            if re.match(r'^[a-zA-Z0-9_-]+:', stripped) and not stripped.startswith('-'):
                current_service = stripped.rstrip(':')
                if current_service not in ['version', 'volumes', 'networks', 'services']:
                    services.append(current_service)
            
            # Extract ports
            elif 'ports:' in stripped or (current_service and re.match(r'-\s*"\d+:\d+"', stripped)):
                port_match = re.search(r'(\d+):(\d+)', stripped)
                if port_match:
                    ports.append({
                        'service': current_service,
                        'host': port_match.group(1),
                        'container': port_match.group(2)
                    })
            
            # Extract environment variables
            elif current_service and re.match(r'-\s*[A-Z_]+=', stripped):
                env_match = re.match(r'-\s*([A-Z_][A-Z0-9_]*)=(.*)', stripped)
                if env_match:
                    env_vars.append({
                        'service': current_service,
                        'name': env_match.group(1),
                        'value': env_match.group(2)
                    })
        
        return {
            'docker_config': {
                'services': services,
                'ports': ports,
                'environment_variables': env_vars
            }
        }
    
    def _parse_dockerfile(self, content: str, file_name: str) -> Dict:
        """Parse Dockerfile"""
        base_image = None
        exposed_ports = []
        env_vars = []
        commands = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith('FROM'):
                base_image = line.split()[1] if len(line.split()) > 1 else None
            elif line.startswith('EXPOSE'):
                ports = line.split()[1:]
                exposed_ports.extend(ports)
            elif line.startswith('ENV'):
                env_match = re.match(r'ENV\s+([A-Z_][A-Z0-9_]*)\s*=?\s*(.*)', line)
                if env_match:
                    env_vars.append({
                        'name': env_match.group(1),
                        'value': env_match.group(2)
                    })
            elif line.startswith('RUN'):
                commands.append(line[4:].strip())
        
        return {
            'docker_config': {
                'base_image': base_image,
                'exposed_ports': exposed_ports,
                'build_commands': commands,
                'environment_variables': env_vars
            }
        }
    
    def _parse_env_example(self, content: str, file_name: str) -> Dict:
        """Parse .env.example or .env files"""
        required_vars = []
        optional_vars = []
        defaults = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Check if it's a placeholder or has actual value
                if not value or value in ['', '""', "''", '<your-value>']:
                    required_vars.append(key)
                else:
                    optional_vars.append(key)
                    defaults[key] = value
        
        return {
            'environment_setup': {
                'required_env_vars': required_vars,
                'optional_env_vars': optional_vars,
                'default_values': defaults
            }
        }
    
    def _parse_config_json(self, content: str, file_name: str) -> Dict:
        """Parse generic JSON config files"""
        try:
            data = json.loads(content)
            return {
                'api_config': data if 'api' in file_name or 'server' in file_name else {},
                'database_config': data if 'database' in file_name or 'db' in file_name else {},
                'general_config': data
            }
        except json.JSONDecodeError:
            return {}
    
    def _parse_tsconfig(self, content: str, file_name: str) -> Dict:
        """Parse TypeScript tsconfig.json"""
        try:
            data = json.loads(content)
            return {
                'build_config': {
                    'typescript': data.get('compilerOptions', {}),
                    'include': data.get('include', []),
                    'exclude': data.get('exclude', [])
                }
            }
        except json.JSONDecodeError:
            return {}
    
    def _parse_webpack(self, content: str, file_name: str) -> Dict:
        """Parse webpack configuration"""
        entry_points = []
        output_path = None
        
        # Simple regex-based extraction
        entry_match = re.search(r"entry:\s*['\"](.+?)['\"]", content)
        if entry_match:
            entry_points.append(entry_match.group(1))
        
        output_match = re.search(r"path:\s*['\"](.+?)['\"]", content)
        if output_match:
            output_path = output_match.group(1)
        
        return {
            'build_config': {
                'webpack': {
                    'entry_points': entry_points,
                    'output_path': output_path
                }
            }
        }
    
    def _parse_gitignore(self, content: str, file_name: str) -> Dict:
        """Parse .gitignore to understand what's excluded"""
        ignored_patterns = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                ignored_patterns.append(line)
        
        return {
            'build_config': {
                'ignored_files': ignored_patterns
            }
        }
    
    def _merge_config_data(self, target: Dict, source: Dict, file_name: str) -> None:
        """Merge parsed config data into main config structure"""
        for key, value in source.items():
            if key == 'dependencies' and isinstance(value, dict):
                for dep_type, deps in value.items():
                    if deps:
                        target['dependencies'][dep_type].extend(deps)
            
            elif key == 'scripts' and isinstance(value, list):
                target['scripts'].extend([
                    {**script, 'source': file_name} for script in value
                ])
            
            elif key == 'environment_setup' and isinstance(value, dict):
                for env_key, env_value in value.items():
                    if isinstance(env_value, list):
                        target['environment_setup'][env_key].extend(env_value)
                    elif isinstance(env_value, dict):
                        target['environment_setup'][env_key].update(env_value)
            
            elif key in target and isinstance(value, dict):
                if isinstance(target[key], dict):
                    target[key].update(value)
                else:
                    target[key] = value