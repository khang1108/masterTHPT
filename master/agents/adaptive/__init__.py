"""Public exports for the adaptive-learning package.

These exports are the intended MVP surface: a typed attempt record, the core
adaptive service, and scored question recommendations.
"""

from master.agents.adaptive.profile_builder import AdaptiveAttempt
from master.agents.adaptive.question_gen import QuestionRecommendation
from master.agents.adaptive.agent import AdaptiveAgent
from master.agents.adaptive.service import AdaptiveService

__all__ = [
    "AdaptiveAttempt",
    "AdaptiveAgent",
    "AdaptiveService",
    "QuestionRecommendation",
]
