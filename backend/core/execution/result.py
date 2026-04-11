"""Structured result wrapper for execution outcomes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ExecutionResult:
    """Structured result from plan execution."""

    success: bool
    results: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    failed_step: Optional[int] = None

    def __str__(self) -> str:
        status = "✓ SUCCESS" if self.success else "✗ FAILED"
        return f"{status} - Steps executed: {len(self.results)}, Error: {self.error or 'None'}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "results": self.results,
            "error": self.error,
            "failed_step": self.failed_step,
            "step_count": len(self.results)
        }
