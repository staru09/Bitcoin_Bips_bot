import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer
from peft import PeftModel, PeftConfig

base_model = "meta-llama/Meta-Llama-3-8B-Instruct" 
adapter_path = "checkpoint-375" 

print("Loading base model...")
tokenizer = AutoTokenizer.from_pretrained(base_model)
model = AutoModelForCausalLM.from_pretrained(
    base_model,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

# Load the LoRA adapter
print("Loading LoRA adapter...")
peft_config = PeftConfig.from_pretrained(adapter_path)
model = PeftModel.from_pretrained(model, adapter_path)

model.set_adapter("default")

streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

print("\nModel ready. Type your message below (type 'exit' to quit):")

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in {"exit", "quit"}:
        print("Exiting...")
        break

    prompt = f"[INST] {user_input} [/INST]"

    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    with torch.no_grad():
        _ = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            top_p=0.95,
            temperature=0.7,
            streamer=streamer
        )
