import json
import re
import threading
import urllib.request
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime

PORT = 3000
BASE_DIR = Path(__file__).parent
PUBLIC_DIR = BASE_DIR / "public"
HISTORY_FILE = BASE_DIR / "chat_history.json"
MEMORY_FILE = BASE_DIR / "memories.json"
PERSONALITY_FILE = BASE_DIR / "personality.txt"
GF_PERSONALITY_FILE = BASE_DIR / "personality_gf.txt"
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

MODEL = "nous-hermes2:34b"

# How many recent messages to always include in full
RECENT_WINDOW = 20
# Summarize when history grows past this
SUMMARIZE_THRESHOLD = 40

EMOJI_PATTERN = re.compile("["
    u"\U0001F600-\U0001F64F"
    u"\U0001F300-\U0001F5FF"
    u"\U0001F680-\U0001F6FF"
    u"\U0001F1E0-\U0001F1FF"
    u"\U00002700-\U000027BF"
    u"\U0001F900-\U0001F9FF"
    u"\U00002600-\U000026FF"
    u"\U0001FA00-\U0001FA6F"
    u"\U0001FA70-\U0001FAFF"
    u"\U00002300-\U000023FF"
"]+", flags=re.UNICODE)

def strip_emojis(text):
    return EMOJI_PATTERN.sub('', text)

def clean_response(text):
    text = EMOJI_PATTERN.sub('', text)
    return text.rstrip().rstrip('.')

def load_personality(mode='flirty'):
    file = GF_PERSONALITY_FILE if mode == 'sweet' else PERSONALITY_FILE
    if file.exists():
        return file.read_text(encoding="utf-8").strip()
    return "You are Emmi, a warm and friendly young woman texting her boyfriend on Instagram. Be casual, fun, and never break character."

SUMMARIZE_PROMPT = """Below is a conversation between Emmi and her boyfriend. Summarize the key things to remember: topics discussed, things he shared about himself, emotional moments, inside jokes, anything promised or mentioned. Be concise — bullet points. This summary will be used so Emmi remembers past conversations.

Conversation:
{conversation}

Summary:"""

MIME_TYPES = {
    ".html": "text/html", ".css": "text/css", ".js": "application/javascript",
    ".jpeg": "image/jpeg", ".jpg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".ico": "image/x-icon", ".json": "application/json",
}

history_lock = threading.Lock()


def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8")).get("messages", [])
        except Exception:
            return []
    return []


