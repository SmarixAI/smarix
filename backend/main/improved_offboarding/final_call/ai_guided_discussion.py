"""
AI-Guided Discussion Module
Implements features 39-45: Agenda generation, questions, discussion order, etc.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_service import AIService


class AIGuidedDiscussionGenerator:
    """
    Generates AI-guided discussion materials for Final Call (Features 39-45)
    Now uses OpenAI for intelligent question generation
    """
    
    def __init__(self):
        self.agenda = []
        self.questions = {}
        self.stakeholders = []
        try:
            self.ai_service = AIService()
            print("✓ OpenAI service initialized")
        except Exception as e:
            print(f"⚠️  OpenAI service unavailable: {e}. Using fallback mode.")
            self.ai_service = None
    
    def process(self, topic_identification_results: Dict[str, Any], 
                prerequisite_data: Dict[str, Any],
                employee_username: Optional[str] = None,
                contributor_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process all AI-guided discussion features
        
        Args:
            topic_identification_results: Results from topic identification
            prerequisite_data: Complete prerequisite analysis (filtered to contributor)
            employee_username: Departing employee username
            contributor_context: Contributor-specific context for AI prompts
            
        Returns:
            Dictionary with all discussion generation results
        """
        results = {
            'final_call_agenda': self._generate_final_call_agenda(topic_identification_results, prerequisite_data, employee_username),
            'questions_per_topic': self._generate_questions_per_topic(topic_identification_results, prerequisite_data, employee_username, contributor_context),
            'suggested_discussion_order': self._suggest_discussion_order(topic_identification_results),
            'time_estimation': self._estimate_time_per_topic(topic_identification_results),
            'stakeholder_suggestions': self._suggest_stakeholders(topic_identification_results, prerequisite_data, employee_username),
            'risk_justification': self._generate_risk_justification(topic_identification_results),
            'ai_confidence_indicators': self._calculate_confidence_indicators(topic_identification_results, prerequisite_data)
        }
        
        return results
    
    def _generate_final_call_agenda(self, topic_results: Dict[str, Any], 
                                   prerequisite_data: Dict[str, Any],
                                   employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 39: AI-generated Final Call agenda"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        
        agenda_items = []
        
        for topic in topics:
            topic_id = topic.get('topic_id', '')
            title = topic.get('title', '')
            category = topic.get('category', '')
            priority = topic.get('priority', 'medium')
            description = topic.get('description', '')
            
            # Generate agenda item
            agenda_item = {
                'topic_id': topic_id,
                'title': title,
                'category': category,
                'priority': priority,
                'description': description,
                'estimated_time_minutes': self._estimate_topic_time(topic),
                'order': len(agenda_items) + 1,
                'related_files': topic.get('related_files', [])[:5],  # Top 5
                'discussion_points': self._generate_discussion_points(topic, prerequisite_data)
            }
            
            agenda_items.append(agenda_item)
        
        # Sort by priority and estimated time
        priority_order = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}
        agenda_items.sort(key=lambda x: (priority_order.get(x.get('priority', 'low'), 0), -x.get('estimated_time_minutes', 0)), reverse=True)
        
        # Re-number after sorting
        for i, item in enumerate(agenda_items):
            item['order'] = i + 1
        
        self.agenda = agenda_items
        
        # Calculate total time
        total_time = sum(item.get('estimated_time_minutes', 0) for item in agenda_items)
        
        return {
            'agenda_items': agenda_items,
            'total_items': len(agenda_items),
            'total_estimated_time_minutes': total_time,
            'total_estimated_time_hours': round(total_time / 60, 1),
            'critical_items': [a for a in agenda_items if a.get('priority') == 'critical'],
            'agenda_summary': {
                'by_category': self._group_by_category(agenda_items),
                'by_priority': self._group_by_priority(agenda_items)
            }
        }
    
    def _estimate_topic_time(self, topic: Dict[str, Any]) -> int:
        """Estimate time for a topic in minutes"""
        priority = topic.get('priority', 'medium')
        related_files = topic.get('related_files', [])
        file_count = len(related_files) if isinstance(related_files, list) else 0
        
        # Base time by priority
        base_time = {
            'critical': 30,
            'high': 20,
            'medium': 15,
            'low': 10
        }.get(priority, 15)
        
        # Add time for files (2 minutes per file, max 20 minutes)
        file_time = min(file_count * 2, 20)
        
        return base_time + file_time
    
    def _generate_discussion_points(self, topic: Dict[str, Any], 
                                   prerequisite_data: Dict[str, Any]) -> List[str]:
        """Generate discussion points for a topic"""
        points = []
        topic_id = topic.get('topic_id', '')
        
        if topic_id == 'high_risk_knowledge':
            points = [
                "Review each high-risk file and explain key concepts",
                "Discuss why these files are critical to the system",
                "Identify potential knowledge gaps",
                "Document any undocumented assumptions or decisions"
            ]
        elif topic_id == 'single_owner_knowledge':
            points = [
                "Explain the purpose and functionality of each single-owner file",
                "Discuss any unique knowledge or context not in code",
                "Identify who should become the backup owner",
                "Document any special considerations or gotchas"
            ]
        elif topic_id == 'operational_responsibilities':
            points = [
                "Walk through operational procedures and runbooks",
                "Explain deployment processes and configurations",
                "Discuss monitoring and alerting setup",
                "Review on-call procedures and escalation paths"
            ]
        elif topic_id == 'architecture_decisions':
            points = [
                "Explain the rationale behind key architecture decisions",
                "Discuss trade-offs and alternatives considered",
                "Document any constraints or assumptions",
                "Review future scalability or maintenance considerations"
            ]
        elif topic_id == 'failure_scenarios':
            points = [
                "Review known failure scenarios and their causes",
                "Discuss workarounds and temporary fixes",
                "Explain recovery procedures",
                "Document lessons learned from past incidents"
            ]
        else:
            points = [
                f"Review {topic.get('title', 'topic')} in detail",
                "Discuss key concepts and implementation details",
                "Identify knowledge gaps and documentation needs",
                "Document important decisions and rationale"
            ]
        
        return points
    
    def _group_by_category(self, agenda_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group agenda items by category"""
        categories = defaultdict(int)
        for item in agenda_items:
            categories[item.get('category', 'other')] += 1
        return dict(categories)
    
    def _group_by_priority(self, agenda_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group agenda items by priority"""
        priorities = defaultdict(int)
        for item in agenda_items:
            priorities[item.get('priority', 'medium')] += 1
        return dict(priorities)
    
    def _generate_questions_per_topic(self, topic_results: Dict[str, Any],
                                     prerequisite_data: Dict[str, Any],
                                     employee_username: Optional[str] = None,
                                     contributor_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Feature 40: AI-generated questions per topic using OpenAI"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        
        questions_by_topic = {}
        
        for topic in topics:
            topic_id = topic.get('topic_id', '')
            title = topic.get('title', '')
            
            # Use AI service if available, otherwise fallback
            if self.ai_service:
                try:
                    ai_questions = self.ai_service.generate_questions(
                        topic, prerequisite_data, employee_username or 'employee', contributor_context
                    )
                    # Merge AI questions with base questions
                    questions = self._merge_ai_questions(ai_questions, topic, prerequisite_data)
                except Exception as e:
                    print(f"⚠️  AI question generation failed for {topic_id}: {e}. Using fallback.")
                    questions = self._generate_topic_questions(topic, prerequisite_data)
            else:
                questions = self._generate_topic_questions(topic, prerequisite_data)
            
            questions_by_topic[topic_id] = {
                'topic_title': title,
                'questions': questions,
                'total_questions': len(questions),
                'critical_questions': [q for q in questions if q.get('priority') == 'critical'],
                'follow_up_questions': [q for q in questions if q.get('type') == 'follow_up'],
                'extraction_questions': [q for q in questions if 'extraction' in q.get('category', '').lower()]
            }
        
        self.questions = questions_by_topic
        
        return {
            'questions_by_topic': questions_by_topic,
            'total_questions': sum(len(v.get('questions', [])) for v in questions_by_topic.values()),
            'question_summary': {
                topic_id: len(v.get('questions', [])) 
                for topic_id, v in questions_by_topic.items()
            }
        }
    
    def _merge_ai_questions(self, ai_questions: List[Dict[str, Any]], 
                           topic: Dict[str, Any],
                           prerequisite_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Merge AI-generated questions with base questions"""
        # Convert AI questions to our format
        formatted_questions = []
        for ai_q in ai_questions:
            formatted_questions.append({
                'question': ai_q.get('question', ''),
                'type': ai_q.get('category', 'knowledge_gap'),
                'category': ai_q.get('category', 'knowledge_gap'),
                'priority': ai_q.get('priority', 'high'),
                'what_it_reveals': ai_q.get('what_it_reveals', ''),
                'follow_up_if': ai_q.get('follow_up_if', ''),
                'expected_answer_type': 'explanation'
            })
        
        # Add a few base questions if AI didn't cover them
        base_questions = self._generate_topic_questions(topic, prerequisite_data)
        
        # Combine, avoiding duplicates
        all_questions = formatted_questions.copy()
        existing_questions = {q.get('question', '').lower() for q in formatted_questions}
        
        for base_q in base_questions:
            if base_q.get('question', '').lower() not in existing_questions:
                all_questions.append(base_q)
        
        return all_questions
    
    def _generate_topic_questions(self, topic: Dict[str, Any], 
                                prerequisite_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific questions for a topic"""
        questions = []
        topic_id = topic.get('topic_id', '')
        related_files = topic.get('related_files', [])
        
        # Base questions for all topics
        base_questions = [
            {
                'question': f"What is the purpose and functionality of {topic.get('title', 'this topic')}?",
                'type': 'understanding',
                'priority': 'critical',
                'expected_answer_type': 'explanation'
            },
            {
                'question': "What are the key dependencies and integration points?",
                'type': 'dependencies',
                'priority': 'high',
                'expected_answer_type': 'list'
            },
            {
                'question': "What are the most common issues or gotchas?",
                'type': 'troubleshooting',
                'priority': 'high',
                'expected_answer_type': 'list'
            }
        ]
        
        questions.extend(base_questions)
        
        # Topic-specific questions
        if topic_id == 'high_risk_knowledge':
            questions.extend([
                {
                    'question': "Why are these files considered high-risk?",
                    'type': 'risk_analysis',
                    'priority': 'critical',
                    'expected_answer_type': 'explanation'
                },
                {
                    'question': "What would happen if knowledge of these files is lost?",
                    'type': 'impact_analysis',
                    'priority': 'critical',
                    'expected_answer_type': 'scenario'
                }
            ])
        
        elif topic_id == 'single_owner_knowledge':
            for file_path in related_files[:3]:  # Top 3 files
                questions.append({
                    'question': f"Can you explain the implementation details of {file_path}?",
                    'type': 'technical_detail',
                    'priority': 'high',
                    'expected_answer_type': 'technical_explanation',
                    'related_file': file_path
                })
        
        elif topic_id == 'operational_responsibilities':
            questions.extend([
                {
                    'question': "What are the step-by-step deployment procedures?",
                    'type': 'process',
                    'priority': 'critical',
                    'expected_answer_type': 'step_by_step'
                },
                {
                    'question': "What monitoring and alerting is in place?",
                    'type': 'monitoring',
                    'priority': 'high',
                    'expected_answer_type': 'list'
                },
                {
                    'question': "What are the on-call escalation procedures?",
                    'type': 'oncall',
                    'priority': 'critical',
                    'expected_answer_type': 'process'
                }
            ])
        
        elif topic_id == 'architecture_decisions':
            questions.extend([
                {
                    'question': "What was the rationale behind this architecture decision?",
                    'type': 'rationale',
                    'priority': 'high',
                    'expected_answer_type': 'explanation'
                },
                {
                    'question': "What alternatives were considered and why were they rejected?",
                    'type': 'alternatives',
                    'priority': 'medium',
                    'expected_answer_type': 'comparison'
                }
            ])
        
        elif topic_id == 'failure_scenarios':
            questions.extend([
                {
                    'question': "What are the known failure scenarios and their root causes?",
                    'type': 'failure_analysis',
                    'priority': 'high',
                    'expected_answer_type': 'list'
                },
                {
                    'question': "What workarounds exist and when should they be used?",
                    'type': 'workarounds',
                    'priority': 'high',
                    'expected_answer_type': 'list'
                }
            ])
        
        # Add follow-up questions
        questions.append({
            'question': "Is there anything else important about this topic that should be documented?",
            'type': 'follow_up',
            'priority': 'medium',
            'expected_answer_type': 'open_ended'
        })
        
        return questions
    
    def _suggest_discussion_order(self, topic_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 41: Suggested discussion order"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        
        # Sort by priority and risk score
        priority_order = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}
        
        sorted_topics = sorted(
            topics,
            key=lambda x: (
                priority_order.get(x.get('priority', 'low'), 0),
                x.get('risk_score', 0)
            ),
            reverse=True
        )
        
        # Create ordered list
        discussion_order = []
        for i, topic in enumerate(sorted_topics):
            discussion_order.append({
                'order': i + 1,
                'topic_id': topic.get('topic_id', ''),
                'title': topic.get('title', ''),
                'priority': topic.get('priority', 'medium'),
                'risk_score': topic.get('risk_score', 0),
                'estimated_time_minutes': self._estimate_topic_time(topic),
                'rationale': self._generate_order_rationale(topic, i + 1)
            })
        
        return {
            'discussion_order': discussion_order,
            'total_topics': len(discussion_order),
            'estimated_total_time_minutes': sum(t.get('estimated_time_minutes', 0) for t in discussion_order),
            'order_rationale': "Topics ordered by priority (critical > high > medium > low) and risk score"
        }
    
    def _generate_order_rationale(self, topic: Dict[str, Any], position: int) -> str:
        """Generate rationale for topic position"""
        priority = topic.get('priority', 'medium')
        
        if position == 1:
            return f"First topic due to {priority} priority and high risk score"
        elif priority == 'critical':
            return f"Critical priority topic - address early in discussion"
        else:
            return f"Positioned based on priority ({priority}) and risk assessment"
    
    def _estimate_time_per_topic(self, topic_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 42: Time estimation per topic"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        
        time_estimates = []
        total_time = 0
        
        for topic in topics:
            estimated_minutes = self._estimate_topic_time(topic)
            total_time += estimated_minutes
            
            time_estimates.append({
                'topic_id': topic.get('topic_id', ''),
                'title': topic.get('title', ''),
                'estimated_minutes': estimated_minutes,
                'estimated_hours': round(estimated_minutes / 60, 1),
                'factors': self._explain_time_factors(topic, estimated_minutes)
            })
        
        return {
            'time_estimates': time_estimates,
            'total_estimated_minutes': total_time,
            'total_estimated_hours': round(total_time / 60, 1),
            'breakdown': {
                'critical_topics': sum(t.get('estimated_minutes', 0) for t in time_estimates 
                                      if any(top.get('topic_id') == t.get('topic_id') 
                                            for top in topics if top.get('priority') == 'critical')),
                'high_priority_topics': sum(t.get('estimated_minutes', 0) for t in time_estimates 
                                           if any(top.get('topic_id') == t.get('topic_id') 
                                                 for top in topics if top.get('priority') == 'high')),
                'medium_priority_topics': sum(t.get('estimated_minutes', 0) for t in time_estimates 
                                              if any(top.get('topic_id') == t.get('topic_id') 
                                                    for top in topics if top.get('priority') == 'medium'))
            }
        }
    
    def _explain_time_factors(self, topic: Dict[str, Any], estimated_minutes: int) -> List[str]:
        """Explain factors affecting time estimation"""
        factors = []
        priority = topic.get('priority', 'medium')
        related_files = topic.get('related_files', [])
        file_count = len(related_files) if isinstance(related_files, list) else 0
        
        factors.append(f"Priority level: {priority}")
        if file_count > 0:
            factors.append(f"Number of related files: {file_count}")
        if topic.get('category') == 'operational':
            factors.append("Operational topics typically require more detailed explanation")
        if topic.get('risk_score', 0) > 0.8:
            factors.append("High risk score indicates need for thorough discussion")
        
        return factors
    
    def _suggest_stakeholders(self, topic_results: Dict[str, Any], 
                             prerequisite_data: Dict[str, Any],
                             employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 43: Stakeholder suggestions (who should attend)"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        data_collection = prerequisite_data.get('data_collection', {})
        
        # Get contributors from repository
        contributors = data_collection.get('multi_repo_contribution', {}).get('contributors', {})
        
        # Identify stakeholders by topic
        stakeholders_by_topic = {}
        all_stakeholders = set()
        
        for topic in topics:
            topic_id = topic.get('topic_id', '')
            related_files = topic.get('related_files', [])
            
            # Find stakeholders who worked on related files
            topic_stakeholders = []
            
            # Get file ownership history
            ownership_history = data_collection.get('file_ownership_history', {}).get('ownership_history', {})
            
            for file_path in related_files:
                history = ownership_history.get(file_path, [])
                file_contributors = set([h.get('author') for h in history if h.get('author')])
                
                for contributor in file_contributors:
                    if contributor != employee_username:  # Exclude departing employee
                        topic_stakeholders.append({
                            'username': contributor,
                            'contribution_type': 'file_owner',
                            'file': file_path,
                            'relevance': 'high'
                        })
                        all_stakeholders.add(contributor)
            
            # Add role-based stakeholders
            if topic.get('category') == 'operational':
                topic_stakeholders.append({
                    'username': 'devops_team',
                    'contribution_type': 'role_based',
                    'relevance': 'critical',
                    'note': 'Required for operational topics'
                })
            
            if topic.get('category') == 'architecture':
                topic_stakeholders.append({
                    'username': 'tech_lead',
                    'contribution_type': 'role_based',
                    'relevance': 'high',
                    'note': 'Required for architecture discussions'
                })
            
            stakeholders_by_topic[topic_id] = {
                'topic_title': topic.get('title', ''),
                'stakeholders': topic_stakeholders,
                'required_attendees': [s for s in topic_stakeholders if s.get('relevance') in ['critical', 'high']],
                'optional_attendees': [s for s in topic_stakeholders if s.get('relevance') == 'medium']
            }
        
        # Generate overall stakeholder list
        stakeholder_summary = {}
        for stakeholder in all_stakeholders:
            # Count topics where stakeholder is relevant
            topic_count = sum(1 for topic_data in stakeholders_by_topic.values() 
                            if any(s.get('username') == stakeholder for s in topic_data.get('stakeholders', [])))
            
            stakeholder_summary[stakeholder] = {
                'topics_involved': topic_count,
                'attendance_priority': 'required' if topic_count > 2 else 'recommended'
            }
        
        self.stakeholders = list(all_stakeholders)
        
        return {
            'stakeholders_by_topic': stakeholders_by_topic,
            'overall_stakeholders': stakeholder_summary,
            'required_attendees': [s for s, data in stakeholder_summary.items() 
                                 if data.get('attendance_priority') == 'required'],
            'total_unique_stakeholders': len(all_stakeholders)
        }
    
    def _generate_risk_justification(self, topic_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 44: Risk justification for each topic"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        
        risk_justifications = {}
        
        for topic in topics:
            topic_id = topic.get('topic_id', '')
            risk_score = topic.get('risk_score', 0)
            priority = topic.get('priority', 'medium')
            
            justification = {
                'topic_id': topic_id,
                'topic_title': topic.get('title', ''),
                'risk_score': risk_score,
                'priority': priority,
                'justification': self._generate_topic_justification(topic),
                'risk_factors': self._identify_risk_factors(topic),
                'impact_if_missed': self._assess_impact_if_missed(topic),
                'recommendation': self._generate_risk_recommendation(topic)
            }
            
            risk_justifications[topic_id] = justification
        
        return {
            'risk_justifications': risk_justifications,
            'high_risk_topics': [j for j in risk_justifications.values() if j.get('risk_score', 0) >= 0.8],
            'critical_priority_topics': [j for j in risk_justifications.values() if j.get('priority') == 'critical']
        }
    
    def _generate_topic_justification(self, topic: Dict[str, Any]) -> str:
        """Generate justification for including topic"""
        topic_id = topic.get('topic_id', '')
        risk_score = topic.get('risk_score', 0)
        priority = topic.get('priority', 'medium')
        
        base_justification = f"This topic has {priority} priority with a risk score of {risk_score:.2f}. "
        
        if topic_id == 'high_risk_knowledge':
            return base_justification + "High-risk knowledge files represent critical system components where knowledge loss could significantly impact operations."
        elif topic_id == 'single_owner_knowledge':
            return base_justification + "Single-owner files contain knowledge concentrated in one person, creating a significant knowledge risk."
        elif topic_id == 'operational_responsibilities':
            return base_justification + "Operational responsibilities are critical for system continuity and require thorough knowledge transfer."
        else:
            return base_justification + "This topic requires discussion to ensure knowledge continuity."
    
    def _identify_risk_factors(self, topic: Dict[str, Any]) -> List[str]:
        """Identify specific risk factors for topic"""
        factors = []
        topic_id = topic.get('topic_id', '')
        
        if topic_id == 'high_risk_knowledge':
            factors = [
                "Knowledge concentrated in few files",
                "High change frequency indicates complexity",
                "Low owner count increases risk"
            ]
        elif topic_id == 'single_owner_knowledge':
            factors = [
                "Single point of failure for knowledge",
                "No backup knowledge available",
                "High impact if knowledge is lost"
            ]
        elif topic_id == 'operational_responsibilities':
            factors = [
                "Critical for system operations",
                "Requires immediate knowledge transfer",
                "High impact on system availability"
            ]
        else:
            factors = [
                f"Risk score: {topic.get('risk_score', 0):.2f}",
                f"Priority: {topic.get('priority', 'medium')}"
            ]
        
        return factors
    
    def _assess_impact_if_missed(self, topic: Dict[str, Any]) -> str:
        """Assess impact if topic is not discussed"""
        topic_id = topic.get('topic_id', '')
        priority = topic.get('priority', 'medium')
        
        if priority == 'critical':
            return "Critical impact: System operations may be disrupted, knowledge may be permanently lost, and recovery could be difficult."
        elif priority == 'high':
            return "High impact: Significant knowledge gaps may develop, requiring extensive time to recover understanding."
        else:
            return "Medium impact: Knowledge gaps may develop, but recovery is possible with additional effort."
    
    def _generate_risk_recommendation(self, topic: Dict[str, Any]) -> str:
        """Generate recommendation based on risk"""
        priority = topic.get('priority', 'medium')
        
        if priority == 'critical':
            return "Must be discussed in Final Call. Consider scheduling additional follow-up sessions if needed."
        elif priority == 'high':
            return "Strongly recommended for Final Call discussion. Document all key points."
        else:
            return "Recommended for discussion if time permits, or document for later review."
    
    def _calculate_confidence_indicators(self, topic_results: Dict[str, Any], 
                                        prerequisite_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 45: AI confidence indicator per question"""
        questions_data = self._generate_questions_per_topic(topic_results, prerequisite_data)
        questions_by_topic = questions_data.get('questions_by_topic', {})
        
        confidence_indicators = {}
        
        for topic_id, topic_questions in questions_by_topic.items():
            questions = topic_questions.get('questions', [])
            
            question_confidence = []
            for question in questions:
                confidence = self._calculate_question_confidence(question, prerequisite_data)
                
                question_confidence.append({
                    'question': question.get('question', ''),
                    'confidence_score': confidence,
                    'confidence_level': self._get_confidence_level(confidence),
                    'confidence_factors': self._explain_confidence_factors(question, prerequisite_data),
                    'recommendation': self._get_confidence_recommendation(confidence)
                })
            
            confidence_indicators[topic_id] = {
                'topic_id': topic_id,
                'questions': question_confidence,
                'average_confidence': sum(q.get('confidence_score', 0) for q in question_confidence) / len(question_confidence) if question_confidence else 0
            }
        
        return {
            'confidence_by_topic': confidence_indicators,
            'overall_average_confidence': sum(
                data.get('average_confidence', 0) 
                for data in confidence_indicators.values()
            ) / len(confidence_indicators) if confidence_indicators else 0,
            'high_confidence_questions': sum(
                sum(1 for q in data.get('questions', []) if q.get('confidence_score', 0) > 0.7)
                for data in confidence_indicators.values()
            ),
            'low_confidence_questions': sum(
                sum(1 for q in data.get('questions', []) if q.get('confidence_score', 0) < 0.5)
                for data in confidence_indicators.values()
            )
        }
    
    def _calculate_question_confidence(self, question: Dict[str, Any], 
                                      prerequisite_data: Dict[str, Any]) -> float:
        """Calculate confidence score for a question"""
        confidence = 0.5  # Base confidence
        
        question_type = question.get('type', '')
        priority = question.get('priority', 'medium')
        
        # Adjust based on question type
        if question_type in ['understanding', 'rationale']:
            confidence += 0.2  # These are generally answerable
        elif question_type == 'follow_up':
            confidence -= 0.1  # Open-ended questions have lower confidence
        
        # Adjust based on priority
        if priority == 'critical':
            confidence += 0.1  # Critical questions are more likely to be answerable
        
        # Adjust based on available data
        if prerequisite_data:
            confidence += 0.1  # Having prerequisite data increases confidence
        
        return min(max(confidence, 0.0), 1.0)
    
    def _get_confidence_level(self, confidence_score: float) -> str:
        """Get confidence level label"""
        if confidence_score >= 0.8:
            return 'high'
        elif confidence_score >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _explain_confidence_factors(self, question: Dict[str, Any], 
                                   prerequisite_data: Dict[str, Any]) -> List[str]:
        """Explain factors affecting confidence"""
        factors = []
        question_type = question.get('type', '')
        
        if question_type in ['understanding', 'rationale']:
            factors.append("Question type is well-defined and answerable")
        
        if prerequisite_data:
            factors.append("Prerequisite data available to inform question")
        
        if question.get('priority') == 'critical':
            factors.append("Critical priority indicates high likelihood of answerability")
        
        return factors
    
    def _get_confidence_recommendation(self, confidence_score: float) -> str:
        """Get recommendation based on confidence"""
        if confidence_score >= 0.8:
            return "High confidence - question is well-formed and answerable"
        elif confidence_score >= 0.6:
            return "Medium confidence - question should be answerable with available context"
        else:
            return "Low confidence - consider rephrasing or providing more context"

