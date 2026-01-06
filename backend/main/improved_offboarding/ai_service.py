"""
OpenAI Service Module
Handles all OpenAI API interactions for AI-driven analysis
"""

import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
import json

# Load environment variables
load_dotenv()


class AIService:
    """
    Service for OpenAI API interactions
    Handles prompts, responses, and error handling
    """
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in .env file. "
                "Please add: OPENAI_API_KEY=your_key_here"
            )
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # Use cheaper model by default
        self.use_ai = os.getenv('USE_OPENAI', 'true').lower() == 'true'
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
        
        if not self.use_ai:
            print("⚠️  OpenAI is disabled. Set USE_OPENAI=true in .env to enable.")
    
    def generate_extraction_analysis(self, 
                                     knowledge_unit: Dict[str, Any],
                                     context: Dict[str, Any],
                                     employee_username: str) -> Dict[str, Any]:
        """
        Generate AI-driven extraction analysis for a knowledge unit
        
        Returns analysis with:
        - Decision extraction
        - Risk extraction
        - Dependency extraction
        - Knowledge gap detection
        """
        if not self.use_ai:
            return self._fallback_analysis(knowledge_unit, context)
        
        prompt = self._build_extraction_prompt(knowledge_unit, context, employee_username)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert knowledge extraction analyst. Analyze code and contributions to identify critical knowledge, risks, and dependencies. Provide clear, actionable insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"⚠️  OpenAI API error: {e}. Using fallback analysis.")
            return self._fallback_analysis(knowledge_unit, context)
    
    def generate_questions(self,
                          topic: Dict[str, Any],
                          context: Dict[str, Any],
                          employee_username: str,
                          contributor_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Generate AI-driven extraction questions for a topic
        
        Args:
            topic: Topic dictionary
            context: General context
            employee_username: Username of departing employee
            contributor_context: Contributor-specific context (optional)
        
        Returns questions that answer:
        - "What do they know that others don't?"
        - "What could break after they leave?"
        - "What must the manager ask them before Day-0?"
        """
        if not self.use_ai:
            return self._fallback_questions(topic)
        
        # Add contributor context to context dict
        if contributor_context:
            context = context.copy()
            context['contributor_context'] = contributor_context
        
        prompt = self._build_question_prompt(topic, context, employee_username)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at generating insightful questions for knowledge transfer. Create specific, actionable questions that extract critical knowledge."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('questions', [])
            
        except Exception as e:
            print(f"⚠️  OpenAI API error: {e}. Using fallback questions.")
            return self._fallback_questions(topic)
    
    def generate_knowledge_summary(self,
                                   file_data: Dict[str, Any],
                                   context: Dict[str, Any],
                                   employee_username: str) -> Dict[str, Any]:
        """
        Generate a clear summary answering key questions:
        - "What do they know that others don't?"
        - "What could break after they leave?"
        - "What must the manager ask them before Day-0?"
        """
        if not self.use_ai:
            return self._fallback_summary(file_data, context)
        
        prompt = self._build_summary_prompt(file_data, context, employee_username)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert knowledge analyst. Provide clear, concise summaries that answer critical knowledge transfer questions. Be specific and actionable."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"⚠️  OpenAI API error: {e}. Using fallback summary.")
            return self._fallback_summary(file_data, context)
    
    def _build_extraction_prompt(self, knowledge_unit: Dict[str, Any], 
                                context: Dict[str, Any],
                                employee_username: str) -> str:
        """Build prompt for extraction analysis with contributor context"""
        file_name = knowledge_unit.get('file', 'Unknown')
        risk_score = knowledge_unit.get('risk_score', 0)
        owner_count = knowledge_unit.get('owner_count', 0)
        
        # Get contributor context if available
        contributor_context = context.get('contributor_context', {})
        contribution_stats = contributor_context.get('contribution_stats', {})
        ownership = contributor_context.get('ownership', {})
        
        # Build contributor-specific context string
        contributor_info = f"""
Contributor Profile:
- Username: {employee_username}
- Total PRs: {contribution_stats.get('prs', 0)}
- Total Commits: {contribution_stats.get('commits', 0)}
- Files Modified: {contribution_stats.get('files_modified', 0)}
- Files Owned: {ownership.get('total_files_owned', 0)}
- High-Risk Files Owned: {len(ownership.get('high_risk_files_owned', []))}
- Single-Owner Files: {len(ownership.get('single_owner_files_owned', []))}
- Operational Files: {len(ownership.get('operational_files_owned', []))}

Files Owned by This Contributor:
{', '.join(ownership.get('owned_files', [])[:10])}
"""
        
        return f"""Analyze this knowledge unit and extract critical information for the departing contributor:

Knowledge Unit:
- File/System: {file_name}
- Risk Score: {risk_score}
- Owner Count: {owner_count}
- Employee: {employee_username}

{contributor_info}

Context:
- This contributor is leaving the organization
- This file is part of their ownership/contribution
- We need to identify what unique knowledge will be lost
- Focus on undocumented decisions, risks, and dependencies specific to this contributor's work

Provide a JSON response with these exact keys:
{{
  "decision_extraction": {{
    "undocumented_decisions": ["decision1", "decision2"],
    "architectural_choices": ["choice1", "choice2"],
    "design_rationale": "explanation of why decisions were made"
  }},
  "risk_extraction": {{
    "what_could_break": ["risk1", "risk2"],
    "failure_scenarios": ["scenario1", "scenario2"],
    "impact_assessment": "description of potential impact"
  }},
  "dependency_extraction": {{
    "tightly_coupled_systems": ["system1", "system2"],
    "people_dependencies": ["person1", "person2"],
    "external_dependencies": ["dep1", "dep2"]
  }},
  "knowledge_gap_detection": {{
    "what_new_engineer_would_struggle_with": ["gap1", "gap2"],
    "implicit_knowledge": ["knowledge1", "knowledge2"],
    "missing_documentation": ["doc1", "doc2"]
  }}
}}

Be specific and actionable. Focus on what unique knowledge this contributor has that would be lost if they leave."""
    
    def _build_question_prompt(self, topic: Dict[str, Any],
                              context: Dict[str, Any],
                              employee_username: str) -> str:
        """Build prompt for question generation with contributor context"""
        topic_title = topic.get('title', 'Unknown Topic')
        related_files = topic.get('related_files', [])
        priority = topic.get('priority', 'medium')
        
        # Get contributor context
        contributor_context = context.get('contributor_context', {})
        contribution_stats = contributor_context.get('contribution_stats', {})
        ownership = contributor_context.get('ownership', {})
        
        contributor_info = f"""
Contributor Profile:
- Username: {employee_username}
- Total PRs: {contribution_stats.get('prs', 0)}
- Files Owned: {ownership.get('total_files_owned', 0)}
- High-Risk Files: {len(ownership.get('high_risk_files_owned', []))}
- Files in This Topic: {len([f for f in related_files if f in ownership.get('owned_files', [])])}

This contributor's files in this topic:
{', '.join([f for f in related_files if f in ownership.get('owned_files', [])][:5])}
"""
        
        return f"""Generate extraction questions for this Final Call topic with the departing contributor:

Topic: {topic_title}
Priority: {priority}
Related Files: {', '.join(related_files[:5])}
Employee: {employee_username}

{contributor_info}

Generate questions that answer these three critical questions:
1. "What do they know that others don't?" (Focus on their unique contributions)
2. "What could break after they leave?" (Focus on their owned files and systems)
3. "What must the manager ask them before Day-0?" (Focus on critical knowledge transfer)

Provide a JSON response with this structure:
{{
  "questions": [
    {{
      "question": "specific question text",
      "category": "decision_extraction|risk_extraction|dependency_extraction|knowledge_gap",
      "priority": "critical|high|medium",
      "what_it_reveals": "what answer reveals",
      "follow_up_if": "when to ask follow-up"
    }}
  ]
}}

Generate 5-8 specific, actionable questions. Focus on extracting implicit knowledge unique to this contributor's work."""
    
    def _build_summary_prompt(self, file_data: Dict[str, Any],
                             context: Dict[str, Any],
                             employee_username: str) -> str:
        """Build prompt for knowledge summary"""
        file_name = file_data.get('file', 'Unknown')
        risk_score = file_data.get('risk_score', 0)
        
        return f"""Create a clear knowledge transfer summary for this file:

File: {file_name}
Risk Score: {risk_score}
Employee: {employee_username}

Answer these three critical questions clearly and concisely:

1. "What do they know that others don't?"
   - What unique knowledge does this employee have?
   - What undocumented decisions or context?
   
2. "What could break after they leave?"
   - What systems or processes depend on their knowledge?
   - What failures could occur?
   
3. "What must the manager ask them before Day-0?"
   - What critical questions must be answered?
   - What knowledge must be transferred?

Provide a JSON response:
{{
  "what_they_know": {{
    "unique_knowledge": ["knowledge1", "knowledge2"],
    "undocumented_decisions": ["decision1", "decision2"],
    "implicit_context": "explanation"
  }},
  "what_could_break": {{
    "systems_at_risk": ["system1", "system2"],
    "failure_scenarios": ["scenario1", "scenario2"],
    "impact_severity": "high|medium|low"
  }},
  "must_ask_before_day0": {{
    "critical_questions": ["question1", "question2"],
    "knowledge_to_transfer": ["knowledge1", "knowledge2"],
    "urgency": "immediate|high|medium"
  }},
  "summary": "one paragraph executive summary"
}}

Be specific, actionable, and clear."""
    
    def _fallback_analysis(self, knowledge_unit: Dict[str, Any],
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when AI is unavailable"""
        return {
            "decision_extraction": {
                "undocumented_decisions": ["Analysis requires AI"],
                "architectural_choices": [],
                "design_rationale": "AI analysis unavailable"
            },
            "risk_extraction": {
                "what_could_break": ["Knowledge loss risk identified"],
                "failure_scenarios": [],
                "impact_assessment": "High risk due to single owner"
            },
            "dependency_extraction": {
                "tightly_coupled_systems": [],
                "people_dependencies": [],
                "external_dependencies": []
            },
            "knowledge_gap_detection": {
                "what_new_engineer_would_struggle_with": ["System understanding"],
                "implicit_knowledge": [],
                "missing_documentation": []
            }
        }
    
    def _fallback_questions(self, topic: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback questions when AI is unavailable"""
        return [
            {
                "question": f"What is the purpose and functionality of {topic.get('title', 'this topic')}?",
                "category": "knowledge_gap",
                "priority": "high",
                "what_it_reveals": "Basic understanding of the topic",
                "follow_up_if": "Answer is unclear"
            },
            {
                "question": "What could break if this knowledge is lost?",
                "category": "risk_extraction",
                "priority": "critical",
                "what_it_reveals": "Critical dependencies and risks",
                "follow_up_if": "High risk identified"
            }
        ]
    
    def _fallback_summary(self, file_data: Dict[str, Any],
                         context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback summary when AI is unavailable"""
        return {
            "what_they_know": {
                "unique_knowledge": ["File ownership and context"],
                "undocumented_decisions": [],
                "implicit_context": "AI analysis unavailable - manual review required"
            },
            "what_could_break": {
                "systems_at_risk": ["System using this file"],
                "failure_scenarios": [],
                "impact_severity": "medium"
            },
            "must_ask_before_day0": {
                "critical_questions": ["What is the purpose of this file?", "Who else understands this?"],
                "knowledge_to_transfer": ["File context and usage"],
                "urgency": "high"
            },
            "summary": "Manual review required - AI analysis unavailable"
        }

