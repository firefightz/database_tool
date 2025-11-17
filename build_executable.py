import os
import sys
import subprocess

# --------------------------
# Configurations
# --------------------------
MAIN_SCRIPT = "main.py"        # Your main CLI script
EXECUTABLE_NAME = "admin_cli"  # Desired executable name
ENV_FILE = ".env"              # .env file to bundle
CONSOLE = True                 # True for CLI, False for GUI apps

# --------------------------
# Determine OS-specific add-data syntax
# --------------------------
if sys.platform.startswith("win"):
    # Windows uses semicolon
    add_data = f"{ENV_FILE};."
else:
    # Linux / macOS use colon
    add_data = f"{ENV_FILE}:."

# --------------------------
# PyInstaller command
# --------------------------
cmd = [
    "pyinstaller",
    "--onefile",
    f"--name={EXECUTABLE_NAME}",
    f"--add-data={add_data}"
]

if CONSOLE:
    cmd.append("--console")
else:
    cmd.append("--noconsole")

cmd.append(MAIN_SCRIPT)

# --------------------------
# Run PyInstaller
# --------------------------
print("Building executable...")
result = subprocess.run(cmd, capture_output=True, text=True)

print(result.stdout)
if result.returncode != 0:
    print("Error building executable:")
    print(result.stderr)
else:
    print(f"Executable built successfully! Check the 'dist' folder for {EXECUTABLE_NAME}")
