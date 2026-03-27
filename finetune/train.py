"""
Fine-tunes dolphin3:8b (Llama 3.1 8B base) on the Emmi personality dataset.
Uses Unsloth + QLoRA — fits in 12 GB VRAM.

Outputs:
  ./outputs/emmi-lora/          — LoRA adapter (checkpoint)
  ./outputs/emmi-gguf/          — merged GGUF ready for Ollama
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template, standardize_sharegpt
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset
import torch
import os

# ── Config ─────────────────────────────────────────────────────────────────
BASE_MODEL   = "cognitivecomputations/Dolphin3.0-Llama3.1-8B"
DATASET_FILE = "../dataset.jsonl"
OUTPUT_LORA  = "./outputs/emmi-lora"
OUTPUT_GGUF  = "./outputs/emmi-gguf"

MAX_SEQ_LEN  = 2048
LORA_RANK    = 16
BATCH_SIZE   = 2
GRAD_ACCUM   = 4          # effective batch = 8
EPOCHS       = 3
LR           = 2e-4
# ───────────────────────────────────────────────────────────────────────────


def main():
    # 1. Load base model with 4-bit quantization
    print("Loading model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LEN,
        dtype=None,           # auto-detect (bf16 on RTX 5070)
        load_in_4bit=True,
    )

    # 2. Attach LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=LORA_RANK * 2,
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # 3. Apply ChatML template (dolphin3 uses ChatML)
    tokenizer = get_chat_template(tokenizer, chat_template="chatml")

    # 4. Load and format dataset
    print("Loading dataset...")
    raw = load_dataset("json", data_files=DATASET_FILE, split="train")
    dataset = standardize_sharegpt(raw)

    def format_conversations(examples):
        texts = [
            tokenizer.apply_chat_template(
                conv, tokenize=False, add_generation_prompt=False
            )
            for conv in examples["conversations"]
        ]
        return {"text": texts}

    dataset = dataset.map(format_conversations, batched=True)
    print(f"Dataset: {len(dataset)} conversations")

    # 5. Train
    print("Starting training...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=SFTConfig(
            dataset_text_field="text",
            max_seq_length=MAX_SEQ_LEN,
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM,
            num_train_epochs=EPOCHS,
            learning_rate=LR,
            lr_scheduler_type="cosine",
            warmup_ratio=0.05,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=10,
            save_steps=100,
            output_dir=OUTPUT_LORA,
            optim="adamw_8bit",
            weight_decay=0.01,
            seed=42,
            report_to="none",
        ),
    )

    trainer_stats = trainer.train()
    print(f"\nTraining done. Loss: {trainer_stats.training_loss:.4f}")

    # 6. Save LoRA adapter
    model.save_pretrained(OUTPUT_LORA)
    tokenizer.save_pretrained(OUTPUT_LORA)
    print(f"LoRA adapter saved to {OUTPUT_LORA}")

    # 7. Export to GGUF (Q4_K_M — best quality/size balance for Ollama)
    print("\nExporting to GGUF (Q4_K_M)...")
    os.makedirs(OUTPUT_GGUF, exist_ok=True)
    model.save_pretrained_gguf(
        OUTPUT_GGUF,
        tokenizer,
        quantization_method="q4_k_m",
    )
    print(f"GGUF saved to {OUTPUT_GGUF}")
    print("\nDone! Next: run create_modelfile.py to import into Ollama.")


if __name__ == "__main__":
    main()
