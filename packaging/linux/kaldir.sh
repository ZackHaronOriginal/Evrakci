#!/bin/sh
# Evrakçı'yı kaldırır: program klasörü, komut bağlantıları, menü kaydı ve simge.
# İşleriniz, şablonlarınız ve ayarlarınız silinmez.
# kur.sh'nin kopyaladığı yerden çalıştırın (yolu kur.sh yazar).
set -eu

hata() {
    echo "$1" >&2
    exit 1
}

burasi=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
yollar="$burasi/kurulum-yollari.txt"
if [ ! -f "$burasi/evrakci-arayuz" ] || [ ! -f "$yollar" ]; then
    hata "Bu klasör bir Evrakçı kurulumu değil: $burasi (kaldir.sh'yi kurulum klasöründen çalıştırın)"
fi
{
    read -r hedef
    read -r bin
    read -r menu
    read -r simge
} < "$yollar"
if [ "$(CDPATH='' cd -- "$hedef" 2>/dev/null && pwd -P)" != "$burasi" ]; then
    hata "Kurulum kaydı bu klasörle uyuşmuyor: $yollar"
fi

for ad in evrakci evrakci-arayuz; do
    # Yalnızca bu kurulumun bağlantısı silinir.
    if [ -L "$bin/$ad" ] && [ "$(readlink "$bin/$ad")" = "$hedef/$ad" ]; then
        rm -f "$bin/$ad"
    fi
done
rm -f "$menu/evrakci-arayuz.desktop" "$simge/evrakci.svg"
chmod -R u+w "$hedef" 2>/dev/null || true
rm -rf "$hedef"
echo "Evrakçı kaldırıldı. İşleriniz ve şablonlarınız silinmedi."
