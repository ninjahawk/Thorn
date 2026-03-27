"""
Step 1: Merge LoRA adapter into base weights and save as HF safetensors.
Step 2: Download llama.cpp pre-built Windows binaries from GitHub.
Step 3: Convert merged model to F16 GGUF, then quantize to Q4_K_M.

Run after train.py has completed.
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
import subprocess
import zipfile
import json
import urllib.request
import shutil

from unsloth import FastLanguageModel

LORA_PATH       = "./outputs/emmi-lora"
MERGED_PATH     = "./outputs/emmi-merged"
GGUF_F16_PATH   = "./outputs/emmi-f16.gguf"
GGUF_Q4_PATH    = "./outputs/emmi-gguf/emmi-q4_k_m.gguf"
LLAMACPP_DIR    = "./outputs/llama-cpp"
MAX_SEQ_LEN     = 2048


# ── Step 1: Merge LoRA and save as HF ──────────────────────────────────────
def save_merged():
    if os.path.exists(MERGED_PATH) and os.listdir(MERGED_PATH):
        print(f"Merged model already exists at {MERGED_PATH}, skipping.")
        return

    print("Loading base model + LoRA adapter...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=LORA_PATH,
        max_seq_length=MAX_SEQ_LEN,
        dtype=None,
        load_in_4bit=True,
    )

    print("Merging and saving as 16-bit HF format...")
    model.save_pretrained_merged(MERGED_PATH, tokenizer, save_method="merged_16bit")
    print(f"Merged model saved to {MERGED_PATH}")


# ── Step 2: Download llama.cpp pre-built Windows release ───────────────────
def get_llamacpp():
    quantize_exe = os.path.join(LLAMACPP_DIR, "llama-quantize.exe")
    convert_py   = os.path.join(LLAMACPP_DIR, "convert_hf_to_gguf.py")

    if os.path.exists(quantize_exe) and os.path.exists(convert_py):
        print("llama.cpp tools already present.")
        return quantize_exe, convert_py

    os.makedirs(LLAMACPP_DIR, exist_ok=True)

    # Get latest release with CUDA Windows assets
    print("Finding latest llama.cpp release...")
    with urllib.request.urlopen(
        "https://api.github.com/repos/ggerganov/llama.cpp/releases/latest"
    ) as resp:
        release = json.loads(resp.read().decode())

    # Find CUDA Windows asset (prefer cudart, fall back to any win zip)
    assets = release.get("assets", [])
    win_asset = None
    for a in assets:
        name = a["name"].lower()
        if "win" in name and "cuda" in name and name.endswith(".zip"):
            win_asset = a
            break
    if not win_asset:
        for a in assets:
            name = a["name"].lower()
            if "win" in name and name.endswith(".zip"):
                win_asset = a
                break

    if not win_asset:
        raise RuntimeError("No Windows llama.cpp release found. Check https://github.com/ggerganov/llama.cpp/releases manually.")

    print(f"Downloading: {win_asset['name']} ({win_asset['size'] // 1024 // 1024} MB)...")
    zip_path = os.path.join(LLAMACPP_DIR, win_asset["name"])
    urllib.request.urlretrieve(win_asset["browser_download_url"], zip_path)

    print("Extracting...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            fname = os.path.basename(member)
            if fname in ("llama-quantize.exe",) or fname.endswith(".dll"):
                zf.extract(member, LLAMACPP_DIR)
                # flatten nested dirs
                extracted = os.path.join(LLAMACPP_DIR, member)
                target = os.path.join(LLAMACPP_DIR, fname)
                if extracted != target and os.path.exists(extracted):
                    shutil.move(extracted, target)
    os.remove(zip_path)

    # Download convert_hf_to_gguf.py from the matching tag
    tag = release["tag_name"]
    convert_url = f"https://raw.githubusercontent.com/ggerganov/llama.cpp/{tag}/convert_hf_to_gguf.py"
    print(f"Downloading convert_hf_to_gguf.py ({tag})...")
    urllib.request.urlretrieve(convert_url, convert_py)

    print("llama.cpp tools ready.")
    return quantize_exe, convert_py


# ── Step 3: Convert and quantize ───────────────────────────────────────────
def convert_and_quantize(quantize_exe, convert_py):
    os.makedirs(os.path.dirname(GGUF_Q4_PATH), exist_ok=True)

    # Convert to F16 GGUF
    if not os.path.exists(GGUF_F16_PATH):
        print(f"\nConverting to F16 GGUF...")
        result = subprocess.run(
            [sys.executable, convert_py, MERGED_PATH,
             "--outfile", GGUF_F16_PATH, "--outtype", "f16"],
            capture_output=False
        )
        if result.returncode != 0:
            raise RuntimeError("convert_hf_to_gguf.py failed")
    else:
        print(f"F16 GGUF already exists at {GGUF_F16_PATH}")

    # Quantize to Q4_K_M
    if not os.path.exists(GGUF_Q4_PATH):
        print(f"\nQuantizing to Q4_K_M...")
        result = subprocess.run(
            [quantize_exe, GGUF_F16_PATH, GGUF_Q4_PATH, "Q4_K_M"],
            capture_output=False,
            cwd=LLAMACPP_DIR
        )
        if result.returncode != 0:
            raise RuntimeError("llama-quantize.exe failed")
    else:
        print(f"Q4_K_M GGUF already exists at {GGUF_Q4_PATH}")

    print(f"\nFinal model: {os.path.abspath(GGUF_Q4_PATH)}")
    size_mb = os.path.getsize(GGUF_Q4_PATH) / 1024 / 1024
    print(f"Size: {size_mb:.0f} MB")
    print("\nNext: run create_modelfile.py to register with Ollama.")


def main():
    save_merged()
    quantize_exe, convert_py = get_llamacpp()
    convert_and_quantize(quantize_exe, convert_py)


if __name__ == "__main__":
    main()
