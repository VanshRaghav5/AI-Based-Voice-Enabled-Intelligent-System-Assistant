"""
Enhanced Command Parser

Orchestrates the full command processing pipeline:
1. Intent Recognition (with confidence)
2. Parameter Extraction
3. Parameter Validation
4. Execution or Clarification Request
"""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import re
from backend.services.llm_service import LLMClient
from backend.services.llm.parameter_extractor import parameter_extractor
from backend.services.llm.parameter_validator import parameter_validator, ValidationResult
from backend.core.intent.confidence_tracker import confidence_tracker
from backend.core.intent.confidence_config import confidence_config
from backend.utils.logger import logger


@dataclass
class ParsedCommand:
    """Result of command parsing."""
    intent: str  # Tool name
    confidence: float  # 0.0 to 1.0
    parameters: Dict[str, Any]
    validation: ValidationResult
    needs_clarification: bool
    clarification_prompt: Optional[str] = None
    execution_plan: Optional[Dict[str, Any]] = None


class CommandParser:
    """
    Enhanced command parser with multi-stage pipeline.
    
    Pipeline:
    1. Intent Recognition â†’ Get tool name + confidence
    2. Parameter Extraction â†’ Extract entities from command
    3. Parameter Validation â†’ Validate extracted parameters
    4. Decision â†’ Execute or request clarification
    """
    
    # Confidence thresholds
    HIGH_CONFIDENCE = 0.8
    MEDIUM_CONFIDENCE = 0.5
    LOW_CONFIDENCE = 0.3

    # Canonicalize equivalent tool names emitted by different planner paths.
    INTENT_ALIASES = {
        "app.open": "app.launch",
        "browser.open_url": "browser.open",
        "browser.open_youtube": "browser.search_youtube",
    }
    
    def __init__(self):
        """Initialize command parser."""
        self.llm_client = LLMClient()
        self.extractor = parameter_extractor
        self.validator = parameter_validator
    
    def parse(self, command: str) -> ParsedCommand:
        """
        Parse command through full pipeline.
        
        Args:
            command: Natural language command
            
        Returns:
            ParsedCommand with parsing results
        """
        logger.info(f"Parsing command: {command}")
        
        # Stage 1: Intent Recognition with confidence
        intent, confidence, execution_plan = self._recognize_intent(command)
        logger.info(f"Intent: {intent} (confidence: {confidence:.2f})")
        
        # Stage 2: Parameter Extraction
        parameters, extraction_confidence = self.extractor.extract(command, intent)
        if intent == "unknown":
            extraction_confidence = 0.0
        logger.info(f"Extracted parameters: {parameters} (confidence: {extraction_confidence:.2f})")
        
        # Combine confidences (weighted average)
        overall_confidence = (confidence * 0.6) + (extraction_confidence * 0.4)
        logger.info(f"Overall confidence: {overall_confidence:.2f}")
        
        # Stage 3: Parameter Validation
        validation = self.validator.validate(intent, parameters)
        logger.info(f"Validation: {'PASS' if validation.is_valid else 'FAIL'} - {validation.get_message()}")
        
        # Stage 4: Check for missing parameters
        missing_params = self.extractor.get_missing_parameters(intent, parameters)
        
        # Stage 5: Decision - Clarification or Execution
        needs_clarification, clarification_prompt = self._needs_clarification(
            intent, 
            overall_confidence, 
            validation, 
            missing_params,
            command
        )
        
        # Record confidence for tracking and analytics
        source = getattr(self.llm_client, 'last_source', 'unknown')
        confidence_tracker.record(
            command=command,
            intent=intent,
            confidence=overall_confidence,
            source=source,
            executed=not needs_clarification,  # Will be executed if no clarification needed
            needed_clarification=needs_clarification,
            validation_passed=validation.is_valid
        )
        
        # Log confidence classification
        conf_class = confidence_config.classify_confidence(overall_confidence)
        action = confidence_config.get_action(overall_confidence)
        logger.info(
            f"[Confidence System] Level: {conf_class.upper()} | "
            f"Score: {overall_confidence:.3f} | "
            f"Action: {action.upper()}"
        )
        
        return ParsedCommand(
            intent=intent,
            confidence=overall_confidence,
            parameters=parameters,
            validation=validation,
            needs_clarification=needs_clarification,
            clarification_prompt=clarification_prompt,
            execution_plan=execution_plan
        )
    
    def _recognize_intent(self, command: str) -> Tuple[str, float, Optional[Dict]]:
        """
        Recognize intent from command with confidence score.
        
        Returns:
            Tuple of (intent/tool_name, confidence, execution_plan)
        """
        # Get execution plan from LLM
        plan = self.llm_client.generate_plan(command)
        
        if not plan or "steps" not in plan or len(plan["steps"]) == 0:
            return "unknown", 0.0, None
        
        # Extract first tool as primary intent
        first_step = plan["steps"][0]
        intent = first_step.get("tool", "unknown")
        intent = self._canonicalize_intent(intent)
        
        # Calculate confidence based on multiple factors
        confidence = self._calculate_intent_confidence(command, intent, plan)
        
        return intent, confidence, plan

    def _canonicalize_intent(self, intent: str) -> str:
        """Map equivalent planner tool names to canonical parser intents."""
        return self.INTENT_ALIASES.get(intent, intent)
    
    def _calculate_intent_confidence(self, command: str, intent: str, plan: Dict) -> float:
        """
        Calculate confidence score for intent recognition.
        
        Factors:
        - LLM source (Ollama vs fallback)
        - Keyword matches
        - Plan complexity
        - Command clarity
        """
        confidence = 0.5  # Base confidence
        
        # Factor 1: LLM source
        if hasattr(self.llm_client, 'last_source'):
            if self.llm_client.last_source == "ollama":
                confidence += 0.3
            else:
                confidence += 0.1  # Fallback has lower confidence
        
        # Factor 2: Keyword match strength
        keyword_score = self._calculate_keyword_match(command, intent)
        confidence += keyword_score * 0.2
        
        # Factor 3: Command clarity (shorter, clearer commands = higher confidence)
        words = command.split()
        if len(words) <= 5:
            confidence += 0.1
        elif len(words) > 15:
            confidence -= 0.1
        
        # Factor 4: Plan simplicity (single step = higher confidence)
        if len(plan.get("steps", [])) == 1:
            confidence += 0.1
        
        return min(max(confidence, 0.0), 1.0)  # Clamp to [0, 1]
    
    def _calculate_keyword_match(self, command: str, intent: str) -> float:
        """Calculate keyword match score (0.0 to 1.0)."""
        command_lower = command.lower()
        intent = self._canonicalize_intent(intent)

        if intent == "browser.open":
            has_navigation_verb = any(token in command_lower for token in ["open", "visit", "go to", "browse"])
            has_domain_hint = bool(re.search(r"\b[a-z0-9\-]+\.[a-z]{2,}\b", command_lower))
            if has_navigation_verb and has_domain_hint:
                return 1.0
        
        # Define strong keywords for each intent category
        keyword_map = {
            "file.create": ["create file", "new file", "make file", "generate file", "add file"],
            "file.delete": ["delete file", "remove file", "erase file"],
            "file.open": ["open file", "show file", "view file", "read file"],
            "file.move": ["move file", "rename file", "relocate file"],
            "folder.create": ["create folder", "new folder", "make folder", "create directory"],
            "folder.delete": ["delete folder", "remove folder", "delete directory"],
            "folder.open": ["open folder", "show folder", "open directory"],
            "whatsapp.send": ["whatsapp", "send message", "message on whatsapp", "text on whatsapp"],
            "email.send": ["send email", "email to", "mail to", "compose email", "draft email"],
            "browser.search_google": ["search", "google", "look up", "find online", "web search"],
            "browser.search_youtube": ["youtube", "video", "search youtube", "play on youtube"],
            "browser.open": ["open website", "go to", "browse", "open url", "visit"],
            "system.volume.up": ["volume up", "increase volume", "turn up volume", "louder"],
            "system.volume.down": ["volume down", "decrease volume", "turn down volume", "quieter"],
            "system.lock": ["lock", "lock computer", "lock pc", "lock screen"],
            "system.shutdown": ["shutdown", "turn off", "power off"],
            "app.launch": ["open", "launch", "start", "run", "open app", "launch app"],
        }
        
        keywords = keyword_map.get(intent, [])
        
        # Check for exact matches
        for keyword in keywords:
            if keyword in command_lower:
                return 1.0
        
        # Check for partial matches
        intent_words = intent.split('.')
        matches = sum(1 for word in intent_words if word in command_lower)
        return matches / len(intent_words) if intent_words else 0.0
    
    def _needs_clarification(
        self, 
        intent: str, 
        confidence: float, 
        validation: ValidationResult,
        missing_params: List[str],
        original_command: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if clarification is needed.
        
        Uses confidence_config thresholds for decision making.
        
        Returns:
            Tuple of (needs_clarification, clarification_prompt)
        """
        # Case 1: Very low confidence - reject or request clarification
        if confidence_config.should_reject(confidence):
            return True, f"I couldn't understand that command (confidence: {confidence:.2f}). Could you rephrase it?"
        
        # Case 2: Validation errors
        if not validation.is_valid:
            suggestion = self.validator.suggest_fix(intent, {}, validation)
            error_msg = validation.get_message()
            return True, f"{error_msg}. {suggestion}"
        
        # Case 3: Missing required parameters
        if missing_params:
            prompt = self._create_missing_param_prompt(intent, missing_params)
            return True, prompt
        
        # Case 4: Should confirm - ask for confirmation
        if confidence_config.should_confirm(confidence):
            return True, f"I think you want to {self._intent_to_human(intent)}. Is that correct? (confidence: {confidence:.2f})"
        
        # Case 5: High confidence - auto-execute
        if confidence_config.should_auto_execute(confidence):
            logger.info(f"Auto-executing with high confidence: {confidence:.2f}")
            return False, None
        
        # Case 6: Validation warnings only - proceed but warn
        if validation.warnings:
            logger.warning(f"Proceeding with warnings: {validation.get_message()}")
        
        return False, None
    
    def _create_missing_param_prompt(self, intent: str, missing_params: List[str]) -> str:
        """Create user-friendly prompt for missing parameters."""
        param_names = {
            "path": "file or folder path",
            "source": "source file path",
            "destination": "destination file path",
            "message": "message to send",
            "contact": "contact name",
            "to": "recipient email address",
            "subject": "email subject",
            "body": "email message",
            "url": "website URL",
            "query": "search query",
            "app_name": "application name",
        }
        
        human_params = [param_names.get(p, p) for p in missing_params]
        
        if len(human_params) == 1:
            return f"Please provide the {human_params[0]}."
        elif len(human_params) == 2:
            return f"Please provide the {human_params[0]} and {human_params[1]}."
        else:
            return f"Please provide: {', '.join(human_params[:-1])}, and {human_params[-1]}."
    
    def _intent_to_human(self, intent: str) -> str:
        """Convert tool name to human-readable description."""
        descriptions = {
            "file.create": "create a file",
            "file.delete": "delete a file",
            "file.open": "open a file",
            "file.move": "move or rename a file",
            "folder.create": "create a folder",
            "folder.delete": "delete a folder",
            "whatsapp.send": "send a WhatsApp message",
            "email.send": "send an email",
            "browser.search_google": "search on Google",
            "browser.search_youtube": "search on YouTube",
            "system.volume.up": "increase volume",
            "system.volume.down": "decrease volume",
            "system.lock": "lock the computer",
            "app.launch": "launch an application",
        }
        
        return descriptions.get(intent, intent.replace('.', ' ').replace('_', ' '))
    
    def _suggest_intents(self, command: str) -> str:
        """Suggest possible intents based on command keywords."""
        suggestions = []
        command_lower = command.lower()
        
        if "file" in command_lower:
            suggestions.append("work with files")
        if "folder" in command_lower:
            suggestions.append("work with folders")
        if "whatsapp" in command_lower or "message" in command_lower:
            suggestions.append("send a message")
        if "email" in command_lower:
            suggestions.append("send an email")
        if "search" in command_lower:
            suggestions.append("search online")
        if "volume" in command_lower:
            suggestions.append("change volume")
        if "open" in command_lower or "launch" in command_lower:
            suggestions.append("open an application")
        
        if suggestions:
            return " or ".join(suggestions)
        else:
            return "specify what you'd like to do"


# Global instance
command_parser = CommandParser()
