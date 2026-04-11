"""Plan schema for the planner layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Step:
    """Single executable step in a plan."""

    step_id: int
    action: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    """Structured plan produced from an intent."""

    goal: str
    steps: List[Step] = field(default_factory=list)
    requires_confirmation: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)