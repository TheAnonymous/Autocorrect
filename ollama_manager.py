#!/usr/bin/env python3

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

OLLAMA_SERVICE = "ollama"
OLLAMA_URL = "http://localhost:11434"


def is_running() -> bool:
    try:
        result = subprocess.run(
            ["curl", "-sf", "--max-time", "3", f"{OLLAMA_URL}/api/tags"],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def is_service_active() -> bool:
    for scope in ["--user", ""]:
        try:
            result = subprocess.run(
                ["systemctl"] + ([scope] if scope else []) + ["is-active", OLLAMA_SERVICE],
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass
    return False


def get_service_type() -> str:
    for scope, label in [("--user", "user"), ("", "system")]:
        try:
            cmd = ["systemctl"] + ([scope] if scope else []) + ["is-enabled", OLLAMA_SERVICE]
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            if result.returncode == 0:
                return label
        except Exception:
            pass
    return "none"


def get_memory_usage() -> str:
    try:
        result = subprocess.run(
            ["pgrep", "-f", "ollama serve"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return "0"
        pid = result.stdout.strip().split("\n")[0]
        ps_result = subprocess.run(
            ["ps", "-o", "rss=", "-p", pid],
            capture_output=True, text=True, timeout=5
        )
        rss_kb = ps_result.stdout.strip()
        if rss_kb:
            return str(int(rss_kb) // 1024)
        return "?"
    except Exception:
        return "0"


def get_model_info() -> list[str]:
    if not is_running():
        return []
    try:
        result = subprocess.run(
            ["curl", "-sf", "--max-time", "3", f"{OLLAMA_URL}/api/tags"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            return [m["name"] for m in data.get("models", []) if m.get("name")][:5]
    except Exception:
        pass
    return []


def status() -> None:
    if is_running():
        mem = get_memory_usage()
        svc_type = get_service_type()
        models = get_model_info()
        print("running")
        print(f"memory_mb={mem}")
        print(f"service_type={svc_type}")
        if models:
            print(f"models={','.join(models)}")
    elif is_service_active():
        print("service_active_no_response")
    else:
        print("stopped")


def start() -> bool:
    if is_running():
        print("already_running")
        return True

    svc_type = get_service_type()

    if svc_type != "none":
        try:
            if svc_type == "user":
                subprocess.run(["systemctl", "--user", "start", OLLAMA_SERVICE],
                             capture_output=True, timeout=10)
            else:
                subprocess.run(["sudo", "systemctl", "start", OLLAMA_SERVICE],
                             capture_output=True, timeout=10)
        except Exception:
            pass
    else:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

    retries = 30
    while retries > 0:
        if is_running():
            print("started")
            return True
        time.sleep(1)
        retries -= 1

    print("start_timeout")
    return False


def stop() -> bool:
    if not is_running():
        print("already_stopped")
        return True

    svc_type = get_service_type()

    if svc_type != "none":
        try:
            if svc_type == "user":
                subprocess.run(["systemctl", "--user", "stop", OLLAMA_SERVICE],
                             capture_output=True, timeout=10)
            else:
                subprocess.run(["sudo", "systemctl", "stop", OLLAMA_SERVICE],
                             capture_output=True, timeout=10)
        except Exception:
            pass

    try:
        result = subprocess.run(
            ["pgrep", "-f", "ollama serve"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            pid = result.stdout.strip().split("\n")[0]
            os.kill(int(pid), signal.SIGTERM)
    except Exception:
        pass

    retries = 15
    while retries > 0:
        if not is_running():
            print("stopped")
            return True
        time.sleep(1)
        retries -= 1

    try:
        result = subprocess.run(
            ["pgrep", "-f", "ollama serve"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            pid = result.stdout.strip().split("\n")[0]
            os.kill(int(pid), signal.SIGKILL)
    except Exception:
        pass

    print("force_stopped")
    return True


def restart() -> None:
    stop()
    time.sleep(1)
    start()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    actions: dict[str, callable] = {
        "status": status,
        "start": start,
        "stop": stop,
        "restart": restart,
    }
    if cmd in actions:
        actions[cmd]()
    else:
        print(f"Usage: {sys.argv[0]} {{status|start|stop|restart}}", file=sys.stderr)
        sys.exit(1)
