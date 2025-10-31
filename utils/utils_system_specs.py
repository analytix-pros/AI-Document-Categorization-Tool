import os
import sys
import json
import socket
import platform
import psutil

# ─────────────────────────────────────────────────────────────────────────────
# Set project root and change working directory
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(PROJECT_ROOT)

try:
    from utils.utils_uuid import derive_uuid
    from config.config import FULL_DATABASE_FILE_PATH
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {str(e)}")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Functions to get metadata
# ─────────────────────────────────────────────────────────────────────────────

def get_hostname():
    hostname = socket.gethostname()
    return hostname


def get_system_specs():
    """
    Retrieve system specifications including machine name, OS, CPU, cores, GPU availability,
    hard drive space, CPU utilization, processor information, and **Python version**.
    Returns a JSON-compatible dictionary.
    """
    try:
        # Initialize dictionary to store specs
        specs = {}

        # Machine name
        hostname = socket.gethostname()
        specs["hostname"] = hostname

        # Machine UUID
        specs["hostname_uuid"] = derive_uuid(hostname)

        # Operating system details
        specs["os"] = {
            "name": platform.system(),
            "version": platform.release(),
            "full_name": platform.platform()
        }

        # Python version
        specs["python"] = {
            "version": platform.python_version(),
            "version_tuple": sys.version_info[:3],  # (major, minor, micro)
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
            "build": platform.python_build()[0],
            "build_date": platform.python_build()[1]
        }

        # CPU details
        specs["cpu"] = {
            "name": platform.processor(),
            "architecture": platform.machine(),
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
            "utilization_percent": psutil.cpu_percent(interval=1)
        }

        # GPU availability (basic check)
        specs["gpu_available"] = False  # Default to False
        try:
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name'] or ""
                if 'nvidia' in proc_name.lower() or 'cuda' in proc_name.lower():
                    specs["gpu_available"] = True
                    break
        except Exception:
            specs["gpu_available"] = "Unknown (requires additional libraries for accurate detection)"

        # Hard drive space (for root directory)
        try:
            disk = psutil.disk_usage('/')
            specs["disk"] = {
                "total_mb": round(disk.total / (1024 * 1024), 2),
                "used_mb": round(disk.used / (1024 * 1024), 2),
                "free_mb": round(disk.free / (1024 * 1024), 2),
                "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                "used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                "free_gb": round(disk.free / (1024 * 1024 * 1024), 2)
            }
        except Exception as e:
            specs["disk"] = {"error": f"Could not retrieve disk info: {str(e)}"}

        # Memory information
        memory = psutil.virtual_memory()
        specs["memory"] = {
            "total_mb": round(memory.total / (1024 * 1024), 2),
            "used_mb": round(memory.used / (1024 * 1024), 2),
            "free_mb": round(memory.free / (1024 * 1024), 2),
            "total_gb": round(memory.total / (1024 * 1024 * 1024), 2),
            "used_gb": round(memory.used / (1024 * 1024 * 1024), 2),
            "free_gb": round(memory.free / (1024 * 1024 * 1024), 2)
        }

        # Additional processor info (if available)
        specs["processor_info"] = {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }

        return specs
    except Exception as e:
        return {"error": f"Failed to retrieve system specs: {str(e)}"}


# Example usage:
if __name__ == "__main__":
    print(json.dumps(get_system_specs(), indent=4, default=str))