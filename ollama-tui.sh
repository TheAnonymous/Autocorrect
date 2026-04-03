#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANAGER="$SCRIPT_DIR/ollama-manager.sh"
source "$SCRIPT_DIR/i18n.sh"

DIALOG_CMD=""
for cmd in dialog whiptail; do
    if command -v "$cmd" &>/dev/null; then
        DIALOG_CMD="$cmd"
        break
    fi
done

if [[ -z "$DIALOG_CMD" ]]; then
    echo "Fehler: Weder 'dialog' noch 'whiptail' gefunden." >&2
    exit 1
fi

get_ollama_status() {
    "$MANAGER" status 2>/dev/null || echo "stopped"
}

get_status_line() {
    local status_output
    status_output=$(get_ollama_status)
    local state
    state=$(echo "$status_output" | head -1)

    case "$state" in
        running)
            local mem
            mem=$(echo "$status_output" | grep "^memory_mb=" | cut -d= -f2)
            tr "status_running" "$mem"
            ;;
        stopped)
            tr "status_stopped"
            ;;
        *)
            tr "status_unknown" "$state"
            ;;
    esac
}

get_models_list() {
    local status_output
    status_output=$(get_ollama_status)
    local state
    state=$(echo "$status_output" | head -1)

    if [[ "$state" == "running" ]]; then
        echo "$status_output" | grep "^models=" | cut -d= -f2- | tr '\n' ', ' | sed 's/,$//'
    else
        echo "(Ollama nicht gestartet)"
    fi
}

main_menu() {
    while true; do
        local status_line
        status_line=$(get_status_line)
        local models
        models=$(get_models_list)

        local choice
        choice=$("$DIALOG_CMD" --title "$(tr "ollama_manager")" \
            --menu "$status_line\n\nGeladene Modelle:\n  $models" \
            18 60 8 \
            "1" "$(tr "menu_start")" \
            "2" "$(tr "menu_stop")" \
            "3" "$(tr "menu_restart")" \
            "4" "$(tr "menu_models")" \
            "5" "$(tr "menu_pull")" \
            "6" "$(tr "menu_remove")" \
            "7" "$(tr "menu_ac_status")" \
            "8" "$(tr "menu_exit")" \
            3>&1 1>&2 2>&3) || return 0

        case "$choice" in
            1) action_start ;;
            2) action_stop ;;
            3) action_restart ;;
            4) action_models ;;
            5) action_pull_model ;;
            6) action_remove_model ;;
            7) action_autocorrect_status ;;
            8) return 0 ;;
        esac
    done
}

action_start() {
    local result
    result=$("$MANAGER" start 2>&1) || true
    case "$result" in
        already_running)
            "$DIALOG_CMD" --title "$(tr "info")" --msgbox "$(tr "already_running")" 8 50 ;;
        started)
            "$DIALOG_CMD" --title "$(tr "success")" --msgbox "$(tr "started")" 8 50 ;;
        *)
            "$DIALOG_CMD" --title "$(tr "error")" --msgbox "$(tr "start_failed")\n\n$result" 10 60 ;;
    esac
}

action_stop() {
    local result
    result=$("$MANAGER" stop 2>&1) || true
    case "$result" in
        already_stopped)
            "$DIALOG_CMD" --title "$(tr "info")" --msgbox "$(tr "already_stopped")" 8 50 ;;
        *)
            "$DIALOG_CMD" --title "$(tr "success")" --msgbox "$(tr "stopped")" 8 50 ;;
    esac
}

action_restart() {
    "$DIALOG_CMD" --title "$(tr "menu_restart")" --infobox "$(tr "restarting")" 8 50
    sleep 1
    "$MANAGER" stop &>/dev/null || true
    sleep 1
    local result
    result=$("$MANAGER" start 2>&1) || true
    case "$result" in
        started)
            "$DIALOG_CMD" --title "$(tr "success")" --msgbox "$(tr "restart_done")" 8 50 ;;
        *)
            "$DIALOG_CMD" --title "$(tr "error")" --msgbox "$(tr "restart_failed")\n\n$result" 10 60 ;;
    esac
}

