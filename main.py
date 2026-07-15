"""
main.py


  - api.py  -> runs on an internal fixed port (8000)
  - ui.py   -> runs on Render's public $PORT, so it's the one users reach.

Render start command should be:
    python main.py

(This replaces separately running `uvicorn api:app` and `streamlit run ui.py`.)
"""

import os
import sys
import time
import subprocess
import requests

INTERNAL_API_PORT = 8000
API_HEALTH_URL = f"http://localhost:{INTERNAL_API_PORT}/health"

api_process = None


def start_api():
    global api_process
    print(f"Starting API on internal port {INTERNAL_API_PORT} (loopback only)...")
    api_process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "api:app",
            "--host", "127.0.0.1",   # loopback only - keeps Render's port scanner from seeing it
            "--port", str(INTERNAL_API_PORT),
        ]
    )


def wait_for_api(timeout=60):
    print("Waiting for API to become ready...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(API_HEALTH_URL, timeout=2)
            if r.status_code == 200:
                print("API is ready.")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("Timed out waiting for the API to start. Continuing anyway - "
          "check the API logs above for errors.")
    return False


def start_streamlit():
    public_port = os.environ.get("PORT", "8501")
    print(f"Starting Streamlit UI on public port {public_port}...")
    # Foreground: this call blocks for the lifetime of the container.
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "ui.py",
        "--server.port", public_port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
    ])


if __name__ == "__main__":
    start_api()
    wait_for_api()
    start_streamlit()

    # If Streamlit exits, clean up the API process too.
    if api_process and api_process.poll() is None:
        api_process.terminate()