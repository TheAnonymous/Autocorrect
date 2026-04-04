#!/bin/bash

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/i18n.sh"

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}   Gemma 4 Autokorrektur - Installationsassistent   ${NC}"
echo -e "${BLUE}====================================================${NC}"
echo

echo -e "${GREEN}[1/5] $(tr "inst_check_deps")${NC}"
DEPENDENCIES=("wl-copy" "wl-paste" "wtype" "curl" "notify-send" "ollama")
MISSING=()

for cmd in "${DEPENDENCIES[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
        MISSING+=("$cmd")
    fi
done

if [ ${#MISSING[@]} -ne 0 ]; then
    echo -e "${RED}$(tr "inst_missing")${NC} ${MISSING[*]}"
    
    PKM=""
    if command -v apt &> /dev/null; then PKM="apt"
    elif command -v pacman &> /dev/null; then PKM="pacman"
    elif command -v dnf &> /dev/null; then PKM="dnf"
    elif command -v zypper &> /dev/null; then PKM="zypper"
    fi

    if [ -n "$PKM" ]; then
        read -p "$(tr "inst_install_prompt")" -n 1 -r
        echo
        if [[ $REPLY =~ ^[JjYy]$ ]]; then
            declare -A PKG_MAP
            PKG_MAP=( ["wl-copy"]="wl-clipboard" ["wl-paste"]="wl-clipboard" ["wtype"]="wtype" ["jq"]="jq" ["curl"]="curl" ["notify-send"]="libnotify-bin" ["ollama"]="ollama" )
            
            if [ "$PKM" != "apt" ]; then
                PKG_MAP["notify-send"]="libnotify"
            fi

            TO_INSTALL=()
            for cmd in "${MISSING[@]}"; do
                TO_INSTALL+=("${PKG_MAP[$cmd]}")
            done
            
            TO_INSTALL=($(printf "%s\n" "${TO_INSTALL[@]}" | sort -u))

            OLLAMA_MISSING=false
            if [[ " ${MISSING[*]} " =~ " ollama " ]]; then
                OLLAMA_MISSING=true
                NEW_TO_INSTALL=()
                for item in "${TO_INSTALL[@]}"; do
                    if [ "$item" != "ollama" ]; then
                        NEW_TO_INSTALL+=("$item")
                    fi
                done
                TO_INSTALL=("${NEW_TO_INSTALL[@]+"${NEW_TO_INSTALL[@]}"}")
            fi

            if [ ${#TO_INSTALL[@]} -ne 0 ]; then
                echo -e "${BLUE}$(tr "inst_installing")${NC} ${TO_INSTALL[*]}"
                case $PKM in
                    apt) sudo apt update && sudo apt install -y "${TO_INSTALL[@]}" ;;
                    pacman) sudo pacman -S --noconfirm "${TO_INSTALL[@]}" ;;
                    dnf) sudo dnf install -y "${TO_INSTALL[@]}" ;;
                    zypper) sudo zypper install -y "${TO_INSTALL[@]}" ;;
                esac
            fi

            if [ "$OLLAMA_MISSING" = true ]; then
                echo -e "${BLUE}$(tr "inst_ollama_install")${NC}"
                curl -fsSL https://ollama.com/install.sh | sh
            fi

            STILL_MISSING=()
            for cmd in "${MISSING[@]}"; do
                if ! command -v "$cmd" &> /dev/null; then
                    STILL_MISSING+=("$cmd")
                fi
            done
            
            if [ ${#STILL_MISSING[@]} -ne 0 ]; then
                echo -e "${RED}$(tr "inst_some_missing")${NC} ${STILL_MISSING[*]}"
                echo "$(tr "inst_manual_install")"
                exit 1
            fi
        else
            echo "$(tr "inst_aborted")"
            exit 1
        fi
    else
        echo "$(tr "inst_no_pkgmgr")"
        echo "$(tr "inst_manual_deps") ${MISSING[*]}"
        exit 1
    fi
else
    echo -e "   $(tr "inst_all_deps")"
fi

echo -e "\n${GREEN}[2/6] $(tr "inst_check_ram")${NC}"

TOTAL_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
AVAIL_KB=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
TOTAL_MB=$(( TOTAL_KB / 1024 ))
AVAIL_MB=$(( AVAIL_KB / 1024 ))
REQUIRED_MB=4096

echo "   RAM: $(tr "inst_ram_total" "$TOTAL_MB") | $(tr "inst_ram_avail" "$AVAIL_MB")"

if [ "$AVAIL_MB" -lt "$REQUIRED_MB" ]; then
    echo -e "   ${YELLOW}$(tr "inst_ram_low" "$REQUIRED_MB")${NC}"
    read -p "$(tr "inst_ram_prompt")" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
        echo "$(tr "inst_ram_abort")"
        exit 1
    fi
else
    echo -e "   ${GREEN}$(tr "inst_ram_ok")${NC}"
fi

echo -e "\n${GREEN}[3/6] $(tr "inst_check_ollama")${NC}"
if ! curl -sf --max-time 5 http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${RED}$(tr "inst_ollama_err")${NC}"
    echo "$(tr "inst_ollama_start_hint")"
    exit 1
else
    echo "$(tr "inst_ollama_ready")"
fi

MODEL="gemma4:e2b"
echo -e "\n${GREEN}[3/5] $(tr "inst_download_model" "$MODEL")${NC}"
echo "$(tr "inst_model_hint")"
ollama pull "$MODEL"

INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"
SCRIPT_PATH="$INSTALL_DIR/autocorrect-gemma.sh"
UNDO_PATH="$INSTALL_DIR/autocorrect_undo.py"
MANAGER_PATH="$INSTALL_DIR/ollama_manager.py"
TUI_PATH="$INSTALL_DIR/ollama_tui.py"
TRAY_PATH="$INSTALL_DIR/ollama-tray.py"
I18N_PATH="$INSTALL_DIR/i18n.py"

echo -e "\n${GREEN}[4/6] Installiere Skripte nach /home/jodie/.local/bin...${NC}"
cp "$SCRIPT_DIR/autocorrect.sh" "$SCRIPT_PATH"
chmod +x "$SCRIPT_PATH"
echo "   $SCRIPT_PATH"

cp "$SCRIPT_DIR/autocorrect_undo.py" "$UNDO_PATH"
chmod +x "$UNDO_PATH"
echo "   $UNDO_PATH"

cp "$SCRIPT_DIR/ollama_manager.py" "$MANAGER_PATH"
chmod +x "$MANAGER_PATH"
echo "   $MANAGER_PATH"

cp "$SCRIPT_DIR/ollama_tui.py" "$TUI_PATH"
chmod +x "$TUI_PATH"
echo "   $TUI_PATH"

cp "$SCRIPT_DIR/ollama-tray.py" "$TRAY_PATH"
chmod +x "$TRAY_PATH"
echo "   $TRAY_PATH"

cp "$SCRIPT_DIR/i18n.py" "$I18N_PATH"
chmod +x "$I18N_PATH"
echo "   $I18N_PATH"

if command -v python3 &>/dev/null; then
    if ! python3 -c "import pystray" &>/dev/null 2>&1 || ! python3 -c "import PIL" &>/dev/null 2>&1; then
        echo -e "   ${YELLOW}$(tr "inst_py_missing")${NC}"
        read -p "   $(tr "inst_py_prompt")" -n 1 -r
        echo
        if [[ $REPLY =~ ^[JjYy]$ ]]; then
            PYTHON_INSTALLED=false

            if command -v pacman &>/dev/null; then
                echo -e "   ${BLUE}$(tr "inst_py_installing" "pacman")${NC}"
                sudo pacman -S --noconfirm python-pystray python-pillow 2>&1 && PYTHON_INSTALLED=true
            elif command -v apt &>/dev/null; then
                echo -e "   ${BLUE}$(tr "inst_py_installing" "apt")${NC}"
                sudo apt update -qq 2>&1 | tail -1
                sudo apt install -y python3-pystray python3-pil 2>&1 && PYTHON_INSTALLED=true
            elif command -v dnf &>/dev/null; then
                echo -e "   ${BLUE}$(tr "inst_py_installing" "dnf")${NC}"
                sudo dnf install -y python3-pystray python3-pillow 2>&1 && PYTHON_INSTALLED=true
            elif command -v zypper &>/dev/null; then
                echo -e "   ${BLUE}$(tr "inst_py_installing" "zypper")${NC}"
                sudo zypper install -y python3-pystray python3-Pillow 2>&1 && PYTHON_INSTALLED=true
            fi

            if [ "$PYTHON_INSTALLED" = false ]; then
                PIP_CMD=""
                if command -v pip3 &>/dev/null; then PIP_CMD="pip3"
                elif command -v pip &>/dev/null; then PIP_CMD="pip"
                elif python3 -m pip --version &>/dev/null; then PIP_CMD="python3 -m pip"
                fi

                if [ -n "$PIP_CMD" ]; then
                    echo -e "   ${BLUE}$(tr "inst_py_pip")${NC}"
                    if eval "$PIP_CMD install --user pystray Pillow" 2>&1; then
                        PYTHON_INSTALLED=true
                    fi
                fi
            fi

            if [ "$PYTHON_INSTALLED" = false ]; then
                echo -e "   ${RED}$(tr "inst_py_fail")${NC}"
                echo -e "   $(tr "inst_py_manual_arch")"
                echo -e "   $(tr "inst_py_manual_deb")"
            else
                echo -e "   ${GREEN}$(tr "inst_py_done")${NC}"
            fi
        else
            echo "   $(tr "inst_py_skip")"
        fi
    else
        echo "   $(tr "inst_py_exists")"
    fi
fi

echo -e "\n${GREEN}[5/6] $(tr "inst_setup_shortcut")${NC}"

COSMIC_CONFIG_DIR="$HOME/.config/cosmic/com.system76.CosmicSettings.Shortcuts"
COSMIC_CUSTOM_FILE="$COSMIC_CONFIG_DIR/v1/custom"

SHORTCUT_ADDED=false

if [ -d "$COSMIC_CONFIG_DIR" ] || command -v cosmic-comp &> /dev/null; then
    mkdir -p "$COSMIC_CONFIG_DIR/v1"
    
    HAS_AC=0
    HAS_UNDO=0
    if [ -f "$COSMIC_CUSTOM_FILE" ]; then
        HAS_AC=$(grep -c "autocorrect-gemma" "$COSMIC_CUSTOM_FILE" 2>/dev/null || true)
        HAS_UNDO=$(grep -c "autocorrect_undo" "$COSMIC_CUSTOM_FILE" 2>/dev/null || true)
        HAS_AC=${HAS_AC:-0}
        HAS_UNDO=${HAS_UNDO:-0}
    fi

    if [ "$HAS_AC" -gt 0 ] && [ "$HAS_UNDO" -gt 0 ]; then
        echo -e "   ${YELLOW}$(tr "inst_shortcut_exists")${NC}"
        SHORTCUT_ADDED=true
    else
        if [ -f "$COSMIC_CUSTOM_FILE" ]; then
            CONTENT=$(sed '$ d' "$COSMIC_CUSTOM_FILE")
        else
            CONTENT="{"
        fi
        
        if [ "$HAS_AC" -eq 0 ]; then
            CONTENT="$CONTENT
    (
        modifiers: [
            Super,
            Shift,
        ],
        key: \"g\",
        description: Some(\"Gemma Autokorrektur\"),
    ): Spawn(\"$SCRIPT_PATH\"),"
        fi
        
        if [ "$HAS_UNDO" -eq 0 ]; then
            CONTENT="$CONTENT
    (
        modifiers: [
            Super,
            Shift,
        ],
        key: \"u\",
        description: Some(\"Gemma Undo\"),
    ): Spawn(\"$UNDO_PATH\"),"
        fi
        
        CONTENT="$CONTENT
}"
        echo "$CONTENT" > "$COSMIC_CUSTOM_FILE"
        SHORTCUT_ADDED=true
        
        if [ "$SHORTCUT_ADDED" = true ]; then
            echo -e "   ${GREEN}$(tr "inst_shortcut_added")${NC}"
            echo "$(tr "inst_shortcut_hint")"
        fi
    fi
fi

if [ "$SHORTCUT_ADDED" = false ]; then
    echo -e "${YELLOW}   $(tr "inst_cosmic_fail")${NC}"
    echo -e "   $(tr "inst_manual_shortcut")"
    echo
    echo -e "   ${BLUE}1.${NC} $(tr "inst_manual_1")"
    echo -e "   ${BLUE}2.${NC} $(tr "inst_manual_2")"
    echo -e "   ${BLUE}3.${NC} $(tr "inst_manual_3")"
    echo -e "   ${BLUE}4.${NC} $(tr "inst_manual_4" "$SCRIPT_PATH")"
    echo -e "   ${BLUE}5.${NC} $(tr "inst_manual_5")"
fi

echo
echo -e "${GREEN}[6/6] $(tr "inst_tray_setup")${NC}"

AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/ollama-tray.desktop" << DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=Ollama Tray Manager
Comment=System tray indicator for Ollama
Exec=python3 $TRAY_PATH
Icon=utilities-terminal
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
X-KDE-autostart-after-panell=true
DESKTOP_EOF

echo "   $(tr "inst_tray_autostart" "$AUTOSTART_DIR/ollama-tray.desktop")"

SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"

cat > "$SYSTEMD_DIR/ollama-tray.service" << SERVICE_EOF
[Unit]
Description=Ollama Tray Manager
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=python3 $TRAY_PATH
Restart=on-failure
RestartSec=5
Environment=WAYLAND_DISPLAY=\${WAYLAND_DISPLAY:-wayland-0}
Environment=XDG_SESSION_TYPE=wayland

[Install]
WantedBy=graphical-session.target
SERVICE_EOF

systemctl --user daemon-reload 2>/dev/null || true
if systemctl --user enable ollama-tray.service 2>/dev/null; then
    echo "   $(tr "inst_tray_systemd")"
else
    echo "   $(tr "inst_tray_no_systemd")"
fi

echo
echo -e "${GREEN}$(tr "inst_done")${NC}"
echo
echo -e "${BLUE}$(tr "inst_commands")${NC}"
echo -e "  ${GREEN}autocorrect.py${NC}       - Text korrigieren (via Shortcut)"
echo -e "  ${GREEN}ollama_manager.py${NC}    - Ollama starten/stoppen/status"
echo -e "  ${GREEN}ollama_tui.py${NC}        - Terminal-Oberflaeche"
echo -e "  ${GREEN}ollama-tray.py${NC}       - Systemtray-Applet"
echo
echo -e "${BLUE}$(tr "inst_tray_info")${NC}"
echo -e "       $(tr "inst_tray_start")"