action_models() {
    local status_output
    status_output=$(get_ollama_status)
    local state
    state=$(echo "$status_output" | head -1)

    if [[ "$state" != "running" ]]; then
        "$DIALOG_CMD" --title "$(tr "info")" --msgbox "$(tr "need_running_models")" 8 60
        return
    fi

    local models_json
    models_json=$(curl -sf --max-time 5 http://localhost:11434/api/tags 2>/dev/null) || true

    if [[ -z "$models_json" ]]; then
        "$DIALOG_CMD" --title "$(tr "error")" --msgbox "$(tr "fetch_models_err")" 8 50
        return
    fi

    local models_info
    models_info=$(echo "$models_json" | jq -r '.models[]? | "\(.name) | \(.size // 0 / 1073741824 * 100 | floor / 100) GB"' 2>/dev/null) || true

    if [[ -z "$models_info" ]]; then
        "$DIALOG_CMD" --title "$(tr "ollama_manager")" --msgbox "$(tr "no_models")" 8 50
        return
    fi

    "$DIALOG_CMD" --title "$(tr "ollama_manager")" --msgbox "$models_info" 15 60
}

action_pull_model() {
    local model_name
    model_name=$("$DIALOG_CMD" --title "$(tr "menu_pull")" \
        --inputbox "$(tr "pull_prompt")" \
        10 60 "gemma4:e2b" 3>&1 1>&2 2>&3) || return 0

    if [[ -z "$model_name" ]]; then
        return
    fi

    local tmpfile
    tmpfile=$(mktemp)
    
    "$DIALOG_CMD" --title "$(tr "download_title")" --infobox "$(tr "download_msg" "$model_name")" 10 60
    ollama pull "$model_name" > "$tmpfile" 2>&1 &
    local pid=$!

    while kill -0 "$pid" 2>/dev/null; do
        sleep 1
    done

    wait "$pid" 2>/dev/null
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        "$DIALOG_CMD" --title "$(tr "success")" --msgbox "$(tr "download_success" "$model_name")" 8 60
    else
        "$DIALOG_CMD" --title "$(tr "error")" --msgbox "$(tr "download_failed" "$model_name")\n\n$(cat "$tmpfile" | tail -5)" 12 60
    fi

    rm -f "$tmpfile"
}

action_remove_model() {
    local status_output
    status_output=$(get_ollama_status)
    local state
    state=$(echo "$status_output" | head -1)

    if [[ "$state" != "running" ]]; then
        "$DIALOG_CMD" --title "$(tr "info")" --msgbox "$(tr "need_running_remove")" 8 60
        return
    fi

    local models_json
    models_json=$(curl -sf --max-time 5 http://localhost:11434/api/tags 2>/dev/null) || true

    if [[ -z "$models_json" ]]; then
        "$DIALOG_CMD" --title "$(tr "error")" --msgbox "$(tr "fetch_models_err")" 8 50
        return
    fi

    local menu_items=()
    local i=1
    while IFS= read -r model_name; do
        if [[ -n "$model_name" ]]; then
            menu_items+=("$i" "$model_name")
            i=$((i + 1))
        fi
    done < <(echo "$models_json" | jq -r '.models[]?.name // empty' 2>/dev/null)

    if [[ ${#menu_items[@]} -eq 0 ]]; then
        "$DIALOG_CMD" --title "$(tr "info")" --msgbox "$(tr "no_models")" 8 50
        return
    fi

    local choice
    choice=$("$DIALOG_CMD" --title "$(tr "menu_remove")" \
        --menu "$(tr "menu_remove")" \
        15 60 8 \
        "${menu_items[@]}" \
        3>&1 1>&2 2>&3) || return 0

    local selected_model
    selected_model="${menu_items[$(( (choice - 1) * 2 + 1 ))]}"

    if "$DIALOG_CMD" --title "$(tr "confirm")" --yesno "$(tr "remove_confirm" "$selected_model")" 8 60; then
        ollama rm "$selected_model" 2>&1 | "$DIALOG_CMD" --title "$(tr "menu_remove")" --msgbox "$(tr "model_removed")" 8 50
    fi
}

action_autocorrect_status() {
    local deps_ok=true
    local missing_deps=""
    for cmd in wl-copy wl-paste wtype jq curl notify-send; do
        if ! command -v "$cmd" &>/dev/null; then
            deps_ok=false
            missing_deps="$missing_deps  $cmd\n"
        fi
    done

    local script_path="$HOME/.local/bin/autocorrect-gemma.sh"
    local script_status
    if [[ -x "$script_path" ]]; then
        script_status="$(tr "ac_installed" "$script_path")"
    else
        script_status="$(tr "ac_not_installed")"
    fi

    local ollama_status
    ollama_status=$(get_status_line)

    local message="$ollama_status\n\nAutokorrektur-Skript: $script_status\n"
    
    if [[ "$deps_ok" = true ]]; then
        message+="$(tr "ac_deps_ok")\n"
    else
        message+="$(tr "ac_deps_missing")\n$missing_deps"
    fi

    local shortcut_file="$HOME/.config/cosmic/com.system76.CosmicSettings.Shortcuts/v1/custom.ron"
    if [[ -f "$shortcut_file" ]] && grep -q "autocorrect-gemma" "$shortcut_file" 2>/dev/null; then
        message+="\n$(tr "ac_shortcut_yes")"
    else
        message+="\n$(tr "ac_shortcut_no")"
    fi

    "$DIALOG_CMD" --title "$(tr "menu_ac_status")" --msgbox "$message" 14 60
}

main_menu
