#!/bin/sh
# Evrakçı'yı yalnızca bu kullanıcı için kurar; yönetici (root) izni gerekmez.
#   ./kur.sh      kurar ya da eski kurulumun yerine yenisini koyar
# İşler ve şablonlar ayrı bir klasörde durur; kurulum onlara dokunmaz.
set -eu

if [ -z "${HOME:-}" ] || [ "$HOME" = "/" ]; then
    echo "Ev klasörü (HOME) belirsiz; kurulum yapılmadı." >&2
    exit 1
fi
kaynak=$(cd "$(dirname "$0")" && pwd)
veri="${XDG_DATA_HOME:-$HOME/.local/share}"
hedef="$veri/evrakci-uygulama"
bin="$HOME/.local/bin"
menu="$veri/applications"

if [ ! -x "$kaynak/uygulama/evrakci-arayuz" ] || [ ! -x "$kaynak/uygulama/evrakci" ]; then
    echo "Uygulama dosyaları eksik: $kaynak/uygulama" >&2
    exit 1
fi

mkdir -p "$veri" "$bin" "$menu"
# Yeni kopya önce yanına yazılır; yarım kalan bir kopya hiç kullanılmaz.
gecici="$hedef.yeni.$$"
rm -rf "$gecici"
cp -R "$kaynak/uygulama" "$gecici"
cp "$kaynak/kaldir.sh" "$gecici/kaldir.sh"
chmod +x "$gecici/kaldir.sh"
rm -rf "$hedef"
mv "$gecici" "$hedef"

for ad in evrakci evrakci-arayuz; do
    if [ -e "$bin/$ad" ] && [ ! -L "$bin/$ad" ]; then
        echo "Not: $bin/$ad başka bir programa ait; değiştirilmedi."
    else
        ln -sf "$hedef/$ad" "$bin/$ad"
    fi
done

cat > "$menu/evrakci.desktop" <<MENU
[Desktop Entry]
Type=Application
Name=Evrakçı
Comment=Taranan evrakı belgelere ayırır, adlandırır ve dışa aktarır
Exec="$hedef/evrakci-arayuz"
Icon=x-office-document
Terminal=false
Categories=Office;
MENU

echo "Evrakçı kuruldu: $hedef"
echo "Başlatmak için uygulama menüsünden Evrakçı'yı seçin ya da: evrakci-arayuz"
if ! command -v tesseract >/dev/null 2>&1; then
    echo "Uyarı: Tesseract bulunamadı; OCR (metin katmanı) için gerekir:"
    echo "    sudo apt install tesseract-ocr"
fi
if command -v ldconfig >/dev/null 2>&1 && ! ldconfig -p 2>/dev/null | grep -q libxcb-cursor; then
    echo "Uyarı: pencere için libxcb-cursor0 gerekebilir: sudo apt install libxcb-cursor0"
fi
case ":$PATH:" in
    *":$bin:"*) ;;
    *) echo "Not: $bin PATH içinde değil; komut satırından çalıştırmak için ekleyin." ;;
esac
