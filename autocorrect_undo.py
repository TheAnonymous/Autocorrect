#!/usr/bin/env python3

import subprocess
import sys
import time
from pathlib import Path

STATE_DIR = Path.home() / ".local" / "state" / "autocorrect"
ORIGINAL_FILE = STATE_DIR / "last_original.txt"


def wtype_ctrl_key(key: str) -> None:
    subprocess.run(["wtype", "-M", "ctrl", "-P", key, "-p", key, "-m", "ctrl"],
                   capture_output=True)


def main() -> None:
    if not ORIGINAL_FILE.exists():
        subprocess.run(
            ["notify-send", "Autocorrect", "Nothing to undo.", "-t", "2000"],
            capture_output=True
        )
        sys.exit(0)

    original_text = ORIGINAL_FILE.read_text()

    if not original_text:
        subprocess.run(
            ["notify-send", "Autocorrect", "Nothing to undo.", "-t", "2000"],
            capture_output=True
        )
        sys.exit(0)

    subprocess.run(["wl-copy"], input=original_text, text=True, capture_output=True)
    time.sleep(0.2)
    wtype_ctrl_key("v")

    ORIGINAL_FILE.unlink()

    subprocess.run(
        ["notify-send", "Autocorrect", "Original restored.", "-t", "2000"],
        capture_output=True
    )


if __name__ == "__main__":
    main()
