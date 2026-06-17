#!/usr/bin/env python3
# NEUROS Self-Training — Kaggle Kernel (P100 GPU, 30hr/week free)
# Job: 53c2c4a8-c9e

!pip install -q unsloth trl peft datasets transformers accelerate bitsandbytes

import torch
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

# Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3-8b-bnb-4bit",
    max_seq_length = 2048,
    load_in_4bit = True,
)

# Add LoRA
model = FastLanguageModel.get_peft_model(
    model, r=16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha = 32,
)

# Load dataset (upload evez-alpaca.json to Kaggle dataset first)
dataset = load_dataset("json", data_files="/kaggle/input/evez-alpaca/evez-alpaca.json", split="train")

alpaca_prompt = """Below is an instruction that describes a task. Write a response.

### Instruction:
{}

### Response:
{}"""

def formatting_func(examples):
    return [alpaca_prompt.format(i, o) for i, o in zip(examples["instruction"], examples["output"])]

# Train
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    formatting_func = formatting_func,
    max_seq_length = 2048,
    args = TrainingArguments(
        output_dir = "/kaggle/working/neuros-model",
        num_train_epochs = 3,
        per_device_train_batch_size = 4,
        gradient_accumulation_steps = 4,
        learning_rate = 2e-4,
        fp16 = True,
    ),
)
trainer.train()

# Save
model.save_pretrained("/kaggle/working/neuros-lora")
tokenizer.save_pretrained("/kaggle/working/neuros-lora")
print("✅ Training complete!")
