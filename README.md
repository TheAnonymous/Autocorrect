# Autocorrect

System-wide AI autocorrection for COSMIC/Wayland desktops via local Ollama LLM.

Select text, press a shortcut — done. No cloud service, everything runs locally.

## Features

- **System-wide autocorrection** — Works in any app (browser, editor, chat, etc.)
- **Local LLM** — Ollama with Gemma 4, no data leaves your machine
- **Ollama on-demand** — Start server only when needed, saves ~4GB RAM
- **System tray icon** — Start/stop Ollama with a click, always accessible
- **Terminal UI** — Full management via TUI (dialog/whiptail)
- **COSMIC integration** — Automatic keyboard shortcut + autostart on login
- **i18n** — German and English, detects language automatically via `$LANG`

## Quick Start

```bash
./install.sh
```

The installer handles dependencies, downloads the model, sets up the keyboard shortcut, and enables tray autostart.

## Components

| File | Purpose |
|---|---|
| `autocorrect.py` | Core script: copies selected text, sends to Ollama, pastes correction |
| `ollama_manager.py` | CLI: `start`, `stop`, `restart`, `status` for Ollama |
| `ollama_tui.py` | Terminal UI: menu-based management of all functions |
| `ollama-tray.py` | System tray applet: icon in the COSMIC panel with start/stop |
| `install.sh` | Installer: dependencies, model, scripts, shortcut, autostart |
| `i18n.py` | Translation system: German/English via `$LANG` |

## Usage

### Autocorrection

Select text → press `Super+Shift+G` → correction is pasted in place.

### Managing Ollama

**Via tray icon:** Click the icon in the panel → Start / Stop / Restart

**Via TUI:**
```bash
ollama_tui.py
```

**Via CLI:**
```bash
ollama_manager.py status
ollama_manager.py start
ollama_manager.py stop
```

**Start immediately (without re-login):**
```bash
systemctl --user start ollama-tray
```

## Configuration

Environment variables for `autocorrect.py`:

| Variable | Default | Description |
|---|---|---|
| `AUTOCORRECT_MODEL` | `gemma4:e2b` | Ollama model to use |
| `AUTOCORRECT_OLLAMA_URL` | `http://localhost:11434/api/generate` | Ollama API endpoint |
| `AUTOCORRECT_DELAY` | `0.2` | Delay between copy/paste (seconds) |
| `AUTOCORRECT_CURL_TIMEOUT` | `60` | Timeout for Ollama request (seconds) |
| `AUTOCORRECT_DEBUG` | `0` | Enable debug output (`1`) |

## Dependencies

**System:** `wl-clipboard`, `wtype`, `curl`, `libnotify`, `ollama`

**TUI:** `dialog` or `whiptail`

**Tray:** `python3`, `pystray`, `Pillow`

The installer detects and installs missing packages automatically (apt, pacman, dnf, zypper).

## Project Structure

```
autocorrect/
├── autocorrect.py      # Main autocorrection script
├── ollama_manager.py   # Ollama CLI manager
├── ollama_tui.py       # Terminal user interface
├── ollama-tray.py      # System tray applet
├── install.sh          # One-shot installer
└── i18n.py             # Translations (de/en)
```

## License

MIT
