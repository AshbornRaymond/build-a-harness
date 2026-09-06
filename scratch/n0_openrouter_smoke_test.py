import json
import os
import subprocess
import glob
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Hard fail if OPENROUTER_API_KEY is not set in environment or .env
if "OPENROUTER_API_KEY" not in os.environ or not os.environ["OPENROUTER_API_KEY"]:
    raise KeyError("OPENROUTER_API_KEY environment variable is not set. Please add it to your .env file.")

API_KEY = os.environ["OPENROUTER_API_KEY"]

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

messages = [{"role": "user", "content": "How many .py files are in this folder?"}]

payload = {
    "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "messages": messages,
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "bash",
                "description": "Run a shell command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cmd": {
                            "type": "string"
                        }
                    },
                    "required": ["cmd"]
                }
            }
        }
    ]
}

def emulate_bash(cmd):
    cmd_clean = cmd.lower()
    # Emulate unix file counting commands on Windows natively using Python glob
    if "*.py" in cmd_clean and ("wc -l" in cmd_clean or "count" in cmd_clean):
        py_files = glob.glob("*.py")
        return f"{len(py_files)}\n", ""
    
    # Fallback to subprocess execution
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr

print("Sending initial request...", flush=True)
res = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    data=json.dumps(payload),
    timeout=60
)

data = res.json()

if "choices" not in data:
    print("API Error Payload:")
    print(json.dumps(data, indent=2))
else:
    message = data["choices"][0]["message"]
    print("\nInitial Response:")
    print(json.dumps(message, indent=2))
    
    if message.get("tool_calls"):
        # Append the assistant's response to the conversation history
        messages.append(message)
        
        for tool_call in message["tool_calls"]:
            if tool_call["function"]["name"] == "bash":
                args = json.loads(tool_call["function"]["arguments"])
                cmd = args.get("cmd")
                print(f"\n[Executing Bash Command]: {cmd}")
                
                stdout, stderr = emulate_bash(cmd)
                
                print(f"[Command Output]:\n{stdout}")
                if stderr:
                    print(f"[Command Error]:\n{stderr}")
                
                # Append the tool execution result message
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": "bash",
                    "content": stdout if stdout or not stderr else stderr
                })
        
        # Send second request with tool output
        print("\nSending follow-up request with tool outputs...", flush=True)
        followup_payload = {
            "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
            "messages": messages,
            "tools": payload["tools"]
        }
        res2 = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(followup_payload),
            timeout=60
        )
        data2 = res2.json()
        if "choices" not in data2:
            print("API Error Payload in follow-up:")
            print(json.dumps(data2, indent=2))
        else:
            final_message = data2["choices"][0]["message"]
            print("\nFinal Response:")
            print(json.dumps(final_message, indent=2))
    else:
        print("\nFinal Response (No tools called):")
        print(message.get("content"))
