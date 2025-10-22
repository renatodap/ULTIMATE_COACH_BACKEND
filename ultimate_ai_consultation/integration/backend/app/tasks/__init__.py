"""
Background Tasks Module

Drop-in for: ULTIMATE_COACH_BACKEND/app/tasks/

Handles:
- Scheduled bi-weekly reassessments
- Automated plan adjustments
- Background processing
"""

from .scheduled_tasks import (
    init_scheduler,
    shutdown_scheduler,
    trigger_daily_reassessment_check,
    run_reassessment_for_user,
)

__all__ = [
    "init_scheduler",
    "shutdown_scheduler",
    "trigger_daily_reassessment_check",
    "run_reassessment_for_user",
]
