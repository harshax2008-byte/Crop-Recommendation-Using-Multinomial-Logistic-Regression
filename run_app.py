"""
AgroSense AI - Application Launcher
Starts the FastAPI/Uvicorn server on http://localhost:8000
"""
import subprocess
import sys
import time
import webbrowser
import os

HOST = "127.0.0.1"
PORT = 8000
URL  = f"http://{HOST}:{PORT}"

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("   AgroSense AI — Premium Crop Recommendation Platform")
    print(f"{'='*60}")
    print(f"   Starting server at: {URL}")
    print(f"   Press Ctrl+C to stop the server.")
    print(f"{'='*60}\n")

    # Open browser after a short delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(URL)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Ensure UTF-8 in child process
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    # Start uvicorn
    subprocess.run([
        sys.executable, "-m", "uvicorn", "server:app",
        "--host", HOST,
        "--port", str(PORT),
        "--reload"
    ], env=env)

