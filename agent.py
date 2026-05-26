import subprocess
import os

try:
    from llama_cpp import Llama
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "qwen", "Qwen3-0.6B-Q8_0.gguf")
    llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=False)
    def chat(prompt):
        out = llm(f"<|user|>\n{prompt}\n<|assistant|>\n", max_tokens=512, echo=False)
        return out["choices"][0]["text"].strip()
except Exception as e:
    print(f"⚠️  LLM not available ({e}). Using shell fallback.")
    def chat(prompt):
        return f"You said: {prompt}  (install a GGUF model in models/qwen/ to enable AI)"

print("🔥 Local Developer Agent (OpenCode-style)")
print("Type 'exit' to quit.\n")

while True:
    prompt = input("You: ")

    if prompt.lower() in ["exit", "quit"]:
        break

    response = chat(prompt)
    print("\nAI:", response, "\n")

    if response.startswith("!"):
        cmd = response[1:]
        print(subprocess.getoutput(cmd))