def save_history(messages):
    with history_lock:
        HISTORY_FILE.write_text(
            json.dumps({"messages": messages, "updated": datetime.now().isoformat()}, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )


def load_memory():
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8")).get("summary", "")
        except Exception:
            return ""
    return ""


def save_memory(summary):
    with history_lock:
        MEMORY_FILE.write_text(
            json.dumps({"summary": summary, "updated": datetime.now().isoformat()}, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )


def summarize_in_background(messages_to_summarize):
    """Call Ollama to compress old messages into a memory summary."""
    try:
        convo_text = "\n".join(
            f"{'boyfriend' if m['role'] == 'user' else 'Emmi'}: {m['content']}"
            for m in messages_to_summarize
        )
        prompt = SUMMARIZE_PROMPT.format(conversation=convo_text)
        payload = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.4}
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            summary = result.get("message", {}).get("content", "").strip()
            if summary:
                # Append to existing memory rather than replace
                existing = load_memory()
                combined = (existing + "\n\n" + summary).strip() if existing else summary
                save_memory(combined)
                print(f"[memory] summary updated ({len(combined)} chars)", flush=True)
    except Exception as e:
        print(f"[memory] summarize failed: {e}", flush=True)


STYLE_REMINDER = (
    "[style reminder: short replies only. always lowercase i. "
    "no filler phrases. no paragraphs. match the length of his message. "
    "never say 'that's good to hear' or 'hey there' or 'sounds like'. "
    "one thought per reply.]"
)
REMINDER_INTERVAL = 8  # inject a reminder every N user messages

def build_ollama_messages(all_messages, length_instruction=None, mode='flirty'):
    """Return system context + trimmed message list for Ollama."""
    memory = load_memory()
    system = load_personality(mode)
    if memory:
        system += f"\n\nMemory from previous conversations:\n{memory}"
    if length_instruction:
        system += f"\n\nRESPONSE LENGTH RULE (overrides all other length rules): {length_instruction}"

    recent = all_messages[-RECENT_WINDOW:] if len(all_messages) > RECENT_WINDOW else all_messages

    # Inject a brief style reminder every N user messages so it stays near
    # the top of the model's attention as history grows
    result = [{"role": "system", "content": system}]
    user_count = 0
    for msg in recent:
        if msg["role"] == "user":
            user_count += 1
            if user_count % REMINDER_INTERVAL == 0:
                result.append({"role": "user", "content": STYLE_REMINDER})
                result.append({"role": "assistant", "content": "got it"})
        result.append(msg)
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.startswith("/images/"):
            self._serve_file(BASE_DIR / path[len("/images/"):])
            return
        if path == "/history":
            msgs = load_history()
            body = json.dumps(msgs).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/debug-prompt":
            system = load_personality()
            body = json.dumps({"personality": system}, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/":
            path = "/index.html"
        self._serve_file(PUBLIC_DIR / path.lstrip("/"))

    def _serve_file(self, file_path):
        try:
            data = file_path.read_bytes()
            mime = MIME_TYPES.get(file_path.suffix.lower(), "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        if self.path == "/save":
            messages = body.get("messages", [])
            save_history(messages)
            if len(messages) >= SUMMARIZE_THRESHOLD:
                to_summarize = messages[:-RECENT_WINDOW]
                threading.Thread(target=summarize_in_background, args=(to_summarize,), daemon=True).start()
            self.send_response(200)
            self.end_headers()
            return

        if self.path == "/new-session":
            messages = body.get("messages", [])
            # Archive current session
            if messages:
                ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                archive = SESSIONS_DIR / f"session_{ts}.json"
                archive.write_text(json.dumps({"messages": messages, "saved": ts}, indent=2, ensure_ascii=False), encoding="utf-8")
                # Summarize everything into memory
                threading.Thread(target=summarize_in_background, args=(messages,), daemon=True).start()
            # Clear active history
            HISTORY_FILE.write_text(json.dumps({"messages": [], "updated": datetime.now().isoformat()}, indent=2), encoding="utf-8")
            self.send_response(200)
            self.end_headers()
            return

        if self.path != "/chat":
            self.send_response(404)
            self.end_headers()
            return

        messages = body.get("messages", [])
        length_instruction = body.get("length_instruction", None)
        mode = body.get("mode", "flirty")
        ollama_messages = build_ollama_messages(messages, length_instruction, mode)

        print(f"[chat] sending {len(ollama_messages)} messages to ollama", flush=True)
        print(f"[chat] system prompt (first 120 chars): {ollama_messages[0]['content'][:120]}", flush=True)
        print(f"[chat] history messages: {len(ollama_messages)-1}", flush=True)
        payload = json.dumps({
            "model": MODEL,
            "messages": ollama_messages,
            "stream": True,
            "options": {"temperature": 0.92, "top_p": 0.9}
        }).encode()

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        try:
            req = urllib.request.Request(
                "http://localhost:11434/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                full = ""
                for raw_line in resp:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        content = obj.get("message", {}).get("content", "")
                        if content:
                            full += content
                            # stream emojis stripped in real time
                            cleaned = clean_response(full)
                            self.wfile.write(f"data: {json.dumps({'content': content, 'full': cleaned})}\n\n".encode())
                            self.wfile.flush()
                        if obj.get("done"):
                            final = clean_response(full)
                            self.wfile.write(f"data: {json.dumps({'final': final})}\n\ndata: [DONE]\n\n".encode())
                            self.wfile.flush()
                            return
                    except Exception:
                        pass
        except Exception:
            msg = "Ollama is not running. Open a new terminal and run: ollama serve"
            try:
                self.wfile.write(f"data: {json.dumps({'error': msg})}\n\ndata: [DONE]\n\n".encode())
                self.wfile.flush()
            except Exception:
                pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"\n  Emmi chat running at http://localhost:{PORT}\n")
    import webbrowser
    webbrowser.open(f"http://localhost:{PORT}")
    server.serve_forever()
