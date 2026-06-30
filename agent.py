import subprocess
import requests

BLOCKED_COMMANDS = ['rm -rf', 'dd', 'mkfs', 'shutdown', 'reboot', 'halt', 'poweroff', 'init 0', 'init 6']

def chat(prompt: str) -> str:
    try:
        resp = requests.post("http://127.0.0.1:8000/chat", json={"message": prompt}, timeout=30)
        return resp.json().get("response", "")
    except Exception as e:
        return f"[Error calling local AI: {e}]"

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
        cmd_lower = cmd.lower().strip()
        blocked = False
        for b in BLOCKED_COMMANDS:
            if b in cmd_lower:
                print(f"Blocked dangerous command: {b}")
                blocked = True
                break
        if not blocked:
            print(f"Executing: {cmd}")
            confirm = input("Run this command? (y/N): ")
            if confirm.lower() == 'y':
                print(subprocess.getoutput(cmd))
            else:
                print("Skipped.")
