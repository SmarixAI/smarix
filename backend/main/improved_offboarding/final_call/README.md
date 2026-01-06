# Final Call Module

This module implements features 31-52 for exit discussion and knowledge extraction as part of the improved offboarding system.

## Features Implemented

### Final Call Identification (31-38)
- **31. Automatic Final Call topic detection** - Identifies topics that must be discussed
- **32. High-risk knowledge prioritization** - Prioritizes knowledge based on risk scores
- **33. Knowledge units requiring explanation** - Identifies knowledge units needing discussion
- **34. Implicit knowledge identification** - Detects implicit knowledge that may not be documented
- **35. Architecture decision extraction** - Extracts architecture decisions from PRs and code
- **36. Failure scenario identification** - Identifies known failure scenarios and workarounds
- **37. Business logic explanation detection** - Detects business logic files requiring explanation
- **38. Operational flow explanation detection** - Identifies operational flows needing documentation

### AI-Guided Discussion (39-45)
- **39. AI-generated Final Call agenda** - Generates structured agenda for Final Call
- **40. AI-generated questions per topic** - Creates specific questions for each topic
- **41. Suggested discussion order** - Recommends optimal order for discussing topics
- **42. Time estimation per topic** - Estimates time needed for each topic
- **43. Stakeholder suggestions** - Recommends who should attend Final Call
- **44. Risk justification for each topic** - Provides justification for including each topic
- **45. AI confidence indicator per question** - Calculates confidence for each question

### Execution & Tracking (46-52)
- **46. Final Call task grouping by knowledge unit** - Groups tasks by knowledge category
- **47. Completion checklist per topic** - Creates checklists for tracking completion
- **48. Recording & transcript linkage** - Sets up structure for recording linkage
- **49. Knowledge validation checklist** - Creates validation criteria for knowledge transfer
- **50. Manager approval for completion** - Sets up approval workflow
- **51. Partial completion tracking** - Tracks partial completion of topics
- **52. Escalation for missed Final Calls** - Defines escalation procedures

## Usage

### Command Line

```bash
# Process Final Call for a repository
python -m main.improved_offboarding.final_call.main \
    --prerequisite-file backend/data/improved_offboarding/torvalds_test-tlb_prerequisites.json \
    --employee torvalds \
    --output-dir backend/data/improved_offboarding/final_call
```

### Python API

```python
from main.improved_offboarding.final_call.main_processor import FinalCallProcessor
import json

# Load prerequisite data
with open('prerequisites.json', 'r') as f:
    prerequisite_data = json.load(f)

# Initialize processor
processor = FinalCallProcessor()

# Process Final Call
results = processor.process(prerequisite_data, employee_username='employee_name')

# Save results
processor.save_results(results, 'owner', 'repo', 'employee_name')
```

## Input Requirements

The Final Call module requires:
- **Prerequisite data**: Complete JSON output from the prerequisite module (features 1-30)
- **Employee username** (optional): Username of departing employee for filtering

## Output Structure

The module generates a comprehensive JSON file containing:

```json
{
  "metadata": {
    "employee_username": "...",
    "processed_at": "ISO timestamp",
    "processor_version": "1.0.0",
    "features_implemented": [31, 32, ..., 52]
  },
  "topic_identification": {
    "final_call_topics": {...},
    "high_risk_prioritization": {...},
    "knowledge_units_requiring_explanation": {...},
    "implicit_knowledge": {...},
    "architecture_decisions": {...},
    "failure_scenarios": {...},
    "business_logic_explanations": {...},
    "operational_flow_explanations": {...}
  },
  "ai_guided_discussion": {
    "final_call_agenda": {...},
    "questions_per_topic": {...},
    "suggested_discussion_order": {...},
    "time_estimation": {...},
    "stakeholder_suggestions": {...},
    "risk_justification": {...},
    "ai_confidence_indicators": {...}
  },
  "execution_tracking": {
    "task_grouping": {...},
    "completion_checklists": {...},
    "recording_linkage": {...},
    "knowledge_validation_checklist": {...},
    "manager_approval_workflow": {...},
    "partial_completion_tracking": {...},
    "escalation_workflow": {...}
  },
  "summary": {...}
}
```

## Module Structure

```
final_call/
├── __init__.py
├── topic_identification.py    # Features 31-38
├── ai_guided_discussion.py    # Features 39-45
├── execution_tracking.py      # Features 46-52
├── main_processor.py          # Orchestrates all modules
├── main.py                    # CLI entry point
└── README.md
```

## Key Features

### Topic Detection
Automatically identifies topics that must be discussed in Final Call based on:
- High-risk knowledge files
- Single-owner files
- Critical subsystems
- Operational responsibilities
- Hidden dependencies
- Architecture decisions
- Failure scenarios

### AI-Guided Discussion
Generates comprehensive discussion materials including:
- Structured agenda with time estimates
- Specific questions for each topic
- Recommended discussion order
- Stakeholder recommendations
- Risk justifications

### Execution Tracking
Provides complete tracking infrastructure:
- Task grouping by knowledge unit
- Completion checklists
- Validation criteria
- Manager approval workflow
- Partial completion tracking
- Escalation procedures

## Integration

The Final Call module integrates seamlessly with:
- **Prerequisite module** (features 1-30) - Uses prerequisite analysis results
- **Handover module** (features 53-73) - Can use Final Call results for handover planning
- **Documentation module** (features 74-89) - Can use Final Call results for documentation needs

## Next Steps

After Final Call processing, you can:
1. Use results for **Handover** planning (features 53-73)
2. Use results for **Documentation** generation (features 74-89)
3. Schedule Final Call sessions based on agenda
4. Track completion using checklists and validation criteria

