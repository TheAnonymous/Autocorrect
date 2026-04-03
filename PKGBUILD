# Maintainer: TheAnonymous <github.com/TheAnonymous>
pkgname=ollama-autocorrect-git
provides=('ollama-autocorrect')
conflicts=('ollama-autocorrect')
source=("git+https://github.com/TheAnonymous/Autocorrect.git")
sha256sums=('SKIP')

pkgver() {
    cd "Autocorrect"
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

package() {
    cd "Autocorrect"

    install -d "$pkgdir/usr/lib/autocorrect"
    install -d "$pkgdir/usr/bin"

    for py in autocorrect.py autocorrect_undo.py ollama_manager.py ollama_tui.py ollama-tray.py i18n.py; do
        install -Dm755 "$py" "$pkgdir/usr/lib/autocorrect/$py"
    done

    cat > "$pkgdir/usr/bin/autocorrect" << 'BINSCRIPT'
#!/bin/bash
exec python3 /usr/lib/autocorrect/autocorrect.py "$@"
BINSCRIPT
    chmod 755 "$pkgdir/usr/bin/autocorrect"

    cat > "$pkgdir/usr/bin/autocorrect-undo" << 'BINSCRIPT'
#!/bin/bash
exec python3 /usr/lib/autocorrect/autocorrect_undo.py "$@"
BINSCRIPT
    chmod 755 "$pkgdir/usr/bin/autocorrect-undo"

    cat > "$pkgdir/usr/bin/ollama-manager" << 'BINSCRIPT'
#!/bin/bash
exec python3 /usr/lib/autocorrect/ollama_manager.py "$@"
BINSCRIPT
    chmod 755 "$pkgdir/usr/bin/ollama-manager"

    cat > "$pkgdir/usr/bin/ollama-tui" << 'BINSCRIPT'
#!/bin/bash
exec python3 /usr/lib/autocorrect/ollama_tui.py "$@"
BINSCRIPT
    chmod 755 "$pkgdir/usr/bin/ollama-tui"

    install -Dm755 "ollama-tray.py" "$pkgdir/usr/bin/ollama-tray"
    sed -i '1s|.*|#!/usr/bin/env python3|' "$pkgdir/usr/bin/ollama-tray"

    cat > "$pkgdir/usr/lib/systemd/user/ollama-tray.service" << 'SVCEOF'
[Unit]
Description=Ollama Tray Manager
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/ollama-tray
Restart=on-failure
RestartSec=5
Environment=WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0}
Environment=XDG_SESSION_TYPE=wayland

[Install]
WantedBy=graphical-session.target
SVCEOF

    cat > "$pkgdir/etc/xdg/autostart/ollama-tray.desktop" << 'DSKEOF'
[Desktop Entry]
Type=Application
Name=Ollama Tray Manager
Comment=System tray indicator for Ollama
Exec=/usr/bin/ollama-tray
Icon=utilities-terminal
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
X-KDE-autostart-after-panell=true
DSKEOF

    install -Dm644 "LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
