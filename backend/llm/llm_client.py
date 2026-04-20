import subprocess
import json
import os
import re
import shutil
import requests
from urllib.parse import quote_plus
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
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
        self.ollama_api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        
        # Setup HTTP session with connection pooling
        self.session = self._create_session()
        
        self.ollama_available = self._check_ollama()
        self.last_source = None  # Track last plan source: "ollama" or "fallback"
        self.system_prompt = self._load_system_prompt()
    
    def _create_session(self):
        """Create requests session with connection pooling and retries."""
        session = requests.Session()
        
        # Configure retries for robustness
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        
        # Mount adapters for both http and https
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def _check_ollama(self):
        """Check if Ollama API is available and accessible."""
        try:
            # Use a plain request (no retry adapter) so a refused connection fails fast
            response = requests.get(f"{self.ollama_api_url}/api/tags", timeout=2)
            if response.status_code == 200:
                logger.info(f"[LLMClient] Ollama API is available at: {self.ollama_api_url}")
                # Check if our model is available
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                if self.model in model_names or any(self.model in name for name in model_names):
                    logger.info(f"[LLMClient] Model '{self.model}' is available")
                else:
                    logger.warning(f"[LLMClient] Model '{self.model}' not found. Available models: {model_names}")
                return True
        except Exception as e:
            logger.warning(f"[LLMClient] Ollama API not accessible: {e} - will use fallback mode")
        
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
            
            # Try Ollama HTTP API
            logger.info(f"[LLMClient] Calling Ollama API with model: {self.model}")
            
            # Format the complete prompt: system instructions + user command
            full_prompt = f"{self.system_prompt}\n\nUSER COMMAND: {prompt}\n\nJSON RESPONSE:"
            
            # Prepare API request
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower = more deterministic, faster
                    "num_predict": 512,
                    "top_k": 20,  # Limit choices for faster processing
                    "top_p": 0.9  # Nucleus sampling for better quality
                }
            }
            
            # Call Ollama API using session (with connection pooling)
            response = self.session.post(
                f"{self.ollama_api_url}/api/generate",
                json=payload,
                timeout=LLM_TIMEOUT_SECONDS
            )

            if response.status_code != 200:
                logger.warning(f"[LLMClient] API error {response.status_code}, using fallback")
                self.last_source = "fallback"
                return self._create_fallback_plan(prompt)

            result = response.json()
            output = result.get('response', '').strip()
            logger.info(f"[LLM Output] {output}")

            try:
                # Try to parse as JSON
                plan = json.loads(output)
                if self._plan_has_steps(plan):
                    self.last_source = "ollama"
                    return plan
                logger.warning("[LLMClient] Ollama returned plan without executable steps, using fallback")
                self.last_source = "fallback"
                return self._create_fallback_plan(prompt)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', output, re.DOTALL)
                if json_match:
                    try:
                        plan = json.loads(json_match.group(1))
                        if self._plan_has_steps(plan):
                            self.last_source = "ollama"
                            return plan
                        logger.warning("[LLMClient] Extracted JSON plan has no steps, using fallback")
                        self.last_source = "fallback"
                        return self._create_fallback_plan(prompt)
                    except json.JSONDecodeError:
                        pass
                
                logger.warning(f"[LLMClient] Invalid JSON from Ollama, using fallback")
                self.last_source = "fallback"
                return self._create_fallback_plan(prompt)

        except requests.Timeout:
            logger.warning("[LLMClient] Ollama timeout - using fallback")
            self.last_source = "fallback"
            return self._create_fallback_plan(prompt)
        except requests.RequestException as e:
            logger.warning(f"[LLMClient] API request error: {e} - using fallback")
            self.last_source = "fallback"
            return self._create_fallback_plan(prompt)
        except Exception as e:
            logger.warning(f"[LLMClient] Error: {e} - using fallback")
            self.last_source = "fallback"
            return self._create_fallback_plan(prompt)

    def _plan_has_steps(self, plan) -> bool:
        """Return True when a parsed plan contains executable steps."""
        if not isinstance(plan, dict):
            return False
        steps = plan.get("steps")
        if isinstance(steps, list) and len(steps) > 0:
            return True
        tool_calls = plan.get("tool_calls")
        if isinstance(tool_calls, list) and len(tool_calls) > 0:
            return True
        return False

    def _extract_user_command_from_prompt(self, prompt: str) -> str:
        """Extract the real user command from planning/replan prompt wrappers."""
        if not prompt:
            return ""

        # Prefer explicit USER COMMAND field when present.
        command_matches = re.findall(r"USER COMMAND:\s*(.+)", prompt, flags=re.IGNORECASE)
        if command_matches:
            return command_matches[-1].strip()

        # For replan prompt or missing USER COMMAND, try to find the command after the MEMORY CONTEXT block.
        lines = prompt.splitlines()
        extracted_lines = []
        in_memory_block = False
        for line in lines:
            stripped = line.strip()
            if stripped.lower().startswith("memory context"):
                in_memory_block = True
                continue
            
            # Memory facts usually start with a dash
            if in_memory_block and (stripped.startswith("- ") or not stripped):
                continue
            
            if in_memory_block and not stripped.startswith("- "):
                in_memory_block = False
            
            if "REPLAN ITERATION" in stripped:
                break
            
            if stripped:
                extracted_lines.append(stripped)

        if extracted_lines:
            return extracted_lines[0]

        return str(prompt).strip()

    def _normalize_command_text(self, text: str) -> str:
        """Normalize polite/free-form phrasing while preserving task keywords."""
        normalized = str(text or "").lower()

        # Remove common conversational wrappers that hurt strict keyword matching.
        wrapper_patterns = [
            r"\b(can you|could you|would you|will you|please|kindly)\b",
            r"\bfor me\b",
            r"\bhey\s+assistant\b",
            r"\bassistant\b",
            r"\bplz\b",
        ]
        for pattern in wrapper_patterns:
            normalized = re.sub(pattern, " ", normalized)

        # Normalize punctuation and whitespace.
        normalized = re.sub(r"[^a-z0-9:\\/_\-.\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _create_fallback_plan(self, prompt: str):
        """Create a fallback plan based on comprehensive keyword matching.
        
        Args:
            prompt: User input text.
            
        Returns:
            A basic execution plan as a dict with steps, or None if no match.
        """
        effective_prompt = self._extract_user_command_from_prompt(prompt)
        logger.info(f"[LLMClient] Matching keywords in user command: {effective_prompt}")

        prompt_lower = self._normalize_command_text(effective_prompt)
        steps = []

        # Compound browser requests like:
        # "search youtube on chrome and open Mr Beast on youtube"
        # should execute as multi-step plans instead of a single generic action.
        if any(x in prompt_lower for x in ["youtube", "google", "search"]) and any(
            x in prompt_lower for x in ["search", "open", "play", "find"]
        ):
            youtube_query = self._extract_youtube_query(effective_prompt)
            google_query = self._extract_search_query(effective_prompt)
            wants_latest_video = self._wants_latest_video(prompt_lower)

            if "chrome" in prompt_lower:
                steps.append({"name": "app.open", "args": {"app_name": "chrome"}})

            if "youtube" in prompt_lower:
                query = youtube_query or google_query
                if query:
                    query = query.strip()
                    if wants_latest_video:
                        steps.append({"name": "browser.open_youtube_latest_video", "args": {"query": query}})
                    else:
                        search_url = self._build_youtube_search_url(query)
                        steps.append({"name": "browser.open_url", "args": {"url": search_url}})
                elif any(x in prompt_lower for x in ["open", "launch", "start", "go", "play", "run"]):
                    steps.append({"name": "browser.open_youtube", "args": {}})
            elif "search" in prompt_lower and google_query:
                steps.append({"name": "browser.search_google", "args": {"query": google_query}})
        
        # WhatsApp commands
        if not steps and any(x in prompt_lower for x in ["whatsapp", "whats app"]):
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
        elif not steps and any(x in prompt_lower for x in ["email", "e-mail", "send email", "mail"]):
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
        elif not steps and any(x in prompt_lower for x in ["youtube", "you tube"]):
            wants_latest_video = self._wants_latest_video(prompt_lower)
            if any(x in prompt_lower for x in ["open", "launch", "start", "go", "play", "run"]):
                query = self._extract_youtube_query(effective_prompt) or self._extract_search_query(effective_prompt)
                if wants_latest_video and query:
                    steps.append({"name": "browser.open_youtube_latest_video", "args": {"query": query.strip()}})
                else:
                    steps.append({"name": "browser.open_youtube", "args": {}})
            elif "search" in prompt_lower:
                query = self._extract_search_query(effective_prompt)
                if query:
                    steps.append({"name": "browser.open_url", "args": {"url": self._build_youtube_search_url(query)}})
        
        # Browser commands - Google search
        elif not steps and any(x in prompt_lower for x in ["google", "search"]):
            if "google" in prompt_lower or "search" in prompt_lower:
                query = self._extract_search_query(effective_prompt)
                if query:
                    steps.append({"name": "browser.search_google", "args": {"query": query}})
                else:
                    # Just open google
                    steps.append({"name": "browser.open_url", "args": {"url": "https://www.google.com"}})
        
        # Browser commands - Open URL
        elif not steps and any(x in prompt_lower for x in ["http://", "https://", ".com", ".org", ".net"]):
            url = self._extract_url(effective_prompt)
            if url:
                steps.append({"name": "browser.open_url", "args": {"url": url}})
        
        # App launcher - specific apps
        elif not steps and any(x in prompt_lower for x in ["open", "launch", "start", "run"]):
            app_name = self._extract_app_name(effective_prompt)
            if app_name and app_name not in ["file", "folder", "document"]:
                steps.append({"name": "app.open", "args": {"app_name": app_name}})
            # Otherwise fall through to file open commands
            elif any(x in prompt_lower for x in ["file", "document"]):
                path = self._extract_path(effective_prompt) or self._extract_filename(effective_prompt)
                if path:
                    steps.append({"name": "file.open", "args": {"path": path}})
                else:
                    logger.warning("[LLMClient] Open command but no path/file found")
        
        # File open commands (moved to else-if below app launcher)
        
        # File create commands
        elif not steps and any(x in prompt_lower for x in ["create", "make", "new"]):
            if any(x in prompt_lower for x in ["file"]):
                path = self._extract_path(effective_prompt) or self._extract_filename(effective_prompt)
                if not path:
                    path = os.path.expanduser("~\\Desktop\\new_file.txt")
                steps.append({"name": "file.create", "args": {"path": path}})
            elif any(x in prompt_lower for x in ["folder", "directory"]):
                path = self._extract_path(effective_prompt) or self._extract_filename(effective_prompt)
                if not path:
                    path = os.path.expanduser("~\\Desktop\\new_folder")
                steps.append({"name": "folder.create", "args": {"path": path}})
        
        # File delete commands
        elif not steps and any(x in prompt_lower for x in ["delete", "remove", "erase"]):
            if any(x in prompt_lower for x in ["file"]):
                path = self._extract_path(effective_prompt)
                if path:
                    steps.append({"name": "file.delete", "args": {"path": path}})
                else:
                    # Try to create a default path if no path specified
                    steps.append({"name": "file.delete", "args": {"path": ""}})
            elif any(x in prompt_lower for x in ["folder", "directory"]):
                path = self._extract_path(effective_prompt) or self._extract_filename(effective_prompt)
                if path:
                    steps.append({"name": "folder.delete", "args": {"path": path}})
        
        # File move/copy commands
        elif not steps and any(x in prompt_lower for x in ["move", "copy", "rename"]):
            source = self._extract_path(effective_prompt)
            if source:
                steps.append({"name": "file.move", "args": {"source": source, "destination": ""}})
        
        # Brightness commands
        elif not steps and any(x in prompt_lower for x in ["brightness", "bright", "dim", "screen"]):
            if any(x in prompt_lower for x in ["up", "increase", "brighter", "raise"]):
                steps.append({"name": "display.brightness.increase", "args": {}})
            elif any(x in prompt_lower for x in ["down", "decrease", "lower", "dim", "darker"]):
                steps.append({"name": "display.brightness.decrease", "args": {}})
            elif any(x in prompt_lower for x in ["set", "to"]):
                # Extract brightness level from command like "set brightness to 50"
                import re
                match = re.search(r'(\d+)', effective_prompt)
                if match:
                    level = int(match.group(1))
                    steps.append({"name": "display.brightness.set", "args": {"level": level}})
        
        # Clipboard commands
        elif not steps and any(x in prompt_lower for x in ["clipboard", "copy text", "paste"]):
            if any(x in prompt_lower for x in ["clear", "empty"]):
                steps.append({"name": "clipboard.clear", "args": {}})
            elif any(x in prompt_lower for x in ["paste", "get"]):
                steps.append({"name": "clipboard.paste", "args": {}})
            elif any(x in prompt_lower for x in ["copy"]):
                # Try to extract text to copy
                text = self._extract_clipboard_text(effective_prompt)
                if text:
                    steps.append({"name": "clipboard.copy", "args": {"text": text}})
        
        # Window management commands
        elif not steps and any(x in prompt_lower for x in ["window", "minimize", "maximize", "show desktop"]):
            if any(x in prompt_lower for x in ["minimize all", "show desktop", "hide all"]):
                steps.append({"name": "window.minimize_all", "args": {}})
            elif any(x in prompt_lower for x in ["maximize"]):
                steps.append({"name": "window.maximize", "args": {}})
            elif any(x in prompt_lower for x in ["minimize"]) and not "all" in prompt_lower:
                steps.append({"name": "window.minimize", "args": {}})
            elif any(x in prompt_lower for x in ["switch", "change"]):
                title = self._extract_window_title(effective_prompt)
                if title:
                    steps.append({"name": "window.switch", "args": {"window_title": title}})
            elif any(x in prompt_lower for x in ["task view", "all windows"]):
                steps.append({"name": "window.task_view", "args": {}})
        
        # Volume commands - use correct tool names
        elif not steps and any(x in prompt_lower for x in ["volume", "sound", "audio"]):
            if any(x in prompt_lower for x in ["up", "increase", "louder", "raise", "higher"]):
                steps.append({"name": "system.volume.up", "args": {}})
            elif any(x in prompt_lower for x in ["down", "decrease", "quieter", "lower", "softer"]):
                steps.append({"name": "system.volume.down", "args": {}})
            elif "mute" in prompt_lower:
                steps.append({"name": "system.volume.mute", "args": {}})
        
        # System lock - use correct tool name
        elif not steps and any(x in prompt_lower for x in ["lock"]) and not "unlock" in prompt_lower:
            steps.append({"name": "system.lock", "args": {}})
        
        # System shutdown - use correct tool name
        elif not steps and any(x in prompt_lower for x in ["shutdown", "shut down", "power off", "turn off"]):
            steps.append({"name": "system.shutdown", "args": {}})
        
        # System restart - use correct tool name
        elif not steps and any(x in prompt_lower for x in ["restart", "reboot"]):
            steps.append({"name": "system.restart", "args": {}})
        
        # System sleep - use correct tool name
        elif not steps and any(x in prompt_lower for x in ["sleep"]) and any(x in prompt_lower for x in ["system", "computer", "put"]):
            steps.append({"name": "system.sleep", "args": {}})
        
        # System hibernate - use correct tool name
        elif not steps and any(x in prompt_lower for x in ["hibernate"]):
            steps.append({"name": "system.hibernate", "args": {}})
        
        # Screenshot
        elif not steps and any(x in prompt_lower for x in ["screenshot", "screen shot", "capture screen", "take picture"]):
            if any(x in prompt_lower for x in ["region", "area", "selection"]):
                steps.append({"name": "system.screenshot.region", "args": {}})
            else:
                steps.append({"name": "system.screenshot", "args": {}})
        
        # System shortcuts - task manager
        elif not steps and any(x in prompt_lower for x in ["task manager", "taskmgr", "ctrl alt delete"]):
            steps.append({"name": "system.task_manager", "args": {}})
        
        # System shortcuts - file explorer
        elif not steps and any(x in prompt_lower for x in ["file explorer", "windows explorer", "this pc"]) and "open" in prompt_lower:
            steps.append({"name": "system.file_explorer", "args": {}})
        
        # System shortcuts - settings
        elif not steps and any(x in prompt_lower for x in ["windows settings", "pc settings"]) and "open" in prompt_lower:
            steps.append({"name": "system.settings", "args": {}})
        
        # System shortcuts - run dialog
        elif not steps and any(x in prompt_lower for x in ["run dialog", "run command", "win+r", "windows+r"]) and "open" in prompt_lower:
            steps.append({"name": "system.run_dialog", "args": {}})
        
        # System shortcuts - empty recycle bin
        elif not steps and any(x in prompt_lower for x in ["empty recycle", "empty trash", "clear recycle"]):
            steps.append({"name": "system.recycle_bin.empty", "args": {}})
        
        # Turn off monitor (prevent shutdown conflict)
        elif not steps and any(x in prompt_lower for x in ["monitor off", "screen off", "display off", "turn off monitor", "turn off screen"]):
            steps.append({"name": "display.monitor.off", "args": {}})
        
        # File search - must come after other commands to avoid conflicts
        elif not steps and any(x in prompt_lower for x in ["search", "find", "locate"]):
            if any(x in prompt_lower for x in ["file", "files", "for file"]):
                term = self._extract_filename(effective_prompt)
                if term:
                    steps.append({"name": "file.search", "args": {"filename": term}})
        
        # --- CODING: open project in VS Code ---
        elif not steps and any(x in prompt_lower for x in ["open project", "open in vscode",
                                                            "open in vs code", "vscode project"]):
            path = self._extract_path(effective_prompt) or "."
            steps.append({"name": "code.open_project", "args": {"path": path}})

        # --- CODING: detect project type ---
        elif not steps and any(x in prompt_lower for x in ["detect project", "what kind of project",
                                                            "project type"]):
            path = self._extract_path(effective_prompt) or "."
            steps.append({"name": "code.detect_project", "args": {"path": path}})

        # --- CODING: run terminal command ---
        elif not steps and any(x in prompt_lower for x in ["run command", "execute command",
                                                            "terminal run", "run in terminal"]):
            command = self._extract_terminal_command(effective_prompt)
            steps.append({"name": "terminal.run", "args": {"command": command}})

        # --- CODING: start dev server / background process ---
        elif not steps and any(x in prompt_lower for x in ["run project", "start server",
                                                            "start dev", "run dev server"]):
            path = self._extract_path(effective_prompt) or "."
            steps.append({"name": "code.detect_project", "args": {"path": path}})

        # --- CODING: stop/kill background process ---
        elif not steps and any(x in prompt_lower for x in ["stop server", "kill server",
                                                            "stop process", "kill process",
                                                            "stop dev server"]):
            steps.append({"name": "terminal.kill", "args": {}})

        # --- CODING: list running processes ---
        elif not steps and any(x in prompt_lower for x in ["what is running", "list running",
                                                            "show running", "list processes"]):
            steps.append({"name": "terminal.list_running", "args": {}})

        # --- GIT: status ---
        elif not steps and "git" in prompt_lower and any(x in prompt_lower for x in ["status", "changes"]):
            path = self._extract_path(effective_prompt) or "."
            steps.append({"name": "git.status", "args": {"cwd": path}})

        # --- GIT: commit (stages + commits) ---
        elif not steps and "commit" in prompt_lower:
            message = self._extract_commit_message(effective_prompt)
            path = self._extract_path(effective_prompt) or "."
            steps.append({"name": "git.add", "args": {"cwd": path, "files": "."}})
            steps.append({"name": "git.commit", "args": {"cwd": path, "message": message}})

        # --- GIT: push ---
        elif not steps and "git" in prompt_lower and "push" in prompt_lower:
            path = self._extract_path(effective_prompt) or "."
            steps.append({"name": "git.push", "args": {"cwd": path}})

        # --- GIT: pull ---
        elif not steps and "git" in prompt_lower and "pull" in prompt_lower:
            path = self._extract_path(effective_prompt) or "."
            steps.append({"name": "git.pull", "args": {"cwd": path}})

        # --- GIT: log / history ---
        elif not steps and "git" in prompt_lower and any(x in prompt_lower for x in ["log", "history"]):
            path = self._extract_path(effective_prompt) or "."
            steps.append({"name": "git.log", "args": {"cwd": path}})

        # --- TIME & DATE ---
        elif not steps and any(x in prompt_lower for x in ["what time is it", "current time", "tell me the time", "time is it"]):
            steps.append({"name": "system.time", "args": {}})

        elif not steps and any(x in prompt_lower for x in ["what day is it", "current date", "tell me the date", "what is today", "day is today"]):
            steps.append({"name": "system.date", "args": {}})

        if not steps:
            logger.warning(f"[LLMClient] No keyword match for normalized input: {prompt_lower}")
            return None

        # Backward-compatible output shape used by some tests and parser paths.
        for step in steps:
            if isinstance(step, dict):
                if "name" in step and "tool" not in step:
                    step["tool"] = step["name"]
        
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

    def _extract_youtube_query(self, text: str) -> str:
        """Extract target query for YouTube-focused complex commands."""
        if not text:
            return ""

        # Prefer quoted query first.
        quoted = re.search(r'"([^"]+)"', text)
        if quoted:
            return quoted.group(1).strip()

        patterns = [
            r'\band\s+(?:open|play|search(?:\s+for)?)\s+(.+?)\s+on\s+youtube\b',
            r'\b(?:open|play|search(?:\s+for)?)\s+(.+?)\s+on\s+youtube\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip(" .,!?")

        query = self._extract_search_query(text)
        if query:
            query = re.sub(r'\bon\s+chrome\b', '', query, flags=re.IGNORECASE)
            query = re.sub(r'\bon\s+youtube\b', '', query, flags=re.IGNORECASE)
            query = re.sub(r'\band\s+open\b.*$', '', query, flags=re.IGNORECASE)
            query = query.strip(" .,!?")
        return query

    def _build_youtube_search_url(self, query: str) -> str:
        """Build a stable YouTube search URL for a query."""
        cleaned = (query or "").strip()
        if not cleaned:
            return "https://www.youtube.com"
        return f"https://www.youtube.com/results?search_query={quote_plus(cleaned)}"

    def _wants_latest_video(self, normalized_text: str) -> bool:
        """Return True when user explicitly asks for latest/newest/recent video."""
        lowered = str(normalized_text or "").lower()
        return any(term in lowered for term in ["latest", "newest", "recent", "last video", "latest video", "new video"])

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

    def _extract_terminal_command(self, text: str) -> str:
        """Extract terminal command from text.

        Handles patterns like:
          'run command "npm install"'
          'execute npm test'
          'terminal run pip freeze'

        Args:
            text: Input text.

        Returns:
            Extracted command or empty string.
        """
        # 1. Look for quoted command.
        quoted = re.search(r'["\']([^"\']+)["\']', text)
        if quoted:
            return quoted.group(1).strip()

        # 2. Strip known prefixes to isolate the command.
        cleaned = re.sub(
            r'^(?:run|execute|terminal)\s+(?:command|in terminal)?\s*',
            '', text, flags=re.IGNORECASE,
        ).strip()

        return cleaned

    def _extract_commit_message(self, text: str) -> str:
        """Extract git commit message from text.

        Handles patterns like:
          'commit with message fix login bug'
          'git commit -m "added tests"'
          'commit all changes'

        Args:
            text: Input text.

        Returns:
            Commit message or 'update' as default.
        """
        # 1. Look for quoted message.
        quoted = re.search(r'["\']([^"\']+)["\']', text)
        if quoted:
            return quoted.group(1).strip()

        # 2. Look for 'message <text>' or '-m <text>'.
        msg_match = re.search(
            r'(?:message|msg|-m)\s+(.+)',
            text, flags=re.IGNORECASE,
        )
        if msg_match:
            msg = msg_match.group(1).strip().rstrip(".!")
            if msg:
                return msg

        # 3. Strip prefixes and see if there's content left.
        cleaned = re.sub(
            r'^(?:git\s+)?commit\s+(?:all\s+)?(?:changes?\s+)?(?:with\s+)?',
            '', text, flags=re.IGNORECASE,
        ).strip().rstrip(".!")

        if cleaned and len(cleaned) > 2:
            return cleaned

        return "update"
