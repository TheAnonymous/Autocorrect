#!/usr/bin/env python3

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

try:
    import pystray
    from PIL import Image, ImageDraw
    from pystray import MenuItem, Menu
except ImportError:
    print("Fehler: pystray und Pillow werden benoetigt.", file=sys.stderr)
    print("Installiere mit: pip install pystray Pillow", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))
from i18n import tr
import ollama_manager as manager

TUI_SCRIPT = SCRIPT_DIR / "ollama_tui.py"
POLL_INTERVAL = 5
ICON_SIZE = 24

MODEL_CONFIG = Path.home() / ".config" / "autocorrect" / "model"

_OLLAMA_RUNNING: bool = False
_icon: Optional[pystray.Icon] = None

MODEL_PRESETS: dict[str, str] = {
    "gemma4:e2b": "Gemma 4 (2B)",
    "qwen3.5:0.8b": "Qwen 3.5 (0.8B)",
    "qwen3.5:2b": "Qwen 3.5 (2B)",
}


def _get_current_model() -> str:
    default = os.environ.get("AUTOCORRECT_MODEL", "gemma4:e2b")
    if MODEL_CONFIG.exists():
        return MODEL_CONFIG.read_text().strip()
    return default


def _set_model(name: str) -> None:
    MODEL_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    MODEL_CONFIG.write_text(name)
    subprocess.run(
        ["notify-send", tr("app_name"), tr("model_changed", name), "-t", "2000"],
        capture_output=True
    )
    if _icon:
        _icon.update_menu()


def _action_model_preset(name: str):
    def _inner() -> None:
        _set_model(name)
    return _inner


def _action_model_custom() -> None:
    subprocess.Popen(
        [sys.executable, str(TUI_SCRIPT)],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _make_icon(color: str) -> Image.Image:
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy, r = ICON_SIZE // 2, ICON_SIZE // 2, ICON_SIZE // 2 - 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline="white", width=1)
    return img


def _icon_green() -> Image.Image:
    return _make_icon("#4ade80")


def _icon_red() -> Image.Image:
    return _make_icon("#f87171")


def _run_manager(action: str) -> str:
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "ollama_manager.py"), action],
            capture_output=True, text=True, timeout=60
        )
        return result.stdout.strip() or result.stderr.strip() or "done"
    except Exception as e:
        return str(e)


def _action_start() -> None:
    _run_manager("start")


def _action_stop() -> None:
    _run_manager("stop")


def _action_restart() -> None:
    _run_manager("stop")
    time.sleep(1)
    _run_manager("start")


def _action_open_tui() -> None:
    if TUI_SCRIPT.exists():
        subprocess.Popen(
            [sys.executable, str(TUI_SCRIPT)],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def _poll_loop() -> None:
    global _OLLAMA_RUNNING
    while True:
        running = manager.is_running()
        if running != _OLLAMA_RUNNING:
            _OLLAMA_RUNNING = running
            if _icon:
                _icon.icon = _icon_green() if running else _icon_red()
                _icon.update_menu()
        time.sleep(POLL_INTERVAL)


def _build_menu() -> Menu:
    status_label = tr("tray_running") if _OLLAMA_RUNNING else tr("tray_stopped")
    current_model = _get_current_model()

    model_items = [
        MenuItem(
            f"{'\u2713 ' if current_model == m else '  '}{label}",
            _action_model_preset(m),
            enabled=(current_model != m),
        )
        for m, label in MODEL_PRESETS.items()
    ]

    return Menu(
        MenuItem(status_label, lambda: None, enabled=False),
        MenuItem("---", None),
        MenuItem(tr("tray_shortcut"), lambda: None, enabled=False),
        MenuItem("---", None),
        MenuItem(tr("tray_start"), _action_start, enabled=not _OLLAMA_RUNNING),
        MenuItem(tr("tray_stop"), _action_stop, enabled=_OLLAMA_RUNNING),
        MenuItem(tr("tray_restart"), _action_restart, enabled=_OLLAMA_RUNNING),
        MenuItem("---", None),
        MenuItem(
            f"{tr('menu_model')}: {current_model}",
            None,
            enabled=False,
        ),
        MenuItem(
            tr("menu_model"),
            None,
            menu=Menu(
                *model_items,
                MenuItem("---", None),
                MenuItem(tr("model_custom"), _action_model_custom),
            ),
        ),
        MenuItem("---", None),
        MenuItem(tr("tray_open_tui"), _action_open_tui),
        MenuItem(tr("tray_quit"), lambda: _icon.stop()),
    )


def main() -> None:
    global _icon, _OLLAMA_RUNNING

    _OLLAMA_RUNNING = manager.is_running()
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
