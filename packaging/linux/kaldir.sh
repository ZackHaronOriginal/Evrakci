#!/bin/sh
# Evrakçı'yı kaldırır: program klasörü, komut bağlantıları ve menü kaydı.
# İşleriniz, şablonlarınız ve ayarlarınız silinmez.
set -eu

if [ -z "${HOME:-}" ] || [ "$HOME" = "/" ]; then
    echo "Ev klasörü (HOME) belirsiz; hiçbir şey silinmedi." >&2
    exit 1
fi
veri="${XDG_DATA_HOME:-$HOME/.local/share}"
hedef="$veri/evrakci-uygulama"
bin="$HOME/.local/bin"

for ad in evrakci evrakci-arayuz; do
    # Yalnızca bu kurulumun bağlantısı silinir.
    if [ -L "$bin/$ad" ] && [ "$(readlink "$bin/$ad")" = "$hedef/$ad" ]; then
        rm -f "$bin/$ad"
    fi
done
rm -f "$veri/applications/evrakci.desktop"
echo "Evrakçı kaldırıldı. İşleriniz ve şablonlarınız silinmedi."
rm -rf "$hedef"
