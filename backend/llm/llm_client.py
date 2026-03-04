import subprocess
import json
import os
import re
import shutil
from backend.config.logger import logger
from backend.config.settings import LLM_MODEL, LLM_TIMEOUT_SECONDS


class LLMClient:

    def __init__(self, model=None):
        """Initialize LLM client with specified model.
        
        Args:
            model: Model name. If None, uses OLLAMA_MODEL env var or default qwen2.5:7b-instruct-q4_0.
        """
        default_model = os.getenv("OLLAMA_MODEL", LLM_MODEL)
        self.model = model or default_model
        self.ollama_bin = None
        self.ollama_available = self._check_ollama()
        self.last_source = None  # Track last plan source: "ollama" or "fallback"
        self.system_prompt = self._load_system_prompt()

    def _get_ollama_candidates(self):
        """Return possible Ollama executable paths in priority order."""
        candidates = []

        env_bin = os.getenv("OLLAMA_BIN")
        if env_bin:
            candidates.append(env_bin)

        # PATH-discovered binary
        path_bin = shutil.which("ollama")
        if path_bin:
            candidates.append(path_bin)

        # Common Windows install location
        candidates.append(os.path.expanduser(r"~\AppData\Local\Programs\Ollama\ollama.exe"))

        # Keep order and remove duplicates
        seen = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate and candidate not in seen:
                unique_candidates.append(candidate)
                seen.add(candidate)

        return unique_candidates

    def _check_ollama(self):
        """Check if Ollama is available and accessible."""
        for candidate in self._get_ollama_candidates():
            try:
                result = subprocess.run(
                    [candidate, "--version"],
                    capture_output=True,
                    timeout=5,
                    shell=False,
                    encoding='utf-8',
                    errors='replace'
                )
                if result.returncode == 0:
                    self.ollama_bin = candidate
                    logger.info(f"[LLMClient] Ollama is available at: {candidate}")
                    return True
            except Exception:
                continue

        logger.warning("[LLMClient] Ollama not accessible - will use fallback mode")
        return False

    def _load_system_prompt(self):
        """Load the system prompt template from prompt.txt.
        
        Returns:
            The system prompt template string or a basic fallback.
        """
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt = f.read().strip()
                logger.info("[LLMClient] Loaded system prompt from prompt.txt")
                return prompt
            else:
                logger.warning(f"[LLMClient] prompt.txt not found at {prompt_path}")
        except Exception as e:
            logger.warning(f"[LLMClient] Failed to load prompt.txt: {e}")
        
        # Minimal fallback prompt
        return "You are an automation assistant. Return only valid JSON with 'steps' array containing tool calls."

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
                self.last_source = "fallback"
                return self._create_fallback_plan(prompt)
            
            # Try Ollama
            logger.info(f"[LLMClient] Calling Ollama with model: {self.model}")
            
            # Format the complete prompt: system instructions + user command
            full_prompt = f"{self.system_prompt}\n\nUSER COMMAND: {prompt}\n\nJSON RESPONSE:"
            
            cmd = [self.ollama_bin, "run", self.model]
            logger.debug(f"[LLMClient] Command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                input=full_prompt,
                text=True,
                capture_output=True,
                timeout=LLM_TIMEOUT_SECONDS,
                shell=False,
                encoding='utf-8',
                errors='replace'  # Replace undecodable bytes with replacement character
            )

            if result.returncode != 0:
                self.last_source = "fallback"
                return self._create_fallback_plan(prompt)

            output = result.stdout.strip()
            logger.info(f"[LLM Output] {output}")

            try:
                plan = json.loads(output)
                self.last_source = "ollama"
                return plan
            except json.JSONDecodeError:
                logger.warning(f"[LLMClient] Invalid JSON from Ollama, using fallback")
                self.last_source = "fallback"
                return self._create_fallback_plan(prompt)

        except subprocess.TimeoutExpired:
            logger.warning("[LLMClient] Ollama timeout - using fallback")
            self.last_source = "fallback"
            return self._create_fallback_plan(prompt)
        except Exception as e:
            logger.warning(f"[LLMClient] Error: {e} - using fallback")
            self.last_source = "fallback"
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
            # Prefer explicit send -> use registered send tool
            if "send" in prompt_lower:
                target = self._extract_contact(prompt)
                message = self._extract_whatsapp_message(prompt)
                steps.append({"name": "whatsapp.send", "args": {"target": target, "message": message}})
            # If user asked to open/launch WhatsApp (without send), map to open tool
            elif any(x in prompt_lower for x in ["open", "launch"]):
                # If they asked to open a chat with a specific contact, open that chat
                target = self._extract_contact(prompt)
                if target and target != "default":
                    steps.append({"name": "whatsapp.open_chat", "args": {"target": target}})
                else:
                    steps.append({"name": "whatsapp.open", "args": {}})

        # Email commands
        elif any(x in prompt_lower for x in ["email", "e-mail", "send email", "mail"]):
            # Only trigger send when explicit 'send' is present; otherwise request agent
            if "send" in prompt_lower or "email" in prompt_lower and any(k in prompt_lower for k in ["to", "subject", "body", "message"]):
                recipient = self._extract_email_recipient(prompt)
                subject = self._extract_email_subject(prompt)
                body = self._extract_email_body(prompt)
                steps.append({"name": "email.send", "args": {"recipient": recipient, "subject": subject, "body": body}})
            else:
                # If user only said 'open email' or similar, skip
                logger.warning("[LLMClient] Email detected but no send intent found")
        
        # Browser commands - YouTube  
        elif any(x in prompt_lower for x in ["youtube", "you tube"]):
            if any(x in prompt_lower for x in ["open", "launch", "start", "go", "play"]):
                steps.append({"name": "browser.open_youtube", "args": {}})
            elif "search" in prompt_lower:
                query = self._extract_search_query(prompt)
                steps.append({"name": "browser.search_google", "args": {"query": f"youtube {query}"}})
        
        # Browser commands - Google search
        elif any(x in prompt_lower for x in ["google", "search"]):
            if "google" in prompt_lower or "search" in prompt_lower:
                query = self._extract_search_query(prompt)
                if query:
                    steps.append({"name": "browser.search_google", "args": {"query": query}})
                else:
                    # Just open google
                    steps.append({"name": "browser.open_url", "args": {"url": "https://www.google.com"}})
        
        # Browser commands - Open URL
        elif any(x in prompt_lower for x in ["http://", "https://", ".com", ".org", ".net"]):
            url = self._extract_url(prompt)
            if url:
                steps.append({"name": "browser.open_url", "args": {"url": url}})
        
        # App launcher - specific apps
        elif any(x in prompt_lower for x in ["open", "launch", "start"]):
            app_name = self._extract_app_name(prompt)
            if app_name and app_name not in ["file", "folder", "document"]:
                steps.append({"name": "app.open", "args": {"app_name": app_name}})
            # Otherwise fall through to file open commands
            elif any(x in prompt_lower for x in ["file", "document"]):
                path = self._extract_path(prompt) or self._extract_filename(prompt)
                if path:
                    steps.append({"name": "file.open", "args": {"path": path}})
                else:
                    logger.warning("[LLMClient] Open command but no path/file found")
        
        # File open commands (moved to else-if below app launcher)
        
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
                path = self._extract_path(prompt) or self._extract_filename(prompt)
                if path:
                    steps.append({"name": "folder.delete", "args": {"path": path}})
        
        # File move/copy commands
        elif any(x in prompt_lower for x in ["move", "copy", "rename"]):
            source = self._extract_path(prompt)
            if source:
                steps.append({"name": "file.move", "args": {"source": source, "destination": ""}})
        
        # Brightness commands
        elif any(x in prompt_lower for x in ["brightness", "bright", "dim", "screen"]):
            if any(x in prompt_lower for x in ["up", "increase", "brighter", "raise"]):
                steps.append({"name": "display.brightness.increase", "args": {}})
            elif any(x in prompt_lower for x in ["down", "decrease", "lower", "dim", "darker"]):
                steps.append({"name": "display.brightness.decrease", "args": {}})
            elif any(x in prompt_lower for x in ["set", "to"]):
                # Extract brightness level from command like "set brightness to 50"
                import re
                match = re.search(r'(\d+)', prompt)
                if match:
                    level = int(match.group(1))
                    steps.append({"name": "display.brightness.set", "args": {"level": level}})
        
        # Clipboard commands
        elif any(x in prompt_lower for x in ["clipboard", "copy text", "paste"]):
            if any(x in prompt_lower for x in ["clear", "empty"]):
                steps.append({"name": "clipboard.clear", "args": {}})
            elif any(x in prompt_lower for x in ["paste", "get"]):
                steps.append({"name": "clipboard.paste", "args": {}})
            elif any(x in prompt_lower for x in ["copy"]):
                # Try to extract text to copy
                text = self._extract_clipboard_text(prompt)
                if text:
                    steps.append({"name": "clipboard.copy", "args": {"text": text}})
        
        # Window management commands
        elif any(x in prompt_lower for x in ["window", "minimize", "maximize", "show desktop"]):
            if any(x in prompt_lower for x in ["minimize all", "show desktop", "hide all"]):
                steps.append({"name": "window.minimize_all", "args": {}})
            elif any(x in prompt_lower for x in ["maximize"]):
                steps.append({"name": "window.maximize", "args": {}})
            elif any(x in prompt_lower for x in ["minimize"]) and not "all" in prompt_lower:
                steps.append({"name": "window.minimize", "args": {}})
            elif any(x in prompt_lower for x in ["switch", "change"]):
                title = self._extract_window_title(prompt)
                if title:
                    steps.append({"name": "window.switch", "args": {"window_title": title}})
            elif any(x in prompt_lower for x in ["task view", "all windows"]):
                steps.append({"name": "window.task_view", "args": {}})
        
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
        
        # System sleep - use correct tool name
        elif any(x in prompt_lower for x in ["sleep"]) and any(x in prompt_lower for x in ["system", "computer", "put"]):
            steps.append({"name": "system.sleep", "args": {}})
        
        # System hibernate - use correct tool name
        elif any(x in prompt_lower for x in ["hibernate"]):
            steps.append({"name": "system.hibernate", "args": {}})
        
        # Screenshot
        elif any(x in prompt_lower for x in ["screenshot", "screen shot", "capture screen", "take picture"]):
            if any(x in prompt_lower for x in ["region", "area", "selection"]):
                steps.append({"name": "system.screenshot.region", "args": {}})
            else:
                steps.append({"name": "system.screenshot", "args": {}})
        
        # System shortcuts - task manager
        elif any(x in prompt_lower for x in ["task manager", "taskmgr", "ctrl alt delete"]):
            steps.append({"name": "system.task_manager", "args": {}})
        
        # System shortcuts - file explorer
        elif any(x in prompt_lower for x in ["file explorer", "windows explorer", "this pc"]) and "open" in prompt_lower:
            steps.append({"name": "system.file_explorer", "args": {}})
        
        # System shortcuts - settings
        elif any(x in prompt_lower for x in ["windows settings", "pc settings"]) and "open" in prompt_lower:
            steps.append({"name": "system.settings", "args": {}})
        
        # System shortcuts - run dialog
        elif any(x in prompt_lower for x in ["run dialog", "run command", "win+r", "windows+r"]) and "open" in prompt_lower:
            steps.append({"name": "system.run_dialog", "args": {}})
        
        # System shortcuts - empty recycle bin
        elif any(x in prompt_lower for x in ["empty recycle", "empty trash", "clear recycle"]):
            steps.append({"name": "system.recycle_bin.empty", "args": {}})
        
        # Turn off monitor (prevent shutdown conflict)
        elif any(x in prompt_lower for x in ["monitor off", "screen off", "display off", "turn off monitor", "turn off screen"]):
            steps.append({"name": "display.monitor.off", "args": {}})
        
        # File search - must come after other commands to avoid conflicts
        elif any(x in prompt_lower for x in ["search", "find", "locate"]):
            if any(x in prompt_lower for x in ["file", "files", "for file"]):
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

    def _extract_email_recipient(self, text: str) -> str:
        """Extract recipient email or name after 'to'"""
        # Try to find an email address
        email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', text)
        if email_match:
            return email_match.group(1)

        # Look for 'to <name>' patterns
        match = re.search(r'(?:to|send to|email to)\s+"?([a-zA-Z0-9_\- ]+)"?', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return ""

    def _extract_email_subject(self, text: str) -> str:
        """Extract subject from phrases like 'subject', 'about', or quoted subject."""
        # Look for subject: ...
        match = re.search(r'subject\s+(?:is|:)?\s*"?([^\"]+)"?', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Look for 'about <text>' after recipient
        match = re.search(r'about\s+([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return ""

    def _extract_email_body(self, text: str) -> str:
        """Extract the email body from phrases like 'saying', 'message', or quoted text."""
        match = re.search(r'(?:saying|message|body|with message)\s+"?([^\"]+)"?', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Fallback: quoted text
        quoted = re.search(r'"([^"]+)"', text)
        if quoted:
            return quoted.group(1)

        return ""

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

    def _extract_search_query(self, text: str) -> str:
        """Extract search query from commands like 'search for python tutorials'.
        
        Args:
            text: Input text.
            
        Returns:
            Search query or empty string.
        """
        # Remove common command words to isolate the query
        patterns = [
            r'(?:search|google|find|look)\s+(?:for|up)?\s*(?:on)?\s*(?:google|youtube)?\s*(.+)',
            r'(?:open|go to)\s+(?:google|youtube)\s+(?:and\s+)?(?:search\s+)?(?:for)?\s*(.+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                query = match.group(1).strip()
                # Clean up any trailing words like "on google", "on youtube"
                query = re.sub(r'\s+on\s+(google|youtube)$', '', query, flags=re.IGNORECASE)
                return query
        
        # Fallback: quoted text
        quoted = re.search(r'"([^"]+)"', text)
        if quoted:
            return quoted.group(1)
        
        return ""

    def _extract_url(self, text: str) -> str:
        """Extract URL from text.
        
        Args:
            text: Input text.
            
        Returns:
            URL or empty string.
        """
        # Match http:// https:// or www. URLs
        url_pattern = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.(com|org|net|edu|gov|io)[^\s]*)'
        match = re.search(url_pattern, text, re.IGNORECASE)
        if match:
            url = match.group(1)
            # Add https:// if not present
            if not url.startswith('http'):
                url = 'https://' + url
            return url
        return ""

    def _extract_app_name(self, text: str) -> str:
        """Extract application name from commands like 'open chrome' or 'launch notepad'.
        
        Args:
            text: Input text.
            
        Returns:
            Application name or empty string.
        """
        # Remove command words to isolate app name
        cleaned = re.sub(r'^(?:open|launch|start|run)\s+', '', text, flags=re.IGNORECASE).strip()
        
        # Common app names/keywords
        app_keywords = {
            'chrome': 'chrome',
            'google chrome': 'chrome',
            'firefox': 'firefox',
            'edge': 'msedge',
            'microsoft edge': 'msedge',
            'notepad': 'notepad',
            'calculator': 'calc',
            'calc': 'calc',
            'word': 'winword',
            'excel': 'excel',
            'powerpoint': 'powerpnt',
            'outlook': 'outlook',
            'explorer': 'explorer',
            'file explorer': 'explorer',
            'task manager': 'taskmgr',
            'paint': 'mspaint',
            'cmd': 'cmd',
            'command prompt': 'cmd',
            'powershell': 'powershell',
            'vscode': 'code',
            'visual studio code': 'code',
            'spotify': 'spotify',
            'discord': 'discord',
            'slack': 'slack',
            'teams': 'teams',
            'zoom': 'zoom',
        }
        
        # Check for known apps
        for keyword, app_name in app_keywords.items():
            if keyword in cleaned.lower():
                return app_name
        
        # If no match, return the cleaned text (first word only)
        words = cleaned.split()
        if words and words[0] not in ['file', 'folder', 'document', 'the', 'a', 'an']:
            return words[0].lower()
        
        return ""

    def _extract_clipboard_text(self, text: str) -> str:
        """Extract text to copy to clipboard.
        
        Args:
            text: Input text (e.g., 'copy hello world to clipboard').
            
        Returns:
            Text to copy or empty string.
        """
        # Look for text after 'copy' keyword
        match = re.search(r'copy\s+(?:text\s+)?(.+?)\s+(?:to\s+)?(?:clipboard|clip)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Look for quoted text
        quoted = re.search(r'"([^"]+)"', text)
        if quoted:
            return quoted.group(1)
        
        return ""

    def _extract_window_title(self, text: str) -> str:
        """Extract window title from switch command.
        
        Args:
            text: Input text (e.g., 'switch to chrome').
            
        Returns:
            Window title or empty string.
        """
        # Look for text after 'to' or 'switch' keyword
        match = re.search(r'(?:switch|change)\s+(?:to|window)?\s+(.+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Look for quoted text
        quoted = re.search(r'"([^"]+)"', text)
        if quoted:
            return quoted.group(1)
        
        return ""
