# 🚀 Security Features - Quick Start Guide

## Installation Steps

### 1. Install New Security Dependencies

Run this command in your project root:

```bash
cd "d:\AI Based Voice Intelligent System\AI-Based-Voice-Enabled-Intelligent-System-Assistant"
.\venv\Scripts\activate
pip install PyJWT Flask-JWT-Extended bcrypt Flask-Limiter SQLAlchemy marshmallow email-validator
```

Or install from requirements.txt:

```bash
pip install -r backend/requirements.txt
```

### 2. Start the Backend

```bash
cd backend
python api_service.py
```

**Expected Output:**
```
[Database] Database initialized successfully
[Auth] Default admin user created!
[Auth] Username: admin
[Auth] Password: Admin@123
[Auth] ⚠️  PLEASE CHANGE THE DEFAULT PASSWORD IMMEDIATELY!
[Database] Found 1 existing user(s)
API Service starting on http://0.0.0.0:5000
  POST /api/auth/register - Register new user
  POST /api/auth/login - Login and get token
  POST /api/auth/logout - Logout (protected)
  GET  /api/auth/verify - Verify token (protected)
  POST /api/process_command - Process text command (protected)
  POST /api/start_listening - Start voice listening (protected)
  ...
```

### 3. Start the Frontend

```bash
cd desktop_1
python main.py
```

**Expected Behavior:**
- Login window appears
- Use default credentials: `admin` / `Admin@123`
- Main chat window opens after successful login

---

## What's New?

### 🔐 Security Features Implemented

1. **JWT Authentication** - All API requests now require login
2. **Password Hashing** - bcrypt encryption for passwords
3. **Rate Limiting** - Protection against brute force attacks
4. **SQL Injection Prevention** - SQLAlchemy ORM with validation
5. **Input Validation** - Marshmallow schemas for all inputs
6. **Role-Based Access** - Admin and User roles

### 📁 New Files Created

**Backend:**
- `backend/auth/auth_service.py` - Authentication logic
- `backend/middleware/auth_middleware.py` - Authorization decorators
- `backend/middleware/validation.py` - Input validation schemas
- `backend/database/__init__.py` - Database initialization
- `backend/database/models.py` - User and Session models

**Frontend:**
- `desktop_1/ui/login_window.py` - Login UI

**Modified:**
- `backend/api_service.py` - Added auth endpoints, rate limiting
- `desktop_1/main.py` - Added authentication flow
- `desktop_1/services/api_client.py` - JWT token handling
- `backend/requirements.txt` - Added security dependencies

**Documentation:**
- `docs/SECURITY_IMPLEMENTATION.md` - Complete security guide

### 🗄️ Database

**Location:** `~/.omniassist/assistant.db`

**Tables:**
- `users` - User accounts
- `sessions` - JWT token sessions

**Auto-created on first run!**

---

## Default Admin Account

### Credentials
```
Username: admin
Password: Admin@123
```

### ⚠️ IMPORTANT
**Change this password immediately after first login!**

Currently, password change must be done manually:
1. Hash new password using bcrypt
2. Update in database

*Future enhancement: Password change UI*

---

## Usage

### Login Flow

1. **Start app** → Login window appears
2. **Enter credentials** → admin / Admin@123
3. **Click Login** → Token saved locally
4. **Main app opens** → Full functionality unlocked

### Token Storage

**Location:** `~/.omniassist/token.json`

**Contents:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

**Auto-login:** Token verified on app restart

### Logout

Currently: Close app to logout

*Future enhancement: Logout button in settings*

---

## Testing

### Test Login (curl)

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@123"}'
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "token": "eyJ0eXAi...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

### Test Protected Endpoint

```bash
# Without token (should fail)
curl -X POST http://localhost:5000/api/process_command \
  -H "Content-Type: application/json" \
  -d '{"command": "hello"}'

# With token (should work)
curl -X POST http://localhost:5000/api/process_command \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"command": "hello"}'
```

### Test Rate Limiting

Try logging in 11 times in a minute → Should block on 11th attempt

---

## Troubleshooting

### Installation Issues

**Error:** `ModuleNotFoundError: No module named 'bcrypt'`
**Solution:** `pip install bcrypt PyJWT Flask-JWT-Extended Flask-Limiter SQLAlchemy marshmallow email-validator`

### Login Issues

**Error:** "Authentication required"
**Solution:** Delete `~/.omniassist/token.json` and restart app

**Error:** "Invalid username or password"
**Solution:** Use default credentials: `admin` / `Admin@123`

**Error:** "Rate limit exceeded"
**Solution:** Wait 1 minute and try again

### Database Issues

**Error:** "Database initialization error"
**Solution:** 
1. Delete `~/.omniassist/assistant.db`
2. Restart backend (will recreate)

**Error:** "No module named 'sqlalchemy'"
**Solution:** `pip install SQLAlchemy`

---

## Quick Command Reference

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start backend
cd backend && python api_service.py

# Start frontend
cd desktop_1 && python main.py

# Test login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@123"}'

# View database
sqlite3 ~/.omniassist/assistant.db
SELECT * FROM users;
SELECT * FROM sessions;
.quit

# Reset everything
rm -rf ~/.omniassist/
# Restart backend (recreates database and admin user)
```

---

## What Happens on First Run?

1. **Backend starts:**
   - Creates `~/.omniassist/assistant.db`
   - Creates `users` and `sessions` tables
   - Creates default admin user
   - Logs credentials to console

2. **Frontend starts:**
   - Shows login window
   - Waits for authentication

3. **After login:**
   - Saves token to `~/.omniassist/token.json`
   - Opens main chat window
   - All features work normally

4. **Next startup:**
   - Checks for saved token
   - Verifies with server
   - If valid, auto-logs in
   - If invalid, shows login

---

## Security Checklist

After installation:

- [ ] Backend starts without errors
- [ ] Database created at `~/.omniassist/assistant.db`
- [ ] Default admin user created
- [ ] Frontend shows login window
- [ ] Can login with `admin` / `Admin@123`
- [ ] Token saved to `~/.omniassist/token.json`
- [ ] Main app opens after login
- [ ] Voice commands work
- [ ] Settings sync works
- [ ] Protected endpoints require auth
- [ ] Rate limiting active (test with multiple failed logins)

---

## Need More Details?

See **`docs/SECURITY_IMPLEMENTATION.md`** for:
- Complete technical documentation
- Security architecture
- API endpoint reference
- Testing procedures
- Configuration options
- Troubleshooting guide
- Future enhancements

---

## Summary

✅ **Authentication:** JWT-based login required  
✅ **Authorization:** Role-based access control  
✅ **Protection:** Rate limiting, input validation, SQL injection prevention  
✅ **Encryption:** bcrypt password hashing  
✅ **Session Management:** Token expiration, revocation  

**Default Login:** `admin` / `Admin@123` (CHANGE THIS!)

**Ready to use!** 🚀
