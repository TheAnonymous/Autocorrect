#!/usr/bin/env python3

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))
from i18n import tr

MODEL_CONFIG = Path.home() / ".config" / "autocorrect" / "model"
if MODEL_CONFIG.exists():
    MODEL = MODEL_CONFIG.read_text().strip()
else:
    MODEL = os.environ.get("AUTOCORRECT_MODEL", "gemma4:e2b")

OLLAMA_BASE = os.environ.get("AUTOCORRECT_OLLAMA_BASE", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_BASE}/api/generate"
COPY_PASTE_DELAY = float(os.environ.get("AUTOCORRECT_DELAY", "0.2"))
CURL_TIMEOUT = int(os.environ.get("AUTOCORRECT_CURL_TIMEOUT", "60"))
MAX_RETRIES = int(os.environ.get("AUTOCORRECT_MAX_RETRIES", "3"))

STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "autocorrect"
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = STATE_DIR / "autocorrect.log"
ORIGINAL_FILE = STATE_DIR / "last_original.txt"

REQUIRED_CMDS = ["wl-copy", "wl-paste", "wtype", "curl", "notify-send"]


def log_msg(msg: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")


def notify_err(msg: str) -> None:
    log_msg(f"ERROR: {msg}")
    subprocess.run(["notify-send", tr("app_name"), msg, "-u", "critical"],
                   capture_output=True)


def notify_info(msg: str) -> None:
    subprocess.run(["notify-send", tr("app_name"), msg, "-t", "2000"],
                   capture_output=True)


def log_debug(msg: str) -> None:
    if os.environ.get("AUTOCORRECT_DEBUG") == "1":
        print(f"[DEBUG] {msg}", file=sys.stderr)
        log_msg(f"DEBUG: {msg}")


def detect_language(text: str) -> str:
    lower = text.lower()
    score = 0

    if re.search(r'[äöüß]', lower):
        score += 3

    for word in ["der", "die", "das", "und", "ist", "ein", "eine", "nicht", "mit", "von", "dem", "den"]:
        if re.search(rf'\b{word}\b', lower):
            score += 1

    for word in ["the", "and", "is", "not", "with", "from", "that", "this", "have"]:
        if re.search(rf'\b{word}\b', lower):
            score -= 1

    return "de" if score > 0 else "en"


def get_system_prompt(lang: str) -> str:
    return "You are a pure autocorrection tool. Correct the text for spelling and grammar. Keep the original language. Output ONLY the corrected text, without introduction, explanations, or quotation marks."


def check_dependencies() -> None:
    for cmd in REQUIRED_CMDS:
        if not shutil.which(cmd):
            notify_err(tr("err_cmd_missing", cmd))
            sys.exit(1)


def check_ollama() -> None:
    try:
        result = subprocess.run(
            ["curl", "-sf", "--max-time", "5", f"{OLLAMA_BASE}/api/tags"],
            capture_output=True, timeout=7
        )
        if result.returncode != 0:
            notify_err(tr("err_ollama_unreachable", OLLAMA_URL))
            sys.exit(1)
    except Exception:
        notify_err(tr("err_ollama_unreachable", OLLAMA_URL))
        sys.exit(1)


def is_model_loaded() -> bool:
    try:
        result = subprocess.run(
            ["curl", "-sf", "--max-time", "2", f"{OLLAMA_BASE}/api/ps"],
            capture_output=True, text=True, timeout=4
        )
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            return any(m.get("name") == MODEL for m in data.get("models", []))
    except Exception:
        pass
    return False


def wtype_ctrl_key(key: str) -> None:
    subprocess.run(["wtype", "-M", "ctrl", "-P", key, "-p", key, "-m", "ctrl"],
                   capture_output=True)


def get_clipboard_text() -> tuple[str, Optional[str]]:
    result = subprocess.run(["wl-paste", "-n"], capture_output=True, text=True)
    text = result.stdout.strip()
    if text:
        return text, "clipboard"

    result = subprocess.run(["wl-paste", "-n", "--primary"], capture_output=True, text=True)
    text = result.stdout.strip()
    if text:
        return text, "primary"

    return "", None


def clean_response(text: str) -> str:
    text = text.strip()

    text = re.sub(r'^```(?:\w+)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)

    text = re.sub(r'^[""\u201e]', '', text)
    text = re.sub(r'[""\u201c]$', '', text)

    text = text.strip()
    return text


def send_request(payload: dict, attempt: int = 0) -> tuple[Optional[dict], Optional[str]]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        curl_result = subprocess.run(
            ["curl", "-s", "-w", "%{http_code}", "-o", tmp_path,
             "--max-time", str(CURL_TIMEOUT),
             "-X", "POST", OLLAMA_URL,
             "-H", "Content-Type: application/json",
             "-d", json.dumps(payload)],
            capture_output=True, text=True, timeout=CURL_TIMEOUT + 10
        )
        http_code = curl_result.stdout.strip()[-3:]

        if http_code != "200":
            os.unlink(tmp_path)
            return None, http_code

        with open(tmp_path) as f:
            response_data = json.load(f)
        os.unlink(tmp_path)
        return response_data, None
    except subprocess.TimeoutExpired:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def main() -> None:
    check_dependencies()
    check_ollama()

    wtype_ctrl_key("c")
    time.sleep(COPY_PASTE_DELAY)

    original_text, source = get_clipboard_text()

    if not original_text:
        notify_info(tr("no_text"))
        sys.exit(0)

    log_msg(f"Input (from {source}): {original_text[:200]}...")

    ORIGINAL_FILE.write_text(original_text)

    detected_lang = detect_language(original_text)
    log_debug(f"Detected language: {detected_lang}")

    if not is_model_loaded():
        notify_info(f"{MODEL}: loading...")
    else:
        notify_info(tr("correcting"))

    system_instruction = get_system_prompt(detected_lang)

    payload = {
        "model": MODEL,
        "system": system_instruction,
        "prompt": original_text,
        "stream": False,
        "options": {"temperature": 0}
    }

    response_data = None
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response_data, http_code = send_request(payload, attempt)
            if response_data is not None:
                break
            if http_code == "503" or http_code == "429":
                wait_time = (2 ** attempt) * 2
                log_debug(f"Ollama busy (HTTP {http_code}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            log_debug(f"HTTP Response: {http_code}")
            notify_err(tr("err_ollama_http", http_code))
            sys.exit(1)
        except subprocess.TimeoutExpired:
            last_error = "timeout"
            if attempt < MAX_RETRIES - 1:
                wait_time = (2 ** attempt) * 2
                log_debug(f"Request timed out, retrying in {wait_time}s...")
                time.sleep(wait_time)
            continue
        except Exception as e:
            last_error = str(e)
            if attempt < MAX_RETRIES - 1:
                wait_time = (2 ** attempt) * 2
                log_debug(f"Error: {e}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            continue

    if response_data is None:
        if last_error == "timeout":
            notify_err(tr("err_timeout"))
        else:
            notify_err(tr("err_ollama_response", str(last_error)[:80]))
        sys.exit(1)

    error_msg = response_data.get("error", "")
    if error_msg:
        log_debug(f"Ollama Error: {error_msg}")
        notify_err(tr("err_ollama_response", error_msg[:80]))
        sys.exit(1)

    corrected_text = clean_response(response_data.get("response", ""))

    if not corrected_text:
        notify_err(tr("err_empty_response"))
        sys.exit(1)

    log_debug(f"Corrected: {corrected_text[:200]}...")
    log_msg(f"Output: {corrected_text[:200]}...")

    subprocess.run(["wl-copy"], input=corrected_text, text=True, capture_output=True)
    time.sleep(COPY_PASTE_DELAY)

    wtype_ctrl_key("v")

    if original_text == corrected_text:
        notify_info(tr("already_correct"))
    else:
        subprocess.run(["wl-copy"], input=original_text, text=True, capture_output=True)
        notify_info(tr("correction_done"))


if __name__ == "__main__":
    main()


