import platform
import subprocess
import os
import shutil

def is_poppler_installed():
    """
    Check if Poppler is installed by verifying if 'pdftotext' is in PATH.
    Returns True if found, False otherwise.
    """
    return shutil.which("pdftotext") is not None

def install_poppler():
    if is_poppler_installed():
        print("Poppler is already installed and available in PATH. Skipping installation.")
        return

    print("Poppler not found in PATH. Starting installation...")
    os_name = platform.system()

    if os_name == "Windows":
        print("Installing Poppler on Windows...")
        print("For Windows, it is recommended to manually download Poppler binaries "
              "(e.g., from https://github.com/oschwartz10612/poppler-windows) "
              "and add the 'bin' directory to your system's PATH.")
        print("Alternatively, if Chocolatey is installed, run in admin terminal:")
        print("    choco install poppler-utils")
        print("Note: Automatic installation via Chocolatey is not enabled in this script "
              "to avoid requiring admin privileges in non-interactive environments.")

    elif os_name == "Darwin":  # macOS
        print("Installing Poppler on macOS...")
        try:
            # Check if Homebrew is installed
            result = subprocess.run(["brew", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                raise FileNotFoundError("Homebrew not found")

            print("Homebrew detected. Installing Poppler...")
            subprocess.run(["brew", "install", "poppler"], check=True)
            print("Poppler installed successfully via Homebrew.")
        except FileNotFoundError:
            print("Homebrew is not installed.")
            print("Please install Homebrew first: https://brew.sh")
            print("Then run: brew install poppler")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install Poppler via Homebrew: {e}")
            print("Try running 'brew install poppler' manually.")

    elif os_name == "Linux":
        print("Installing Poppler on Linux...")
        try:
            # Try to get distro info
            distro = None
            if hasattr(platform, 'freedesktop_os_release'):
                os_release = platform.freedesktop_os_release()
                distro = os_release.get('ID')
            else:
                # Fallback: check common package managers
                if shutil.which("apt-get"):
                    distro = "debian"
                elif shutil.which("pacman"):
                    distro = "arch"
        except Exception:
            distro = None

        if distro in ["ubuntu", "debian"] or shutil.which("apt-get"):
            print("Detected Debian/Ubuntu-based system. Using apt-get...")
            try:
                print("Updating package list...")
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                print("Installing poppler-utils...")
                subprocess.run(["sudo", "apt-get", "install", "-y", "poppler-utils"], check=True)
                print("Poppler installed successfully via apt.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install Poppler: {e}")
                print("Ensure you have sudo privileges and internet access.")

        elif distro == "arch" or shutil.which("pacman"):
            print("Detected Arch Linux. Using pacman...")
            try:
                subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "poppler"], check=True)
                print("Poppler installed successfully via pacman.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install Poppler: {e}")
                print("Ensure you have sudo privileges.")

        else:
            print(f"Unsupported or undetected Linux distribution: {distro}")
            print("Please install Poppler manually using your package manager.")
            print("Examples:")
            print("  Ubuntu/Debian: sudo apt-get install poppler-utils")
            print("  Arch: sudo pacman -S poppler")
            print("  Fedora: sudo dnf install poppler-utils")

    else:
        print(f"Unsupported operating system: {os_name}")
        print("Please install Poppler manually for your platform.")

    # Final check after attempted install
    if is_poppler_installed():
        print("Poppler is now available in PATH.")
    else:
        print("Warning: Poppler installation may have failed or requires restart/PATH update.")

if __name__ == "__main__":
    install_poppler()