# Thorn — AI Girlfriend Chat (Instagram DM Clone)

## Project Overview
Instagram DM-style chat app where users talk to "Emmi" (thornlust), an AI girlfriend. Hosted on GitHub Pages with Ollama as the AI backend via Cloudflare Tunnel.

## Architecture
- **Frontend:** Single-file static site (`public/index.html`) — no build step, no framework
- **Backend:** Ollama running locally, exposed via Cloudflare Tunnel for remote access
- **Hosting:** GitHub Pages from `public/` folder, deployed via GitHub Actions on push to `dev`
- **State:** All chat history and settings stored in browser `localStorage`

## Key Files
- `public/index.html` — entire frontend (HTML + CSS + JS in one file)
- `public/sw.js` — service worker for PWA + image caching
- `public/manifest.json` — PWA manifest
- `personality.txt` — flirty/dominant personality (embedded in index.html)
- `personality_gf.txt` — sweet personality (embedded in index.html)
- `dataset.txt` / `dataset.jsonl` — 402 training conversations for fine-tuning
- `server.js` — legacy Express server (kept for local dev, not used on Pages)
- `start-tunnel.bat` — starts Ollama with CORS + Cloudflare Tunnel
- `.github/workflows/deploy.yml` — auto-deploy to GitHub Pages on push to `dev`

## Fine-tuning (not yet done)
- Script at `finetune/train_unsloth.py` — LoRA fine-tune using Unsloth
- Base model: `unsloth/Qwen2.5-7B-Instruct-bnb-4bit`
- Dataset: `dataset.jsonl` (402 multi-turn conversations)
- Must stop Ollama before training (frees VRAM on the RTX 5070, 12GB)
- After training: export GGUF → create Ollama model `emmi`

## Branches
- `dev` — active development, deploys to GitHub Pages
- `main` — stable, merge from dev when ready
- GitHub Pages deploys from `dev` branch

## GitHub Pages Notes
- Repo must be **public** for Pages to work (free plan)
- All asset paths use `./` (relative) not `/` (absolute) because site lives at `/Thorn/`
- Settings panel: long-press "thornlust" header name for 1.5s to open
- Tunnel URL + model are stored in localStorage, configured via settings panel

## Running Locally
```powershell
cd public && npx http-server -p 3000 -c-1
```
Or use the legacy Express server:
```powershell
npm start
```

## Starting Tunnel for Remote Access
```powershell
# Set Ollama CORS
$env:OLLAMA_ORIGINS = '*'
ollama serve

# In another terminal
cloudflared tunnel --url http://localhost:11434
# Copy the trycloudflare.com URL → paste in app settings
```

## Images
- Profile pics are gitignored by default (`IMG_*.jpeg` in `.gitignore`)
- Existing ones were force-added with `git add -f`
- New images must also be force-added: `git add -f public/IMG_XXXX.jpeg`
