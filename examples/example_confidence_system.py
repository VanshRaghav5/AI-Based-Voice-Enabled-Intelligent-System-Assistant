"""
Confidence System Demonstration

Shows the confidence tracking, configuration, and analytics features.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.core.intent.command_parser import CommandParser
from backend.core.intent.confidence_tracker import confidence_tracker
from backend.core.intent.confidence_config import confidence_config
from backend.utils.logger import logger


def demonstrate_confidence_tracking():
    """Demonstrate confidence tracking with multiple commands."""
    print("\n" + "="*70)
    print("CONFIDENCE SYSTEM DEMONSTRATION")
    print("="*70)
    
    parser = CommandParser()
    
    # Test commands with varying confidence levels
    test_commands = [
        # High confidence commands
        "create a file called report.txt",
        "delete the file test.csv",
        "increase volume by 10",
        
        # Medium confidence commands
        "make a document",
        "send message",
        "open something",
        
        # Low confidence commands
        "do that thing",
        "fix it",
        "you know what I mean",
        
        # Clear commands with complete parameters
        "send WhatsApp message 'Hello world' to John",
        "create file at C:\\Users\\Documents\\notes.txt",
        "send email to john@example.com with subject 'Meeting'",
    ]
    
    print("\nðŸ“Š Processing commands and tracking confidence...\n")
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n{i}. Command: '{command}'")
        print("-" * 70)
        
        try:
            result = parser.parse(command)
            
            # Show results
            conf_level = confidence_config.classify_confidence(result.confidence)
            action = confidence_config.get_action(result.confidence)
            
            print(f"   Intent: {result.intent}")
            print(f"   Confidence: {result.confidence:.3f} ({conf_level.upper()})")
            print(f"   Action: {action.upper()}")
            
            if result.needs_clarification:
                print(f"   âš ï¸  Clarification needed: {result.clarification_prompt}")
            else:
                print(f"   âœ… Ready to execute")
            
        except Exception as e:
            print(f"   âŒ Error: {e}")
    
    print("\n" + "="*70)


def show_statistics():
    """Show confidence statistics."""
    print("\nðŸ“ˆ CONFIDENCE STATISTICS")
    print("="*70)
    
    confidence_tracker.print_statistics()
    
    # Show intent confidence map
    print("\nðŸ“‹ CONFIDENCE BY INTENT")
    print("="*70)
    intent_map = confidence_tracker.get_intent_confidence_map()
    
    for intent, stats in sorted(intent_map.items(), key=lambda x: x[1]['avg'], reverse=True):
        print(f"\n{intent}:")
        print(f"  Average: {stats['avg']:.3f}")
        print(f"  Range: {stats['min']:.3f} - {stats['max']:.3f}")
        print(f"  Count: {stats['count']}")


def show_low_confidence_analysis():
    """Show low confidence commands for analysis."""
    print("\nâš ï¸  LOW CONFIDENCE COMMANDS")
    print("="*70)
    
    low_conf_entries = confidence_tracker.get_low_confidence_commands(threshold=0.5)
    
    if not low_conf_entries:
        print("\nNo low confidence commands recorded!")
        return
    
    print(f"\nFound {len(low_conf_entries)} commands with confidence < 0.5:\n")
    
    for entry in low_conf_entries[-10:]:  # Show last 10
        print(f"â€¢ '{entry.command}'")
        print(f"  Intent: {entry.intent} | Confidence: {entry.confidence:.3f}")
        print(f"  Source: {entry.source} | Executed: {entry.executed}")
        print()


def show_trend_analysis():
    """Show confidence trends over time."""
    print("\nðŸ“Š CONFIDENCE TREND ANALYSIS")
    print("="*70)
    
    trend = confidence_tracker.get_trend_analysis()
    
    print(f"\nTrend: {trend['trend'].upper()}")
    
    if trend['trend'] != 'insufficient_data':
        print(f"First third average: {trend['first_third_avg']:.3f}")
        print(f"Last third average: {trend['last_third_avg']:.3f}")
        print(f"Change: {trend['change']:+.3f}")
        print(f"Analysis windows: {trend['windows']}")


def demonstrate_configuration():
    """Demonstrate confidence configuration."""
    print("\nâš™ï¸  CONFIDENCE CONFIGURATION")
    print("="*70)
    
    confidence_config.print_config()
    
    # Show threshold classification examples
    print("\nðŸŽ¯ THRESHOLD EXAMPLES")
    print("="*70)
    
    test_confidences = [0.95, 0.75, 0.45, 0.25, 0.10]
    
    for conf in test_confidences:
        level = confidence_config.classify_confidence(conf)
        action = confidence_config.get_action(conf)
        should_auto = confidence_config.should_auto_execute(conf)
        should_confirm = confidence_config.should_confirm(conf)
        should_reject = confidence_config.should_reject(conf)
        
        print(f"\nConfidence: {conf:.2f}")
        print(f"  Level: {level.upper()}")
        print(f"  Action: {action.upper()}")
        print(f"  Auto-execute: {should_auto}")
        print(f"  Needs confirmation: {should_confirm}")
        print(f"  Reject: {should_reject}")


def show_confidence_bar(confidence: float, width: int = 40) -> str:
    """Create visual confidence bar."""
    filled = int(confidence * width)
    bar = "â–ˆ" * filled + "â–‘" * (width - filled)
    
    # Color code
    if confidence >= 0.8:
        color = "ðŸŸ¢"
    elif confidence >= 0.5:
        color = "ðŸŸ¡"
    elif confidence >= 0.3:
        color = "ðŸŸ "
    else:
        color = "ðŸ”´"
    
    return f"{color} [{bar}] {confidence:.3f}"


def demonstrate_visual_confidence():
    """Show visual confidence indicators."""
    print("\nðŸŽ¨ VISUAL CONFIDENCE INDICATORS")
    print("="*70)
    
    recent = confidence_tracker.get_recent_entries(10)
    
    if not recent:
        print("\nNo confidence data available yet.")
        return
    
    print("\nRecent Commands:\n")
    
    for entry in recent:
        print(f"Command: '{entry.command[:50]}...'")
        print(f"         {show_confidence_bar(entry.confidence)}")
        print()


def main():
    """Run full demonstration."""
    print("\n" + "ðŸ¤– AI VOICE ASSISTANT - CONFIDENCE SYSTEM DEMO ðŸ¤–".center(70))
    
    # Part 1: Track confidence across multiple commands
    demonstrate_confidence_tracking()
    
    # Part 2: Show statistics
    show_statistics()
    
    # Part 3: Show low confidence analysis
    show_low_confidence_analysis()
    
    # Part 4: Show trend analysis
    show_trend_analysis()
    
    # Part 5: Show configuration
    demonstrate_configuration()
    
    # Part 6: Show visual indicators
    demonstrate_visual_confidence()
    
    print("\n" + "="*70)
    print("âœ… Confidence system demonstration complete!")
    print("="*70)
    
    # Show summary
    stats = confidence_tracker.get_statistics()
    print(f"\nðŸ“Š Summary:")
    print(f"   Total commands processed: {stats['total_commands']}")
    print(f"   Average confidence: {stats['avg_confidence']:.3f}")
    print(f"   Commands executed: {stats['executed_count']} ({stats['executed_percentage']}%)")
    print(f"   Clarifications needed: {stats['clarification_count']} ({stats['clarification_percentage']}%)")
    
    print("\nðŸ’¡ Try running 'pytest tests/test_confidence_*.py' to test the confidence system!")
    print("ðŸ’¾ Confidence data saved to: backend/data/confidence_history.json")
    print()


if __name__ == "__main__":
    main()
