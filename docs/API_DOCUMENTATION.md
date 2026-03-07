# Backend API Documentation

## Overview

The Voice Assistant Backend API provides RESTful endpoints and WebSocket connections for desktop applications to interact with the voice assistant system. This enables real-time voice processing, command execution, and bidirectional communication.

## Base URL

```
http://localhost:5000
```

## API Endpoints

### Health & Status

#### `GET /api/health`

Health check endpoint to verify service availability.

**Response:**
```json
{
  "status": "healthy",
  "service": "voice-assistant-api",
  "version": "1.0.0"
}
```

---

#### `GET /api/status`

Get current assistant status including listening state and pending confirmations.

**Response:**
```json
{
  "status": "online",
  "listening": false,
  "pending_confirmation": false,
  "confirmation_details": null
}
```

**Status when confirmation is pending:**
```json
{
  "status": "online",
  "listening": true,
  "pending_confirmation": true,
  "confirmation_details": {
    "status": "confirmation_required",
    "message": "About to delete file important.txt. Confirm?",
    "action": "delete_file",
    "data": {"file": "important.txt"}
  }
}
```

---

### Command Processing

#### `POST /api/process_command`

Process a text command through the assistant controller.

**Request Body:**
```json
{
  "command": "open notepad"
}
```

**Success Response:**
```json
{
  "status": "success",
  "message": "Opened Notepad successfully",
  "data": {
    "tool": "app_launcher",
    "app": "notepad"
  }
}
```

**Confirmation Required Response:**
```json
{
  "status": "confirmation_required",
  "message": "About to delete file document.txt. Confirm?",
  "action": "delete_file",
  "data": {
    "file": "document.txt"
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Command processing failed: Invalid command"
}
```

---

### Voice Control

#### `POST /api/start_listening`

Start voice listening mode. The backend will continuously listen for voice input and process commands.

**Response:**
```json
{
  "message": "Listening started",
  "listening": true
}
```

**Already Listening Response:**
```json
{
  "message": "Already listening",
  "listening": true
}
```

---

#### `POST /api/stop_listening`

Stop voice listening mode.

**Response:**
```json
{
  "message": "Listening stopped",
  "listening": false
}
```

---

### Confirmation Management

#### `POST /api/confirm`

Approve or reject a pending action that requires confirmation.

**Request Body:**
```json
{
  "approved": true
}
```

**Success Response:**
```json
{
  "status": "success",
  "message": "File deleted successfully"
}
```

**Rejection Response:**
```json
{
  "status": "cancelled",
  "message": "Action cancelled by user"
}
```

**Error Response (No Pending Confirmation):**
```json
{
  "error": "No pending confirmation"
}
```

---

### Text-to-Speech

#### `POST /api/speak`

Make the assistant speak text using TTS.

**Request Body:**
```json
{
  "text": "Hello, how can I help you?"
}
```

**Response:**
```json
{
  "message": "Speech completed",
  "text": "Hello, how can I help you?"
}
```

---

## WebSocket Events

The API provides real-time updates via WebSocket connections on the same base URL.

### Client Events (Emit to Server)

#### `connect`
Client initiates connection to server.

**Server Response (Automatic):**
```json
{
  "status": "connected",
  "listening": false,
  "pending_confirmation": false
}
```

---

#### `send_command`
Send a command via WebSocket for real-time processing.

**Emit Data:**
```json
{
  "command": "what time is it"
}
```

**Server Broadcasts:** `command_result` event to all clients.

---

#### `ping`
Ping the server to check connection.

**Server Response:** `pong` event.

---

### Server Events (Listen from Client)

#### `connection_status`
Sent when client connects, provides current state.

**Data:**
```json
{
  "status": "connected",
  "listening": false,
  "pending_confirmation": false
}
```

---

#### `voice_input`
Broadcast when voice input is detected and transcribed.

**Data:**
```json
{
  "text": "open calculator",
  "timestamp": "2026-03-02T10:30:00"
}
```

---

#### `command_result`
Broadcast when a command is processed.

**Data:**
```json
{
  "status": "success",
  "message": "Calculator opened",
  "data": {
    "tool": "app_launcher",
    "app": "calculator"
  }
}
```

---

#### `confirmation_required`
Broadcast when an action needs user confirmation.

**Data:**
```json
{
  "status": "confirmation_required",
  "message": "About to shut down computer. Confirm?",
  "action": "system_shutdown",
  "data": {}
}
```

---

#### `confirmation_result`
Broadcast after confirmation is processed.

**Data:**
```json
{
  "status": "success",
  "message": "Computer will shut down in 60 seconds"
}
```

---

#### `listening_status`
Broadcast when listening state changes.

**Data:**
```json
{
  "listening": true
}
```

---

#### `speech_complete`
Broadcast when TTS finishes speaking.

**Data:**
```json
{
  "text": "Command completed successfully"
}
```

---

#### `assistant_shutdown`
Broadcast when assistant is shutting down.

**Data:**
```json
{
  "message": "Shutting down"
}
```

---

#### `error`
Broadcast when an error occurs.

