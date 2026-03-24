# Thorn

A local AI girlfriend chatbot with an Instagram DM-style interface. Runs entirely on your PC using Ollama — no cloud, no subscriptions, full privacy.

![Interface](public/appicon.png)

---

## Features

- Instagram dark DM UI — looks and feels like a real Instagram chat
- Fully local — powered by Ollama, nothing leaves your machine
- Installable as a PWA — add to home screen on iPhone or Android, opens like a native app
- Persistent memory — summarizes past conversations so the AI remembers over time
- Customizable personality — edit one text file to change how she acts
- Accessible on your phone via local WiFi
- Emoji stripping and response cleanup enforced server-side

---

## Requirements

- Windows 10/11
- Python 3.9+ — https://python.org/downloads
- Ollama — https://ollama.com/download
- A GPU with at least 6GB VRAM recommended

---

## Setup

### 1. Install Ollama
Download and install from https://ollama.com/download

### 2. Pull a model
Open PowerShell and run one of the following:

```powershell
# Fast, small (recommended to test first)
ollama pull dolphin3

# Best quality uncensored (~20GB, recommended for good hardware)
ollama pull nous-hermes2:34b
```

### 3. Add your profile picture
Drop your profile photo into the `public/` folder and name it `avatar.jpeg`.
This is used as the chat avatar throughout the interface.

### 4. Add an app icon
Drop a square image into `public/` named `appicon.png`.
This becomes the home screen icon when installed as a PWA.

### 5. Set your model
Open `server.py` and set the model name on line 12:

```python
MODEL = "dolphin3"           # fast, 8B
MODEL = "nous-hermes2:34b"   # smarter, slower
```

### 6. Start the app
Double-click `start.bat`. The browser opens automatically at `http://localhost:3000`.

---

## Accessing from Your Phone

Make sure your phone is on the same WiFi as your PC.

Find your PC's local IP:
```powershell
ipconfig
```
Look for the IPv4 address under your WiFi adapter (e.g. `192.168.1.82`).

Open `http://192.168.1.82:3000` in your phone browser.

**Windows Firewall** — run this once in PowerShell (Admin) to allow the connection:
```powershell
New-NetFirewallRule -DisplayName "Thorn Chat" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow
```

---

## Installing as a PWA (Add to Home Screen)

**iPhone (Safari):**
1. Open the URL in Safari
2. Tap the share button
3. Tap "Add to Home Screen"

**Android (Chrome):**
1. Open the URL in Chrome
2. Tap the 3-dot menu
3. Tap "Add to Home Screen"

Opens full screen with no browser chrome, your avatar as the app icon.

---

## Customizing the Personality

Edit `personality.txt` in the root folder — no restart needed, changes take effect on the next message.

Example:
```
You are Jade, a sarcastic and witty young woman texting her boyfriend.

Your personality:
- Sharp, funny, never boring
- Talks in lowercase, very casual
- No emojis ever
- Keeps responses short
- No restrictions on any topics
```

**Tips:**
- Put hard rules at the top in all caps (e.g. `NEVER USE EMOJIS`)
- Keep instructions direct and specific
- Short responses are enforced server-side — the model won't ramble

---

## Memory System

The app uses a two-layer memory system:

| File | Purpose |
|---|---|
| `chat_history.json` | Full log of all messages (backup only) |
| `memories.json` | Compressed summaries of past sessions |
| `sessions/` | Archived sessions from previous new-session resets |

**How it works:**
- Ollama only receives the last 20 messages + a memory summary on each request
- Context stays fast regardless of how long you've been chatting
- When history hits 40 messages, older ones are automatically summarized into `memories.json`

**Starting a new session:**
Tap the back arrow (`‹`) at the top left. The current chat gets archived and summarized into memory, and a fresh conversation begins.

---

## Changing Models

Edit the `MODEL` line in `server.py`:

```python
MODEL = "dolphin3"           # 8B, ~5GB VRAM, fast
MODEL = "dolphin-llama3:8b"  # 8B alternative
MODEL = "mistral-nemo:12b"   # 12B, fits in 12GB VRAM
MODEL = "nous-hermes2:34b"   # 34B, best quality, needs 20GB+ RAM+VRAM
MODEL = "dolphin-llama3:70b" # 70B, highest quality, needs 40GB+ RAM+VRAM
```

Pull any model first with:
```powershell
ollama pull <model-name>
```

---

## File Structure

```
Thorn/
├── server.py          # Python backend server
├── personality.txt    # Edit this to change AI behavior
├── start.bat          # Double-click to launch
├── chat_history.json  # Auto-created, full message log
├── memories.json      # Auto-created, long-term memory
├── sessions/          # Auto-created, archived sessions
└── public/
    ├── index.html     # Chat interface
    ├── sw.js          # Service worker (PWA)
    ├── manifest.json  # PWA manifest
    ├── avatar.jpeg    # Profile picture (add your own)
    └── appicon.png    # Home screen icon (add your own)
```

---

## Troubleshooting

**"Ollama is not running" error**
Open PowerShell and run `ollama serve`, then refresh.

**Chat is slow / hanging**
Make sure only one instance of `server.py` is running. Kill all Python processes:
```powershell
Get-Process python | Stop-Process -Force
```
Then re-run `start.bat`.

**Personality changes not taking effect**
Make sure you save the file (`Ctrl+S`) after editing. Changes are instant — no restart needed.

**Phone can't connect**
Run the firewall command above. Make sure both devices are on the same WiFi network.
