"""
Finds the GGUF file from training output, writes a Modelfile,
and registers it with Ollama as 'emmi'.

Run this after train.py finishes.
"""

import os
import subprocess
import glob

GGUF_DIR   = "./outputs/emmi-gguf"
MODEL_NAME = "emmi"

MODELFILE_TEMPLATE = """FROM {gguf_path}

PARAMETER temperature 0.92
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"
"""

def main():
    # Find the GGUF file
    gguf_files = glob.glob(os.path.join(GGUF_DIR, "*.gguf"))
    if not gguf_files:
        print(f"No GGUF files found in {GGUF_DIR}. Did train.py finish?")
        return

    gguf_path = os.path.abspath(gguf_files[0])
    print(f"Found GGUF: {gguf_path}")

    # Write Modelfile
    modelfile_path = os.path.join(GGUF_DIR, "Modelfile")
    with open(modelfile_path, "w") as f:
        f.write(MODELFILE_TEMPLATE.format(gguf_path=gguf_path))
    print(f"Modelfile written to {modelfile_path}")

    # Register with Ollama
    print(f"Registering as '{MODEL_NAME}' in Ollama...")
    result = subprocess.run(
        ["ollama", "create", MODEL_NAME, "-f", modelfile_path],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"Success! Run with: ollama run {MODEL_NAME}")
        print(f"Or update server.py MODEL = '{MODEL_NAME}'")
    else:
        print("Ollama create failed:")
        print(result.stderr)
        print(f"\nManually run: ollama create {MODEL_NAME} -f {modelfile_path}")


if __name__ == "__main__":
    main()
