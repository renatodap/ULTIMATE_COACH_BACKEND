"""
Consultation API Endpoints

Exposes the ConsultationAIService for frontend integration.
"""

import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel
from typing import Optional

from app.api.dependencies import get_current_user
from app.services.consultation_ai_service import ConsultationAIService

logger = structlog.get_logger()

router = APIRouter()


# ========================================================================
# REQUEST/RESPONSE MODELS
# ========================================================================

class StartConsultationRequest(BaseModel):
    consultation_key: Optional[str] = None  # Now optional - free for all users


class SendMessageRequest(BaseModel):
    session_id: str
    message: str


# ========================================================================
# ENDPOINTS
# ========================================================================

@router.post(
    "/consultation/start",
    status_code=status.HTTP_200_OK,
    summary="Start AI consultation session (GATED)",
    description="Start consultation session. Requires consultation_enabled=true on user profile."
)
async def start_consultation(
    request_data: StartConsultationRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Start a new AI-powered consultation session.

    ACCESS CONTROL: User must have consultation_enabled=true in their profile.
    This is manually set by admins in Supabase.

    Args:
        consultation_key: Optional consultation key (legacy support)
        user: Current authenticated user

    Returns:
        session_id, initial message, and progress info

    Raises:
        403 Forbidden: If user doesn't have consultation access
    """
    try:
        # STEP 1: Check if user has consultation access
        from app.services.supabase_service import SupabaseService
        db = SupabaseService()

        profile_result = db.client.table("profiles")\
            .select("consultation_enabled")\
            .eq("id", user["id"])\
            .single()\
            .execute()

        if not profile_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )

        consultation_enabled = profile_result.data.get("consultation_enabled", False)

        if not consultation_enabled:
            logger.warning(
                "consultation_access_denied",
                user_id=user["id"][:8],
                reason="consultation_enabled=false"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Consultation access not enabled for this account. Please contact support."
            )

        logger.info(
            "consultation_access_granted",
            user_id=user["id"][:8]
        )

        # Get client info
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Initialize service
        service = ConsultationAIService()

        # Start consultation
        result = await service.start_consultation(
            user_id=user["id"],
            consultation_key=request_data.consultation_key,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if not result.get("success"):
            # Map error codes to HTTP status
            error = result.get("error", "unknown")
            if error in ["key_required", "invalid_key", "key_exhausted", "key_expired"]:
                status_code = status.HTTP_400_BAD_REQUEST
            elif error == "key_not_assigned":
                status_code = status.HTTP_403_FORBIDDEN
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "Failed to start consultation")
            )

        logger.info(
            "consultation_started",
            user_id=user["id"],
            session_id=result["session_id"]
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("start_consultation_error", user_id=user["id"], error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start consultation. Please try again."
        )


@router.post(
    "/consultation/message",
    status_code=status.HTTP_200_OK,
    summary="Send message in consultation",
    description="Send a user message and get AI response"
)
async def send_consultation_message(
    request_data: SendMessageRequest,
    user: dict = Depends(get_current_user)
):
    """
    Send a message in an active consultation session.

    The AI will process the message, extract structured data,
    and return a conversational response.

    Args:
        session_id: Active consultation session UUID
        message: User's message text
        user: Current authenticated user

    Returns:
        AI response, extracted data count, section progress
    """
    try:
        # Initialize service
        service = ConsultationAIService()

        # Process message
        result = await service.process_message(
            user_id=user["id"],
            session_id=request_data.session_id,
            message=request_data.message
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to process message")
            )

        logger.info(
            "consultation_message_processed",
            user_id=user["id"],
            session_id=request_data.session_id,
            extracted_items=result.get("extracted_items", 0),
            section=result.get("current_section")
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "send_message_error",
            user_id=user["id"],
            session_id=request_data.session_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message. Please try again."
        )


@router.post(
    "/consultation/{session_id}/complete",
    status_code=status.HTTP_200_OK,
    summary="Mark consultation as complete and generate program",
    description="Mark consultation session as completed, update user profile, and automatically generate personalized 2-week program"
)
async def complete_consultation(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Mark a consultation session as complete and auto-generate personalized program.

    This endpoint:
    1. Sets consultation_completed=true on user profile
    2. Marks session as completed (100% progress)
    3. Generates 2-week training + nutrition program from consultation data
    4. Stores program in database (ready to use)

    Args:
        session_id: Consultation session UUID
        user: Current authenticated user

    Returns:
        Success status, program_id, and program summary
    """
    try:
        from app.services.supabase_service import SupabaseService
        from app.services.program_storage_service import ProgramStorageService
        from uuid import UUID
        from datetime import datetime, timedelta

        db = SupabaseService()
        user_id = UUID(user["id"])

        # Update user profile
        await db.update_profile(user_id, {
            "consultation_completed": True,
            "consultation_completed_at": datetime.utcnow().isoformat()
        })

        # Mark session as completed
        db.client.table("consultation_sessions")\
            .update({
                "completed_at": datetime.utcnow().isoformat(),
                "progress_percentage": 100
            })\
            .eq("id", session_id)\
            .execute()

        logger.info(
            "consultation_completed",
            user_id=user["id"],
            session_id=session_id
        )

        # ================================================================
        # GENERATE CONVERSATIONAL PROFILE & PERSONALIZED SYSTEM PROMPT
        # ================================================================
        # NOTE: This takes 5-10 seconds for two Claude API calls:
        #   1. Generate conversational_profile (200 words) - ~3 seconds
        #   2. Generate initial system prompt (500-800 words) - ~5 seconds
        #
        # RACE CONDITION MITIGATION:
        # If user starts coaching immediately after this, they might hit the
        # coach before prompt is saved. The coach gracefully falls back to
        # generic prompt in this case.
        #
        # RECOMMENDATION: Frontend should show "Generating your personalized
        # coach... (10 seconds)" loading state before enabling chat.
        # ================================================================
        try:
            from app.services.consultation_ai_service import ConsultationAIService
            from app.services.system_prompt_generator import get_system_prompt_generator

            consultation_service = ConsultationAIService()

            # Step 1: Generate conversational_profile from consultation messages
            logger.info(
                "generating_conversational_profile",
                user_id=user["id"],
                session_id=session_id
            )

            conversational_profile = await consultation_service.generate_conversational_profile(
                session_id=session_id,
                user_id=user["id"]
            )

            logger.info(
                "conversational_profile_generated",
                user_id=user["id"][:8],
                profile_words=len(conversational_profile.split())
            )

            # Step 2: Fetch user data for prompt generation
            profile_result = db.client.table("profiles")\
                .select("*")\
                .eq("id", user["id"])\
                .single()\
                .execute()

            if not profile_result.data:
                raise Exception("User profile not found")

            profile_data = profile_result.data

            # Step 3: Generate initial personalized system prompt
            logger.info(
                "generating_initial_system_prompt",
                user_id=user["id"][:8]
            )

            prompt_generator = get_system_prompt_generator()

            onboarding_data = {
                "age": profile_data.get("age", 30),
                "biological_sex": profile_data.get("biological_sex", "male"),
                "current_weight_kg": profile_data.get("current_weight_kg", 75.0),
                "goal_weight_kg": profile_data.get("goal_weight_kg", 70.0),
                "height_cm": profile_data.get("height_cm", 175.0),
                "activity_level": profile_data.get("activity_level", "moderate")
            }

            user_goals = {
                "primary_goal": profile_data.get("primary_goal", "maintain"),
                "experience_level": profile_data.get("experience_level", "beginner"),
                "daily_calories": profile_data.get("daily_calories", 2000),
                "protein_g": profile_data.get("protein_g", 150)
            }

            initial_prompt = await prompt_generator.generate_initial_prompt(
                conversational_profile=conversational_profile,
                onboarding_data=onboarding_data,
                user_goals=user_goals
            )

            logger.info(
                "initial_system_prompt_generated",
                user_id=user["id"][:8],
                prompt_length=len(initial_prompt)
            )

            # Step 4: Save conversational_profile and system prompt to profiles
            db.client.table("profiles")\
                .update({
                    "conversational_profile": conversational_profile,
                    "coaching_system_prompt": initial_prompt,
                    "system_prompt_version": 1,
                    "last_prompt_update": datetime.utcnow().isoformat()
                })\
                .eq("id", user["id"])\
                .execute()

            logger.info(
                "personalized_coaching_ready",
                user_id=user["id"][:8],
                has_profile=True,
                has_prompt=True,
                prompt_version=1
            )

        except Exception as profile_error:
            # Log but don't fail consultation completion
            logger.error(
                "personalized_prompt_generation_failed",
                user_id=user["id"],
                session_id=session_id,
                error=str(profile_error),
                exc_info=True
            )
            # Continue to program generation even if this fails

        # ================================================================
        # AUTO-GENERATE PROGRAM FROM CONSULTATION DATA
        # ================================================================
        logger.info(
            "generating_program_from_consultation",
            user_id=user["id"],
            session_id=session_id
        )

        try:
            from ultimate_ai_consultation.api.generate_program import generate_program_from_consultation
            from ultimate_ai_consultation.api.schemas.inputs import ConsultationTranscript, GenerationOptions

            # Fetch consultation data from database
            session_data = db.client.table("consultation_sessions")\
                .select("*")\
                .eq("id", session_id)\
                .single()\
                .execute()

            if not session_data.data:
                raise Exception("Consultation session not found")

            # Fetch user profile for demographics
            profile = db.client.table("profiles")\
                .select("*")\
                .eq("id", str(user_id))\
                .single()\
                .execute()

            if not profile.data:
                raise Exception("User profile not found")

            # Build ConsultationTranscript from database
            # This uses the rich consultation data (9+ tables) instead of basic onboarding
            consultation = ConsultationTranscript(
                user_id=str(user_id),
                session_id=session_id,
                # Demographics from profile
                age=profile.data.get("age", 30),
                biological_sex=profile.data.get("biological_sex", "male"),
                height_cm=profile.data.get("height_cm", 175.0),
                current_weight_kg=profile.data.get("current_weight_kg", 75.0),
                goal_weight_kg=profile.data.get("goal_weight_kg", 70.0),
                # Goals from profile
                primary_goal=profile.data.get("primary_goal", "maintain"),
                experience_level=profile.data.get("experience_level", "beginner"),
                # NOTE: Additional consultation data (training_modalities, availability, etc.)
                # will be fetched from dedicated tables by the generator
            )

            # Generation options (default to 2 weeks)
            options = GenerationOptions(
                program_duration_weeks=2,
                meals_per_day=profile.data.get("meals_per_day", 3)
            )

            # Generate program
            logger.info("calling_program_generator", user_id=str(user_id))
            program_bundle, warnings = generate_program_from_consultation(consultation, options)

            # Store program in database
            storage_service = ProgramStorageService()
            program_id = await storage_service.store_program_bundle(
                program_bundle=program_bundle.model_dump(),
                user_id=str(user_id)
            )

            logger.info(
                "program_generated_successfully",
                program_id=program_id,
                user_id=str(user_id),
                session_id=session_id,
                warnings_count=len(warnings)
            )

            return {
                "success": True,
                "message": "Consultation completed and program generated successfully!",
                "consultation_completed": True,
                "program_generated": True,
                "program_id": program_id,
                "program_summary": {
                    "duration_weeks": 2,
                    "sessions_per_week": program_bundle.training_plan.sessions_per_week,
                    "daily_calories": program_bundle.target_calories_kcal,
                    "start_date": program_bundle.created_at.date().isoformat(),
                    "next_reassessment": (program_bundle.created_at.date() + timedelta(days=14)).isoformat()
                }
            }

        except Exception as program_error:
            # If program generation fails, log but don't fail the consultation completion
            logger.error(
                "program_generation_failed_after_consultation",
                user_id=user["id"],
                session_id=session_id,
                error=str(program_error),
                exc_info=True
            )

            # Return success for consultation but indicate program generation failed
            return {
                "success": True,
                "message": "Consultation completed successfully, but program generation failed. You can generate manually later.",
                "consultation_completed": True,
                "program_generated": False,
                "program_error": str(program_error)
            }

    except Exception as e:
        logger.error(
            "complete_consultation_error",
            user_id=user["id"],
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete consultation. Please try again."
        )
