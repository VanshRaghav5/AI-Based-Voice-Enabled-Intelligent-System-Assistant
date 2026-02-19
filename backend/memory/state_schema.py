from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class SessionStateSchema:
    active_application: Optional[str] = None
    active_window: Optional[str] = None

    last_file_path: Optional[str] = None
    last_folder_path: Optional[str] = None

    last_contact: Optional[str] = None
    last_url: Optional[str] = None

    last_intent: Optional[str] = None

    execution_history: List[Dict] = field(default_factory=list)
