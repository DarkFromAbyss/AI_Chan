"""System prompt management for the Sensei agent.

Loads and assembles system instructions from markdown files in brain/ directory.
Follows rules.md: prompts treated as code with version control.
"""

import os
from typing import Dict, Optional
from llm_core.utils.logger import get_logger
from llm_core.utils.data_loaders import load_markdown_file

logger = get_logger(__name__)


class SystemPromptManager:
    """Manages system prompts for the Sensei agent.
    
    Loads intro.md, context.md, and rules.md from brain/ directory.
    Assembles complete system prompt with dynamic language settings.
    """
    
    def __init__(self, brain_path: str):
        """Initialize prompt manager and load brain files.
        
        Args:
            brain_path: Path to brain/7B directory
        """
        self.brain_path = brain_path
        self.logger = logger
        
        # Load markdown files
        self.intro_content = load_markdown_file(os.path.join(brain_path, "intro.md"))
        self.context_content = load_markdown_file(os.path.join(brain_path, "context.md"))
        self.rules_content = load_markdown_file(os.path.join(brain_path, "rules.md"))
        
        self.logger.info("System prompts loaded from %s", brain_path)
    
    def get_system_prompt(self, 
                          display_lang: str = "en", 
                          recent_time: str = "") -> str:
        """Assemble complete system prompt with language settings and TTS instructions.
        
        Args:
            display_lang: Output language ("en", "vi", or "ja")
            recent_time: Current time for temporal awareness
        
        Returns:
            Complete system prompt string with dual-track XML output enforcer
        """
        xml_output_enforcer = """[MANDATORY OUTPUT FORMAT - DUAL TRACK XML]

You MUST output responses ONLY using these EXACT FOUR independent XML tags. 
CRITICAL: DO NOT nest tags inside each other. They MUST be top-level siblings.

<html>
  [Detailed academic content with HTML5 tags: <p>, <ul>, <li>, <b>, <i>, <br>, etc.]
  [Use this section for explanations, examples, structured data in {display_lang}]
</html>

<display>
  [Short, conversational text in {display_lang} summarizing the response]
  [NO technical jargon, only natural language]
  [Max 150 characters]
</display>

<voice>
  [Pure Japanese text for TTS synthesis]
  [Use Hiragana/Katakana for difficult Kanji to ensure clarity]
  [Include natural Japanese rhythm and punctuation: 、。！？]
  [This section MUST be natural-sounding Japanese, not robotic]
  [Max 300 characters]
</voice>

<intent>
  [ONLY "other" or "search" - MUST be in English]
  [Use "search" if user is asking for knowledge/information]
  [Use "other" for casual conversation, greetings, etc.]
</intent>

CRITICAL RULES:
1. Always use ALL FOUR tags exactly as formatted above.
2. No markdown, no code blocks, no extra text outside these tags.
3. Tags must be INDEPENDENT (e.g., <voice> must NOT be inside <html>).
4. <voice> MUST be natural, fluent Japanese ONLY (never mix languages).
5. <display> must be in the language specified: {display_lang}.

[SYSTEM SETTINGS]
- Output language for <display>: "{display_lang}"
- Current time for context: {recent_time}
- TTS voice synthesis enabled: YES
- Max reasoning steps: 3
- Safety guardrails: Enabled
"""
        
        system_prompt = f"""
{self.intro_content}

{self.context_content}

{self.rules_content}

{xml_output_enforcer}
"""
        return system_prompt.strip()

    def get_prompt_stats(self) -> Dict[str, int]:
        """Return prompt statistics for monitoring."""
        return {
            "intro_chars": len(self.intro_content),
            "context_chars": len(self.context_content),
            "rules_chars": len(self.rules_content),
            "total_chars": (len(self.intro_content) + 
                          len(self.context_content) + 
                          len(self.rules_content))
        }
