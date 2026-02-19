import subprocess
import json
import os
import re
from backend.config.logger import logger


class LLMClient:

    def __init__(self, model="qwen2.5"):
        """Initialize LLM client with specified model.
        
        Args:
            model: Model name (e.g., 'qwen2.5', 'qwen2.5:7b-instruct-q4_0')
        """
        self.model = model
        self.ollama_available = self._check_ollama()

    def _check_ollama(self):
        """Check if Ollama is available and accessible."""
        try:
            result = subprocess.run(
                'ollama --version',
                capture_output=True,
                timeout=5,
                shell=True
            )
            is_available = result.returncode == 0
            if is_available:
                logger.info("[LLMClient] Ollama is available")
            else:
                logger.warning("[LLMClient] Ollama not accessible - will use fallback mode")
            return is_available
        except Exception as e:
            logger.warning(f"[LLMClient] Ollama check failed: {e}")
            return False

    def generate_plan(self, prompt: str):
        """Generate execution plan from user input using Ollama or fallback.
        
        Args:
            prompt: User input text.
            
        Returns:
            Parsed JSON response with execution plan or None on error.
        """
        try:
            logger.info(f"[LLMClient] Generating plan for: {prompt}")
            
            if not self.ollama_available:
                logger.info("[LLMClient] Using fallback plan generation (keyword matching)")
                return self._create_fallback_plan(prompt)
            
            # Try Ollama
            logger.info(f"[LLMClient] Calling Ollama with model: {self.model}")
            
            cmd = f'ollama run {self.model}'
            logger.debug(f"[LLMClient] Command: {cmd}")
            
            result = subprocess.run(
                cmd,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=120,  # Increased timeout for slower inference
                shell=True
            )

            if result.returncode != 0:
                logger.error(f"[LLMClient] Ollama error: {result.stderr}")
                return self._create_fallback_plan(prompt)

            output = result.stdout.strip()
            logger.info(f"[LLM Output] {output}")

            try:
                return json.loads(output)
            except json.JSONDecodeError:
                logger.warning(f"[LLMClient] Invalid JSON from Ollama, using fallback")
                return self._create_fallback_plan(prompt)

        except subprocess.TimeoutExpired:
            logger.warning("[LLMClient] Ollama timeout - using fallback")
            return self._create_fallback_plan(prompt)
        except Exception as e:
            logger.warning(f"[LLMClient] Error: {e} - using fallback")
            return self._create_fallback_plan(prompt)

    def _create_fallback_plan(self, prompt: str):
        """Create a fallback plan based on comprehensive keyword matching.
        
        Args:
            prompt: User input text.
            
        Returns:
            A basic execution plan as a dict with steps, or None if no match.
        """
        logger.info(f"[LLMClient] Matching keywords in: {prompt}")
        
        prompt_lower = prompt.lower()
        steps = []
        
        # WhatsApp commands
        if any(x in prompt_lower for x in ["whatsapp", "whats app"]):
            if any(x in prompt_lower for x in ["open", "launch", "send"]):
                target = self._extract_contact(prompt)
                message = self._extract_whatsapp_message(prompt)
                steps.append({"name": "whatsapp.send", "args": {"target": target, "message": message}})
        
        # File open commands
        elif any(x in prompt_lower for x in ["open", "view", "read", "show"]):
            if any(x in prompt_lower for x in ["file", "document"]):
                path = self._extract_path(prompt) or self._extract_filename(prompt)
                if path:
                    steps.append({"name": "file.open", "args": {"path": path}})
                else:
                    logger.warning("[LLMClient] Open command but no path/file found")
        
        # File create commands
        elif any(x in prompt_lower for x in ["create", "make", "new"]):
            if any(x in prompt_lower for x in ["file"]):
                path = self._extract_path(prompt) or self._extract_filename(prompt)
                if not path:
                    path = os.path.expanduser("~\\Desktop\\new_file.txt")
                steps.append({"name": "file.create", "args": {"path": path}})
            elif any(x in prompt_lower for x in ["folder", "directory"]):
                path = self._extract_path(prompt) or self._extract_filename(prompt)
                if not path:
                    path = os.path.expanduser("~\\Desktop\\new_folder")
                steps.append({"name": "folder.create", "args": {"path": path}})
        
        # File delete commands
        elif any(x in prompt_lower for x in ["delete", "remove", "erase"]):
            if any(x in prompt_lower for x in ["file"]):
                path = self._extract_path(prompt)
                if path:
                    steps.append({"name": "file.delete", "args": {"path": path}})
                else:
                    # Try to create a default path if no path specified
                    steps.append({"name": "file.delete", "args": {"path": ""}})
            elif any(x in prompt_lower for x in ["folder", "directory"]):
                path = self._extract_path(prompt)
                if path:
                    steps.append({"name": "folder.delete", "args": {"path": path}})
        
        # File move/copy commands
        elif any(x in prompt_lower for x in ["move", "copy", "rename"]):
            source = self._extract_path(prompt)
            if source:
                steps.append({"name": "file.move", "args": {"source": source, "destination": ""}})
        
        # Volume commands - use correct tool names
        elif any(x in prompt_lower for x in ["volume", "sound", "audio"]):
            if any(x in prompt_lower for x in ["up", "increase", "louder", "raise", "higher"]):
                steps.append({"name": "system.volume.up", "args": {}})
            elif any(x in prompt_lower for x in ["down", "decrease", "quieter", "lower", "softer"]):
                steps.append({"name": "system.volume.down", "args": {}})
            elif "mute" in prompt_lower:
                steps.append({"name": "system.volume.mute", "args": {}})
        
        # System lock - use correct tool name
        elif any(x in prompt_lower for x in ["lock"]) and not "unlock" in prompt_lower:
            steps.append({"name": "system.lock", "args": {}})
        
        # System shutdown - use correct tool name
        elif any(x in prompt_lower for x in ["shutdown", "shut down", "power off", "turn off"]):
            steps.append({"name": "system.shutdown", "args": {}})
        
        # System restart - use correct tool name
        elif any(x in prompt_lower for x in ["restart", "reboot"]):
            steps.append({"name": "system.restart", "args": {}})
        
        # File search
        elif any(x in prompt_lower for x in ["search", "find", "locate"]):
            if any(x in prompt_lower for x in ["file", "files"]):
                term = self._extract_filename(prompt)
                if term:
                    steps.append({"name": "file.search", "args": {"filename": term}})
        
        if not steps:
            logger.warning(f"[LLMClient] No keyword match for: {prompt}")
            return None
        
        logger.info(f"[LLMClient] Generated {len(steps)} fallback steps: {steps}")
        return {"steps": steps}

    def _extract_path(self, text: str) -> str:
        """Extract a file path from text (Windows or Unix style).
        
        Args:
            text: Input text.
            
        Returns:
            Extracted path or empty string.
        """
        # Match Windows paths (D:\path\to\file.txt or D:/path/to/file.txt)
        windows_pattern = r'[A-Z]:[\\\/][^\s"<>|]+'
        match = re.search(windows_pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
        return ""

    def _extract_filename(self, text: str) -> str:
        """Extract a filename or name from text.
        
        Args:
            text: Input text.
            
        Returns:
            Extracted filename or empty string.
        """
        # Look for quoted strings first
        quoted = re.search(r'"([^"]+)"', text)
        if quoted:
            return quoted.group(1)
        
        # Look for text after "named", "called", "as", etc
        patterns = [
            r'(?:named|called|as)\s+"?([a-zA-Z0-9_\-\.]+)"?',
            r'(?:file|folder)\s+"?([a-zA-Z0-9_\-\.]+)"?',
            r'"([^"]+)"',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""

    def _extract_contact(self, text: str) -> str:
        """Extract a WhatsApp contact name from text.
        
        Args:
            text: Input text (e.g., 'send whatsapp to swayam').
            
        Returns:
            Contact name or 'default' if not found.
        """
        # Look for text after "to" keyword
        match = re.search(r'(?:to|for|send to)\s+([a-zA-Z0-9_\-]+)', text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Fallback: extract quoted strings
        quoted = re.search(r'"([^"]+)"', text)
        if quoted:
            return quoted.group(1)
        
        # Default fallback
        return "default"

    def _extract_whatsapp_message(self, text: str) -> str:
        """Extract message text from WhatsApp command.
        
        Args:
            text: Input text (e.g., 'send whatsapp to swayam saying hi').
            
        Returns:
            Message text or empty string if not found.
        """
        # Look for text after contact name, optionally skipping 'saying', 'message', 'say', etc.
        match = re.search(r'(?:to|for)\s+([a-zA-Z0-9_\-]+)\s+(?:saying|message|say|with)?\s*(.+)', text, re.IGNORECASE)
        if match:
            msg = match.group(2).strip()
            # Remove leading "saying ", "message ", "say " if still present
            msg = re.sub(r'^(?:saying|message|say|with)\s+', '', msg, flags=re.IGNORECASE).strip()
            return msg
        
        # Look for quoted message
        quoted = re.search(r'"([^"]+)"', text)
        if quoted:
            return quoted.group(1)
        
        # No message found
        return ""
