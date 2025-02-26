"""
GUI launcher for VHS Tape Scanner.
"""
import os
import sys
from pathlib import Path
import subprocess

def launch_gui():
    """Launch the PyQt GUI."""
    try:
        # Get script path
        script_path = os.path.join(os.path.dirname(__file__), "..", "run_gui.py")
        
        # Launch PyQt interface
        subprocess.Popen([sys.executable, script_path])
            
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)

def main():
    """Launch the GUI."""
    launch_gui()

if __name__ == "__main__":
    sys.exit(main())
