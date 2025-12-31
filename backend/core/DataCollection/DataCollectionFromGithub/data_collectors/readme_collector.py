"""
README and Documentation Collector
Collects setup instructions, architecture docs, and onboarding materials
"""

from typing import Dict, List, Any, Optional
import re


class ReadmeCollector:
    """Extracts structured onboarding information from README and docs"""
    
    def __init__(self):
        self.setup_keywords = [
            'installation', 'setup', 'getting started', 'quick start',
            'prerequisites', 'requirements', 'configuration', 'environment'
        ]
        self.architecture_keywords = [
            'architecture', 'structure', 'design', 'components', 
            'system design', 'overview', 'how it works'
        ]
    
    def collect_readme_data(self, documentation_files: List[Dict]) -> Dict[str, Any]:
        """Extract structured data from README and documentation files"""
        
        readme_data = {
            'setup_instructions': [],
            'architecture_overview': {},
            'environment_variables': [],
            'dependencies_info': {},
            'quick_start_guide': [],
            'troubleshooting': [],
            'api_documentation': [],
            'deployment_info': []
        }
        
        for doc in documentation_files:
            content = doc.get('content', '')
            file_name = doc.get('name', '').lower()
            
            # Process README files
            if 'readme' in file_name:
                readme_data['setup_instructions'].extend(
                    self._extract_setup_instructions(content)
                )
                readme_data['environment_variables'].extend(
                    self._extract_env_variables(content)
                )
                readme_data['quick_start_guide'].extend(
                    self._extract_quick_start(content)
                )
                readme_data['architecture_overview'] = self._extract_architecture(content)
            
            # Process specific documentation files
            if 'contributing' in file_name:
                readme_data['setup_instructions'].extend(
                    self._extract_contributing_setup(content)
                )
            
            if 'deploy' in file_name or 'deployment' in file_name:
                readme_data['deployment_info'].extend(
                    self._extract_deployment_info(content)
                )
            
            if 'troubleshoot' in file_name or 'faq' in file_name:
                readme_data['troubleshooting'].extend(
                    self._extract_troubleshooting(content)
                )
            
            if 'api' in file_name:
                readme_data['api_documentation'].extend(
                    self._extract_api_docs(content)
                )
        
        return readme_data
    
    def _extract_setup_instructions(self, content: str) -> List[Dict]:
        """Extract setup and installation instructions"""
        instructions = []
        lines = content.split('\n')
        
        in_setup_section = False
        current_section = None
        current_steps = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Detect setup section headers
            if any(keyword in line_lower for keyword in self.setup_keywords):
                if current_section and current_steps:
                    instructions.append({
                        'section': current_section,
                        'steps': current_steps,
                        'line_number': i
                    })
                current_section = line.strip('#').strip()
                current_steps = []
                in_setup_section = True
            
            # Extract numbered or bulleted steps
            elif in_setup_section:
                if re.match(r'^\s*[\d\-\*\+]\s+', line):
                    current_steps.append(line.strip())
                elif line.startswith('```') and current_steps:
                    # End of setup section
                    in_setup_section = False
                    if current_section:
                        instructions.append({
                            'section': current_section,
                            'steps': current_steps,
                            'line_number': i
                        })
        
        # Add last section if exists
        if current_section and current_steps:
            instructions.append({
                'section': current_section,
                'steps': current_steps,
                'line_number': len(lines)
            })
        
        return instructions
    
    def _extract_env_variables(self, content: str) -> List[Dict]:
        """Extract environment variables and configuration"""
        env_vars = []
        
        # Pattern 1: .env file format
        env_pattern = r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$'
        
        # Pattern 2: Documented env vars
        doc_pattern = r'`([A-Z_][A-Z0-9_]*)`[:\s-]*(.{0,200})'
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Check for .env format
            match = re.match(env_pattern, line.strip())
            if match:
                env_vars.append({
                    'name': match.group(1),
                    'example_value': match.group(2).strip(),
                    'line_number': i + 1,
                    'format': 'env_file'
                })
            
            # Check for documented format
            match = re.search(doc_pattern, line)
            if match:
                env_vars.append({
                    'name': match.group(1),
                    'description': match.group(2).strip(),
                    'line_number': i + 1,
                    'format': 'documented'
                })
        
        return env_vars
    
    def _extract_architecture(self, content: str) -> Dict[str, Any]:
        """Extract architecture and system design information"""
        architecture = {
            'overview': '',
            'components': [],
            'diagrams': [],
            'tech_stack': []
        }
        
        lines = content.split('\n')
        in_arch_section = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in self.architecture_keywords):
                in_arch_section = True
                architecture['overview'] = line.strip('#').strip()
            
            elif in_arch_section:
                # Extract component lists
                if re.match(r'^\s*[\-\*\+]\s+', line):
                    architecture['components'].append(line.strip())
                
                # Detect diagram references
                if 'diagram' in line_lower or line.strip().startswith('!['):
                    architecture['diagrams'].append({
                        'reference': line.strip(),
                        'line_number': i + 1
                    })
                
                # End section on next major header
                if line.startswith('#') and not any(k in line_lower for k in self.architecture_keywords):
                    in_arch_section = False
        
        return architecture
    
    def _extract_quick_start(self, content: str) -> List[Dict]:
        """Extract quick start or getting started guide"""
        quick_start = []
        lines = content.split('\n')
        
        in_quick_start = False
        code_blocks = []
        current_block = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            if 'quick start' in line_lower or 'getting started' in line_lower:
                in_quick_start = True
            
            elif in_quick_start:
                if line.strip().startswith('```'):
                    if current_block:
                        code_blocks.append('\n'.join(current_block))
                        current_block = []
                    else:
                        current_block = []
                elif current_block is not None and len(current_block) >= 0:
                    if line.strip() and not line.strip().startswith('```'):
                        current_block.append(line)
                
                if line.startswith('#') and 'quick start' not in line_lower:
                    in_quick_start = False
        
        for i, block in enumerate(code_blocks):
            quick_start.append({
                'step': i + 1,
                'code': block,
                'type': 'command' if block.strip().startswith('$') else 'code'
            })
        
        return quick_start
    
    def _extract_contributing_setup(self, content: str) -> List[Dict]:
        """Extract development setup from CONTRIBUTING file"""
        setup_steps = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if re.match(r'^\s*[\d\-\*\+]\s+', line):
                setup_steps.append({
                    'step': line.strip(),
                    'line_number': i + 1,
                    'source': 'CONTRIBUTING.md'
                })
        
        return setup_steps
    
    def _extract_deployment_info(self, content: str) -> List[Dict]:
        """Extract deployment instructions"""
        deployment = []
        lines = content.split('\n')
        
        current_method = None
        current_steps = []
        
        for i, line in enumerate(lines):
            if line.startswith('#'):
                if current_method and current_steps:
                    deployment.append({
                        'method': current_method,
                        'steps': current_steps
                    })
                current_method = line.strip('#').strip()
                current_steps = []
            elif re.match(r'^\s*[\d\-\*\+]\s+', line):
                current_steps.append(line.strip())
        
        if current_method and current_steps:
            deployment.append({
                'method': current_method,
                'steps': current_steps
            })
        
        return deployment
    
    def _extract_troubleshooting(self, content: str) -> List[Dict]:
        """Extract troubleshooting and FAQ information"""
        troubleshooting = []
        lines = content.split('\n')
        
        current_issue = None
        current_solution = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Detect Q&A or issue patterns
            if line.startswith('##') or line.lower().startswith('q:') or 'error' in line_lower:
                if current_issue and current_solution:
                    troubleshooting.append({
                        'issue': current_issue,
                        'solution': '\n'.join(current_solution),
                        'line_number': i
                    })
                current_issue = line.strip('#').strip()
                current_solution = []
            elif current_issue and line.strip():
                current_solution.append(line.strip())
        
        if current_issue and current_solution:
            troubleshooting.append({
                'issue': current_issue,
                'solution': '\n'.join(current_solution),
                'line_number': len(lines)
            })
        
        return troubleshooting
    
    def _extract_api_docs(self, content: str) -> List[Dict]:
        """Extract API documentation"""
        api_docs = []
        lines = content.split('\n')
        
        current_endpoint = None
        current_details = {}
        
        for i, line in enumerate(lines):
            # Detect endpoint definitions
            if re.search(r'(GET|POST|PUT|DELETE|PATCH)\s+/', line):
                if current_endpoint:
                    api_docs.append(current_details)
                
                current_endpoint = line.strip()
                current_details = {
                    'endpoint': current_endpoint,
                    'description': '',
                    'parameters': [],
                    'line_number': i + 1
                }
            elif current_endpoint:
                if 'parameter' in line.lower() or 'param' in line.lower():
                    current_details['parameters'].append(line.strip())
                elif line.strip() and not line.startswith('#'):
                    current_details['description'] += line.strip() + ' '
        
        if current_endpoint:
            api_docs.append(current_details)
        
        return api_docs