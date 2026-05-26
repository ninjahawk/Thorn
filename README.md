# Thorn

**[Live Site](https://ninjahawk.github.io/Thorn/)**

A local AI girlfriend chatbot with an Instagram DM-style interface. Runs entirely on your PC using Ollama — no cloud, no subscriptions, full privacy.

![Interface](public/appicon.png)

---

## Features

- Instagram dark DM UI — looks and feels like a real Instagram chat
- Fully local — powered by Ollama, nothing leaves your machine
- Installable as a PWA — add to home screen on iPhone or Android, opens like a native app
- Two personality modes — Flirty mode and Sweet mode, toggled from the header
- Instagram-style profile page — photo grid, story highlights, stats, bio
- Post viewer — tap any photo to open a scrollable feed with likes, comments, pinch-to-zoom and double-tap zoom
- Story highlights — tap a highlight circle to open a full story viewer with progress bars and auto-advance
- Gift and cash system — send virtual gifts or cash and she reacts accordingly
- Saved chats — sessions stored in browser localStorage, tap the clock icon to browse and resume past chats
- Swipe right on the chat to auto-save and start a new conversation instantly
- Customizable personality — edit one text file to change how she acts
- Accessible on your phone via local WiFi
- Emoji stripping and response cleanup enforced server-side

---

## Model

The default model is **nous-hermes2:34b**, an uncensored 34B model that performs well for this use case.

```python
MODEL = "nous-hermes2:34b"
```

You can change this in `server.py`. See the Changing Models section below.

---

## Requirements

- Windows 10/11
- Python 3.9+ — https://python.org/downloads
- Ollama — https://ollama.com/download
- A GPU with at least 6GB VRAM recommended (20GB+ for the default 34b model)

---

## Setup

### 1. Install Ollama
Download and install from https://ollama.com/download

### 2. Pull the model
Open PowerShell and run:

```powershell
# Default — best quality for this use case (~20GB)
ollama pull nous-hermes2:34b

# Lighter alternative if you don't have the VRAM
ollama pull dolphin3
```

### 3. Add your profile picture
Drop your profile photo into the `public/` folder and name it `avatar.jpeg`.

### 4. Start the app
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

**Windows Firewall** — run this once in PowerShell (Admin):
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

## Personality Modes

Two modes are available, toggled via the button in the header:

- **Flirty** — dominant, teasing, reacts to gifts and cash with attitude
- **Sweet** — warm, funny, natural girlfriend energy

Both are defined in separate files:

| File | Mode |
|---|---|
| `personality.txt` | Flirty (default) |
| `personality_gf.txt` | Sweet |

Edit either file to change her behavior — no restart needed.

---

## Session & Chat History

- **Swipe right** on the chat area to instantly save the current chat and start fresh
- **Back arrow** (top left) does the same with a confirmation prompt
- **Clock icon** (top right) opens the Saved Chats screen — browse all past sessions and tap one to resume it
- Sessions are stored in your browser's `localStorage` — no server required

---

## Profile Page

Tap her name or avatar in the header to open her Instagram-style profile:

- Bio, follower/post counts
- Story highlights with custom icons — tap any to open a full story viewer
- Photo grid — tap any photo to open the post viewer
- Post viewer is a scrollable feed with like/comment counts, pinch-to-zoom, and double-tap zoom
- Swipe right to go back from the profile or post viewer

---

## Customizing the Personality

Edit `personality.txt` (or `personality_gf.txt` for Sweet mode) — changes take effect on the next message sent.

**Tips:**
- Put hard rules at the top in all caps (e.g. `NEVER USE EMOJIS`)
- Keep instructions direct and specific
- The money/gift asking frequency and per-gift reactions are all defined in the personality file

---

## Changing Models

Edit the `MODEL` line in `server.py`:

```python
MODEL = "nous-hermes2:34b"   # default — 34B, best quality, needs 20GB+ RAM+VRAM
MODEL = "dolphin3"           # 8B, ~5GB VRAM, fast
MODEL = "dolphin-llama3:8b"  # 8B alternative
MODEL = "mistral-nemo:12b"   # 12B, fits in 12GB VRAM
MODEL = "dolphin-llama3:70b" # 70B, highest quality, needs 40GB+ RAM+VRAM
```

Pull any model first:
```powershell
ollama pull <model-name>
```

---

## File Structure

```
Thorn/
├── server.py              # Python backend server
├── personality.txt        # Flirty mode personality
├── personality_gf.txt     # Sweet mode personality
├── start.bat              # Double-click to launch
├── chat_history.json      # Auto-created, persists chat across refreshes
├── memories.json          # Auto-created, long-term memory summaries
├── sessions/              # Auto-created, server-side session archives
└── public/
    ├── index.html         # Full frontend — chat UI, profile, post viewer
    ├── sw.js              # Service worker (PWA offline support)
    ├── manifest.json      # PWA manifest
    ├── avatar.jpeg        # Profile picture
    ├── appicon.png        # Home screen icon
    └── IMG_*.jpeg         # Profile post images
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
Save the file after editing (`Ctrl+S`). Changes are instant — no restart needed.

**Phone can't connect**
Run the firewall command above. Make sure both devices are on the same WiFi network.

**Saved chats not persisting**
Sessions are stored in `localStorage`. Clearing your browser data will erase them. This is per-browser, per-device.
