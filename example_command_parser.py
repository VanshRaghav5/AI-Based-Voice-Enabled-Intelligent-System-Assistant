"""
Example: Using Enhanced Command Parser

Demonstrates the multi-stage command parsing pipeline with:
1. Intent Recognition (with confidence)
2. Parameter Extraction
3. Parameter Validation
4. Execution or Clarification
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.core.command_parser import command_parser
from backend.config.logger import logger


def demonstrate_command_parsing():
    """Demonstrate the enhanced command parsing system."""
    
    print("=" * 70)
    print("ENHANCED COMMAND PARSING DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Example 1: Clear command with all parameters
    print("1. CLEAR COMMAND WITH ALL PARAMETERS")
    print("-" * 70)
    command = "send 'Hello world' to John on WhatsApp"
    print(f"Command: {command}")
    print()
    
    result = command_parser.parse(command)
    print(f"  Intent: {result.intent}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Parameters: {result.parameters}")
    print(f"  Validation: {'✅ VALID' if result.validation.is_valid else '❌ INVALID'}")
    print(f"  Needs Clarification: {'Yes' if result.needs_clarification else 'No'}")
    if result.needs_clarification:
        print(f"  Clarification: {result.clarification_prompt}")
    print()
    
    # Example 2: Command with missing parameters
    print("2. COMMAND WITH MISSING PARAMETERS")
    print("-" * 70)
    command = "send WhatsApp message"
    print(f"Command: {command}")
    print()
    
    result = command_parser.parse(command)
    print(f"  Intent: {result.intent}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Parameters: {result.parameters}")
    print(f"  Validation: {'✅ VALID' if result.validation.is_valid else '❌ INVALID'}")
    print(f"  Needs Clarification: {'Yes' if result.needs_clarification else 'No'}")
    if result.needs_clarification:
        print(f"  Clarification: {result.clarification_prompt}")
    print()
    
    # Example 3: File command with path
    print("3. FILE COMMAND WITH COMPLETE PATH")
    print("-" * 70)
    command = "create file C:\\Users\\test\\document.txt"
    print(f"Command: {command}")
    print()
    
    result = command_parser.parse(command)
    print(f"  Intent: {result.intent}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Parameters: {result.parameters}")
    print(f"  Validation: {'✅ VALID' if result.validation.is_valid else '❌ INVALID'}")
    if result.validation.warnings:
        print(f"  Warnings: {result.validation.warnings}")
    print(f"  Needs Clarification: {'Yes' if result.needs_clarification else 'No'}")
    print()
    
    # Example 4: Volume command with step
    print("4. VOLUME COMMAND WITH STEP PARAMETER")
    print("-" * 70)
    command = "volume up 15"
    print(f"Command: {command}")
    print()
    
    result = command_parser.parse(command)
    print(f"  Intent: {result.intent}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Parameters: {result.parameters}")
    print(f"  Validation: {'✅ VALID' if result.validation.is_valid else '❌ INVALID'}")
    print(f"  Needs Clarification: {'Yes' if result.needs_clarification else 'No'}")
    print()
    
    # Example 5: Invalid parameters
    print("5. COMMAND WITH INVALID PARAMETERS")
    print("-" * 70)
    command = "send email to not-an-email subject Test"
    print(f"Command: {command}")
    print()
    
    result = command_parser.parse(command)
    print(f"  Intent: {result.intent}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Parameters: {result.parameters}")
    print(f"  Validation: {'✅ VALID' if result.validation.is_valid else '❌ INVALID'}")
    if not result.validation.is_valid:
        print(f"  Errors: {result.validation.errors}")
    print(f"  Needs Clarification: {'Yes' if result.needs_clarification else 'No'}")
    if result.needs_clarification:
        print(f"  Clarification: {result.clarification_prompt}")
    print()
    
    # Example 6: Ambiguous command (low confidence)
    print("6. AMBIGUOUS COMMAND (LOW CONFIDENCE)")
    print("-" * 70)
    command = "do something"
    print(f"Command: {command}")
    print()
    
    result = command_parser.parse(command)
    print(f"  Intent: {result.intent}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Parameters: {result.parameters}")
    print(f"  Needs Clarification: {'Yes' if result.needs_clarification else 'No'}")
    if result.needs_clarification:
        print(f"  Clarification: {result.clarification_prompt}")
    print()
    
    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)


def show_confidence_levels():
    """Show different confidence levels for various commands."""
    
    print("\n")
    print("=" * 70)
    print("CONFIDENCE LEVEL ANALYSIS")
    print("=" * 70)
    print()
    
    test_commands = [
        "volume up",
        "open file test.txt",
        "send 'hello' to John on WhatsApp",
        "create folder MyDocuments",
        "do something with files",
        "maybe open something",
    ]
    
    print(f"{'Command':<40} {'Intent':<25} {'Confidence':<12} {'Status'}")
    print("-" * 70)
    
    for cmd in test_commands:
        result = command_parser.parse(cmd)
        confidence_bar = "█" * int(result.confidence * 10)
        status = "✅" if not result.needs_clarification else "❓"
        print(f"{cmd:<40} {result.intent:<25} {confidence_bar:<12} {status}")
    
    print()


def show_pipeline_stages():
    """Show detailed breakdown of pipeline stages."""
    
    print("\n")
    print("=" * 70)
    print("PIPELINE STAGE BREAKDOWN")
    print("=" * 70)
    print()
    
    command = "send 'meeting at 3pm' to Sarah on WhatsApp"
    print(f"Command: {command}")
    print()
    
    # Stage 1: Intent Recognition
    print("Stage 1: Intent Recognition")
    result = command_parser.parse(command)
    print(f"  → Identified Intent: {result.intent}")
    print(f"  → Source: {command_parser.llm_client.last_source}")
    print()
    
    # Stage 2: Parameter Extraction
    print("Stage 2: Parameter Extraction")
    print(f"  → Extracted Parameters:")
    for key, value in result.parameters.items():
        print(f"      {key}: {value}")
    print()
    
    # Stage 3: Parameter Validation
    print("Stage 3: Parameter Validation")
    print(f"  → Validation Status: {'✅ PASS' if result.validation.is_valid else '❌ FAIL'}")
    if result.validation.errors:
        print(f"  → Errors: {result.validation.errors}")
    if result.validation.warnings:
        print(f"  → Warnings: {result.validation.warnings}")
    print()
    
    # Stage 4: Decision
    print("Stage 4: Decision")
    print(f"  → Overall Confidence: {result.confidence:.2f}")
    print(f"  → Needs Clarification: {'Yes' if result.needs_clarification else 'No'}")
    if result.needs_clarification:
        print(f"  → Clarification Prompt: {result.clarification_prompt}")
    else:
        print(f"  → Decision: READY FOR EXECUTION ✅")
    print()


if __name__ == "__main__":
    try:
        demonstrate_command_parsing()
        show_confidence_levels()
        show_pipeline_stages()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
