#!/bin/bash

set -euo pipefail

OLLAMA_SERVICE="ollama"
OLLAMA_URL="http://localhost:11434"

is_running() {
    curl -sf --max-time 3 "$OLLAMA_URL/api/tags" &>/dev/null
}

is_service_active() {
    systemctl --user is-active "$OLLAMA_SERVICE" &>/dev/null || \
    systemctl is-active "$OLLAMA_SERVICE" &>/dev/null
}

get_service_type() {
    if systemctl --user is-enabled "$OLLAMA_SERVICE" &>/dev/null 2>&1; then
        echo "user"
    elif systemctl is-enabled "$OLLAMA_SERVICE" &>/dev/null 2>&1; then
        echo "system"
    else
        echo "none"
    fi
}

get_memory_usage() {
    local pid
    pid=$(pgrep -f "ollama serve" 2>/dev/null | head -1) || true
    if [[ -n "$pid" ]]; then
        local rss_kb
        rss_kb=$(ps -o rss= -p "$pid" 2>/dev/null | tr -d ' ') || true
        if [[ -n "$rss_kb" && "$rss_kb" -gt 0 ]]; then
            echo "$(( rss_kb / 1024 ))"
        else
            echo "?"
        fi
    else
        echo "0"
    fi
}

get_model_info() {
    if is_running; then
        local models
        models=$(curl -sf --max-time 3 "$OLLAMA_URL/api/tags" 2>/dev/null) || true
        if [[ -n "$models" ]]; then
            echo "$models" | jq -r '.models[]?.name // empty' 2>/dev/null | head -5 || true
        fi
    fi
}

status() {
    if is_running; then
        local mem
        mem=$(get_memory_usage)
        echo "running"
        echo "memory_mb=$mem"
        local svc_type
        svc_type=$(get_service_type)
        echo "service_type=$svc_type"
        local models
        models=$(get_model_info)
        if [[ -n "$models" ]]; then
            echo "models=$models"
        fi
    elif is_service_active; then
        echo "service_active_no_response"
    else
        echo "stopped"
    fi
}

start() {
    if is_running; then
        echo "already_running"
        return 0
    fi

    local svc_type
    svc_type=$(get_service_type)

    if [[ "$svc_type" != "none" ]]; then
        if [[ "$svc_type" == "user" ]]; then
            systemctl --user start "$OLLAMA_SERVICE" 2>/dev/null || true
        else
            sudo systemctl start "$OLLAMA_SERVICE" 2>/dev/null || true
        fi
    else
        nohup ollama serve &>/dev/null &
    fi

    local retries=30
    while [[ $retries -gt 0 ]]; do
        if is_running; then
            echo "started"
            return 0
        fi
        sleep 1
        retries=$((retries - 1))
    done

    echo "start_timeout"
    return 1
}

stop() {
    if ! is_running; then
        echo "already_stopped"
        return 0
    fi

    local svc_type
    svc_type=$(get_service_type)

    if [[ "$svc_type" != "none" ]]; then
        if [[ "$svc_type" == "user" ]]; then
            systemctl --user stop "$OLLAMA_SERVICE" 2>/dev/null || true
        else
            sudo systemctl stop "$OLLAMA_SERVICE" 2>/dev/null || true
        fi
    fi

    local pid
    pid=$(pgrep -f "ollama serve" 2>/dev/null | head -1) || true
    if [[ -n "$pid" ]]; then
        kill "$pid" 2>/dev/null || true
    fi

    local retries=15
    while [[ $retries -gt 0 ]]; do
        if ! is_running; then
            echo "stopped"
            return 0
        fi
        sleep 1
        retries=$((retries - 1))
    done

    pid=$(pgrep -f "ollama serve" 2>/dev/null | head -1) || true
    if [[ -n "$pid" ]]; then
        kill -9 "$pid" 2>/dev/null || true
    fi

    echo "force_stopped"
}

case "${1:-status}" in
    status)  status  ;;
    start)   start   ;;
    stop)    stop    ;;
    restart) stop; sleep 1; start ;;
    *)
        echo "Usage: $0 {status|start|stop|restart}"
        exit 1
        ;;
esac
