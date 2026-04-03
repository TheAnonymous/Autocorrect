#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))
from i18n import tr
import ollama_manager as manager

DIALOG_CMD = shutil.which("dialog") or shutil.which("whiptail")

if not DIALOG_CMD:
    print("Fehler: Weder 'dialog' noch 'whiptail' gefunden.", file=sys.stderr)
    sys.exit(1)


def run_dialog(*args):
    cmd = [DIALOG_CMD, "--stdout"] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


def run_dialog_nostdout(*args):
    cmd = [DIALOG_CMD] + list(args)
    try:
        subprocess.run(cmd, capture_output=True, text=True)
        return True
    except Exception:
        return False


def get_status_line():
    status_output = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "ollama_manager.py"), "status"],
        capture_output=True, text=True, timeout=10
    ).stdout.strip()
    state = status_output.split("\n")[0] if status_output else "stopped"

    if state == "running":
        for line in status_output.split("\n"):
            if line.startswith("memory_mb="):
                mem = line.split("=")[1]
                return tr("status_running", mem)
        return tr("status_running", "?")
    elif state == "stopped":
        return tr("status_stopped")
    else:
        return tr("status_unknown", state)


def get_models_list():
    if not manager.is_running():
        return "(Ollama nicht gestartet)"
    models = manager.get_model_info()
    return ", ".join(models) if models else "(keine Modelle)"


def main_menu():
    while True:
        status_line = get_status_line()
        models = get_models_list()

        choice = run_dialog(
            "--title", tr("ollama_manager"),
            "--menu", f"{status_line}\n\nGeladene Modelle:\n  {models}",
            "18", "60", "8",
            "1", tr("menu_start"),
            "2", tr("menu_stop"),
            "3", tr("menu_restart"),
            "4", tr("menu_models"),
            "5", tr("menu_pull"),
            "6", tr("menu_remove"),
            "7", tr("menu_ac_status"),
            "8", tr("menu_model"),
            "9", tr("menu_exit"),
        )

        if choice is None:
            return

        actions = {
            "1": action_start,
            "2": action_stop,
            "3": action_restart,
            "4": action_models,
            "5": action_pull_model,
            "6": action_remove_model,
            "7": action_autocorrect_status,
            "8": action_model_select,
            "9": lambda: None,
        }

        if choice in actions:
            if choice == "9":
                return
            actions[choice]()


def action_start():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "ollama_manager.py"), "start"],
        capture_output=True, text=True, timeout=60
    ).stdout.strip()

    if result == "already_running":
        run_dialog_nostdout("--title", tr("info"), "--msgbox", tr("already_running"), "8", "50")
    elif result == "started":
        run_dialog_nostdout("--title", tr("success"), "--msgbox", tr("started"), "8", "50")
    else:
        run_dialog_nostdout("--title", tr("error"), "--msgbox",
                           f"{tr('start_failed')}\n\n{result}", "10", "60")


def action_stop():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "ollama_manager.py"), "stop"],
        capture_output=True, text=True, timeout=60
    ).stdout.strip()

    if result == "already_stopped":
        run_dialog_nostdout("--title", tr("info"), "--msgbox", tr("already_stopped"), "8", "50")
    else:
        run_dialog_nostdout("--title", tr("success"), "--msgbox", tr("stopped"), "8", "50")


def action_restart():
    run_dialog_nostdout("--title", tr("menu_restart"), "--infobox", tr("restarting"), "8", "50")
    time.sleep(1)
    subprocess.run([sys.executable, str(SCRIPT_DIR / "ollama_manager.py"), "stop"],
                   capture_output=True, timeout=30)
    time.sleep(1)
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "ollama_manager.py"), "start"],
        capture_output=True, text=True, timeout=60
    ).stdout.strip()

    if result == "started":
        run_dialog_nostdout("--title", tr("success"), "--msgbox", tr("restart_done"), "8", "50")
    else:
        run_dialog_nostdout("--title", tr("error"), "--msgbox",
                           f"{tr('restart_failed')}\n\n{result}", "10", "60")


def action_models():
    if not manager.is_running():
        run_dialog_nostdout("--title", tr("info"), "--msgbox", tr("need_running_models"), "8", "60")
        return

    try:
        result = subprocess.run(
            ["curl", "-sf", "--max-time", "5", f"{manager.OLLAMA_URL}/api/tags"],
            capture_output=True, text=True, timeout=7
        )
        if result.returncode != 0:
            run_dialog_nostdout("--title", tr("error"), "--msgbox", tr("fetch_models_err"), "8", "50")
            return

        data = json.loads(result.stdout)
        models_info = []
        for m in data.get("models", []):
            name = m.get("name", "unknown")
            size_bytes = m.get("size", 0)
            size_gb = round(size_bytes / 1073741824, 2)
            models_info.append(f"{name} | {size_gb} GB")

        if not models_info:
            run_dialog_nostdout("--title", tr("ollama_manager"), "--msgbox", tr("no_models"), "8", "50")
            return

        run_dialog_nostdout("--title", tr("ollama_manager"), "--msgbox",
                           "\n".join(models_info), "15", "60")
    except Exception:
        run_dialog_nostdout("--title", tr("error"), "--msgbox", tr("fetch_models_err"), "8", "50")


