#!/bin/sh
# Evrakçı'yı yalnızca bu kullanıcı için kurar; yönetici (root) izni gerekmez.
#   ./kur.sh      kurar ya da eski kurulumun yerine yenisini koyar
# İşler ve şablonlar ayrı bir klasörde durur; kurulum onlara dokunmaz.
set -eu

hata() {
    echo "$1" >&2
    exit 1
}

# EVRAKCI_ROOT_KURULUMU=1: yalnızca root'tan başka kullanıcısı olmayan kaplar (container) için.
if [ "$(id -u)" = 0 ] && [ "${EVRAKCI_ROOT_KURULUMU:-}" != 1 ]; then
    hata "kur.sh yönetici (root/sudo) olarak çalıştırılmaz; kendi kullanıcınızla çalıştırın: ./kur.sh"
fi
if [ -z "${HOME:-}" ] || [ "$HOME" = "/" ]; then
    hata "Ev klasörü (HOME) belirsiz; kurulum yapılmadı."
fi
kaynak=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
veri="${XDG_DATA_HOME:-}"
case "$veri" in
    /*) ;;
    *) veri="$HOME/.local/share" ;;  # XDG: göreli bir yol yok sayılır
esac
hedef="$veri/evrakci-uygulama"
bin="$HOME/.local/bin"
menu="$veri/applications"
simge="$veri/icons/hicolor/scalable/apps"

if [ ! -x "$kaynak/uygulama/evrakci-arayuz" ] || [ ! -x "$kaynak/uygulama/evrakci" ]; then
    hata "Uygulama dosyaları eksik: $kaynak/uygulama"
fi

sil() {
    chmod -R u+w "$1" 2>/dev/null || true
    rm -rf "$1"
}

mkdir -p "$veri" "$bin"
# Yarım kalmış önceki kurulumların artıkları.
for artik in "$hedef".yeni.* "$hedef".eski.*; do
    if [ -e "$artik" ]; then sil "$artik"; fi
done
# Yeni kopya önce yanına yazılır; yarım kalan bir kopya hiç kullanılmaz.
gecici="$hedef.yeni.$$"
trap 'sil "$gecici"' EXIT
cp -R "$kaynak/uygulama" "$gecici"
cp "$kaynak/kaldir.sh" "$gecici/kaldir.sh"
chmod +x "$gecici/kaldir.sh"
# kaldir.sh, ortam sonradan değişse de tam olarak bu kurulumu kaldırır.
printf '%s\n%s\n%s\n%s\n' "$hedef" "$bin" "$menu" "$simge" > "$gecici/kurulum-yollari.txt"
if [ -e "$hedef" ]; then
    mv "$hedef" "$hedef.eski.$$"
fi
mv "$gecici" "$hedef"
trap - EXIT
if [ -e "$hedef.eski.$$" ]; then sil "$hedef.eski.$$"; fi

for ad in evrakci evrakci-arayuz; do
    yol="$bin/$ad"
    if [ -L "$yol" ]; then
        # Yalnızca bu kurulumun bağlantısı ya da hiçbir yere gitmeyen bir bağlantı değiştirilir.
        if [ "$(readlink "$yol")" = "$hedef/$ad" ] || [ ! -e "$yol" ]; then
            ln -sfn "$hedef/$ad" "$yol"
        else
            echo "Not: $yol başka bir programa ait; değiştirilmedi."
        fi
    elif [ -e "$yol" ]; then
        echo "Not: $yol başka bir programa ait; değiştirilmedi."
    else
        ln -s "$hedef/$ad" "$yol"
    fi
done

# Menü kaydı: Exec satırı bu karakterleri taşıyamaz, o zaman kayıt eklenmez.
case "$hedef" in
    *'"'* | *'`'* | *'$'* | *'\'* | *'%'*)
        echo "Not: kurulum yolunda \" \` \$ \\ ya da % var; menü kaydı eklenmedi."
        echo "Başlatmak için: $hedef/evrakci-arayuz"
        ;;
    *)
        mkdir -p "$menu" "$simge"
        cp "$kaynak/evrakci.svg" "$simge/evrakci.svg"
        cat > "$menu/evrakci-arayuz.desktop" <<MENU
[Desktop Entry]
Type=Application
Name=Evrakçı
Comment=Taranan evrakı belgelere ayırır, adlandırır ve dışa aktarır
Exec="$hedef/evrakci-arayuz"
Icon=evrakci
StartupWMClass=evrakci-arayuz
Terminal=false
Categories=Office;
MENU
        ;;
esac

echo "Evrakçı kuruldu: $hedef"
echo "Başlatmak için uygulama menüsünden Evrakçı'yı seçin ya da: evrakci-arayuz"
echo "Kaldırmak için: $hedef/kaldir.sh"
if ! command -v tesseract >/dev/null 2>&1; then
    echo "Uyarı: Tesseract bulunamadı; OCR (metin katmanı) için gerekir:"
    echo "    sudo apt install tesseract-ocr"
fi
# Pencerenin (Qt) sistemden istediği kütüphaneler.
qxcb="$hedef/lib/PySide6/Qt/plugins/platforms/libqxcb.so"
if [ -f "$qxcb" ] && command -v ldd >/dev/null 2>&1; then
    eksik=$(LD_LIBRARY_PATH="$hedef/lib/PySide6/Qt/lib" ldd "$qxcb" 2>/dev/null \
        | awk '/not found/ { print $1 }' | sort -u | tr '\n' ' ')
    if [ -n "$eksik" ]; then
        echo "Uyarı: pencere için eksik sistem kütüphaneleri: $eksik"
        echo "    sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-util1 libxcb-image0" \
            "libxcb-keysyms1 libxcb-render-util0 libxcb-xkb1 libxcb-shape0 libxkbcommon-x11-0 libegl1 libgl1 libdbus-1-3"
    fi
fi
case ":$PATH:" in
    *":$bin:"*) ;;
    *) echo "Not: $bin PATH içinde değil; oturumu kapatıp açınca çoğu sistemde eklenir." ;;
esac
