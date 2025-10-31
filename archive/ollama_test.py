import shutil, subprocess
print("ollama path:", shutil.which("ollama"))

# ollama_langchain_demo_fixed.py
import subprocess
import time
import sys
import json
from pathlib import Path

# ----------------------------------------------------------------------
# 1. Install required packages
# ----------------------------------------------------------------------
def ensure_packages():
    import importlib.util
    required = ["langchain", "langchain-ollama"]
    missing = []
    for pkg in required:
        if importlib.util.find_spec(pkg.replace("-", "_")) is None:
            missing.append(pkg)
    if missing:
        print(f"Installing: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        print("Installed. Re-run the script.")
        sys.exit(0)

ensure_packages()

# ----------------------------------------------------------------------
# 2. Imports
# ----------------------------------------------------------------------
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

# ----------------------------------------------------------------------
# 3. Find Ollama binary
# ----------------------------------------------------------------------
def find_ollama():
    import shutil
    path = shutil.which("ollama")
    if not path:
        raise RuntimeError("Ollama not found in PATH. Install from https://ollama.com")
    print(f"ollama path: {path}")
    return path

OLLAMA_CMD = find_ollama()

# ----------------------------------------------------------------------
# 4. Pull model using subprocess (most reliable)
# ----------------------------------------------------------------------
MODEL = "llama3"

def pull_model():
    print(f"Pulling model '{MODEL}' using `ollama pull`...")
    try:
        result = subprocess.run(
            [OLLAMA_CMD, "pull", MODEL],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print("Pull completed!")
        for line in result.stdout.splitlines():
            if "pulling" in line.lower() or "verifying" in line.lower() or "downloaded" in line.lower():
                print(f"   {line.strip()}")
    except subprocess.CalledProcessError as e:
        print("Pull failed:")
        print(e.stdout)
        raise

def is_model_available():
    result = subprocess.run(
        [OLLAMA_CMD, "list", "--json"],
        capture_output=True,
        text=True
    )
    try:
        data = json.loads(result.stdout)
        return any(m["name"].startswith(MODEL + ":") or m["name"] == MODEL for m in data.get("models", []))
    except:
        return False

# ----------------------------------------------------------------------
# 5. Start Ollama server if not running
# ----------------------------------------------------------------------
def start_ollama_server():
    import psutil
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'ollama':
            print("Ollama server already running.")
            return
    print("Starting Ollama server in background...")
    subprocess.Popen([OLLAMA_CMD, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ----------------------------------------------------------------------
# 6. Main
# ----------------------------------------------------------------------
if __name__ == "__main__":
    start_ollama_server()
    time.sleep(2)  # Give server time to start

    if not is_model_available():
        pull_model()
    else:
        print(f"Model '{MODEL}' already available.")

    # ------------------------------------------------------------------
    # 7. Run LangChain
    # ------------------------------------------------------------------
    print("\nInitializing LangChain...")
    llm = OllamaLLM(model=MODEL)
    prompt = PromptTemplate.from_template("Tell me a fun fact about {topic}.")
    chain = prompt | llm

    topic = "penguins"
    print(f"\nGenerating fun fact about: {topic}")
    response = chain.invoke({"topic": topic})
    print("\nResponse:")
    print(response)