# Desktop UI for Aether AI Assistant

Electron desktop app to control the voice assistant with visual interface, status monitoring, and real-time logs.

---

## 🚀 Quick Start

### Step 1: Install Dependencies (First Time Only)

```bash
cd desktop
npm install
```

### Step 2: Start Backend API

Open **Terminal 1** and run from **project root**:

```bash
uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

✅ **Wait for:** `Uvicorn running on http://0.0.0.0:8000`

### Step 3: Start Desktop UI

Open **Terminal 2** and run:

```bash
cd desktop
npm start
```

✅ **Wait for:** Electron window opens

---

## ✅ Verify It's Working

### 1. Check Connection
- Top right should show: **`LOCAL (CONNECTED)`**
- If shows "OFFLINE", backend is not running or not reachable

### 2. Check Status
- Status indicator should show: **`IDLE`**
- Color: Gray/Blue

### 3. Start Assistant
- Click **START** button
- Status changes: `IDLE` → `STARTING` → `ACTIVE`
- Log panel shows activity

### 4. View Logs
- Logs update every 5 seconds from backend
- Color-coded: Info (blue), Warning (yellow), Error (red)

### 5. Stop Assistant
- Click **STOP** button
- Status changes: `ACTIVE` → `STOPPING` → `IDLE`

---

## 🔧 What Each Button Does

| Button | Action | Result |
|--------|--------|--------|
| **START** | Launches `app.py` in background | Assistant starts listening for voice commands |
| **STOP** | Terminates assistant process | Voice assistant stops |

---

## 🐛 Common Issues

### ❌ UI Shows "OFFLINE"

**Cause:** Backend API not running

**Fix:**
```bash
# In project root
uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

**Verify:** Open browser to http://localhost:8000/status (should show JSON)

---

### ❌ Logs Are Empty

**Cause:** No activity yet or log file doesn't exist

**Fix:**
1. Click **START** to generate logs
2. Check if `backend/data/assistant.log` exists
3. Wait 5 seconds for sync

---

### ❌ Can't Click START Button

**Cause:** Backend not connected

**Fix:** Ensure Terminal 1 shows `Uvicorn running...`

---

### ❌ Status Stuck on "STARTING"

**Cause:** `app.py` failed to start

**Fix:**
1. Check Terminal 1 for errors
2. Ensure Python environment is activated
3. Verify `app.py` exists in project root

---

## 📁 What's Inside

```
desktop/
├── src/
│   ├── components/
│   │   ├── ControlPanel.js      # Start/Stop buttons
│   │   ├── StatusIndicator.js   # Status display
│   │   ├── LogPanel.js          # Log viewer
│   │   └── NotificationToast.js # Notifications
│   └── services/
│       ├── api.js               # Calls backend API
│       ├── NetworkService.js    # Polls backend every 5s
│       └── stateManager.js      # Manages app state
├── main.js                      # Electron entry
├── package.json                 # Dependencies
└── Readme.md                    # This file
```

---

## 🔌 API Endpoints Used

The desktop app connects to these backend endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/status` | GET | Get assistant status (IDLE/ACTIVE) |
| `/start` | POST | Start assistant subprocess |
| `/stop` | POST | Stop assistant subprocess |
| `/logs` | GET | Fetch execution logs |
| `/config/listening` | POST | Toggle always-listening mode |

---

## 📝 Development Notes

- **State updates:** Every 5 seconds via polling
- **Log sync:** Every 5 seconds from `backend/data/assistant.log`
- **Port:** Backend must run on `8000`
- **CORS:** Enabled for all origins in backend

---

## 🎯 Need More Help?

1. **Full system docs:** See root `README.md`
2. **Backend API code:** See `backend/api.py`
3. **Testing:** See `tests/README.md`

---

**Note:** Desktop UI is optional. You can still use `python app.py` directly for CLI mode.