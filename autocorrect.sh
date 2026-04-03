#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/i18n.sh"

MODEL="${AUTOCORRECT_MODEL:-gemma4:e2b}"
OLLAMA_URL="${AUTOCORRECT_OLLAMA_URL:-http://localhost:11434/api/generate}"
COPY_PASTE_DELAY="${AUTOCORRECT_DELAY:-0.2}"
CURL_TIMEOUT="${AUTOCORRECT_CURL_TIMEOUT:-60}"
TEMP_FILE=""

cleanup() {
    [[ -n "$TEMP_FILE" && -f "$TEMP_FILE" ]] && rm -f "$TEMP_FILE"
}
trap cleanup EXIT

notify_err() {
    notify-send "$(tr "app_name")" "$1" -u critical 2>/dev/null || true
}

notify_info() {
    notify-send "$(tr "app_name")" "$1" -t 2000 2>/dev/null || true
}

log_debug() {
    if [[ "${AUTOCORRECT_DEBUG:-0}" == "1" ]]; then
        echo "[DEBUG] $*" >&2
    fi
}

for cmd in wl-copy wl-paste wtype jq curl notify-send; do
    if ! command -v "$cmd" &>/dev/null; then
        notify_err "$(tr "err_cmd_missing" "$cmd")"
        exit 1
    fi
done

if ! curl -sf --max-time 5 "$OLLAMA_URL/../api/tags" &>/dev/null; then
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

log_debug "Original: $ORIGINAL_TEXT"

notify_info "$(tr "correcting")"

SYSTEM_INSTRUCTION="Du bist eine reine Autokorrektur. Korrigiere den Text auf Rechtschreibung und Grammatik. Behalte die Sprache (Deutsch/Englisch) bei. Gib AUSSCHLIESSLICH den korrigierten Text aus, ohne Einleitung, ohne Erklarungen und ohne Anhfuhrungszeichen."

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

log_debug "Korrigiert: $CORRECTED_TEXT"

printf '%s' "$CORRECTED_TEXT" | wl-copy
sleep "$COPY_PASTE_DELAY"

wtype -M ctrl -P v -p v -m ctrl

if [[ "$ORIGINAL_TEXT" == "$CORRECTED_TEXT" ]]; then
    notify_info "$(tr "already_correct")"
else
    notify_info "$(tr "correction_done")"
fi

exit 0
