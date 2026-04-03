#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/i18n.sh"

MODEL_CONFIG="$HOME/.config/autocorrect/model"
if [[ -f "$MODEL_CONFIG" ]]; then
    MODEL="$(cat "$MODEL_CONFIG")"
else
    MODEL_CONFIG="$HOME/.config/autocorrect/model"
if [[ -f "$MODEL_CONFIG" ]]; then
    MODEL="$(cat "$MODEL_CONFIG")"
else
    MODEL="${AUTOCORRECT_MODEL:-gemma4:e2b}"
fi
fi
OLLAMA_BASE="${AUTOCORRECT_OLLAMA_BASE:-http://localhost:11434}"
OLLAMA_URL="$OLLAMA_BASE/api/generate"
COPY_PASTE_DELAY="${AUTOCORRECT_DELAY:-0.2}"
CURL_TIMEOUT="${AUTOCORRECT_CURL_TIMEOUT:-60}"
TEMP_FILE=""
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/autocorrect"
LOG_FILE="$STATE_DIR/autocorrect.log"

mkdir -p "$STATE_DIR"

cleanup() {
    [[ -n "$TEMP_FILE" && -f "$TEMP_FILE" ]] && rm -f "$TEMP_FILE"
}
trap cleanup EXIT

log_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

notify_err() {
    log_msg "ERROR: $1"
    notify-send "$(tr "app_name")" "$1" -u critical 2>/dev/null || true
}

notify_info() {
    notify-send "$(tr "app_name")" "$1" -t 2000 2>/dev/null || true
}

log_debug() {
    if [[ "${AUTOCORRECT_DEBUG:-0}" == "1" ]]; then
        echo "[DEBUG] $*" >&2
        log_msg "DEBUG: $*"
    fi
}

detect_language() {
    local text="$1"
    local lower
    lower=$(echo "$text" | tr '[:upper:]' '[:lower:]')
    local score=0

    if echo "$lower" | grep -qE '[äöüß]'; then
        score=$((score + 3))
    fi
    for word in der die das und ist ein eine nicht mit von dem den das; do
        if echo "$lower" | grep -qw "$word"; then
            score=$((score + 1))
        fi
    done
    for word in the and is not with from that this have; do
        if echo "$lower" | grep -qw "$word"; then
            score=$((score - 1))
        fi
    done

    if [[ $score -gt 0 ]]; then
        echo "de"
    else
        echo "en"
    fi
}

get_system_prompt() {
    local lang="$1"
    if [[ "$lang" == "de" ]]; then
        echo "You are a pure autocorrection tool. Correct the text for spelling and grammar. Keep the original language. Output ONLY the corrected text, without introduction, explanations, or quotation marks."
    else
        echo "You are a pure autocorrection tool. Correct the text for spelling and grammar. Keep the original language. Output ONLY the corrected text, without introduction, explanations, or quotation marks."
    fi
}

for cmd in wl-copy wl-paste wtype jq curl notify-send; do
    if ! command -v "$cmd" &>/dev/null; then
        notify_err "$(tr "err_cmd_missing" "$cmd")"
        exit 1
    fi
done

if ! curl -sf --max-time 5 "$OLLAMA_BASE/api/tags" &>/dev/null; then
    notify_err "$(tr "err_ollama_unreachable" "$OLLAMA_URL")"
    exit 1
fi

wtype -M ctrl -P c -p c -m ctrl
sleep "$COPY_PASTE_DELAY"

ORIGINAL_TEXT=$(wl-paste -n 2>/dev/null || true)
ORIGINAL_TEXT=$(echo "$ORIGINAL_TEXT" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')

if [[ -z "$ORIGINAL_TEXT" ]]; then
    notify_info "$(tr "no_text")"
    exit 0
fi

log_msg "Input: ${ORIGINAL_TEXT:0:200}..."

DETECTED_LANG=$(detect_language "$ORIGINAL_TEXT")
log_debug "Detected language: $DETECTED_LANG"

notify_info "$(tr "correcting")"

SYSTEM_INSTRUCTION=$(get_system_prompt "$DETECTED_LANG")

TEMP_FILE=$(mktemp /tmp/autocorrect.XXXXXX)

JSON_PAYLOAD=$(jq -n \
    --arg system "$SYSTEM_INSTRUCTION" \
    --arg prompt "$ORIGINAL_TEXT" \
    --arg model "$MODEL" \
    '{model: $model, system: $system, prompt: $prompt, stream: false, options: {temperature: 0}}')

HTTP_CODE=$(curl -s -w "%{http_code}" -o "$TEMP_FILE" \
    --max-time "$CURL_TIMEOUT" \
    -X POST "$OLLAMA_URL" \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD" 2>/dev/null) || {
    notify_err "$(tr "err_timeout")"
    exit 1
}

if [[ "$HTTP_CODE" != "200" ]]; then
    log_debug "HTTP Response: $HTTP_CODE"
    notify_err "$(tr "err_ollama_http" "$HTTP_CODE")"
    exit 1
fi

CORRECTED_TEXT=$(jq -r '.response // empty' "$TEMP_FILE" 2>/dev/null | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')

ERROR_MSG=$(jq -r '.error // empty' "$TEMP_FILE" 2>/dev/null)
if [[ -n "$ERROR_MSG" ]]; then
    log_debug "Ollama Error: $ERROR_MSG"
    notify_err "$(tr "err_ollama_response" "${ERROR_MSG:0:80}")"
    exit 1
fi

if [[ -z "$CORRECTED_TEXT" ]]; then
    notify_err "$(tr "err_empty_response")"
    exit 1
fi

log_debug "Corrected: ${CORRECTED_TEXT:0:200}..."
log_msg "Output: ${CORRECTED_TEXT:0:200}..."

printf '%s' "$CORRECTED_TEXT" | wl-copy
sleep "$COPY_PASTE_DELAY"

wtype -M ctrl -P v -p v -m ctrl

if [[ "$ORIGINAL_TEXT" == "$CORRECTED_TEXT" ]]; then
    notify_info "$(tr "already_correct")"
else
    printf '%s' "$ORIGINAL_TEXT" | wl-copy
    notify_info "$(tr "correction_done")"
fi

exit 0