**Data:**
```json
{
  "message": "Command processing failed",
  "source": "voice_loop"
}
```

---

#### `pong`
Response to ping event.

**Data:**
```json
{
  "timestamp": "now"
}
```

---

## Complete Workflow Examples

### 1. Text Command Flow

```
Desktop Client → POST /api/process_command
                 ↓
Backend processes command
                 ↓
← (WebSocket) command_result event
← (HTTP Response) result JSON
```

### 2. Voice Listening Flow

```
Desktop Client → POST /api/start_listening
                 ↓
Backend starts listening
                 ↓
← (WebSocket) listening_status: {listening: true}
                 ↓
User speaks: "open browser"
                 ↓
← (WebSocket) voice_input: {text: "open browser"}
                 ↓
Backend processes command
                 ↓
← (WebSocket) command_result: {status: "success", ...}
                 ↓
Assistant speaks response via TTS
                 ↓
← (WebSocket) speech_complete: {text: "..."}
```

### 3. Confirmation Required Flow

```
Desktop Client → POST /api/process_command {command: "delete myfile.txt"}
                 ↓
Backend detects critical action
                 ↓
← (WebSocket) confirmation_required: {message: "Delete myfile.txt?"}
← (HTTP Response) {status: "confirmation_required"}
                 ↓
Desktop shows confirmation dialog
                 ↓
User clicks "Yes"
                 ↓
Desktop Client → POST /api/confirm {approved: true}
                 ↓
Backend executes action
                 ↓
← (WebSocket) confirmation_result: {status: "success", ...}
← (HTTP Response) {status: "success", ...}
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200 OK** - Request successful
- **400 Bad Request** - Invalid request parameters
- **500 Internal Server Error** - Server-side error

Error responses include:
```json
{
  "error": "Error description",
  "status": "error",
  "message": "Detailed error message"
}
```

---

## Code Examples

### Python (Using requests)

```python
import requests

BASE_URL = "http://localhost:5000"

# Check health
response = requests.get(f"{BASE_URL}/api/health")
print(response.json())

# Send command
response = requests.post(
    f"{BASE_URL}/api/process_command",
    json={"command": "open notepad"}
)
print(response.json())

# Start listening
response = requests.post(f"{BASE_URL}/api/start_listening")
print(response.json())
```

### JavaScript (Fetch API)

```javascript
const BASE_URL = "http://localhost:5000";

// Check health
fetch(`${BASE_URL}/api/health`)
  .then(response => response.json())
  .then(data => console.log(data));

// Send command
fetch(`${BASE_URL}/api/process_command`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({command: "open calculator"})
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### WebSocket (Python)

```python
import socketio

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('Connected to backend')

@sio.on('command_result')
def on_result(data):
    print(f"Result: {data}")

sio.connect('http://localhost:5000')
sio.emit('send_command', {'command': 'what time is it'})
sio.wait()
```

### WebSocket (JavaScript)

```javascript
const socket = io('http://localhost:5000');

socket.on('connect', () => {
  console.log('Connected to backend');
});

socket.on('command_result', (data) => {
  console.log('Result:', data);
});

socket.emit('send_command', {command: 'open browser'});
```

---

## Security Considerations

⚠️ **Important**: This API is designed for local development and testing.

For production use:
1. Change the `SECRET_KEY` in `api_service.py`
2. Implement authentication/authorization
3. Use HTTPS/WSS instead of HTTP/WS
4. Restrict CORS to specific origins
5. Add rate limiting
6. Validate and sanitize all inputs
7. Implement proper error handling

---

## Running the API Service

### Start the Backend API

```bash
# From project root
cd backend
python api_service.py
```

The service will start on `http://localhost:5000`

### Running with Custom Configuration

```python
from backend.api_service import run_api_service

run_api_service(
    host='0.0.0.0',  # Listen on all interfaces
    port=8080,        # Custom port
    debug=False       # Production mode
)
```

---

## Testing the API

### Using cURL

```bash
# Health check
curl http://localhost:5000/api/health

# Get status
curl http://localhost:5000/api/status

# Send command
curl -X POST http://localhost:5000/api/process_command \
  -H "Content-Type: application/json" \
  -d '{"command": "open notepad"}'

# Start listening
curl -X POST http://localhost:5000/api/start_listening

# Stop listening
curl -X POST http://localhost:5000/api/stop_listening
```

### Using the Example Desktop Client

```bash
# Run the example integration
python desktop/example_integration.py
```

---

## Troubleshooting

### Connection Refused
- Ensure the backend API is running: `python backend/api_service.py`
- Check if port 5000 is available
- Verify firewall settings

### WebSocket Connection Failed
- Check CORS settings in `api_service.py`
- Ensure `flask-socketio` is installed: `pip install flask-socketio`
- Try connecting with `allow_unsafe_werkzeug=True` during development

### Commands Not Processing
- Check backend logs for errors
- Verify `AssistantController` is properly initialized
- Ensure required dependencies are installed

---

## Support

For issues or questions:
1. Check the logs in the backend console
2. Review error messages in responses
3. Refer to the example code in `desktop/example_integration.py`
4. Check the `backend/api_service.py` source code
