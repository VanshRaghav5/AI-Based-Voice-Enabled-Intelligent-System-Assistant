# Assistant Handbook

This is the primary operational guide for the project.

## Scope

This handbook consolidates setup, runtime behavior, memory behavior, and daily usage.

## Quick Start

1. Install dependencies.
2. Start backend service.
3. Start desktop client.
4. Login and run commands by text or voice.

## Runtime Model

The assistant uses a bounded agent loop:

1. Plan
2. Act
3. Observe
4. Replan when needed

The loop stops on success, user confirmation checkpoint, or max iteration limit.

## Safety Model

Critical operations require explicit confirmation.

Examples:
- file delete
- folder delete
- system shutdown
- system restart
- email send
- whatsapp send

After confirmation, execution resumes from the exact pending step.

## Persistent Memory

Memory is persisted locally and loaded on startup.

- Memory file: backend/data/session_memory.json
- Config keys:
  - memory.enabled
  - memory.file
  - memory.max_history

Supported user memory commands:
- remember that <key> is <value>
- recall <key>
- what do you remember about <key>
- forget <key>
- list memory

## Usage Examples

- Open notepad
- Search for budget report
- Send hello to John on WhatsApp
- Remember that office city is Pune
- Recall office city

## Canonical Docs

- API reference: API_DOCUMENTATION.md
- Reports summary: reports/REPORTS_SUMMARY.md
- Legacy docs archive: archive/legacy-docs/
- Legacy reports archive: archive/reports/