def action_pull_model():
    model_name = run_dialog(
        "--title", tr("menu_pull"),
        "--inputbox", tr("pull_prompt"),
        "10", "60", "qwen3.5:2b",
    )

    if not model_name:
        return

    run_dialog_nostdout("--title", tr("download_title"), "--infobox",
                       tr("download_msg", model_name), "10", "60")

    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=True, text=True, timeout=3600
        )

        if result.returncode == 0:
            run_dialog_nostdout("--title", tr("success"), "--msgbox",
                               tr("download_success", model_name), "8", "60")
        else:
            error_output = result.stderr.strip().split("\n")[-5:]
            run_dialog_nostdout("--title", tr("error"), "--msgbox",
                               f"{tr('download_failed', model_name)}\n\n" + "\n".join(error_output),
                               "12", "60")
    except Exception as e:
        run_dialog_nostdout("--title", tr("error"), "--msgbox",
                           f"{tr('download_failed', model_name)}\n\n{str(e)}", "12", "60")


def action_remove_model():
    if not manager.is_running():
        run_dialog_nostdout("--title", tr("info"), "--msgbox", tr("need_running_remove"), "8", "60")
        return

    try:
        result = subprocess.run(
            ["curl", "-sf", "--max-time", "5", f"{manager.OLLAMA_URL}/api/tags"],
            capture_output=True, text=True, timeout=7
        )
        if result.returncode != 0:
            run_dialog_nostdout("--title", tr("error"), "--msgbox", tr("fetch_models_err"), "8", "50")
            return

        data = json.loads(result.stdout)
        models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]

        if not models:
            run_dialog_nostdout("--title", tr("info"), "--msgbox", tr("no_models"), "8", "50")
            return

        menu_items = []
        for i, model in enumerate(models, 1):
            menu_items.extend([str(i), model])

        choice = run_dialog(
            "--title", tr("menu_remove"),
            "--menu", tr("menu_remove"),
            "15", "60", "8",
            *menu_items,
        )

        if choice is None:
            return

        selected_model = models[int(choice) - 1]

        if run_dialog_nostdout("--title", tr("confirm"), "--yesno",
                              tr("remove_confirm", selected_model), "8", "60"):
            subprocess.run(["ollama", "rm", selected_model], capture_output=True)
            run_dialog_nostdout("--title", tr("menu_remove"), "--msgbox",
                               tr("model_removed"), "8", "50")
    except Exception:
        run_dialog_nostdout("--title", tr("error"), "--msgbox", tr("fetch_models_err"), "8", "50")


def action_autocorrect_status():
    missing_deps = [cmd for cmd in ["wl-copy", "wl-paste", "wtype", "curl", "notify-send"]
                   if not shutil.which(cmd)]

    script_path = Path.home() / ".local" / "bin" / "autocorrect-gemma.sh"
    if script_path.exists() and os.access(script_path, os.X_OK):
        script_status = tr("ac_installed", str(script_path))
    else:
        script_status = tr("ac_not_installed")

    ollama_status = get_status_line()

    message = f"{ollama_status}\n\nAutokorrektur-Skript: {script_status}\n"

    if not missing_deps:
        message += f"{tr('ac_deps_ok')}\n"
    else:
        message += f"{tr('ac_deps_missing')}\n"
        message += "\n".join(f"  {cmd}" for cmd in missing_deps) + "\n"

    shortcut_file = Path.home() / ".config" / "cosmic" / "com.system76.CosmicSettings.Shortcuts" / "v1" / "custom.ron"
    if shortcut_file.exists() and "autocorrect-gemma" in shortcut_file.read_text():
        message += f"\n{tr('ac_shortcut_yes')}"
    else:
        message += f"\n{tr('ac_shortcut_no')}"

    run_dialog_nostdout("--title", tr("menu_ac_status"), "--msgbox", message, "14", "60")


def action_model_select():
    config_dir = Path.home() / ".config" / "autocorrect"
    model_file = config_dir / "model"

    current_model = os.environ.get("AUTOCORRECT_MODEL", "gemma4:e2b")
    if model_file.exists():
        current_model = model_file.read_text().strip()

    choice = run_dialog(
        "--title", tr("model_select"),
        "--menu", tr("model_info", current_model),
        "14", "60", "4",
        "1", tr("model_gemma"),
        "2", tr("model_qwen_small"),
        "3", tr("model_qwen_med"),
        "4", tr("model_custom"),
    )

    if choice is None:
        return

    new_model = ""
    if choice == "1":
        new_model = "gemma4:e2b"
    elif choice == "2":
        new_model = "qwen3.5:0.8b"
    elif choice == "3":
        new_model = "qwen3.5:2b"
    elif choice == "4":
        new_model = run_dialog(
            "--title", tr("model_select"),
            "--inputbox", tr("model_custom_prompt"),
            "10", "60", "",
        )
        if not new_model:
            return

    if new_model:
        config_dir.mkdir(parents=True, exist_ok=True)
        model_file.write_text(new_model)
        run_dialog_nostdout("--title", tr("success"), "--msgbox",
                           f"{tr('model_changed', new_model)}\n{tr('model_saved')}", "10", "60")


if __name__ == "__main__":
    main_menu()
