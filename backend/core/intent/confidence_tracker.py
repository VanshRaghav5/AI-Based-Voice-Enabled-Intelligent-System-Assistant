"""
Confidence Tracking System

Tracks and analyzes intent recognition confidence scores
for monitoring system intelligence and improving accuracy.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
from backend.utils.logger import logger


@dataclass
class ConfidenceEntry:
    """Single confidence score entry."""
    timestamp: str
    command: str
    intent: str
    confidence: float
    source: str  # "ollama" or "fallback"
    executed: bool
    needed_clarification: bool
    validation_passed: bool


class ConfidenceTracker:
    """
    Tracks confidence scores and provides analytics.
    
    Features:
    - Records all confidence scores
    - Calculates statistics (avg, min, max)
    - Identifies low-confidence commands
    - Tracks confidence trends
    - Exports confidence data
    """
    
    def __init__(self, history_file: str = None):
        """
        Initialize confidence tracker.
        
        Args:
            history_file: Path to confidence history JSON file
        """
        if history_file is None:
            history_file = os.path.join(
                os.path.dirname(__file__), 
                "..", "..", 
                "data", 
                "confidence_history.json"
            )
        
        self.history_file = os.path.abspath(history_file)
        self.history: List[ConfidenceEntry] = []
        self.max_history_size = 1000  # Keep last 1000 entries
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        
        # Load existing history
        self._load_history()
    
    def record(
        self,
        command: str,
        intent: str,
        confidence: float,
        source: str,
        executed: bool = False,
        needed_clarification: bool = False,
        validation_passed: bool = True
    ) -> None:
        """
        Record a confidence score.
        
        Args:
            command: Original command text
            intent: Detected intent/tool name
            confidence: Confidence score (0.0 to 1.0)
            source: Source of intent ("ollama" or "fallback")
            executed: Whether command was executed
            needed_clarification: Whether clarification was needed
            validation_passed: Whether validation passed
        """
        entry = ConfidenceEntry(
            timestamp=datetime.now().isoformat(),
            command=command,
            intent=intent,
            confidence=round(confidence, 3),
            source=source,
            executed=executed,
            needed_clarification=needed_clarification,
            validation_passed=validation_passed
        )
        
        self.history.append(entry)
        
        # Log the entry
        logger.info(
            f"[Confidence] {confidence:.3f} | {intent} | "
            f"Source: {source} | Executed: {executed} | "
            f"Clarification: {needed_clarification}"
        )
        
        # Limit history size
        if len(self.history) > self.max_history_size:
            self.history = self.history[-self.max_history_size:]
        
        # Save to disk
        self._save_history()
    
    def get_statistics(self, last_n: Optional[int] = None) -> Dict[str, Any]:
        """
        Get confidence statistics.
        
        Args:
            last_n: Only analyze last N entries (None = all)
            
        Returns:
            Dictionary with statistics
        """
        entries = self.history[-last_n:] if last_n else self.history
        
        if not entries:
            return {
                "total_commands": 0,
                "avg_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0,
            }
        
        confidences = [e.confidence for e in entries]
        
        # Calculate by source
        ollama_confidences = [e.confidence for e in entries if e.source == "ollama"]
        fallback_confidences = [e.confidence for e in entries if e.source == "fallback"]
        
        # Calculate by execution status
        executed = [e for e in entries if e.executed]
        clarified = [e for e in entries if e.needed_clarification]
        
        stats = {
            "total_commands": len(entries),
            "avg_confidence": round(sum(confidences) / len(confidences), 3),
            "min_confidence": round(min(confidences), 3),
            "max_confidence": round(max(confidences), 3),
            "median_confidence": round(sorted(confidences)[len(confidences)//2], 3),
            
            # Source breakdown
            "ollama_count": len(ollama_confidences),
            "ollama_avg_confidence": round(sum(ollama_confidences) / len(ollama_confidences), 3) if ollama_confidences else 0.0,
            "fallback_count": len(fallback_confidences),
            "fallback_avg_confidence": round(sum(fallback_confidences) / len(fallback_confidences), 3) if fallback_confidences else 0.0,
            
            # Execution status
            "executed_count": len(executed),
            "executed_percentage": round(len(executed) / len(entries) * 100, 1),
            "clarification_count": len(clarified),
            "clarification_percentage": round(len(clarified) / len(entries) * 100, 1),
            
            # Confidence distribution
            "high_confidence_count": sum(1 for c in confidences if c >= 0.8),
            "medium_confidence_count": sum(1 for c in confidences if 0.5 <= c < 0.8),
            "low_confidence_count": sum(1 for c in confidences if c < 0.5),
        }
        
        return stats
    
    def get_low_confidence_commands(self, threshold: float = 0.5) -> List[ConfidenceEntry]:
        """
        Get commands with confidence below threshold.
        
        Args:
            threshold: Confidence threshold
            
        Returns:
            List of low-confidence entries
        """
        return [e for e in self.history if e.confidence < threshold]
    
    def get_intent_confidence_map(self) -> Dict[str, Dict[str, float]]:
        """
        Get average confidence per intent.
        
        Returns:
            Dictionary mapping intent -> {avg, min, max, count}
        """
        intent_confidences = defaultdict(list)
        
        for entry in self.history:
            intent_confidences[entry.intent].append(entry.confidence)
        
        result = {}
        for intent, confidences in intent_confidences.items():
            result[intent] = {
                "avg": round(sum(confidences) / len(confidences), 3),
                "min": round(min(confidences), 3),
                "max": round(max(confidences), 3),
                "count": len(confidences)
            }
        
        return result
    
    def get_recent_entries(self, n: int = 10) -> List[ConfidenceEntry]:
        """Get N most recent entries."""
        return self.history[-n:]
    
    def export_to_json(self, filepath: str) -> None:
        """Export history to JSON file."""
        with open(filepath, 'w') as f:
            json.dump([asdict(e) for e in self.history], f, indent=2)
        
        logger.info(f"Exported {len(self.history)} confidence entries to {filepath}")
    
    def get_trend_analysis(self, window_size: int = 50) -> Dict[str, Any]:
        """
        Analyze confidence trends over time.
        
        Args:
            window_size: Size of sliding window for trend calculation
            
        Returns:
            Trend analysis data
        """
        if len(self.history) < window_size:
            return {"trend": "insufficient_data", "windows": 0}
        
        # Calculate average confidence in sliding windows
        windows = []
        for i in range(0, len(self.history) - window_size + 1, window_size // 2):
            window = self.history[i:i+window_size]
            avg_conf = sum(e.confidence for e in window) / len(window)
            windows.append(avg_conf)
        
        if len(windows) < 2:
            return {"trend": "insufficient_data", "windows": len(windows)}
        
        # Calculate trend
        first_avg = sum(windows[:len(windows)//3]) / max(len(windows)//3, 1)
        last_avg = sum(windows[-len(windows)//3:]) / max(len(windows)//3, 1)
        
        trend = "improving" if last_avg > first_avg + 0.05 else \
                "declining" if last_avg < first_avg - 0.05 else \
                "stable"
        
        return {
            "trend": trend,
            "first_third_avg": round(first_avg, 3),
            "last_third_avg": round(last_avg, 3),
            "change": round(last_avg - first_avg, 3),
            "windows": len(windows)
        }
    
    def _load_history(self) -> None:
        """Load history from disk."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.history = [ConfidenceEntry(**entry) for entry in data]
                logger.info(f"Loaded {len(self.history)} confidence entries from history")
            except Exception as e:
                logger.warning(f"Failed to load confidence history: {e}")
                self.history = []
        else:
            logger.info("No existing confidence history found, starting fresh")
    
    def _save_history(self) -> None:
        """Save history to disk."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump([asdict(e) for e in self.history], f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save confidence history: {e}")
    
    def print_statistics(self, last_n: Optional[int] = None) -> None:
        """Print statistics to console."""
        stats = self.get_statistics(last_n)
        
        print("\n" + "="*70)
        print("CONFIDENCE STATISTICS")
        if last_n:
            print(f"(Last {last_n} commands)")
        print("="*70)
        
        print(f"\nTotal Commands: {stats['total_commands']}")
        print(f"Average Confidence: {stats['avg_confidence']:.3f}")
        print(f"Min/Max: {stats['min_confidence']:.3f} / {stats['max_confidence']:.3f}")
        print(f"Median: {stats['median_confidence']:.3f}")
        
        print(f"\nSource Breakdown:")
        print(f"  Ollama: {stats['ollama_count']} commands (avg: {stats['ollama_avg_confidence']:.3f})")
        print(f"  Fallback: {stats['fallback_count']} commands (avg: {stats['fallback_avg_confidence']:.3f})")
        
        print(f"\nExecution Status:")
        print(f"  Executed: {stats['executed_count']} ({stats['executed_percentage']}%)")
        print(f"  Needed Clarification: {stats['clarification_count']} ({stats['clarification_percentage']}%)")
        
        print(f"\nConfidence Distribution:")
        print(f"  High (â‰¥0.8): {stats['high_confidence_count']}")
        print(f"  Medium (0.5-0.8): {stats['medium_confidence_count']}")
        print(f"  Low (<0.5): {stats['low_confidence_count']}")
        
        print("="*70 + "\n")


# Global instance
confidence_tracker = ConfidenceTracker()
