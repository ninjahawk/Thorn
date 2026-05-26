"""
Converts dataset.txt (Nathan:/emmi: format, --- separators) to JSONL.
Output: ../dataset.jsonl (overwrites)
"""

import json
import re

SYSTEM_PROMPT = (
    "You are Emmi, also known as thornlust. You are texting your boyfriend Nathan on Instagram DMs. "
    "You are confident, dominant, playful, and unpredictable. You never use emojis. "
    "Always write 'i' in lowercase. Keep responses short and natural like a real person texting."
)

INPUT_FILE = "../dataset.txt"
OUTPUT_FILE = "../dataset.jsonl"


def parse_conversations(text):
    blocks = re.split(r"\n---\n", text.strip())
    conversations = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        messages = []
        current_role = None
        current_content = []

        for line in block.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("Nathan:"):
                if current_role and current_content:
                    messages.append({"role": current_role, "content": " ".join(current_content).strip()})
                current_role = "user"
                current_content = [line[len("Nathan:"):].strip()]
            elif line.startswith("emmi:"):
                if current_role and current_content:
                    messages.append({"role": current_role, "content": " ".join(current_content).strip()})
                current_role = "assistant"
                current_content = [line[len("emmi:"):].strip()]
            else:
                # continuation of previous speaker
                if current_role:
                    current_content.append(line)

        if current_role and current_content:
            messages.append({"role": current_role, "content": " ".join(current_content).strip()})

        # must have at least one user+assistant pair
        if len(messages) >= 2:
            full = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            conversations.append({"conversations": full})

    return conversations


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    conversations = parse_conversations(text)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for conv in conversations:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")

    print(f"Wrote {len(conversations)} conversations to {OUTPUT_FILE}")

    # quick sanity check
    total_turns = sum(len(c["conversations"]) - 1 for c in conversations)  # -1 for system
    total_chars = sum(
        len(m["content"])
        for c in conversations
        for m in c["conversations"]
    )
    print(f"Total turns (user+assistant): {total_turns}")
    print(f"Total characters: {total_chars:,}")


if __name__ == "__main__":
    main()
