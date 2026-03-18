"""
Parameter Extraction Module

Extracts structured parameters from natural language commands.
Handles entity recognition, value extraction, and parameter mapping.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class ParameterExtractor:
    """Extracts parameters from natural language commands."""
    
    # File path patterns
    FILE_PATH_PATTERNS = [
        r'(?:file|folder|path)\s+["\']?([A-Za-z]:[\\\/].+?)["\']?(?:\s|$)',  # C:/path/to/file
        r'["\']([A-Za-z]:[\\\/][^"\']+)["\']',  # "C:/path"
        r'(?:file|folder)\s+([A-Za-z]:\\[^\s]+)',  # file C:\path
        r'([A-Za-z]:\\[\w\\\/\.\-]+)',  # C:\path\file.txt
    ]
    
    # Email patterns
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Number patterns
    NUMBER_PATTERN = r'\b(\d+)\b'
    
    # WhatsApp message patterns
    WHATSAPP_PATTERNS = [
        r'send\s+["\'](.+?)["\'](?:\s+to\s+(.+?))?(?:\s+on\s+whatsapp)?',
        r'message\s+(.+?)\s+saying\s+["\'](.+?)["\']',
        r'whatsapp\s+(.+?)\s+["\'](.+?)["\']',
    ]
    
    def __init__(self):
        """Initialize parameter extractor."""
        self.confidence_threshold = 0.7
    
    def extract(self, command: str, tool_name: str) -> Tuple[Dict[str, Any], float]:
        """
        Extract parameters for a specific tool from command.
        
        Args:
            command: Natural language command
            tool_name: Target tool name (e.g., "file.create")
            
        Returns:
            Tuple of (extracted_params, confidence_score)
        """
        command = command.lower().strip()
        
        # Route to specific extractor based on tool category
        if tool_name.startswith("file."):
            return self._extract_file_params(command, tool_name)
        elif tool_name.startswith("folder."):
            return self._extract_folder_params(command, tool_name)
        elif tool_name.startswith("whatsapp"):
            return self._extract_whatsapp_params(command)
        elif tool_name.startswith("email"):
            return self._extract_email_params(command)
        elif tool_name.startswith("system.volume"):
            return self._extract_volume_params(command)
        elif tool_name.startswith("browser"):
            return self._extract_browser_params(command)
        elif tool_name.startswith("app."):
            return self._extract_app_params(command)
        else:
            return {}, 0.5  # Unknown tool, low confidence
    
    def _extract_file_params(self, command: str, tool_name: str) -> Tuple[Dict[str, Any], float]:
        """Extract file operation parameters."""
        params = {}
        confidence = 0.3  # Base confidence
        
        # Extract file path
        path = self._extract_path(command)
        if path:
            params["path"] = path
            confidence += 0.4
        
        # For move/rename operations, extract source and destination
        if tool_name == "file.move" or "move" in command or "rename" in command:
            # Try to extract "from X to Y" pattern
            move_match = re.search(r'(?:from|move)\s+(.+?)\s+(?:to|as)\s+(.+?)(?:\s|$)', command)
            if move_match:
                params["source"] = self._normalize_path(move_match.group(1))
                params["destination"] = self._normalize_path(move_match.group(2))
                confidence = 0.9
            elif path:
                params["source"] = path
                confidence = 0.5  # Missing destination
        
        # For create operations, extract content if provided
        if tool_name == "file.create":
            content_match = re.search(r'(?:with content|containing)\s+["\'](.+?)["\']', command)
            if content_match:
                params["content"] = content_match.group(1)
                confidence += 0.1
        
        return params, min(confidence, 1.0)
    
    def _extract_folder_params(self, command: str, tool_name: str) -> Tuple[Dict[str, Any], float]:
        """Extract folder operation parameters."""
        params = {}
        confidence = 0.3
        
        # Extract folder path
        path = self._extract_path(command)
        if path:
            params["path"] = path
            confidence = 0.8
        else:
            # Try extracting folder name without full path
            folder_match = re.search(r'folder\s+["\']?([A-Za-z0-9_\-\s]+)["\']?', command)
            if folder_match:
                params["path"] = folder_match.group(1).strip()
                confidence = 0.6  # Lower confidence without full path
        
        return params, confidence
    
    def _extract_whatsapp_params(self, command: str) -> Tuple[Dict[str, Any], float]:
        """Extract WhatsApp message parameters."""
        params = {}
        confidence = 0.3

        # Strong natural-language pattern first (works without quotes).
        # Examples:
        # - send testing to vansh on whatsapp
        # - send message testing to vansh
        natural = re.search(
            r'\bsend\s+(.+?)\s+(?:to|for)\s+([A-Za-z0-9@._\-\s]+?)(?:\s+on\s+whats?\s*app|$)',
            command,
            re.IGNORECASE,
        )
        if natural:
            msg = natural.group(1).strip(" .,!?'\"")
            msg = re.sub(r'^(?:message|msg|text)\s+', '', msg, flags=re.IGNORECASE).strip(" .,!?")
            contact = natural.group(2).strip(" .,!?'\"")
            if msg:
                params["message"] = msg
            if contact:
                params["contact"] = contact
            if "message" in params and "contact" in params:
                return params, 0.92
        
        # Try different patterns
        for pattern in self.WHATSAPP_PATTERNS:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    # Pattern: send "message" to "contact"
                    params["message"] = groups[0].strip()
                    params["contact"] = groups[1].strip() if groups[1] else ""
                    confidence = 0.9 if groups[1] else 0.6
                    break
                elif len(groups) == 1:
                    # Only message found
                    params["message"] = groups[0].strip()
                    confidence = 0.5
                    break
        
        # Extract contact name if not found
        if "contact" not in params:
            contact_match = re.search(r'(?:to|message)\s+([A-Za-z\s]+?)(?:\s+on|\s+saying|$)', command)
            if contact_match:
                params["contact"] = contact_match.group(1).strip()
                confidence += 0.2
        
        return params, min(confidence, 1.0)
    
    def _extract_email_params(self, command: str) -> Tuple[Dict[str, Any], float]:
        """Extract email parameters."""
        params = {}
        confidence = 0.3
        
        # Extract recipient email
        email_match = re.search(self.EMAIL_PATTERN, command)
        if email_match:
            params["to"] = email_match.group(0)
            confidence += 0.3
        
        # Extract subject
        subject_match = re.search(r'subject\s+["\'](.+?)["\']', command, re.IGNORECASE)
        if subject_match:
            params["subject"] = subject_match.group(1)
            confidence += 0.2
        
        # Extract body/message
        body_match = re.search(r'(?:body|message)\s+["\'](.+?)["\']', command, re.IGNORECASE)
        if body_match:
            params["body"] = body_match.group(1)
            confidence += 0.2
        
        return params, min(confidence, 1.0)
    
    def _extract_volume_params(self, command: str) -> Tuple[Dict[str, Any], float]:
        """Extract volume control parameters."""
        params = {}
        confidence = 0.8  # High confidence for volume commands
        
        # Extract step amount
        number_match = re.search(self.NUMBER_PATTERN, command)
        if number_match:
            params["step"] = int(number_match.group(1))
            confidence = 0.95
        else:
            # Default step
            params["step"] = 10
            confidence = 0.7
        
        return params, confidence
    
    def _extract_browser_params(self, command: str) -> Tuple[Dict[str, Any], float]:
        """Extract browser parameters."""
        params = {}
        confidence = 0.5
        
        # Extract URL
        url_match = re.search(r'(?:url|link|website)\s+["\']?([a-zA-Z0-9\-\.]+\.[a-z]{2,}[^\s]*)["\']?', command)
        if url_match:
            params["url"] = url_match.group(1)
            confidence = 0.9
        
        # Extract search query
        search_match = re.search(r'(?:search for|google)\s+["\']?(.+?)["\']?(?:\s|$)', command, re.IGNORECASE)
        if search_match:
            params["query"] = search_match.group(1).strip()
            confidence = 0.85
        
        # Extract YouTube query
        youtube_match = re.search(r'(?:youtube|video)\s+["\']?(.+?)["\']?(?:\s|$)', command, re.IGNORECASE)
        if youtube_match:
            params["query"] = youtube_match.group(1).strip()
            confidence = 0.85
        
        return params, min(confidence, 1.0)
    
    def _extract_app_params(self, command: str) -> Tuple[Dict[str, Any], float]:
        """Extract application launch parameters."""
        params = {}
        confidence = 0.5
        
        # Extract app name
        app_match = re.search(r'(?:open|launch|start)\s+([A-Za-z0-9\s]+?)(?:\s|$)', command, re.IGNORECASE)
        if app_match:
            params["app_name"] = app_match.group(1).strip()
            confidence = 0.8
        
        return params, confidence
    
    def _extract_path(self, command: str) -> Optional[str]:
        """Extract file/folder path from command."""
        for pattern in self.FILE_PATH_PATTERNS:
            match = re.search(pattern, command)
            if match:
                return self._normalize_path(match.group(1))
        
        # Try extracting quoted path
        quoted_match = re.search(r'["\']([^"\']+)["\']', command)
        if quoted_match:
            path = quoted_match.group(1)
            if '\\' in path or '/' in path:
                return self._normalize_path(path)
        
        return None
    
    def _normalize_path(self, path: str) -> str:
        """Normalize file path."""
        path = path.strip().strip('"\'')
        # Convert forward slashes to backslashes on Windows
        path = path.replace('/', '\\')
        return path
    
    def get_missing_parameters(self, tool_name: str, extracted_params: Dict[str, Any]) -> List[str]:
        """
        Identify missing required parameters for a tool.
        
        Args:
            tool_name: Tool name
            extracted_params: Already extracted parameters
            
        Returns:
            List of missing parameter names
        """
        required_params = self._get_required_params(tool_name)
        missing = [param for param in required_params if param not in extracted_params]
        return missing
    
    def _get_required_params(self, tool_name: str) -> List[str]:
        """Get required parameters for a tool."""
        requirements = {
            "file.create": ["path"],
            "file.delete": ["path"],
            "file.open": ["path"],
            "file.move": ["source", "destination"],
            "file.search": ["query"],
            "folder.create": ["path"],
            "folder.delete": ["path"],
            "folder.open": ["path"],
            "whatsapp.send": ["message", "contact"],
            "email.send": ["to", "subject", "body"],
            "browser.open": ["url"],
            "browser.search_google": ["query"],
            "browser.search_youtube": ["query"],
            "app.launch": ["app_name"],
            "system.volume.up": [],
            "system.volume.down": [],
            "system.lock": [],
            "system.shutdown": [],
            "system.restart": [],
        }
        
        return requirements.get(tool_name, [])


# Global instance
parameter_extractor = ParameterExtractor()
