"""XML output formatter and validator for LLM responses.

Handles formatting validation and ensures LLM output conforms to dual-track standard.
Provides comprehensive error handling and logging per rules.md requirements.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from llm_core.utils.logger import get_logger
from llm_core.utils.tag_extractor import TagExtractor, ExtractedTags

logger = get_logger(__name__)


@dataclass
class FormattedResponse:
    """Standardized formatted response from LLM output."""
    
    success: bool
    display_text: str
    html_content: str
    voice_text: str
    intent_classification: str
    raw_output: str
    metadata: Dict[str, Any]
    error_details: Optional[str] = None


class OutputFormatter:
    """Formats and validates LLM output into standardized response structure.
    
    Enforces dual-track XML output: <html>, <display>, <voice>, <intent>.
    """

    @staticmethod
    def format_response(llm_output: str) -> FormattedResponse:
        """Format and validate LLM output.
        
        Args:
            llm_output: Raw LLM response text
        
        Returns:
            FormattedResponse with validated components
        """
        logger.debug("Formatting LLM output: %d chars", len(llm_output or ""))

        if not llm_output:
            logger.warning("Empty LLM output received")
            return OutputFormatter._create_error_response(
                llm_output, "Empty output"
            )

        # Extract XML tags
        extracted: ExtractedTags = TagExtractor.extract_tags(llm_output)

        if not extracted.extraction_success:
            logger.warning(
                "Tag extraction failed: %s", 
                extracted.error_message
            )
            return OutputFormatter._create_error_response(
                llm_output, extracted.error_message
            )

        # Sanitize voice text for TTS
        voice_text = TagExtractor.sanitize_voice_text(extracted.voice)

        # Build metadata
        metadata = {
            "extraction_success": extracted.extraction_success,
            "intent_classified_as": extracted.intent,
            "voice_text_length": len(voice_text),
            "display_text_length": len(extracted.display),
            "html_content_length": len(extracted.html),
        }

        logger.info(
            "Response formatted successfully | Intent: %s | Voice: %d chars",
            extracted.intent,
            len(voice_text)
        )

        return FormattedResponse(
            success=True,
            display_text=extracted.display,
            html_content=extracted.html,
            voice_text=voice_text,
            intent_classification=extracted.intent,
            raw_output=llm_output,
            metadata=metadata,
            error_details=None
        )

    @staticmethod
    def validate_xml_tags(text: str) -> tuple[bool, str]:
        """Validate XML tag structure in text.
        
        Args:
            text: Text to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_tags = ['html', 'display', 'voice', 'intent']
        
        is_valid = True
        error_msgs = []

        for tag in required_tags:
            if f'<{tag}>' not in text or f'</{tag}>' not in text:
                is_valid = False
                error_msgs.append(f"Missing tag: <{tag}>")

        if is_valid:
            logger.debug("XML structure validation passed")
            return True, ""
        else:
            error_message = " | ".join(error_msgs)
            logger.warning("XML validation failed: %s", error_message)
            return False, error_message

    @staticmethod
    def get_response_summary(response: FormattedResponse) -> Dict[str, Any]:
        """Generate a summary of the formatted response for logging.
        
        Args:
            response: FormattedResponse to summarize
        
        Returns:
            Dictionary with key metrics
        """
        return {
            "success": response.success,
            "intent": response.intent_classification,
            "display_preview": response.display_text[:50] + "...",
            "voice_chars": len(response.voice_text),
            "has_html": len(response.html_content) > 0,
            "error": response.error_details,
        }

    @staticmethod
    def _create_error_response(
        raw_output: str, 
        error_msg: str
    ) -> FormattedResponse:
        """Create an error response with fallback values.
        
        Args:
            raw_output: Original LLM output
            error_msg: Error message
        
        Returns:
            FormattedResponse with error flag set
        """
        logger.error("Creating error response: %s", error_msg)
        
        return FormattedResponse(
            success=False,
            display_text="申し訳ありません。システムエラーが発生しました。",
            html_content="<p>System error occurred. Please try again.</p>",
            voice_text="エラーが発生しました。",
            intent_classification="other",
            raw_output=raw_output,
            metadata={"error": True, "error_reason": error_msg},
            error_details=error_msg
        )
