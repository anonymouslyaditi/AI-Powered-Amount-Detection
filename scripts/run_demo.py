"""Run local FastAPI demo and optionally expose via ngrok.

Usage:
    python scripts/run_demo.py [--host HOST] [--port PORT] [--ngrok]

Examples (PowerShell):
    python .\scripts\run_demo.py --port 8000 --ngrok

Notes:
- Requires `pyngrok` if using --ngrok. You can install it with `pip install pyngrok`.
- This script starts uvicorn as a subprocess so you can see logs in the console.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
import time


def start_uvicorn(host: str, port: int):
    cmd = [sys.executable, "-m", "uvicorn", "app:app", "--host", host, "--port", str(port)]
    # Use --reload when running locally for development
    print(f"Starting uvicorn on http://{host}:{port}")
    proc = subprocess.Popen(cmd)
    return proc


def start_ngrok(port: int):
    try:
        from pyngrok import ngrok
    except Exception as e:
        print("pyngrok is not installed. Install with: pip install pyngrok")
        return None

    # Start an HTTP tunnel
    public_url = ngrok.connect(port, "http")
    return public_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--ngrok", action="store_true", help="Expose the local server with ngrok")
    args = parser.parse_args()

    uvicorn_proc = start_uvicorn(args.host, args.port)
    public_url = None
    try:
        if args.ngrok:
            public_url = start_ngrok(args.port)
            if public_url:
                print("ngrok public URL:", public_url)

        # Wait for uvicorn to exit (Ctrl+C)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        if uvicorn_proc and uvicorn_proc.poll() is None:
            uvicorn_proc.terminate()
            uvicorn_proc.wait()
        if public_url:
            try:
                from pyngrok import ngrok

                ngrok.disconnect(public_url)
            except Exception:
                pass


if __name__ == "__main__":
    main()
