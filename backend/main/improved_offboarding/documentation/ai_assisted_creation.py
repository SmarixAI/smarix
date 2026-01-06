"""
AI-Assisted Creation Module
Implements features 79-83: Outline generation, section headers, content drafting, etc.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
import re


class AIAssistedCreator:
    """
    Assists with documentation creation using AI (Features 79-83)
    Note: This is a rule-based implementation with placeholders for AI integration
    """
    
    def __init__(self):
        self.outlines = {}
        self.code_mappings = {}
    
    def process(self, prerequisite_data: Dict[str, Any], 
               detection_results: Dict[str, Any],
               final_call_data: Optional[Dict[str, Any]] = None,
               handover_data: Optional[Dict[str, Any]] = None,
               employee_username: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all AI-assisted creation features
        
        Args:
            prerequisite_data: Complete prerequisite analysis results
            detection_results: Results from documentation detection
            final_call_data: Final Call results (optional)
            handover_data: Handover results (optional)
            employee_username: Departing employee username
            
        Returns:
            Dictionary with all AI-assisted creation results
        """
        results = {
            'documentation_outlines': self._generate_documentation_outlines(detection_results, prerequisite_data),
            'section_headers': self._generate_section_headers(detection_results, prerequisite_data),
            'content_drafting': self._assist_content_drafting(detection_results, prerequisite_data, final_call_data),
            'code_to_doc_mapping': self._map_code_to_documentation(detection_results, prerequisite_data),
            'diagram_suggestions': self._suggest_diagrams(detection_results, prerequisite_data)
        }
        
        return results
    
    def _generate_documentation_outlines(self, detection_results: Dict[str, Any], 
                                        prerequisite_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 79: AI-generated documentation outline"""
        prioritized_docs = detection_results.get('documentation_priority', {}).get('prioritized_documentation', [])
        type_definitions = detection_results.get('required_documentation_types', {}).get('type_definitions', {})
        
        outlines = []
        
        for doc_item in prioritized_docs:
            file_path = doc_item.get('file', '')
            doc_type = doc_item.get('recommended_doc_type', 'general')
            priority = doc_item.get('priority_level', 'medium')
            
            # Get section template for doc type
            type_def = type_definitions.get(doc_type, {})
            base_sections = type_def.get('sections', ['overview', 'usage'])
            
            # Generate outline
            outline_sections = []
            
            for section_name in base_sections:
                outline_sections.append({
                    'section': section_name,
                    'title': self._format_section_title(section_name),
                    'description': self._generate_section_description(section_name, file_path, doc_type),
                    'estimated_content_length': self._estimate_content_length(section_name),
                    'key_points': self._suggest_key_points(section_name, file_path, prerequisite_data)
                })
            
            # Add additional sections based on file type
            additional_sections = self._suggest_additional_sections(file_path, doc_type, prerequisite_data)
            outline_sections.extend(additional_sections)
            
            outlines.append({
                'file': file_path,
                'doc_type': doc_type,
                'priority': priority,
                'outline': {
                    'title': self._generate_doc_title(file_path),
                    'sections': outline_sections,
                    'total_sections': len(outline_sections),
                    'estimated_pages': sum(s.get('estimated_content_length', 1) for s in outline_sections) / 2
                },
                'ai_confidence': 0.8  # Would be calculated by AI in real system
            })
        
        self.outlines = {outline.get('file', ''): outline for outline in outlines}
        
        return {
            'documentation_outlines': outlines,
            'total_outlines': len(outlines),
            'outlines_by_priority': {
                'critical': [o for o in outlines if o.get('priority') == 'critical'],
                'high': [o for o in outlines if o.get('priority') == 'high'],
                'medium': [o for o in outlines if o.get('priority') == 'medium']
            }
        }
    
    def _format_section_title(self, section_name: str) -> str:
        """Format section name as title"""
        return section_name.replace('_', ' ').title()
    
    def _generate_section_description(self, section_name: str, file_path: str, doc_type: str) -> str:
        """Generate description for section"""
        descriptions = {
            'overview': f"Overview of {file_path} - purpose, functionality, and key concepts",
            'architecture': f"Architecture and design of {file_path} - components, structure, and relationships",
            'usage': f"How to use {file_path} - examples, common patterns, and best practices",
            'api': f"API reference for {file_path} - endpoints, parameters, and responses",
            'examples': f"Code examples and use cases for {file_path}",
            'troubleshooting': f"Common issues, errors, and solutions for {file_path}",
            'deployment': f"Deployment procedures and configuration for {file_path}",
            'monitoring': f"Monitoring, logging, and observability for {file_path}",
            'escalation': f"Escalation procedures and on-call information for {file_path}",
            'design_decisions': f"Key design decisions and rationale for {file_path}",
            'dependencies': f"Dependencies and integration points for {file_path}",
            'key_concepts': f"Key concepts and domain knowledge for {file_path}",
            'common_issues': f"Common issues and gotchas for {file_path}",
            'gotchas': f"Important gotchas and warnings for {file_path}"
        }
        return descriptions.get(section_name, f"Content for {section_name} section")
    
    def _estimate_content_length(self, section_name: str) -> int:
        """Estimate content length in paragraphs"""
        estimates = {
            'overview': 2,
            'architecture': 4,
            'usage': 3,
            'api': 5,
            'examples': 3,
            'troubleshooting': 4,
            'deployment': 3,
            'monitoring': 2,
            'escalation': 2,
            'design_decisions': 3,
            'dependencies': 2,
            'key_concepts': 3,
            'common_issues': 2,
            'gotchas': 2
        }
        return estimates.get(section_name, 2)
    
    def _suggest_key_points(self, section_name: str, file_path: str, 
                           prerequisite_data: Dict[str, Any]) -> List[str]:
        """Suggest key points for section"""
        key_points = []
        
        if section_name == 'overview':
            key_points = [
                f"Purpose and functionality of {file_path}",
                "Main components and their roles",
                "Key features and capabilities"
            ]
        elif section_name == 'architecture':
            key_points = [
                "System architecture and components",
                "Data flow and interactions",
                "Design patterns used"
            ]
        elif section_name == 'troubleshooting':
            key_points = [
                "Common error messages and solutions",
                "Debugging techniques",
                "Performance issues and optimization"
            ]
        else:
            key_points = [
                f"Key information about {section_name}",
                "Important considerations",
                "Best practices"
            ]
        
        return key_points
    
    def _suggest_additional_sections(self, file_path: str, doc_type: str, 
                                     prerequisite_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest additional sections based on file and type"""
        additional = []
        
        if doc_type == 'runbook':
            additional.append({
                'section': 'incident_response',
                'title': 'Incident Response',
                'description': 'Procedures for handling incidents',
                'estimated_content_length': 2,
                'key_points': ['Incident detection', 'Response procedures', 'Recovery steps']
            })
        
        if 'api' in file_path.lower() or doc_type == 'api':
            additional.append({
                'section': 'authentication',
                'title': 'Authentication',
                'description': 'Authentication and authorization',
                'estimated_content_length': 2,
                'key_points': ['Auth methods', 'Token management', 'Permissions']
            })
        
        return additional
    
    def _generate_doc_title(self, file_path: str) -> str:
        """Generate documentation title"""
        filename = file_path.split('/')[-1] if '/' in file_path else file_path
        name = filename.replace('.py', '').replace('.js', '').replace('.ts', '').replace('.java', '')
        return f"{name.replace('_', ' ').title()} Documentation"
    
    def _generate_section_headers(self, detection_results: Dict[str, Any], 
                                 prerequisite_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 80: AI-generated section headers"""
        outlines = self._generate_documentation_outlines(detection_results, prerequisite_data)
        doc_outlines = outlines.get('documentation_outlines', [])
        
        section_headers = {}
        
        for outline in doc_outlines:
            file_path = outline.get('file', '')
            sections = outline.get('outline', {}).get('sections', [])
            
            headers = []
            for section in sections:
                section_name = section.get('section', '')
                title = section.get('title', '')
                
                # Generate header hierarchy
                headers.append({
                    'level': 1 if section_name == 'overview' else 2,
                    'header': title,
                    'section_id': section_name,
                    'anchor': self._generate_anchor(section_name),
                    'subsections': self._generate_subsections(section_name, file_path, prerequisite_data)
                })
            
            section_headers[file_path] = {
                'file': file_path,
                'headers': headers,
                'total_headers': len(headers),
                'header_structure': self._build_header_structure(headers)
            }
        
        return {
            'section_headers': section_headers,
            'total_docs_with_headers': len(section_headers),
            'total_headers': sum(len(h.get('headers', [])) for h in section_headers.values())
        }
    
    def _generate_anchor(self, section_name: str) -> str:
        """Generate anchor link for section"""
        return section_name.replace('_', '-').lower()
    
    def _generate_subsections(self, section_name: str, file_path: str, 
                             prerequisite_data: Dict[str, Any]) -> List[str]:
        """Generate subsections for a section"""
        subsections_map = {
            'overview': ['Purpose', 'Key Features', 'Use Cases'],
            'architecture': ['Components', 'Data Flow', 'Design Patterns'],
            'usage': ['Basic Usage', 'Advanced Usage', 'Configuration'],
            'api': ['Endpoints', 'Request/Response', 'Error Handling'],
            'troubleshooting': ['Common Issues', 'Debugging', 'Performance']
        }
        return subsections_map.get(section_name, ['Details', 'Examples'])
    
    def _build_header_structure(self, headers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build hierarchical header structure"""
        structure = {
            'main_sections': [h for h in headers if h.get('level') == 1],
            'subsections': [h for h in headers if h.get('level') == 2],
            'total_levels': max([h.get('level', 1) for h in headers]) if headers else 1
        }
        return structure
    
    def _assist_content_drafting(self, detection_results: Dict[str, Any], 
                                prerequisite_data: Dict[str, Any],
                                final_call_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Feature 81: AI-assisted content drafting"""
        prioritized_docs = detection_results.get('documentation_priority', {}).get('prioritized_documentation', [])
        data_collection = prerequisite_data.get('data_collection', {})
        code_files = data_collection.get('code_files', [])
        
        content_drafts = []
        
        for doc_item in prioritized_docs[:10]:  # Top 10 for performance
            file_path = doc_item.get('file', '')
            doc_type = doc_item.get('recommended_doc_type', 'general')
            
            # Find code file
            code_file = next((f for f in code_files if f.get('path') == file_path), None)
            code_content = code_file.get('content', '') if code_file else ''
            
            # Generate draft content for each section
            outline = self.outlines.get(file_path, {})
            sections = outline.get('outline', {}).get('sections', []) if outline else []
            
            draft_sections = []
            for section in sections:
                section_name = section.get('section', '')
                
                # Generate draft content
                draft_content = self._generate_draft_content(
                    section_name, 
                    file_path, 
                    code_content, 
                    doc_type,
                    prerequisite_data,
                    final_call_data
                )
                
                draft_sections.append({
                    'section': section_name,
                    'draft_content': draft_content,
                    'content_length': len(draft_content),
                    'completeness': 'partial',  # Would be 'complete' with full AI
                    'needs_review': True
                })
            
            content_drafts.append({
                'file': file_path,
                'doc_type': doc_type,
                'draft_sections': draft_sections,
                'total_sections': len(draft_sections),
                'overall_completeness': 'partial',
                'ai_confidence': 0.7
            })
        
        return {
            'content_drafts': content_drafts,
            'total_drafts': len(content_drafts),
            'draft_summary': {
                'total_sections_drafted': sum(len(d.get('draft_sections', [])) for d in content_drafts),
                'average_sections_per_doc': sum(len(d.get('draft_sections', [])) for d in content_drafts) / len(content_drafts) if content_drafts else 0
            }
        }
    
    def _generate_draft_content(self, section_name: str, file_path: str, 
                               code_content: str, doc_type: str,
                               prerequisite_data: Dict[str, Any],
                               final_call_data: Optional[Dict[str, Any]]) -> str:
        """Generate draft content for a section"""
        # This is a template - in real system would use AI to generate actual content
        
        if section_name == 'overview':
            return f"""# Overview

{file_path} is a key component of the system. This file provides [functionality description].

## Purpose

[Purpose description based on code analysis]

## Key Features

- Feature 1
- Feature 2
- Feature 3

## Use Cases

[Use cases based on code usage]
"""
        
        elif section_name == 'architecture':
            return f"""# Architecture

## Components

[Component description based on code structure]

## Data Flow

[Data flow description]

## Design Patterns

[Design patterns identified in code]
"""
        
        elif section_name == 'usage':
            return f"""# Usage

## Basic Usage

```python
# Example code snippet
```

## Configuration

[Configuration options]

## Examples

[Usage examples]
"""
        
        else:
            return f"""# {section_name.replace('_', ' ').title()}

[Content for {section_name} section]

## Key Points

- Point 1
- Point 2
- Point 3
"""
    
    def _map_code_to_documentation(self, detection_results: Dict[str, Any], 
                                   prerequisite_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 82: Code-to-doc mapping"""
        prioritized_docs = detection_results.get('documentation_priority', {}).get('prioritized_documentation', [])
        data_collection = prerequisite_data.get('data_collection', {})
        code_files = data_collection.get('code_files', [])
        
        code_mappings = []
        
        for doc_item in prioritized_docs:
            file_path = doc_item.get('file', '')
            
            # Find code file
            code_file = next((f for f in code_files if f.get('path') == file_path), None)
            
            if code_file:
                code_content = code_file.get('content', '')
                
                # Extract code elements
                code_elements = self._extract_code_elements(code_content, file_path)
                
                # Map to documentation sections
                doc_mapping = {
                    'file': file_path,
                    'code_elements': code_elements,
                    'documentation_sections': self._map_elements_to_sections(code_elements, doc_item.get('recommended_doc_type', 'general')),
                    'coverage': {
                        'functions_documented': 0,  # Would calculate based on actual docs
                        'classes_documented': 0,
                        'total_elements': len(code_elements)
                    }
                }
                
                code_mappings.append(doc_mapping)
                self.code_mappings[file_path] = doc_mapping
        
        return {
            'code_to_doc_mappings': code_mappings,
            'total_mappings': len(code_mappings),
            'mapping_summary': {
                'files_mapped': len(code_mappings),
                'total_code_elements': sum(len(m.get('code_elements', [])) for m in code_mappings)
            }
        }
    
    def _extract_code_elements(self, code_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract code elements (functions, classes, etc.)"""
        elements = []
        
        # Extract functions (simple regex - would use AST in real system)
        if file_path.endswith('.py'):
            functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', code_content)
            for func_name in functions:
                elements.append({
                    'type': 'function',
                    'name': func_name,
                    'language': 'python'
                })
            
            classes = re.findall(r'class\s+(\w+)', code_content)
            for class_name in classes:
                elements.append({
                    'type': 'class',
                    'name': class_name,
                    'language': 'python'
                })
        
        elif file_path.endswith(('.js', '.ts')):
            functions = re.findall(r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>)', code_content)
            for match in functions:
                func_name = match[0] or match[1]
                elements.append({
                    'type': 'function',
                    'name': func_name,
                    'language': 'javascript'
                })
        
        return elements
    
    def _map_elements_to_sections(self, code_elements: List[Dict[str, Any]], doc_type: str) -> Dict[str, List[str]]:
        """Map code elements to documentation sections"""
        mapping = defaultdict(list)
        
        for element in code_elements:
            element_name = element.get('name', '')
            element_type = element.get('type', '')
            
            if element_type == 'class':
                mapping['architecture'].append(element_name)
                mapping['api'].append(element_name)
            elif element_type == 'function':
                mapping['api'].append(element_name)
                mapping['usage'].append(element_name)
                mapping['examples'].append(element_name)
        
        return dict(mapping)
    
    def _suggest_diagrams(self, detection_results: Dict[str, Any], 
                         prerequisite_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 83: Diagram suggestion generation"""
        prioritized_docs = detection_results.get('documentation_priority', {}).get('prioritized_documentation', [])
        data_collection = prerequisite_data.get('data_collection', {})
        dependencies = data_collection.get('dependencies', {}).get('file_dependencies', {})
        
        diagram_suggestions = []
        
        for doc_item in prioritized_docs:
            file_path = doc_item.get('file', '')
            doc_type = doc_item.get('recommended_doc_type', 'general')
            
            suggestions = []
            
            # Suggest diagrams based on doc type
            if doc_type == 'architecture':
                suggestions.append({
                    'diagram_type': 'architecture_diagram',
                    'description': 'System architecture diagram showing components and relationships',
                    'format': 'mermaid_or_plantuml',
                    'priority': 'high',
                    'sections': ['architecture', 'overview']
                })
                suggestions.append({
                    'diagram_type': 'component_diagram',
                    'description': 'Component diagram showing internal structure',
                    'format': 'mermaid',
                    'priority': 'medium',
                    'sections': ['architecture']
                })
            
            if doc_type in ['runbook', 'operational']:
                suggestions.append({
                    'diagram_type': 'flowchart',
                    'description': 'Operational flowchart showing procedures',
                    'format': 'mermaid',
                    'priority': 'high',
                    'sections': ['deployment', 'troubleshooting']
                })
            
            # Suggest dependency diagram if file has dependencies
            file_deps = dependencies.get(file_path, [])
            if file_deps:
                suggestions.append({
                    'diagram_type': 'dependency_diagram',
                    'description': f'Dependency diagram showing {len(file_deps)} dependencies',
                    'format': 'mermaid',
                    'priority': 'medium',
                    'sections': ['dependencies', 'architecture'],
                    'dependencies': file_deps[:10]  # Top 10
                })
            
            # Suggest sequence diagram for API docs
            if doc_type == 'api':
                suggestions.append({
                    'diagram_type': 'sequence_diagram',
                    'description': 'Sequence diagram showing API call flow',
                    'format': 'mermaid',
                    'priority': 'high',
                    'sections': ['api', 'usage']
                })
            
            if suggestions:
                diagram_suggestions.append({
                    'file': file_path,
                    'doc_type': doc_type,
                    'suggested_diagrams': suggestions,
                    'total_diagrams': len(suggestions),
                    'high_priority_diagrams': [d for d in suggestions if d.get('priority') == 'high']
                })
        
        return {
            'diagram_suggestions': diagram_suggestions,
            'total_docs_with_diagrams': len(diagram_suggestions),
            'total_diagrams_suggested': sum(len(d.get('suggested_diagrams', [])) for d in diagram_suggestions),
            'diagrams_by_type': self._group_diagrams_by_type(diagram_suggestions)
        }
    
    def _group_diagrams_by_type(self, diagram_suggestions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group diagrams by type"""
        by_type = defaultdict(int)
        for doc_suggestions in diagram_suggestions:
            for diagram in doc_suggestions.get('suggested_diagrams', []):
                by_type[diagram.get('diagram_type', 'unknown')] += 1
        return dict(by_type)

