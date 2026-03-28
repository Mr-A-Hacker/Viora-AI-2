from smoltools import chat
import subprocess
import os

print("🔥 Local Developer Agent (OpenCode-style)")
print("Type 'exit' to quit.\n")

while True:
    prompt = input("You: ")

    if prompt.lower() in ["exit", "quit"]:
        break

    # Send prompt to local model
    response = chat(prompt)
    print("\nAI:", response, "\n")

    # Optional: allow commands
    if response.startswith("!"):
        cmd = response[1:]
        print(subprocess.getoutput(cmd))
