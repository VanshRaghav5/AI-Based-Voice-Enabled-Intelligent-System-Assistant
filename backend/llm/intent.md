# Intent Recognition Guide

## Allowed Intents

### Communication
- `whatsapp_send` - Send WhatsApp message
- `send_email` - Send email

### File Operations
- `file_open` (open_file) - Open/view a file
- `file_create` (create_file) - Create a new file
- `file_delete` (delete_file) - Delete a file
- `file_move` (move_file) - Move/rename a file
- `file_search` (search_file) - Search for files

### Folder Operations
- `folder_create` (create_folder) - Create a new folder
- `folder_delete` (delete_folder) - Delete a folder

### System Control
- `volume_up` - Increase system volume
- `volume_down` - Decrease system volume
- `volume_mute` (mute) - Toggle mute
- `system_lock` (lock) - Lock the computer
- `system_shutdown` (shutdown) - Shutdown the system
- `system_restart` (restart) - Restart the system
- `system_sleep` - Put system to sleep

### Special
- `unknown` - Unable to determine intent

## Entity Requirements by Intent

| Intent | Required | Optional |
|--------|----------|----------|
| whatsapp_send | target, message | - |
| file_open | path | - |
| file_create | path | content |
| file_delete | path | - |
| file_move | source, destination | - |
| file_search | search_term | root |
| folder_create | path | - |
| folder_delete | path | - |

## Response Format

```json
{
  "intent": "string",
  "entities": {
    "key": "value"
  },
  "confidence": 0.0 to 1.0
}
```

## Confidence Levels

- **0.95-1.0**: High confidence - clear intent with specific entities
- **0.75-0.94**: Good confidence - intent recognized but some ambiguity
- **0.50-0.74**: Medium confidence - multiple interpretations possible
- **0.00-0.49**: Low confidence - unclear or ambiguous intent
