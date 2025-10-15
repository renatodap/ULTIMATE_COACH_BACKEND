"""
SDK Validator - Validates Anthropic SDK installation at startup.

Ensures the SDK is properly installed with the correct API structure.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def validate_anthropic_sdk() -> Optional[str]:
    """
    Validate Anthropic SDK installation and return version info.

    Returns:
        None if validation succeeds
        Error message string if validation fails
    """
    try:
        import anthropic

        # Check SDK version
        sdk_version = getattr(anthropic, '__version__', 'unknown')
        logger.info(f"[SDK] Anthropic version: {sdk_version}")

        # Test sync client initialization (don't make actual API calls)
        try:
            sync_client = anthropic.Anthropic(api_key="dummy_key_for_validation")
            if not hasattr(sync_client, 'messages'):
                error_msg = f"Sync client missing 'messages' attribute (v{sdk_version})"
                logger.error(f"[SDK] [FAIL] {error_msg}")
                return error_msg
        except Exception as e:
            error_msg = f"Failed to create sync client: {str(e)}"
            logger.error(f"[SDK] ❌ {error_msg}")
            return error_msg

        # Test async client initialization
        try:
            async_client = anthropic.AsyncAnthropic(api_key="dummy_key_for_validation")
            if not hasattr(async_client, 'messages'):
                error_msg = f"Async client missing 'messages' attribute (v{sdk_version})"
                logger.error(f"[SDK] [FAIL] {error_msg}")
                return error_msg
        except Exception as e:
            error_msg = f"Failed to create async client: {str(e)}"
            logger.error(f"[SDK] ❌ {error_msg}")
            return error_msg

        logger.info(f"[SDK] [OK] Anthropic SDK validated successfully (v{sdk_version})")
        return None

    except ImportError as e:
        error_msg = f"Anthropic SDK not installed: {str(e)}"
        logger.error(f"[SDK] ❌ {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"SDK validation failed: {str(e)}"
        logger.error(f"[SDK] ❌ {error_msg}")
        return error_msg


def get_anthropic_version() -> str:
    """
    Get the installed Anthropic SDK version.

    Returns:
        Version string or 'unknown'
    """
    try:
        import anthropic
        return getattr(anthropic, '__version__', 'unknown')
    except ImportError:
        return 'not_installed'
