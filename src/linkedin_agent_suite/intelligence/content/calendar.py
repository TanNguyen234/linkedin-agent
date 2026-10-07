"""Content calendar and editorial schedule."""
from typing import List, Dict

DEFAULT_SCHEDULE = [
    {"day": "Monday", "theme": "Technical Architecture & Systems"},
    {"day": "Wednesday", "theme": "Engineering Lessons & Optimization"},
    {"day": "Friday", "theme": "Build-In-Public & Project Milestones"}
]

class ContentCalendar:
    @staticmethod
    def get_schedule() -> List[Dict[str, str]]:
        return DEFAULT_SCHEDULE
