#!/usr/bin/env python3

import locale
import os

_LANG = "de" if locale.getlocale()[0][:2] == "de" else "en"

TRANSLATIONS = {
    "app_name": ("Autokorrektur", "Autocorrect"),
    "error": ("Fehler", "Error"),
    "success": ("Erfolg", "Success"),
    "info": ("Info", "Info"),
    "confirm": ("Bestaetigung", "Confirm"),
    "no_text": (
        "Kein Text markiert oder Zwischenablage leer.",
        "No text selected or clipboard empty.",
    ),
    "correcting": ("Gemma korrigiert...", "Gemma is correcting..."),
    "already_correct": ("Text war bereits korrekt.", "Text was already correct."),
    "correction_done": ("Korrektur abgeschlossen.", "Correction complete."),
    "err_cmd_missing": ("Fehler: '{}' ist nicht installiert.", "Error: '{}' is not installed."),
    "err_ollama_unreachable": (
        "Ollama ist nicht erreichbar unter {}",
        "Ollama is not reachable at {}",
    ),
    "err_timeout": (
        "Zeitueberschreitung oder Verbindungsfehler zu Ollama.",
        "Timeout or connection error to Ollama.",
    ),
    "err_ollama_http": ("Ollama-Fehler (HTTP {}).", "Ollama error (HTTP {})."),
    "err_ollama_response": ("Ollama-Fehler: {}", "Ollama error: {}"),
    "err_empty_response": (
        "Leere Antwort von Ollama erhalten.",
        "Received empty response from Ollama.",
    ),
    "already_running": ("Ollama laeuft bereits.", "Ollama is already running."),
    "started": ("Ollama wurde gestartet.", "Ollama has been started."),
    "start_failed": ("Ollama konnte nicht gestartet werden.", "Could not start Ollama."),
    "already_stopped": ("Ollama ist bereits gestoppt.", "Ollama is already stopped."),
    "stopped": ("Ollama wurde gestoppt.", "Ollama has been stopped."),
    "restarting": ("Ollama wird neu gestartet...", "Restarting Ollama..."),
    "restart_done": ("Ollama wurde neu gestartet.", "Ollama has been restarted."),
    "restart_failed": ("Neustart fehlgeschlagen.", "Restart failed."),
    "status_running": ("Status: LAEUFT (RAM: {} MB)", "Status: RUNNING (RAM: {} MB)"),
    "status_stopped": ("Status: GESTOPPT", "Status: STOPPED"),
    "status_unknown": ("Status: {}", "Status: {}"),
    "need_running_models": (
        "Ollama muss gestartet sein, um Modelle anzuzeigen.",
        "Ollama must be running to view models.",
    ),
    "no_models": ("Keine Modelle installiert.", "No models installed."),
    "fetch_models_err": ("Konnte Modelle nicht abrufen.", "Could not fetch models."),
    "need_running_remove": (
        "Ollama muss gestartet sein, um Modelle zu entfernen.",
        "Ollama must be running to remove models.",
    ),
    "remove_confirm": ("Modell '{}' wirklich entfernen?", "Really remove model '{}'?"),
    "model_removed": ("Modell wurde entfernt.", "Model has been removed."),
    "download_title": ("Herunterladen...", "Downloading..."),
    "download_msg": (
        "Lade '{}' herunter...\n\nDies kann je nach Groesse eine Weile dauern.",
        "Downloading '{}'\n\nThis may take a while depending on size.",
    ),
    "download_success": (
        "Modell '{}' erfolgreich heruntergeladen.",
        "Model '{}' downloaded successfully.",
    ),
    "download_failed": ("Fehler beim Herunterladen von '{}'.", "Error downloading '{}'."),
    "pull_prompt": (
        "Modell-Name (z.B. qwen3.5:2b, gemma4:e2b, gemma3:1b):",
        "Model name (e.g. qwen3.5:2b, gemma4:e2b, gemma3:1b):",
    ),
    "ollama_manager": ("Ollama Manager", "Ollama Manager"),
    "menu_start": ("Ollama starten", "Start Ollama"),
    "menu_stop": ("Ollama stoppen", "Stop Ollama"),
    "menu_restart": ("Neustarten", "Restart"),
    "menu_models": ("Modelle anzeigen", "View Models"),
    "menu_pull": ("Modell herunterladen", "Download Model"),
    "menu_remove": ("Modell entfernen", "Remove Model"),
    "menu_ac_status": ("Autokorrektur-Status", "Autocorrect Status"),
    "menu_model": ("Modell wechseln", "Change Model"),
    "menu_exit": ("Beenden", "Exit"),
    "ac_installed": ("Installiert ({})", "Installed ({})"),
    "ac_not_installed": ("Nicht installiert", "Not installed"),
    "ac_deps_ok": ("Abhaengigkeiten: Alle vorhanden", "Dependencies: All present"),
    "ac_deps_missing": ("Fehlende Abhaengigkeiten:", "Missing dependencies:"),
    "ac_shortcut_yes": ("Shortcut: Konfiguriert", "Shortcut: Configured"),
    "ac_shortcut_no": ("Shortcut: Nicht konfiguriert", "Shortcut: Not configured"),
    "tray_running": ("Ollama: Laeuft", "Ollama: Running"),
    "tray_stopped": ("Ollama: Gestoppt", "Ollama: Stopped"),
    "tray_start": ("Starten", "Start"),
    "tray_stop": ("Stoppen", "Stop"),
    "tray_restart": ("Neustarten", "Restart"),
    "tray_open_tui": ("TUI oeffnen", "Open TUI"),
    "tray_quit": ("Beenden", "Quit"),
    "tray_shortcut": ("Autokorrektur: Super+Shift+G", "Autocorrect: Super+Shift+G"),
    "tray_err_deps": (
        "Fehler: pystray und Pillow werden benoetigt.",
        "Error: pystray and Pillow are required.",
    ),
    "tray_err_install": (
        "Installiere mit: pip install pystray Pillow",
        "Install with: pip install pystray Pillow",
    ),
    "inst_check_deps": ("Pruefe System-Abhaengigkeiten...", "Checking system dependencies..."),
    "inst_missing": ("Folgende Programme fehlen:", "Missing programs:"),
    "inst_install_prompt": (
        "Moechtest du die fehlenden Pakete jetzt installieren? (j/n) ",
        "Do you want to install missing packages now? (y/n) ",
    ),
    "inst_installing": ("Installiere:", "Installing:"),
    "inst_ollama_install": (
        "Installiere Ollama via offiziellem Skript...",
        "Installing Ollama via official script...",
    ),
    "inst_some_missing": (
        "Einige Pakete konnten nicht installiert werden:",
        "Some packages could not be installed:",
    ),
    "inst_manual_install": (
        "Bitte installiere diese manuell und starte den Installer erneut.",
        "Please install them manually and re-run the installer.",
    ),
    "inst_aborted": ("Installation abgebrochen.", "Installation aborted."),
    "inst_no_pkgmgr": (
        "Kein bekannter Paketmanager (apt, pacman, dnf, zypper) gefunden.",
        "No known package manager (apt, pacman, dnf, zypper) found.",
    ),
    "inst_manual_deps": (
        "Bitte installiere die Programme manuell:",
        "Please install programs manually:",
    ),
    "inst_all_deps": ("Alle Abhaengigkeiten gefunden.", "All dependencies found."),
    "inst_check_ollama": ("Pruefe Ollama-Status...", "Checking Ollama status..."),
    "inst_check_ram": ("Pruefe RAM-Verfuegbarkeit...", "Checking RAM availability..."),
    "inst_ram_total": ("Gesamt: {} MB", "Total: {} MB"),
    "inst_ram_avail": ("Verfuegbar: {} MB", "Available: {} MB"),
    "inst_ram_low": (
        "Weniger als {} MB verfuegbar. Gemma4 benoetigt ~4GB RAM.",
        "Less than {} MB available. Gemma4 requires ~4GB RAM.",
    ),
    "inst_ram_prompt": ("Trotzdem fortfahren? (j/n) ", "Continue anyway? (y/n) "),
    "inst_ram_abort": ("Installation abgebrochen.", "Installation aborted."),
    "inst_ram_ok": ("Ausreichend RAM verfuegbar.", "Sufficient RAM available."),
    "inst_ollama_err": ("Fehler: Ollama laeuft nicht.", "Error: Ollama is not running."),
    "inst_ollama_start_hint": (
        "Bitte starte Ollama (z.B. 'systemctl start ollama' oder oeffne die Ollama-App) und versuche es erneut.",
        "Please start Ollama (e.g. 'systemctl start ollama' or open the Ollama app) and try again.",
    ),
    "inst_ollama_ready": ("Ollama ist bereit.", "Ollama is ready."),
    "inst_download_model": (
        "Lade Modell {} herunter (kann einen Moment dauern)...",
        "Downloading model {} (may take a moment)...",
    ),
    "inst_model_hint": (
        "Dies wird nur ausgefuehrt, wenn das Modell noch nicht vorhanden ist.",
        "This only runs if the model is not already present.",
    ),
    "inst_copy_scripts": ("Installiere Skripte nach {}...", "Installing scripts to {}..."),
    "inst_setup_shortcut": ("Richte COSMIC Shortcut ein...", "Setting up COSMIC shortcut..."),
    "inst_shortcut_exists": (
        "Shortcut ist bereits konfiguriert.",
        "Shortcut is already configured.",
    ),
    "inst_shortcut_added": (
        "Shortcut hinzugefuegt: Super+Shift+G -> Autokorrektur",
        "Shortcut added: Super+Shift+G -> Autocorrect",
    ),
    "inst_shortcut_hint": (
        "Starte cosmic-comp neu oder logge dich aus/ein, damit die Aenderung wirksam wird.",
        "Restart cosmic-comp or log out/in for changes to take effect.",
    ),
    "inst_cosmic_fail": (
        "COSMIC nicht erkannt oder Konfiguration fehlgeschlagen.",
        "COSMIC not detected or configuration failed.",
    ),
    "inst_manual_shortcut": (
        "Bitte richte den Shortcut manuell ein:",
        "Please set up the shortcut manually:",
    ),
    "inst_manual_1": (
        "Oeffne COSMIC-Einstellungen -> Keyboard -> Shortcuts",
        "Open COSMIC Settings -> Keyboard -> Shortcuts",
    ),
    "inst_manual_2": ("Klicke auf 'Add Shortcut' (Custom)", "Click 'Add Shortcut' (Custom)"),
    "inst_manual_3": ("Name: Gemma Autokorrektur", "Name: Gemma Autocorrect"),
    "inst_manual_4": ("Command: {}", "Command: {}"),
    "inst_manual_5": (
        "Tastenkombination waehlen (z.B. Super+Shift+G)",
        "Choose a key combination (e.g. Super+Shift+G)",
    ),
    "inst_done": ("Installation abgeschlossen!", "Installation complete!"),
    "inst_commands": ("Verfuegbare Befehle:", "Available commands:"),
    "inst_tray_info": (
        "Info: Das Tray-Icon startet automatisch beim naechsten Login.",
        "Info: Tray icon will start automatically on next login.",
    ),
    "inst_tray_start": (
        "Jetzt sofort starten: systemctl --user start ollama-tray",
        "Start now: systemctl --user start ollama-tray",
    ),
    "inst_tray_setup": ("Richte Tray-Autostart ein...", "Setting up tray autostart..."),
    "inst_tray_autostart": ("Autostart-Datei erstellt: {}", "Autostart file created: {}"),
    "inst_tray_systemd": (
        "Systemd-Service aktiviert: ollama-tray.service",
        "Systemd service enabled: ollama-tray.service",
    ),
    "inst_tray_no_systemd": (
        "Autostart ueber .desktop Datei (Systemd nicht verfuegbar)",
        "Autostart via .desktop file (systemd not available)",
    ),
    "inst_py_missing": (
        "Python-Pakete fuer Tray-Applet fehlen (pystray, Pillow).",
        "Python packages for tray applet missing (pystray, Pillow).",
    ),
    "inst_py_prompt": (
        "Moechtest du sie jetzt installieren? (j/n) ",
        "Do you want to install them now? (y/n) ",
    ),
    "inst_py_installing": ("Installiere via {}...", "Installing via {}..."),
    "inst_py_pip": ("Installiere via pip...", "Installing via pip..."),
    "inst_py_done": (
        "Python-Pakete erfolgreich installiert.",
        "Python packages installed successfully.",
    ),
    "inst_py_fail": (
        "Konnte Pakete nicht automatisch installieren.",
        "Could not install packages automatically.",
    ),
    "inst_py_manual_arch": (
        "Manuell: sudo pacman -S python-pystray python-pillow  (Arch)",
        "Manual: sudo pacman -S python-pystray python-pillow  (Arch)",
    ),
    "inst_py_manual_deb": (
        "Oder:      sudo apt install python3-pystray python3-pil  (Debian/Ubuntu)",
        "Or:      sudo apt install python3-pystray python3-pil  (Debian/Ubuntu)",
    ),
    "inst_py_skip": (
        "Tray-Applet uebersprungen. Spaeter nachinstallieren mit: pip3 install --user pystray Pillow",
        "Tray applet skipped. Install later with: pip3 install --user pystray Pillow",
    ),
    "inst_py_exists": (
        "Python-Abhaengigkeiten bereits vorhanden.",
        "Python dependencies already present.",
    ),
    "model_select": ("Modell auswaehlen", "Select Model"),
    "model_gemma": (
        "Gemma 4 (2B) - ~4GB RAM, hohe Qualitaet",
        "Gemma 4 (2B) - ~4GB RAM, high quality",
    ),
    "model_qwen_small": (
        "Qwen 3.5 (0.8B) - ~1GB RAM, SOTA klein",
        "Qwen 3.5 (0.8B) - ~1GB RAM, SOTA small",
    ),
    "model_qwen_med": (
        "Qwen 3.5 (2B) - ~2.7GB RAM, SOTA mittel",
        "Qwen 3.5 (2B) - ~2.7GB RAM, SOTA medium",
    ),
    "model_custom": ("Eigenes Modell eingeben...", "Enter custom model..."),
    "model_custom_prompt": (
        "Modell-Name (z.B. mistral, phi3):",
        "Model name (e.g. mistral, phi3):",
    ),
    "model_info": ("Aktuelles Modell: {}", "Current model: {}"),
    "model_changed": ("Modell geaendert zu: {}", "Model changed to: {}"),
    "model_saved": (
        "Modell gespeichert in ~/.config/autocorrect/model",
        "Model saved to ~/.config/autocorrect/model",
    ),
    "undo_nothing": ("Nichts zum Wiederherstellen.", "Nothing to undo."),
    "undo_done": ("Original wiederhergestellt.", "Original restored."),
}


def tr(key: str, *args: object) -> str:
    idx = 0 if _LANG == "de" else 1
    msg = TRANSLATIONS.get(key, (key, key))[idx]
    return msg.format(*args) if args else msg
