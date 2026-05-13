import subprocess
import sys
import os

if __name__ == "__main__":
    app_path = os.path.join("streamlit", "home.py")

    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        app_path
    ])
