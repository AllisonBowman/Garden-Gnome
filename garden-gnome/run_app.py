"""Standalone launcher for the Garden Gnome desktop app.

Bundled into a single .exe via PyInstaller (see build_exe.ps1). Also runs
directly in dev mode: `python run_app.py`.

The working directory is set to wherever the exe (or this script) lives, so
garden_gnome.db and an optional .env file live alongside it and persist
across runs -- not inside PyInstaller's temp extraction folder.
"""
import os
import sys
import threading
import time
import uuid
import webbrowser


def _app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = _app_dir()
os.chdir(APP_DIR)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(APP_DIR, ".env"))  # no-op if the file doesn't exist


def _ensure_installation_uuid() -> None:
    """Generate a stable UUID for this installation on first run and persist
    it to .env so it survives restarts. Used to identify which installation
    created a stewardship record in the census without exposing user identity."""
    if os.getenv("INSTALLATION_UUID"):
        return
    new_uuid = str(uuid.uuid4())
    env_path = os.path.join(APP_DIR, ".env")
    with open(env_path, "a", encoding="utf-8") as f:
        f.write(f"\nINSTALLATION_UUID={new_uuid}\n")
    os.environ["INSTALLATION_UUID"] = new_uuid
    print(f"Generated installation UUID: {new_uuid}")


_ensure_installation_uuid()

import uvicorn  # noqa: E402

from app.main import app  # noqa: E402
from app.data.seed import seed  # noqa: E402


def _open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000/ui/")


if __name__ == "__main__":
    print("Garden Gnome starting...")
    seed()
    threading.Thread(target=_open_browser, daemon=True).start()
    print("Opening http://127.0.0.1:8000/ui/ in your browser.")
    print("Close this window (or press Ctrl+C) to stop the server.")
    uvicorn.run(app, host="127.0.0.1", port=8000)
