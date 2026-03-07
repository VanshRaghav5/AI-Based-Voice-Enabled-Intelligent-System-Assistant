# backend/automation/file/delete_history.py

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class DeleteHistoryManager:
    """Manages delete history for undo capability"""
    
    def __init__(self, history_file: str = "backend/data/delete_history.json"):
        self.history_file = history_file
        self._ensure_history_file()
    
    def _ensure_history_file(self):
        """Ensure the history file exists"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)
    
    def add_entry(self, path: str, item_type: str, metadata: Optional[Dict] = None) -> str:
        """
        Add a delete entry to history
        
        Args:
            path: Original path of deleted item
            item_type: 'file' or 'folder'
            metadata: Optional additional metadata
            
        Returns:
            entry_id: Unique identifier for this delete operation
        """
        entry_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(path)}"
        
        entry = {
            "id": entry_id,
            "path": path,
            "type": item_type,
            "timestamp": datetime.now().isoformat(),
            "in_recycle_bin": True,
            "metadata": metadata or {}
        }
        
        history = self._load_history()
        history.append(entry)
        
        # Keep only last 100 entries
        if len(history) > 100:
            history = history[-100:]
        
        self._save_history(history)
        return entry_id
    
    def get_recent_deletes(self, limit: int = 10) -> List[Dict]:
        """Get recent delete operations"""
        history = self._load_history()
        return history[-limit:][::-1]  # Return most recent first
    
    def get_entry(self, entry_id: str) -> Optional[Dict]:
        """Get a specific delete entry"""
        history = self._load_history()
        for entry in history:
            if entry.get("id") == entry_id:
                return entry
        return None
    
    def mark_restored(self, entry_id: str):
        """Mark an entry as restored (no longer in recycle bin)"""
        history = self._load_history()
        for entry in history:
            if entry.get("id") == entry_id:
                entry["in_recycle_bin"] = False
                entry["restored_at"] = datetime.now().isoformat()
                break
        self._save_history(history)
    
    def _load_history(self) -> List[Dict]:
        """Load history from file"""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def _save_history(self, history: List[Dict]):
        """Save history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)


# Global instance
delete_history = DeleteHistoryManager()
