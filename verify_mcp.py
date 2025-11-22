import json
import subprocess
import sys


def run_test():
    # Start the server
    process = subprocess.Popen(
        [sys.executable, "-m", "vibesafe.mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/home/diwank/github.com/julep-ai/vibesafe",
    )

    # 1. Initialize
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"},
    }

    # 2. List Tools
    list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

    # 3. Scan (Call Tool)
    scan_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "scan", "arguments": {}},
    }

    # Send requests
    input_str = (
        json.dumps(init_req) + "\n" + json.dumps(list_req) + "\n" + json.dumps(scan_req) + "\n"
    )
    stdout, stderr = process.communicate(input=input_str)

    print("STDERR:", stderr)

    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            resp = json.loads(line)
            print(f"Response ID {resp.get('id')}:")
            if "error" in resp:
                print("  ERROR:", resp["error"])
            else:
                print("  RESULT:", json.dumps(resp["result"], indent=2)[:200] + "...")
        except json.JSONDecodeError:
            print("  INVALID JSON:", line)


if __name__ == "__main__":
    run_test()
