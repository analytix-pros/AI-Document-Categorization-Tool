#!/usr/bin/env python3
"""
requirements_audit.py

Audit a requirements.txt against:
  1) A project virtual environment at ./.venv
  2) The PATH-level Python (whatever `python` resolves to)

Outputs a CSV report at ./tmp/requirements_audit.csv
"""

import argparse
import csv
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# -------------------------------------------------
# 1. Project root (works frozen or not)
# -------------------------------------------------
ROOT = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

# -------- Configurable variables --------
DEFAULT_REQUIREMENTS_FILE = ROOT / "requirements.txt"   # <-- change this if needed
DEFAULT_VENV_DIR = ROOT / ".venv"

print(f"DEFAULT_REQUIREMENTS_FILE: {DEFAULT_REQUIREMENTS_FILE}\nDEFAULT_VENV_DIR: {DEFAULT_VENV_DIR}")

# -------- Utils --------

def pep503_normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()

def strip_extras(req_name: str) -> str:
    return re.sub(r"\[.*\]$", "", req_name)

def parse_requirements(req_path: str) -> List[Tuple[str, str]]:
    if not os.path.exists(req_path):
        raise FileNotFoundError(f"requirements file not found: {req_path}")
    results: List[Tuple[str, str]] = []
    with open(req_path, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            m = re.match(r"^\s*([A-Za-z0-9_.-]+(\[.*?\])?)", raw)
            if not m:
                results.append((raw, pep503_normalize(raw)))
                continue
            name = strip_extras(m.group(1))
            results.append((raw, pep503_normalize(name)))
    return results

def find_venv_python(venv_dir: str) -> str:
    if platform.system() == "Windows":
        candidate = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        candidate = os.path.join(venv_dir, "bin", "python")
    if not os.path.exists(candidate):
        raise FileNotFoundError(
            f"Could not find Python in virtual environment at: {candidate}"
        )
    return candidate

def find_path_python() -> str:
    exe = shutil.which("python")
    if exe:
        return exe
    if platform.system() == "Windows":
        py_launcher = shutil.which("py")
        if py_launcher:
            return py_launcher
    raise FileNotFoundError("No PATH-level Python found (tried `python` and `py`).")

def get_installed_map(python_exec: str) -> Dict[str, str]:
    if os.path.basename(python_exec).lower() == "py":
        cmd = [python_exec, "-3", "-c", _METADATA_SNIPPET]
    else:
        cmd = [python_exec, "-c", _METADATA_SNIPPET]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to query installed packages for {python_exec}:\n{e.output}"
        ) from e
    data = json.loads(out)
    return {pep503_normalize(k): v for k, v in data.items()}

_METADATA_SNIPPET = r"""
import json, sys
try:
    import importlib.metadata as m
except Exception:
    import importlib_metadata as m  # type: ignore
d = {dist.metadata['Name']: dist.version for dist in m.distributions() if dist.metadata and dist.metadata.get('Name')}
print(json.dumps(d))
"""

def ensure_tmp_dir() -> str:
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    return tmp_dir

# -------- Main audit logic --------

def audit_requirements(req_path: str, venv_dir: str) -> str:
    reqs = parse_requirements(req_path)
    if not reqs:
        raise ValueError("No requirements found after parsing (file may be empty).")
    venv_python = find_venv_python(venv_dir)
    path_python = find_path_python()
    venv_installed = get_installed_map(venv_python)
    path_installed = get_installed_map(path_python)

    rows = []
    for raw, norm_name in reqs:
        venv_ver = venv_installed.get(norm_name)
        path_ver = path_installed.get(norm_name)
        rows.append({
            "requirement_line": raw,
            "package": norm_name,
            "in_venv": "Yes" if venv_ver else "No",
            "venv_version": venv_ver or "",
            "in_path": "Yes" if path_ver else "No",
            "path_version": path_ver or "",
            "venv_python": venv_python,
            "path_python": path_python,
        })

    tmp_dir = ensure_tmp_dir()
    csv_path = os.path.join(tmp_dir, "requirements_audit.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "requirement_line",
                "package",
                "in_venv",
                "venv_version",
                "in_path",
                "path_version",
                "venv_python",
                "path_python",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return csv_path

# -------- CLI --------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit requirements against .venv and PATH-level Python."
    )
    parser.add_argument(
        "--req",
        default=DEFAULT_REQUIREMENTS_FILE,
        help=f"Path to requirements.txt (default: {DEFAULT_REQUIREMENTS_FILE})",
    )
    parser.add_argument(
        "--venv",
        default=DEFAULT_VENV_DIR,
        help=f"Path to the virtual environment directory (default: {DEFAULT_VENV_DIR})",
    )

    args = parser.parse_args(argv)
    try:
        audit_requirements(args.req, args.venv)
    except Exception as e:
        raise
    return 0

if __name__ == "__main__":
    sys.exit(main())