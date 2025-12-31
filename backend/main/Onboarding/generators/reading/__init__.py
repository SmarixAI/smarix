"""
Onboarding Data Generators Module
Contains all generators for creating onboarding documentation
"""

from backend.main.Onboarding.generators.reading.generate_repo_structure import generate_repo_structure_data
from backend.main.Onboarding.generators.reading.generate_tech_stacks import generate_tech_stack_data
from backend.main.Onboarding.generators.reading.generate_reading_overview import generate_reading_overview
from backend.main.Onboarding.generators.reading.generate_app_features import generate_app_features_data
from backend.main.Onboarding.generators.reading.generate_dev_setup import generate_dev_setup_data
from backend.main.Onboarding.generators.reading.generate_code_conventions import generate_code_conventions_data

__all__ = [
    'generate_repo_structure_data',
    'generate_tech_stack_data',
    'generate_reading_overview',
    'generate_app_features_data',
    'generate_dev_setup_data',
    'generate_code_conventions_data',
]

