#!/usr/bin/env python3
"""
One-file launcher:
  • Finds project root
  • Auto-activates .venv (or any venv)
  • Starts Ollama (if needed)
  • Runs Streamlit
Works from anywhere, frozen or not.
"""

import os, sys, subprocess, time, urllib.request
from pathlib import Path

# -------------------------------------------------
# 1. Project root (works frozen or not)
# -------------------------------------------------
ROOT = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

# -------------------------------------------------
# 2. Auto-activate virtual environment
# -------------------------------------------------
VENV = ROOT / ".venv"
if VENV.exists():
    BIN = VENV / ("Scripts" if os.name == "nt" else "bin")
    if BIN.exists():
        os.environ["PATH"] = str(BIN) + os.pathsep + os.environ.get("PATH", "")
        if os.name != "nt":
            # On Unix: also set VIRTUAL_ENV
            os.environ["VIRTUAL_ENV"] = str(VENV)
        print(f"[Activated] {VENV}")
    else:
        print(f"[Warning] .venv found but no bin/Scripts: {BIN}")
else:
    print("[No .venv] Using system Python")

# -------------------------------------------------
# 3. Start Ollama if not running
# -------------------------------------------------
def ollama_running():
    try:
        urllib.request.urlopen("http://127.0.0.1:11434", timeout=1)
        return True
    except Exception:
        return False

if not ollama_running():
    print("Starting Ollama…")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=(subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW) if os.name == "nt" else 0,
        start_new_session=os.name != "nt",
    )
    while not ollama_running():
        time.sleep(0.2)

# -------------------------------------------------
# 4. Run Streamlit with correct Python
# -------------------------------------------------
app = ROOT / "app.py"
python = sys.executable  # uses .venv/python if activated
cmd = [python, "-m", "streamlit", "run", str(app)]

print(f"Launching: {' '.join(cmd)}")
try:
    subprocess.run(cmd, check=True)
except FileNotFoundError:
    print("Streamlit missing → run: pip install streamlit")
    sys.exit(1)