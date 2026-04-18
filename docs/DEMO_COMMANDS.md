# OmniAssist: Live Demo Commands Guide

This document provides a curated list of voice commands designed to showcase the full capabilities of the assistant during a live demonstration. The commands are ordered to build up from simple system control to advanced "intelligent" capabilities like persistent memory, app integration, and developer workflows.

---

## 💻 1. System & Utility (Warm-up)
*These commands demonstrate fast, local OS-level integrations, including the latest time/date capabilities.*

* "What time is it right now?"
* "What is today's date?" 
* "Mute the system volume."
* "Set volume to 50 percent."
* "Take a screenshot." *(A great visual cue)*
* "Lock my PC." *(Save this for the very end of your demo!)*

---

## 📁 2. Application & File Management
*Shows that the assistant has real authority over the local Windows desktop, behaving like a true agent rather than just a chatbot.*

* "Open Notepad" or "Launch the calculator."
* "Create a folder called 'Project Backup' on my Desktop."
* "Create a file named 'demo.txt' in my Documents folder."
* "Delete the file 'demo.txt' from Documents." *(Great opportunity to show off safety features if it asks for confirmation before deleting!)*

---

## 🧠 3. Persistent Memory (The "Wow" Factor)
*Most voice assistants forget things instantly. This shows off your local persistent memory system and LLM parameter extraction.*

* "Remember that my flight to New York is tomorrow at 8 AM."
* "Remember that the server password is 'admin123'."
* *(Later in the demo)* "What time is my flight?" or "Recall my flight details."
* "List everything you remember."
* "Forget the server password."

---

## 🌐 4. Web & Browser Control
*These highlight how the assistant parses complex intent rather than just clicking hard-coded buttons.*

* "Open YouTube."
* "Search Google for the latest tech news."
* "Play some lo-fi study music on YouTube." *(Demonstrates multi-step intent: opening the browser, navigating to YouTube, and executing a search)*

---

## 💬 5. App Connectivity (Advanced Automations)
*These are high-value commands that show how the assistant replaces manual typing and app navigation.*

* "Open WhatsApp."
* "Send a message to [Friend's Name] on WhatsApp saying I am running 5 minutes late."
* "Send an email to [test@email.com] with the subject 'Demo' and the body 'This is a test of the voice assistant'."

---

## ⌨️ 6. Developer & Coding Workflows (Latest Features)
*These commands leverage the new Git tool definitions and workspace configurations, showing that the assistant understands developer workflows.*

**Project Setup:**
* "Open my default workspace." *(Highlights the new `default_workspace` config)*
* "Create a new folder called 'PythonProject' on my Desktop."
* "Create a file named 'app.py' in the PythonProject folder."
* "Create a file named '.gitignore'."

**Version Control (Git):**
* "Initialize a git repository in this folder."
* "Check the git status."
* "Create a new git branch called 'feature-login'."
* "Stage all my files and commit them with the message 'initial project setup'."
* "Switch back to the main branch."

**Execution:**
* "Open Visual Studio Code in the current directory." (or "Open this folder in VS Code")
* "Run the python file 'app.py'."
* "Install the 'requests' package using pip."

---

### 💡 Tips for a Great Demo:
1. **Developer Narrative:** Start the developer section by having the assistant create a new folder and a Python file. Then, ask it to initialize Git, check the status, and make the first commit. This creates a highly compelling, continuous "developer workflow" narrative done entirely by voice!
2. **Point out the Intelligence:** If you are using the desktop UI, make sure to point out the **Confidence Score** and the **Execution Plan** as it appears on the screen. Explain to your audience that unlike basic keyword bots, your assistant uses an LLM to generate a structured execution plan (`Plan -> Act -> Observe`) completely offline!