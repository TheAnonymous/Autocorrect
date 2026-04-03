#!/usr/bin/env python3

import locale
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw
    from pystray import MenuItem, Menu
except ImportError:
    print("Fehler: pystray und Pillow werden benoetigt.", file=sys.stderr)
    print("Installiere mit: pip install pystray Pillow", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent.resolve()
MANAGER = SCRIPT_DIR / "ollama-manager.sh"
TUI_SCRIPT = SCRIPT_DIR / "ollama-tui.sh"
OLLAMA_URL = "http://localhost:11434"
POLL_INTERVAL = 5
ICON_SIZE = 24

_LANG = locale.getlocale()[0]
if _LANG and _LANG.startswith("de"):
    _LANG = "de"
else:
    _LANG = "en"

_OLLAMA_RUNNING = False
_icon = None


def _tr(key):
    t = {
        "tray_running": ("Ollama: Laeuft", "Ollama: Running"),
        "tray_stopped": ("Ollama: Gestoppt", "Ollama: Stopped"),
        "tray_start": ("Starten", "Start"),
        "tray_stop": ("Stoppen", "Stop"),
        "tray_restart": ("Neustarten", "Restart"),
        "tray_open_tui": ("TUI oeffnen", "Open TUI"),
        "tray_quit": ("Beenden", "Quit"),
        "tray_err_deps": ("Fehler: pystray und Pillow werden benoetigt.",
                           "Error: pystray and Pillow are required."),
        "tray_err_install": ("Installiere mit: pip install pystray Pillow",
                              "Install with: pip install pystray Pillow"),
    }
    idx = 0 if _LANG == "de" else 1
    return t.get(key, (key, key))[idx]


def _is_running():
    try:
        result = subprocess.run(
            ["curl", "-sf", "--max-time", "3", f"{OLLAMA_URL}/api/tags"],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def _make_icon(color):
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy, r = ICON_SIZE // 2, ICON_SIZE // 2, ICON_SIZE // 2 - 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline="white", width=1)
    return img


def _icon_green():
    return _make_icon("#4ade80")


def _icon_red():
    return _make_icon("#f87171")


def _run_manager(action):
    try:
        result = subprocess.run(
            ["bash", str(MANAGER), action],
            capture_output=True, text=True, timeout=60
        )
        return result.stdout.strip() or result.stderr.strip() or "done"
    except Exception as e:
        return str(e)


def _action_start():
    _run_manager("start")


def _action_stop():
    _run_manager("stop")


def _action_restart():
    _run_manager("stop")
    time.sleep(1)
    _run_manager("start")


def _action_open_tui():
    if TUI_SCRIPT.exists():
        subprocess.Popen(
            ["bash", str(TUI_SCRIPT)],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def _poll_loop():
    global _OLLAMA_RUNNING
    while True:
        running = _is_running()
        if running != _OLLAMA_RUNNING:
            _OLLAMA_RUNNING = running
            if _icon:
                _icon.icon = _icon_green() if running else _icon_red()
                _icon.update_menu()
        time.sleep(POLL_INTERVAL)


def _build_menu():
    status_label = _tr("tray_running") if _OLLAMA_RUNNING else _tr("tray_stopped")

    return Menu(
        MenuItem(status_label, lambda: None, enabled=False),
        MenuItem("---", None),
        MenuItem(_tr("tray_start"), _action_start, enabled=not _OLLAMA_RUNNING),
        MenuItem(_tr("tray_stop"), _action_stop, enabled=_OLLAMA_RUNNING),
        MenuItem(_tr("tray_restart"), _action_restart, enabled=_OLLAMA_RUNNING),
        MenuItem("---", None),
        MenuItem(_tr("tray_open_tui"), _action_open_tui),
        MenuItem(_tr("tray_quit"), lambda: _icon.stop()),
    )


def main():
    global _icon, _OLLAMA_RUNNING

    _OLLAMA_RUNNING = _is_running()
    icon_img = _icon_green() if _OLLAMA_RUNNING else _icon_red()

    _icon = pystray.Icon(
        "ollama-tray",
        icon_img,
        "Ollama Manager",
        _build_menu(),
    )

    poll_thread = threading.Thread(target=_poll_loop, daemon=True)
    poll_thread.start()

    _icon.run()


if __name__ == "__main__":
    main()
