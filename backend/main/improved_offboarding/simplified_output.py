"""
Simplified Output Formatter
Creates clear, actionable output answering key knowledge transfer questions
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from ai_service import AIService


class SimplifiedOutputFormatter:
    """
    Formats output to answer key questions:
    - "What do they know that others don't?"
    - "What could break after they leave?"
    - "What must the manager ask them before Day-0?"
    """
    
    def __init__(self):
        try:
            self.ai_service = AIService()
            print("✓ AI service initialized for simplified output")
        except Exception as e:
            print(f"⚠️  AI service unavailable: {e}. Using fallback mode.")
            self.ai_service = None
    
    def generate_simplified_output(self,
                                   prerequisite_data: Dict[str, Any],
                                   final_call_data: Dict[str, Any],
                                   handover_data: Optional[Dict[str, Any]] = None,
                                   documentation_data: Optional[Dict[str, Any]] = None,
                                   employee_username: str = "employee") -> Dict[str, Any]:
        """
        Generate simplified, clear output answering key questions
        """
        # Extract high-risk files
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        knowledge_loss_risk = risk_analysis.get('knowledge_loss_risk', {})
        high_risk_files = knowledge_loss_risk.get('high_risk_files', [])
        file_risk_scores = knowledge_loss_risk.get('file_risk_scores', {})
        
        # Get topics from final call
        topics = final_call_data.get('topic_identification', {}).get('final_call_topics', {}).get('topics', [])
        
        # Generate knowledge summaries for each high-risk file
        knowledge_summaries = []
        for file_name in high_risk_files[:10]:  # Top 10
            file_data = file_risk_scores.get(file_name, {})
            if self.ai_service:
                try:
                    summary = self.ai_service.generate_knowledge_summary(
                        {'file': file_name, 'risk_score': file_data.get('risk_score', 0)},
                        prerequisite_data,
                        employee_username
                    )
                    knowledge_summaries.append({
                        'file': file_name,
                        'risk_score': file_data.get('risk_score', 0),
                        **summary
                    })
                except Exception as e:
                    print(f"⚠️  AI summary failed for {file_name}: {e}")
                    knowledge_summaries.append(self._fallback_file_summary(file_name, file_data))
            else:
                knowledge_summaries.append(self._fallback_file_summary(file_name, file_data))
        
        # Generate extraction analysis for each topic
        extraction_analyses = []
        for topic in topics[:5]:  # Top 5 topics
            if self.ai_service:
                try:
                    analysis = self.ai_service.generate_extraction_analysis(
                        {
                            'file': topic.get('title', ''),
                            'risk_score': topic.get('risk_score', 0),
                            'owner_count': 1
                        },
                        prerequisite_data,
                        employee_username
                    )
                    extraction_analyses.append({
                        'topic': topic.get('title', ''),
                        'topic_id': topic.get('topic_id', ''),
                        'priority': topic.get('priority', 'medium'),
                        **analysis
                    })
                except Exception as e:
                    print(f"⚠️  AI extraction failed for {topic.get('title')}: {e}")
                    extraction_analyses.append(self._fallback_topic_analysis(topic))
            else:
                extraction_analyses.append(self._fallback_topic_analysis(topic))
        
        # Get AI-generated questions
        questions_data = final_call_data.get('ai_guided_discussion', {}).get('questions_per_topic', {})
        extraction_questions = self._extract_extraction_questions(questions_data)
        
        # Build simplified output
        output = {
            'metadata': {
                'employee': employee_username,
                'generated_at': datetime.now().isoformat(),
                'format_version': '2.0',
                'ai_enabled': self.ai_service is not None
            },
            
            # Core Knowledge Transfer Questions
            'knowledge_transfer_summary': {
                'what_they_know_that_others_dont': self._summarize_unique_knowledge(knowledge_summaries),
                'what_could_break_after_they_leave': self._summarize_breakage_risks(knowledge_summaries, extraction_analyses),
                'what_manager_must_ask_before_day0': self._summarize_critical_questions(extraction_questions, topics)
            },
            
            # Detailed Analysis
            'detailed_analysis': {
                'high_risk_files': knowledge_summaries,
                'topic_extractions': extraction_analyses,
                'extraction_questions': extraction_questions
            },
            
            # Action Items
            'action_items': {
                'immediate_actions': self._generate_immediate_actions(knowledge_summaries, topics),
                'final_call_topics': [
                    {
                        'topic': t.get('title', ''),
                        'priority': t.get('priority', 'medium'),
                        'risk_score': t.get('risk_score', 0),
                        'estimated_time': final_call_data.get('ai_guided_discussion', {})
                            .get('time_estimation', {})
                            .get('time_estimates', [])
                            .__iter__().__next__() if final_call_data.get('ai_guided_discussion', {})
                            .get('time_estimation', {}).get('time_estimates') else {}
                    }
                    for t in topics[:5]
                ]
            }
        }
        
        return output
    
    def _summarize_unique_knowledge(self, knowledge_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize what they know that others don't"""
        all_unique_knowledge = []
        all_decisions = []
        all_implicit_context = []
        
        for summary in knowledge_summaries:
            what_they_know = summary.get('what_they_know', {})
            all_unique_knowledge.extend(what_they_know.get('unique_knowledge', []))
            all_decisions.extend(what_they_know.get('undocumented_decisions', []))
            implicit = what_they_know.get('implicit_context', '')
            if implicit:
                all_implicit_context.append(implicit)
        
        return {
            'unique_knowledge_items': list(set(all_unique_knowledge)),
            'undocumented_decisions': list(set(all_decisions)),
            'implicit_context': all_implicit_context,
            'summary': f"Employee has unique knowledge in {len(knowledge_summaries)} high-risk areas. "
                      f"Key undocumented decisions: {len(set(all_decisions))}. "
                      f"Implicit context exists that may not be captured in code."
        }
    
    def _summarize_breakage_risks(self, knowledge_summaries: List[Dict[str, Any]],
                                 extraction_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize what could break after they leave"""
        all_systems_at_risk = []
        all_failure_scenarios = []
        max_severity = 'low'
        
        for summary in knowledge_summaries:
            what_could_break = summary.get('what_could_break', {})
            all_systems_at_risk.extend(what_could_break.get('systems_at_risk', []))
            all_failure_scenarios.extend(what_could_break.get('failure_scenarios', []))
            severity = what_could_break.get('impact_severity', 'low')
            if severity == 'high':
                max_severity = 'high'
            elif severity == 'medium' and max_severity != 'high':
                max_severity = 'medium'
        
        for analysis in extraction_analyses:
            risk_extraction = analysis.get('risk_extraction', {})
            all_failure_scenarios.extend(risk_extraction.get('failure_scenarios', []))
            what_could_break_list = risk_extraction.get('what_could_break', [])
            all_systems_at_risk.extend(what_could_break_list)
        
        return {
            'systems_at_risk': list(set(all_systems_at_risk)),
            'failure_scenarios': list(set(all_failure_scenarios)),
            'impact_severity': max_severity,
            'summary': f"{len(set(all_systems_at_risk))} systems at risk. "
                      f"{len(set(all_failure_scenarios))} potential failure scenarios identified. "
                      f"Impact severity: {max_severity}."
        }
    
    def _summarize_critical_questions(self, extraction_questions: List[Dict[str, Any]],
                                    topics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize what manager must ask before Day-0"""
        critical_questions = [q for q in extraction_questions if q.get('priority') == 'critical']
        high_priority_questions = [q for q in extraction_questions if q.get('priority') == 'high']
        
        return {
            'critical_questions': [q.get('question', '') for q in critical_questions],
            'high_priority_questions': [q.get('question', '') for q in high_priority_questions],
            'total_critical': len(critical_questions),
            'total_high_priority': len(high_priority_questions),
            'summary': f"Manager must ask {len(critical_questions)} critical questions and "
                      f"{len(high_priority_questions)} high-priority questions before Day-0. "
                      f"Focus on: {', '.join([t.get('title', '') for t in topics[:3]])}."
        }
    
    def _extract_extraction_questions(self, questions_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract extraction questions from questions data"""
        all_questions = []
        questions_by_topic = questions_data.get('questions_by_topic', {})
        
        for topic_id, topic_data in questions_by_topic.items():
            questions = topic_data.get('questions', [])
            for q in questions:
                all_questions.append({
                    'question': q.get('question', ''),
                    'category': q.get('category', q.get('type', '')),
                    'priority': q.get('priority', 'medium'),
                    'what_it_reveals': q.get('what_it_reveals', ''),
                    'topic': topic_data.get('topic_title', '')
                })
        
        return all_questions
    
    def _generate_immediate_actions(self, knowledge_summaries: List[Dict[str, Any]],
                                   topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate immediate action items"""
        actions = []
        
        # Action 1: Schedule Final Call
        critical_topics = [t for t in topics if t.get('priority') == 'critical']
        if critical_topics:
            actions.append({
                'action': 'Schedule Final Call immediately',
                'priority': 'critical',
                'reason': f"{len(critical_topics)} critical topics identified",
                'deadline': 'Before Day-0'
            })
        
        # Action 2: Document high-risk files
        if knowledge_summaries:
            actions.append({
                'action': 'Document high-risk files',
                'priority': 'high',
                'reason': f"{len(knowledge_summaries)} high-risk files need documentation",
                'deadline': 'Within 1 week'
            })
        
        # Action 3: Identify successors
        actions.append({
            'action': 'Identify and assign successors',
            'priority': 'critical',
            'reason': 'Knowledge transfer requires backup owners',
            'deadline': 'Before Day-0'
        })
        
        return actions
    
    def _fallback_file_summary(self, file_name: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback summary when AI is unavailable"""
        return {
            'file': file_name,
            'risk_score': file_data.get('risk_score', 0),
            'what_they_know': {
                'unique_knowledge': [f"Deep understanding of {file_name}"],
                'undocumented_decisions': [],
                'implicit_context': 'Manual review required - AI analysis unavailable'
            },
            'what_could_break': {
                'systems_at_risk': [f"Systems using {file_name}"],
                'failure_scenarios': [],
                'impact_severity': 'medium'
            },
            'must_ask_before_day0': {
                'critical_questions': [f"What is the purpose of {file_name}?", f"Who else understands {file_name}?"],
                'knowledge_to_transfer': [f"Context and usage of {file_name}"],
                'urgency': 'high'
            },
            'summary': f"High-risk file {file_name} requires manual knowledge transfer review."
        }
    
    def _fallback_topic_analysis(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when AI is unavailable"""
        return {
            'topic': topic.get('title', ''),
            'topic_id': topic.get('topic_id', ''),
            'priority': topic.get('priority', 'medium'),
            'decision_extraction': {
                'undocumented_decisions': [],
                'architectural_choices': [],
                'design_rationale': 'Manual review required'
            },
            'risk_extraction': {
                'what_could_break': [f"Systems related to {topic.get('title', '')}"],
                'failure_scenarios': [],
                'impact_assessment': 'High risk due to topic priority'
            },
            'dependency_extraction': {
                'tightly_coupled_systems': [],
                'people_dependencies': [],
                'external_dependencies': []
            },
            'knowledge_gap_detection': {
                'what_new_engineer_would_struggle_with': [f"Understanding {topic.get('title', '')}"],
                'implicit_knowledge': [],
                'missing_documentation': []
            }
        }
    
    def save_simplified_output(self, output: Dict[str, Any], owner: str, repo: str, employee_username: str):
        """Save simplified output to JSON file"""
        output_path = Path("backend/data/improved_offboarding/simplified")
        output_path.mkdir(parents=True, exist_ok=True)
        
        output_file = output_path / f"{owner}_{repo}_{employee_username}_simplified.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        print(f"💾 Simplified output saved to {output_file}")
        return output_file

