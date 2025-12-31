"""
Workflow and Process Collector
Extracts CI/CD pipelines, workflows, and development processes
"""

from typing import Dict, List, Any
import re
import yaml


class WorkflowCollector:
    """Collects CI/CD and workflow information"""
    
    def __init__(self):
        self.workflow_files = {
            '.github/workflows': 'github_actions',
            '.gitlab-ci.yml': 'gitlab_ci',
            'Jenkinsfile': 'jenkins',
            '.travis.yml': 'travis',
            'azure-pipelines.yml': 'azure',
            'bitbucket-pipelines.yml': 'bitbucket',
            'Makefile': 'make',
            '.circleci/config.yml': 'circleci'
        }
    
    def collect_workflow_data(self, code_files: List[Dict], repo_data: Dict) -> Dict[str, Any]:
        """Extract workflow and CI/CD information"""
        
        workflow_data = {
            'ci_cd_pipelines': [],
            'build_steps': [],
            'deployment_steps': [],
            'test_commands': [],
            'code_quality_checks': [],
            'branch_protection': {},
            'release_process': {},
            'scripts': []
        }
        
        # Find and parse workflow files
        for file_data in code_files:
            file_path = file_data.get('path', '')
            file_name = file_data.get('name', '')
            content = file_data.get('content', '')
            
            # GitHub Actions
            if '.github/workflows' in file_path and file_name.endswith('.yml'):
                pipeline = self._parse_github_actions(content, file_name)
                workflow_data['ci_cd_pipelines'].append(pipeline)
            
            # GitLab CI
            elif file_name == '.gitlab-ci.yml':
                pipeline = self._parse_gitlab_ci(content)
                workflow_data['ci_cd_pipelines'].append(pipeline)
            
            # Jenkinsfile
            elif file_name == 'Jenkinsfile':
                pipeline = self._parse_jenkinsfile(content)
                workflow_data['ci_cd_pipelines'].append(pipeline)
            
            # Makefile
            elif file_name == 'Makefile':
                scripts = self._parse_makefile(content)
                workflow_data['scripts'].extend(scripts)
            
            # Travis CI
            elif file_name == '.travis.yml':
                pipeline = self._parse_travis(content)
                workflow_data['ci_cd_pipelines'].append(pipeline)
        
        # Extract test commands from pipelines
        for pipeline in workflow_data['ci_cd_pipelines']:
            if 'jobs' in pipeline:
                for job in pipeline['jobs']:
                    for step in job.get('steps', []):
                        if any(x in step.get('name', '').lower() for x in ['test', 'lint', 'check']):
                            workflow_data['test_commands'].append(step)
        
        # Extract code quality checks
        workflow_data['code_quality_checks'] = self._extract_quality_checks(workflow_data['ci_cd_pipelines'])
        
        return workflow_data
    
    def _parse_github_actions(self, content: str, file_name: str) -> Dict[str, Any]:
        """Parse GitHub Actions workflow"""
        try:
            workflow = yaml.safe_load(content)
            
            pipeline = {
                'name': workflow.get('name', file_name),
                'type': 'github_actions',
                'file': file_name,
                'triggers': [],
                'jobs': []
            }
            
            # Extract triggers
            if 'on' in workflow:
                triggers = workflow['on']
                if isinstance(triggers, dict):
                    pipeline['triggers'] = list(triggers.keys())
                elif isinstance(triggers, list):
                    pipeline['triggers'] = triggers
                else:
                    pipeline['triggers'] = [str(triggers)]
            
            # Extract jobs
            if 'jobs' in workflow:
                for job_name, job_config in workflow['jobs'].items():
                    job_data = {
                        'name': job_name,
                        'runs_on': job_config.get('runs-on', 'unknown'),
                        'steps': []
                    }
                    
                    if 'steps' in job_config:
                        for step in job_config['steps']:
                            step_info = {
                                'name': step.get('name', 'Unnamed step'),
                                'uses': step.get('uses'),
                                'run': step.get('run'),
                                'with': step.get('with', {})
                            }
                            job_data['steps'].append(step_info)
                    
                    pipeline['jobs'].append(job_data)
            
            return pipeline
        except yaml.YAMLError:
            return {
                'name': file_name,
                'type': 'github_actions',
                'error': 'Failed to parse YAML'
            }
    
    def _parse_gitlab_ci(self, content: str) -> Dict[str, Any]:
        """Parse GitLab CI configuration"""
        try:
            config = yaml.safe_load(content)
            
            pipeline = {
                'name': 'GitLab CI Pipeline',
                'type': 'gitlab_ci',
                'stages': config.get('stages', []),
                'jobs': []
            }
            
            # Extract jobs
            for key, value in config.items():
                if isinstance(value, dict) and 'script' in value:
                    job = {
                        'name': key,
                        'stage': value.get('stage', 'unknown'),
                        'script': value.get('script', []),
                        'before_script': value.get('before_script', []),
                        'after_script': value.get('after_script', [])
                    }
                    pipeline['jobs'].append(job)
            
            return pipeline
        except yaml.YAMLError:
            return {
                'name': 'GitLab CI Pipeline',
                'type': 'gitlab_ci',
                'error': 'Failed to parse YAML'
            }
    
    def _parse_jenkinsfile(self, content: str) -> Dict[str, Any]:
        """Parse Jenkinsfile"""
        pipeline = {
            'name': 'Jenkins Pipeline',
            'type': 'jenkins',
            'stages': [],
            'triggers': []
        }
        
        # Extract stages
        stage_matches = re.findall(r'stage\([\'"]([^\'"]+)[\'"]\)', content)
        pipeline['stages'] = stage_matches
        
        # Extract triggers
        if 'cron(' in content:
            pipeline['triggers'].append('cron')
        if 'pollSCM(' in content:
            pipeline['triggers'].append('pollSCM')
        
        return pipeline
    
    def _parse_makefile(self, content: str) -> List[Dict]:
        """Parse Makefile targets"""
        scripts = []
        
        lines = content.split('\n')
        current_target = None
        current_commands = []
        
        for line in lines:
            # Target definition
            if line and not line.startswith('\t') and ':' in line and not line.startswith('#'):
                if current_target:
                    scripts.append({
                        'name': current_target,
                        'type': 'make',
                        'commands': current_commands
                    })
                
                current_target = line.split(':')[0].strip()
                current_commands = []
            
            # Command under target
            elif line.startswith('\t') and current_target:
                current_commands.append(line.strip())
        
        # Add last target
        if current_target:
            scripts.append({
                'name': current_target,
                'type': 'make',
                'commands': current_commands
            })
        
        return scripts
    
    def _parse_travis(self, content: str) -> Dict[str, Any]:
        """Parse Travis CI configuration"""
        try:
            config = yaml.safe_load(content)
            
            pipeline = {
                'name': 'Travis CI Pipeline',
                'type': 'travis',
                'language': config.get('language'),
                'jobs': []
            }
            
            # Extract script steps
            if 'script' in config:
                pipeline['jobs'].append({
                    'name': 'main',
                    'steps': config['script'] if isinstance(config['script'], list) else [config['script']]
                })
            
            return pipeline
        except yaml.YAMLError:
            return {
                'name': 'Travis CI Pipeline',
                'type': 'travis',
                'error': 'Failed to parse YAML'
            }
    
    def _extract_quality_checks(self, pipelines: List[Dict]) -> List[Dict]:
        """Extract code quality and linting steps"""
        quality_checks = []
        
        quality_keywords = [
            'lint', 'eslint', 'pylint', 'flake8', 'black',
            'prettier', 'sonar', 'coverage', 'test', 'security'
        ]
        
        for pipeline in pipelines:
            for job in pipeline.get('jobs', []):
                for step in job.get('steps', []):
                    step_name = step.get('name', '').lower()
                    step_run = str(step.get('run', '')).lower()
                    
                    if any(keyword in step_name or keyword in step_run for keyword in quality_keywords):
                        quality_checks.append({
                            'name': step.get('name'),
                            'command': step.get('run'),
                            'pipeline': pipeline.get('name'),
                            'job': job.get('name')
                        })
        
        return quality_checks