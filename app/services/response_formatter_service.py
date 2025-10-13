"""
Response Formatter Service - Post-Processing with Llama

Takes Claude's responses and makes them:
1. Shorter (max 4 lines, ~60 words)
2. More human/conversational
3. Mobile-friendly

Uses Groq Llama 3.3 70B for fast, cheap reformatting.
Cost: ~$0.0001 per reformat (negligible)
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class ResponseFormatterService:
    """
    Post-process AI responses to enforce brevity and natural language.

    Uses Groq Llama to intelligently shorten responses while preserving
    key information and making them sound more human.
    """

    def __init__(self, groq_client):
        self.groq = groq_client

    async def format_response(
        self,
        original_response: str,
        user_message: str,
        language: str = 'en'
    ) -> tuple[str, dict]:
        """
        Format AI response to be concise and human-sounding.

        Args:
            original_response: Claude's original response
            user_message: User's original message (for context)
            language: User's language

        Returns:
            (formatted_response, metadata)
        """
        # Quick check: if already short, don't reformat
        word_count = len(original_response.split())
        line_count = len([l for l in original_response.split('\n') if l.strip()])

        if word_count <= 70 and line_count <= 4:
            logger.info(f"[ResponseFormatter] ✅ Already concise ({word_count} words, {line_count} lines)")
            return (original_response, {
                "reformatted": False,
                "original_words": word_count,
                "original_lines": line_count
            })

        logger.info(
            f"[ResponseFormatter] ✂️ Reformatting response "
            f"({word_count} words, {line_count} lines → target: 60 words, 4 lines)"
        )

        try:
            # Build reformatting prompt
            system_prompt = self._build_formatter_prompt(language)

            # Call Groq Llama for reformatting
            response = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"""Original message from user:
{user_message}

Coach's response to reformat:
{original_response}

Reformat this to be concise (max 60 words, 4 lines) and sound like a human texting."""}
                ],
                temperature=0.3,  # Low for consistent formatting
                max_tokens=150
            )

            formatted = response.choices[0].message.content.strip()

            # Remove markdown formatting artifacts if present
            formatted = re.sub(r'^```.*\n', '', formatted)
            formatted = re.sub(r'\n```$', '', formatted)
            formatted = formatted.strip()

            # Count result
            formatted_words = len(formatted.split())
            formatted_lines = len([l for l in formatted.split('\n') if l.strip()])

            logger.info(
                f"[ResponseFormatter] ✅ Reformatted: "
                f"{word_count} → {formatted_words} words, "
                f"{line_count} → {formatted_lines} lines"
            )

            return (formatted, {
                "reformatted": True,
                "original_words": word_count,
                "original_lines": line_count,
                "formatted_words": formatted_words,
                "formatted_lines": formatted_lines,
                "reduction_pct": int((1 - formatted_words / word_count) * 100)
            })

        except Exception as e:
            logger.error(f"[ResponseFormatter] ❌ Reformatting failed: {e}", exc_info=True)
            # On error, return original (safer than nothing)
            return (original_response, {
                "reformatted": False,
                "error": str(e)
            })

    def _build_formatter_prompt(self, language: str) -> str:
        """Build system prompt for Llama formatter."""

        if language == 'pt':
            return """Você é um formatador de mensagens. Sua missão: pegar respostas longas e torná-las CURTAS e NATURAIS.

REGRAS:
- Max 4 linhas
- Max 60 palavras
- Som humano (como mensagem de texto, não ensaio)
- Preservar informações-chave
- Uma sentença = uma linha
- Usar linguagem natural ("você tá" não "você está")

MANTENHA:
- Números importantes (proteína, calorias, etc)
- A ação/próximo passo
- O tom direto

REMOVA:
- Introduções ("Ótima pergunta!")
- Conclusões ("Espero ter ajudado!")
- Explicações longas
- Parágrafos múltiplos

Retorne APENAS a mensagem reformatada, sem explicações."""

        elif language == 'es':
            return """Eres un formateador de mensajes. Tu misión: tomar respuestas largas y hacerlas CORTAS y NATURALES.

REGLAS:
- Max 4 líneas
- Max 60 palabras
- Sonar humano (como mensaje de texto, no ensayo)
- Preservar información clave
- Una oración = una línea
- Usar lenguaje natural ("estás" no "usted está")

MANTENER:
- Números importantes (proteína, calorías, etc)
- La acción/próximo paso
- El tono directo

ELIMINAR:
- Introducciones ("¡Buena pregunta!")
- Conclusiones ("¡Espero que ayude!")
- Explicaciones largas
- Múltiples párrafos

Devuelve SOLO el mensaje reformateado, sin explicaciones."""

        else:  # English
            return """You're a message formatter. Your mission: take long responses and make them SHORT and NATURAL.

RULES:
- Max 4 lines
- Max 60 words
- Sound human (like texting, not an essay)
- Preserve key info
- One sentence = one line
- Use natural language (contractions: "you're" not "you are")

KEEP:
- Important numbers (protein, calories, etc)
- The action/next step
- The direct tone

CUT:
- Intros ("Great question!")
- Outros ("Hope this helps!")
- Long explanations
- Multiple paragraphs
- Fluff

BAD (too long):
"That's an excellent question about protein. Protein requirements vary based on several factors including body weight and activity level. Generally speaking, research indicates that 0.8-1g per pound is optimal. I hope this helps!"

GOOD (concise & human):
"0.8-1g per lb bodyweight.
For you at 180 lbs = 144-180g daily.
Track it for 3 days and tell me if you're hitting it."

Return ONLY the reformatted message, no explanations."""


# Singleton
_formatter_service: Optional[ResponseFormatterService] = None

def get_response_formatter(groq_client=None) -> ResponseFormatterService:
    """Get singleton ResponseFormatterService instance."""
    global _formatter_service
    if _formatter_service is None:
        if groq_client is None:
            from groq import Groq
            import os
            groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        _formatter_service = ResponseFormatterService(groq_client)
    return _formatter_service
