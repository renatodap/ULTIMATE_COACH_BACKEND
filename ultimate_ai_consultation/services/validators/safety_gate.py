"""
Safety Validator - Non-Bypassable Medical and Age Gates

This module implements CRITICAL safety checks that MUST pass before
generating any program. These are hard stops - no exceptions.

IMPORTANT: NEVER disable these checks in production. Lives depend on it.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from config import settings

logger = logging.getLogger(__name__)


class SafetyLevel(str, Enum):
    """Safety clearance levels."""

    CLEARED = "cleared"  # Safe to proceed
    BLOCKED = "blocked"  # Cannot proceed without medical clearance
    WARNING = "warning"  # Can proceed with modifications


@dataclass
class SafetyCheckResult:
    """
    Result of safety validation.

    Attributes:
        level: Safety clearance level
        passed: Whether user can proceed
        violations: List of safety issues detected
        recommendations: What user should do
        modifications: Required program modifications if WARNING
        reason: Primary reason for block/warning
    """

    level: SafetyLevel
    passed: bool
    violations: List[Dict[str, str]]
    recommendations: List[str]
    modifications: Dict[str, any]
    reason: Optional[str] = None


class SafetyValidator:
    """
    Validates user safety for program generation.

    Implements evidence-based screening for:
    1. Medical contraindications
    2. Age-appropriate programming
    3. Physiological safety bounds
    4. Eating disorder indicators
    """

    def __init__(self):
        """Initialize safety validator."""
        self.enabled = settings.ENABLE_SAFETY_GATE
        if not self.enabled:
            logger.critical("⚠️ SAFETY GATE DISABLED - THIS IS DANGEROUS!")

    def validate(
        self,
        age: int,
        sex_at_birth: str,
        weight_kg: float,
        height_cm: float,
        medical_conditions: List[str],
        medications: List[str],
        recent_surgeries: Optional[str],
        pregnancy_status: Optional[str],
        doctor_clearance: bool,
        goal: str,
        target_calorie_deficit_pct: Optional[float] = None,
        training_intensity: Optional[str] = None,
    ) -> SafetyCheckResult:
        """
        Perform comprehensive safety validation.

        Args:
            age: Age in years
            sex_at_birth: Biological sex
            weight_kg: Current weight
            height_cm: Height
            medical_conditions: List of medical conditions
            medications: List of current medications
            recent_surgeries: Description of recent surgeries (if any)
            pregnancy_status: Pregnancy/postpartum status
            doctor_clearance: Whether user has doctor clearance for vigorous exercise
            goal: Fitness goal
            target_calorie_deficit_pct: Planned calorie deficit (if cutting)
            training_intensity: Planned training intensity

        Returns:
            SafetyCheckResult with clearance level and recommendations
        """
        if not self.enabled:
            logger.warning("Safety gate disabled - returning automatic clearance")
            return SafetyCheckResult(
                level=SafetyLevel.CLEARED,
                passed=True,
                violations=[],
                recommendations=[],
                modifications={},
            )

        violations = []
        recommendations = []
        modifications = {}
        highest_severity = SafetyLevel.CLEARED

        # ===================================================================
        # 1. MEDICAL RED FLAGS (Auto-block)
        # ===================================================================

        # Cardiac conditions
        cardiac_flags = [
            "heart disease",
            "cardiac",
            "heart attack",
            "myocardial infarction",
            "arrhythmia",
            "heart failure",
            "angina",
            "chest pain",
            "pacemaker",
        ]
        if any(flag in " ".join(medical_conditions).lower() for flag in cardiac_flags):
            if not doctor_clearance:
                violations.append({
                    "type": "cardiac_condition",
                    "severity": "critical",
                    "message": "Cardiac condition detected without medical clearance",
                })
                recommendations.append(
                    "Obtain clearance from cardiologist before starting exercise program"
                )
                highest_severity = SafetyLevel.BLOCKED

        # Uncontrolled hypertension
        if "hypertension" in " ".join(medical_conditions).lower() and not doctor_clearance:
            violations.append({
                "type": "uncontrolled_hypertension",
                "severity": "critical",
                "message": "Hypertension without medical clearance",
            })
            recommendations.append("Get blood pressure controlled and obtain medical clearance")
            highest_severity = SafetyLevel.BLOCKED

        # Recent cardiac event (<6 months)
        if "recent" in str(recent_surgeries).lower() and any(
            flag in str(recent_surgeries).lower() for flag in ["heart", "cardiac", "bypass"]
        ):
            violations.append({
                "type": "recent_cardiac_event",
                "severity": "critical",
                "message": "Recent cardiac surgery or event",
            })
            recommendations.append("Complete cardiac rehabilitation before high-intensity training")
            highest_severity = SafetyLevel.BLOCKED

        # Diabetes (Type 1 requires medical supervision)
        if "type 1 diabetes" in " ".join(medical_conditions).lower() and not doctor_clearance:
            violations.append({
                "type": "type_1_diabetes",
                "severity": "high",
                "message": "Type 1 diabetes requires medical supervision",
            })
            recommendations.append("Work with endocrinologist to adjust insulin around training")
            highest_severity = SafetyLevel.WARNING
            modifications["monitor_blood_sugar"] = True

        # Medications that affect exercise
        dangerous_meds = ["beta-blocker", "insulin", "blood thinner", "warfarin"]
        detected_meds = [med for med in medications if any(d in med.lower() for d in dangerous_meds)]
        if detected_meds and not doctor_clearance:
            violations.append({
                "type": "medication_interaction",
                "severity": "high",
                "message": f"Medications require medical consultation: {', '.join(detected_meds)}",
            })
            recommendations.append("Consult physician about exercise with current medications")
            highest_severity = SafetyLevel.WARNING

        # ===================================================================
        # 2. PREGNANCY & POSTPARTUM
        # ===================================================================

        if pregnancy_status:
            status_lower = pregnancy_status.lower()

            if "pregnant" in status_lower and "post" not in status_lower:
                if not doctor_clearance:
                    violations.append({
                        "type": "pregnancy_no_clearance",
                        "severity": "critical",
                        "message": "Pregnancy without OB clearance for exercise",
                    })
                    recommendations.append("Obtain clearance from OB/GYN before starting program")
                    highest_severity = SafetyLevel.BLOCKED
                else:
                    # Cleared but need modifications
                    violations.append({
                        "type": "pregnancy_modifications",
                        "severity": "moderate",
                        "message": "Pregnancy requires program modifications",
                    })
                    recommendations.append("Avoid supine exercises after 1st trimester")
                    recommendations.append("Monitor for warning signs (dizziness, bleeding, contractions)")
                    modifications.update({
                        "max_heart_rate_bpm": 140,
                        "avoid_supine_after_week": 12,
                        "avoid_contact_sports": True,
                        "avoid_high_impact": True,
                    })
                    if highest_severity == SafetyLevel.CLEARED:
                        highest_severity = SafetyLevel.WARNING

            elif "postpartum" in status_lower or "post-partum" in status_lower:
                # Extract weeks postpartum if possible
                if not doctor_clearance:
                    violations.append({
                        "type": "postpartum_no_clearance",
                        "severity": "high",
                        "message": "Postpartum without medical clearance",
                    })
                    recommendations.append("Obtain postpartum checkup clearance before resuming training")
                    highest_severity = SafetyLevel.WARNING
                else:
                    recommendations.append("Gradual return to training (pelvic floor considerations)")
                    modifications["pelvic_floor_focus"] = True

        # ===================================================================
        # 3. AGE GATES
        # ===================================================================

        if age < 18:
            violations.append({
                "type": "minor",
                "severity": "moderate",
                "message": "Under 18 - growth considerations",
            })
            recommendations.append("No aggressive calorie deficits during growth period")
            recommendations.append("Focus on skill development and movement quality")
            modifications.update({
                "max_calorie_deficit_pct": 0.10,  # Max 10% deficit
                "avoid_max_effort_lifts": True,
                "growth_plate_awareness": True,
            })
            if highest_severity == SafetyLevel.CLEARED:
                highest_severity = SafetyLevel.WARNING

        elif age >= 65:
            violations.append({
                "type": "older_adult",
                "severity": "moderate",
                "message": "Age 65+ - fall risk and bone density considerations",
            })
            recommendations.append("Include balance training")
            recommendations.append("Consider bone density screening")
            recommendations.append("Start conservatively and progress slowly")
            modifications.update({
                "include_balance_training": True,
                "lower_starting_intensity": True,
                "slower_progression": True,
                "fall_risk_awareness": True,
            })
            if not doctor_clearance:
                recommendations.append("Obtain medical clearance for exercise program")
                if highest_severity == SafetyLevel.CLEARED:
                    highest_severity = SafetyLevel.WARNING

        # ===================================================================
        # 4. BMI EXTREMES (Screening Tool, Not Diagnostic)
        # ===================================================================

        bmi = weight_kg / ((height_cm / 100) ** 2)

        if bmi < 16:
            violations.append({
                "type": "very_low_bmi",
                "severity": "critical",
                "message": f"BMI {bmi:.1f} - very underweight",
            })
            recommendations.append("Medical evaluation required before exercise program")
            recommendations.append("Consider eating disorder screening")
            highest_severity = SafetyLevel.BLOCKED

        elif bmi < 18.5:
            violations.append({
                "type": "low_bmi",
                "severity": "moderate",
                "message": f"BMI {bmi:.1f} - underweight",
            })
            recommendations.append("No calorie deficits recommended")
            recommendations.append("Focus on strength and health markers")
            modifications["no_deficit_allowed"] = True
            if highest_severity == SafetyLevel.CLEARED:
                highest_severity = SafetyLevel.WARNING

        elif bmi > 40 and not doctor_clearance:
            violations.append({
                "type": "very_high_bmi",
                "severity": "high",
                "message": f"BMI {bmi:.1f} - Class 3 obesity",
            })
            recommendations.append("Medical clearance recommended")
            recommendations.append("Start with low-impact activities")
            modifications.update({
                "start_low_impact": True,
                "monitor_blood_pressure": True,
            })
            if highest_severity == SafetyLevel.CLEARED:
                highest_severity = SafetyLevel.WARNING

        # ===================================================================
        # 5. EATING DISORDER INDICATORS
        # ===================================================================

        # Extreme calorie deficits
        if target_calorie_deficit_pct and target_calorie_deficit_pct > 0.30:
            violations.append({
                "type": "extreme_deficit",
                "severity": "critical",
                "message": f"Planned deficit of {target_calorie_deficit_pct*100:.0f}% is unsafe",
            })
            recommendations.append("Maximum safe deficit is 25%")
            highest_severity = SafetyLevel.BLOCKED

        # Combination of low BMI + aggressive cutting
        if bmi < 20 and goal.lower() in ["fat_loss", "weight_loss"] and not doctor_clearance:
            violations.append({
                "type": "low_weight_cutting",
                "severity": "high",
                "message": "Already lean - further weight loss may be unhealthy",
            })
            recommendations.append("Consider maintenance or recomp instead of cutting")
            recommendations.append("Psychological evaluation may be beneficial")
            if highest_severity == SafetyLevel.CLEARED:
                highest_severity = SafetyLevel.WARNING

        # ===================================================================
        # 6. SURGICAL CONTRAINDICATIONS
        # ===================================================================

        if recent_surgeries and "recent" in recent_surgeries.lower():
            # Generic post-surgical (assuming <6 weeks)
            if not doctor_clearance:
                violations.append({
                    "type": "recent_surgery",
                    "severity": "high",
                    "message": "Recent surgery without clearance",
                })
                recommendations.append("Obtain surgical clearance before exercise")
                highest_severity = SafetyLevel.WARNING

        # ===================================================================
        # 7. ORTHOPEDIC ISSUES
        # ===================================================================

        joint_issues = ["arthritis", "joint replacement", "herniated disc", "back pain", "knee pain"]
        detected_issues = [
            issue
            for issue in medical_conditions
            if any(j in issue.lower() for j in joint_issues)
        ]

        if detected_issues:
            violations.append({
                "type": "orthopedic_considerations",
                "severity": "low",
                "message": f"Orthopedic issues noted: {', '.join(detected_issues)}",
            })
            recommendations.append("Exercise modifications for joint health")
            recommendations.append("Consider physical therapy consultation")
            modifications["joint_friendly_modifications"] = True
            if highest_severity == SafetyLevel.CLEARED:
                highest_severity = SafetyLevel.WARNING

        # ===================================================================
        # FINAL DETERMINATION
        # ===================================================================

        passed = highest_severity != SafetyLevel.BLOCKED

        # Log result
        if not passed:
            logger.warning(
                f"Safety check BLOCKED for user (age: {age}, BMI: {bmi:.1f}). "
                f"Violations: {len(violations)}"
            )
        elif highest_severity == SafetyLevel.WARNING:
            logger.info(
                f"Safety check PASSED with warnings for user (age: {age}, BMI: {bmi:.1f}). "
                f"Modifications required: {list(modifications.keys())}"
            )
        else:
            logger.info(f"Safety check CLEARED for user (age: {age}, BMI: {bmi:.1f})")

        # Primary block reason (most critical)
        block_reason = None
        if not passed:
            critical_violations = [v for v in violations if v["severity"] == "critical"]
            if critical_violations:
                block_reason = critical_violations[0]["message"]

        return SafetyCheckResult(
            level=highest_severity,
            passed=passed,
            violations=violations,
            recommendations=recommendations,
            modifications=modifications,
            reason=block_reason,
        )

    def validate_plan_adjustments(
        self, current_deficit_pct: float, proposed_deficit_pct: float, adherence_pct: float
    ) -> Tuple[bool, List[str]]:
        """
        Validate proposed plan adjustments during adaptive reassessment.

        Args:
            current_deficit_pct: Current calorie deficit %
            proposed_deficit_pct: Proposed new deficit %
            adherence_pct: Recent adherence rate

        Returns:
            Tuple of (is_safe, warnings)
        """
        warnings = []
        is_safe = True

        # Don't increase deficit if adherence is already low
        if adherence_pct < 0.70 and proposed_deficit_pct > current_deficit_pct:
            warnings.append(
                f"Low adherence ({adherence_pct*100:.0f}%) - don't increase deficit"
            )
            is_safe = False

        # Cap deficit at 25%
        if proposed_deficit_pct > 0.25:
            warnings.append(f"Deficit of {proposed_deficit_pct*100:.0f}% exceeds 25% safety cap")
            is_safe = False

        # Warn on large single adjustments
        adjustment_size = abs(proposed_deficit_pct - current_deficit_pct)
        if adjustment_size > 0.05:
            warnings.append(
                f"Large adjustment ({adjustment_size*100:.0f}%) - consider smaller steps"
            )

        return is_safe, warnings
