from typing import List, Dict, Any
from enum import Enum
import random

class QuestionCategory(Enum):
    CORE = "core"
    APPLIED = "applied"
    CANDIDATE_SPECIFIC = "candidate_specific"

class InterviewPlanner:
    def __init__(self, total_questions: int = 10):
        self.total_questions = total_questions

    def plan_session(self) -> List[QuestionCategory]:
        """
        Pre-plan 8-10 question slots with a mix:
        40% core, 30% applied, 30% candidate-specific.
        """
        plan = []
        
        core_count = int(self.total_questions * 0.4)
        applied_count = int(self.total_questions * 0.3)
        candidate_count = self.total_questions - core_count - applied_count
        
        plan.extend([QuestionCategory.CORE] * core_count)
        plan.extend([QuestionCategory.APPLIED] * applied_count)
        plan.extend([QuestionCategory.CANDIDATE_SPECIFIC] * candidate_count)
        
        # Shuffle to mix them up
        random.shuffle(plan)
        return plan

    def get_prompt_modifier(self, category: QuestionCategory) -> str:
        """Get instructions for the LLM based on the planned category."""
        if category == QuestionCategory.CORE:
            return "Focus on fundamental concepts, theory, and first principles from the documentation."
        if category == QuestionCategory.APPLIED:
            return "Focus on real-world application, implementation details, and edge cases."
        if category == QuestionCategory.CANDIDATE_SPECIFIC:
            return "Focus on how the concepts in the documentation intersect with the candidate's specific background and technologies."
        return ""
