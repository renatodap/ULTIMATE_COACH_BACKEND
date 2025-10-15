"""
Security Service - Prompt Injection Protection

Detects and blocks prompt injection attempts in user messages.
Protects AI coach from malicious manipulation.

Attack Vectors Protected:
1. Role hijacking: "You are now a different AI"
2. Instruction override: "Ignore previous instructions"
3. System prompt extraction: "Repeat your instructions"
4. Jailbreak attempts: "DAN mode", "pretend mode"
5. Context pollution: Long messages with hidden instructions
6. Tool manipulation: Malicious tool inputs
7. Output leakage: Tricks to reveal system prompts
"""

import logging
import re
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SecurityService:
    """
    Detects and blocks prompt injection attacks.
    """

    # Injection patterns (regex)
    INJECTION_PATTERNS = [
        # Role hijacking
        (r'\b(you are (now|actually|really)|act as|pretend (to be|you are)|roleplay as)\b', 'role_hijacking'),
        (r'\b(ignore (your|previous|all) (role|instructions|rules|guidelines))\b', 'role_override'),
        (r'\b(forget (your|previous|everything|all))\b', 'memory_wipe'),

        # System prompt extraction
        (r'\b(show|reveal|display|print|output|tell me|what are) (your|the) (instructions|prompt|system prompt|rules|guidelines)\b', 'prompt_extraction'),
        (r'\b(repeat (your|the) (instructions|prompt|rules))\b', 'prompt_extraction'),
        (r'\b(what (were you told|are you programmed|are your instructions))\b', 'prompt_extraction'),

        # Jailbreak attempts
        (r'\bDAN mode\b', 'jailbreak'),
        (r'\bdo anything now\b', 'jailbreak'),
        (r'\bdeveloper mode\b', 'jailbreak'),
        (r'\bgod mode\b', 'jailbreak'),
        (r'\bunrestricted mode\b', 'jailbreak'),
        (r'\bjailbreak\b', 'jailbreak'),

        # System/admin impersonation
        (r'\b(SYSTEM|ADMIN|DEVELOPER|ANTHROPIC):\s', 'system_impersonation'),
        (r'\b(from now on|new instructions|updated guidelines)\b', 'instruction_injection'),

        # Delimiter attacks (trying to break out of user context)
        (r'(</user>|</system>|</assistant>|<\|im_end\|>|<\|endoftext\|>)', 'delimiter_attack'),
        (r'(\[INST\]|\[/INST\]|\[SYS\]|\[/SYS\])', 'delimiter_attack'),

        # Encoding attacks
        (r'(base64|rot13|hex encode|url encode|unicode escape)', 'encoding_attack'),

        # Instruction override
        (r'\b(disregard|override|bypass|circumvent) (all|previous|your) (rules|instructions|guidelines|safety)\b', 'instruction_override'),
    ]

    # Suspicious phrases (not automatically blocked, but flagged)
    SUSPICIOUS_PHRASES = [
        'ignore', 'disregard', 'forget', 'pretend', 'act as', 'system',
        'prompt', 'instructions', 'rules', 'jailbreak', 'DAN', 'developer'
    ]

    # Maximum message length to prevent context stuffing
    MAX_MESSAGE_LENGTH = 10000

    # Rate limiting
    RATE_LIMIT_WINDOW = 60  # seconds
    RATE_LIMIT_MAX_ATTEMPTS = 10  # max attempts per window

    def __init__(self, cache_service=None):
        """
        Initialize security service.

        Args:
            cache_service: Cache service for rate limiting
        """
        self.cache = cache_service
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), attack_type)
            for pattern, attack_type in self.INJECTION_PATTERNS
        ]

    def validate_message(
        self,
        message: str,
        user_id: str,
        check_rate_limit: bool = True
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate user message for security threats.

        Args:
            message: User's message
            user_id: User UUID (for rate limiting)
            check_rate_limit: Whether to check rate limit

        Returns:
            (is_safe, block_reason, metadata)
            - is_safe: True if message is safe, False if blocked
            - block_reason: Reason for blocking (None if safe)
            - metadata: Additional info (attack_type, confidence, etc.)
        """
        metadata = {
            "detected_attacks": [],
            "suspicion_score": 0.0,
            "suspicious_phrases": [],
            "length_violation": False
        }

        # 1. Check rate limiting
        if check_rate_limit and not self._check_rate_limit(user_id):
            logger.warning(f"[Security] Rate limit exceeded for user {user_id[:8]}...")
            return (False, "Rate limit exceeded. Please slow down.", {
                "attack_type": "rate_limit",
                "confidence": 1.0
            })

        # 2. Check message length (prevent context stuffing)
        if len(message) > self.MAX_MESSAGE_LENGTH:
            logger.warning(
                f"[Security] Message too long from user {user_id[:8]}...: "
                f"{len(message)} chars"
            )
            metadata["length_violation"] = True
            return (False, "Message too long. Please keep messages under 10,000 characters.", {
                "attack_type": "length_violation",
                "confidence": 1.0,
                "message_length": len(message)
            })

        # 3. Check for injection patterns
        message_lower = message.lower()

        for pattern, attack_type in self.compiled_patterns:
            match = pattern.search(message)
            if match:
                metadata["detected_attacks"].append({
                    "attack_type": attack_type,
                    "matched_text": match.group(0),
                    "position": match.start()
                })

                logger.warning(
                    f"[Security] ⚠️ Injection attempt detected from user {user_id[:8]}...\n"
                    f"Attack type: {attack_type}\n"
                    f"Matched: '{match.group(0)}'\n"
                    f"Full message: {message[:100]}..."
                )

                return (False, self._get_block_message(attack_type), {
                    "attack_type": attack_type,
                    "confidence": 0.95,
                    "matched_text": match.group(0),
                    **metadata
                })

        # 4. Check for suspicious phrases (flag but don't block)
        suspicious_count = 0
        for phrase in self.SUSPICIOUS_PHRASES:
            if phrase in message_lower:
                suspicious_count += 1
                metadata["suspicious_phrases"].append(phrase)

        # Calculate suspicion score (0-1)
        metadata["suspicion_score"] = min(suspicious_count / 5, 1.0)

        # 5. Check for excessive repetition (potential attack)
        if self._has_excessive_repetition(message):
            logger.warning(
                f"[Security] Excessive repetition detected from user {user_id[:8]}..."
            )
            return (False, "Message contains excessive repetition. Please rephrase.", {
                "attack_type": "repetition_attack",
                "confidence": 0.8,
                **metadata
            })

        # 6. Check for unusual character patterns
        if self._has_unusual_characters(message):
            logger.warning(
                f"[Security] Unusual characters detected from user {user_id[:8]}..."
            )
            return (False, "Message contains unusual characters. Please use standard text.", {
                "attack_type": "character_attack",
                "confidence": 0.7,
                **metadata
            })

        # Message is safe (but may be suspicious)
        if metadata["suspicion_score"] > 0.5:
            logger.info(
                f"[Security] ⚠️ Suspicious message from user {user_id[:8]}...\n"
                f"Suspicion score: {metadata['suspicion_score']:.2f}\n"
                f"Suspicious phrases: {metadata['suspicious_phrases']}"
            )

        return (True, None, metadata)

    def sanitize_tool_input(
        self,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Sanitize tool inputs to prevent injection via tool arguments.

        Args:
            tool_name: Name of tool being called
            tool_input: Tool input parameters

        Returns:
            (is_safe, block_reason, sanitized_input)
        """
        sanitized = {}

        for key, value in tool_input.items():
            if isinstance(value, str):
                # Check for SQL injection patterns
                if self._has_sql_injection(value):
                    logger.warning(
                        f"[Security] SQL injection attempt in tool '{tool_name}', "
                        f"param '{key}': {value[:100]}"
                    )
                    return (False, "Invalid tool input detected.", {})

                # Remove dangerous characters
                sanitized[key] = self._sanitize_string(value)
            else:
                sanitized[key] = value

        return (True, None, sanitized)

    def validate_ai_output(
        self,
        output: str,
        user_message: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate AI output to prevent prompt leakage or policy violations.

        Args:
            output: AI's response
            user_message: Original user message (for context)

        Returns:
            (is_safe, block_reason)
        """
        output_lower = output.lower()

        # 1. Check for system prompt leakage
        leaked_phrases = [
            'you are an ai fitness coach',
            'your instructions are',
            'i was instructed to',
            'my system prompt',
            'anthropic',
            'claude code'
        ]

        for phrase in leaked_phrases:
            if phrase in output_lower:
                logger.warning(
                    f"[Security] ⚠️ Potential prompt leakage detected\n"
                    f"Output: {output[:200]}..."
                )
                return (False, "Response validation failed. Please try again.")

        # 2. Check for role breaking
        role_breaks = [
            'i am not a fitness coach',
            'i cannot help with fitness',
            'i am actually',
            'pretending to be'
        ]

        for phrase in role_breaks:
            if phrase in output_lower:
                logger.warning(
                    f"[Security] ⚠️ Role breaking detected\n"
                    f"Output: {output[:200]}..."
                )
                return (False, "Response validation failed. Please try again.")

        # Output is safe
        return (True, None)

    def _check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: User UUID

        Returns:
            True if within limit, False if exceeded
        """
        if not self.cache:
            return True  # No cache, no rate limiting

        key = f"security:rate_limit:{user_id}"

        # Get current count
        count = self.cache.get(key) or 0

        if count >= self.RATE_LIMIT_MAX_ATTEMPTS:
            return False

        # Increment count
        self.cache.set(key, count + 1, ttl=self.RATE_LIMIT_WINDOW)

        return True

    def _has_excessive_repetition(self, message: str) -> bool:
        """
        Check if message has excessive character/word repetition.

        Args:
            message: User's message

        Returns:
            True if excessive repetition detected
        """
        # Check for same character repeated 50+ times
        if re.search(r'(.)\1{50,}', message):
            return True

        # Check for same word repeated 20+ times
        words = message.split()
        if len(words) > 0:
            word_counts = {}
            for word in words:
                word_lower = word.lower()
                word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
                if word_counts[word_lower] > 20:
                    return True

        return False

    def _has_unusual_characters(self, message: str) -> bool:
        """
        Check for unusual unicode characters that might be encoding attacks.

        Args:
            message: User's message

        Returns:
            True if unusual characters detected
        """
        # Count non-ASCII characters
        non_ascii_count = sum(1 for char in message if ord(char) > 127)
        non_ascii_ratio = non_ascii_count / len(message) if message else 0

        # Allow up to 30% non-ASCII (for multilingual support)
        # But flag if >50% (potential encoding attack)
        if non_ascii_ratio > 0.5:
            return True

        # Check for zero-width characters (steganography)
        zero_width_chars = ['\u200b', '\u200c', '\u200d', '\ufeff']
        if any(char in message for char in zero_width_chars):
            return True

        return False

    def _has_sql_injection(self, value: str) -> bool:
        """
        Check for SQL injection patterns.

        Args:
            value: Input value to check

        Returns:
            True if SQL injection detected
        """
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
            r"(--|;|/\*|\*/|xp_|sp_)",
            r"('|('')|(\|\|))",
            r"(\bUNION\b.*\bSELECT\b)",
        ]

        value_lower = value.lower()
        for pattern in sql_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True

        return False

    def _sanitize_string(self, value: str) -> str:
        """
        Sanitize string input by removing dangerous characters.

        Args:
            value: Input string

        Returns:
            Sanitized string
        """
        # Remove null bytes
        value = value.replace('\x00', '')

        # Remove control characters (except newlines, tabs)
        value = ''.join(char for char in value if ord(char) >= 32 or char in ['\n', '\t', '\r'])

        # Limit length
        if len(value) > 1000:
            value = value[:1000]

        return value

    def _get_block_message(self, attack_type: str) -> str:
        """
        Get user-friendly block message for attack type.

        Args:
            attack_type: Type of attack detected

        Returns:
            User-friendly error message
        """
        messages = {
            "role_hijacking": "Invalid request. I'm here to help with fitness and nutrition.",
            "role_override": "Invalid request. I'm here to help with fitness and nutrition.",
            "memory_wipe": "Invalid request. I'm here to help with fitness and nutrition.",
            "prompt_extraction": "I can't share my internal instructions. How can I help with your fitness goals?",
            "jailbreak": "Invalid request. I'm here to help with fitness and nutrition.",
            "system_impersonation": "Invalid request format. Please rephrase your message.",
            "instruction_injection": "Invalid request. I'm here to help with fitness and nutrition.",
            "delimiter_attack": "Invalid characters detected. Please use standard text.",
            "encoding_attack": "Invalid encoding detected. Please use plain text.",
            "instruction_override": "Invalid request. I'm here to help with fitness and nutrition.",
        }

        return messages.get(attack_type, "Invalid request. Please try again with a different message.")


# Singleton
_security_service: Optional[SecurityService] = None

def get_security_service(cache_service=None) -> SecurityService:
    """Get singleton SecurityService instance."""
    global _security_service
    if _security_service is None:
        from app.services.cache_service import get_cache_service
        if cache_service is None:
            cache_service = get_cache_service()
        _security_service = SecurityService(cache_service)
    return _security_service
