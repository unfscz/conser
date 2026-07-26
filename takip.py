import hashlib
import os
import re
from bs4 import BeautifulSoup
import requests
from pushbullet import Pushbullet

# --- AYARLAR ---
API_KEY = "o.5I5ylsDKv92FcKMVxBjb5tf6VRIYW7Mi"
pb = Pushbullet(API_KEY)

# Takip etmek istediğin iki farklı URL:
FESTIVAL_URL = "https://milyonbilet.com/etkinlik/4b29da50-5bce-462f-aa20-f74ad1aa44b2/"
BILET_URL = "https://www.biletix.com/etkinlik/5PFZ3/TURKIYE/tr"

# Hafıza dosyaları
KADRO_HAFIZA = "son_kadro.txt"
FIYAT_HAFIZA = "son_fiyat.txt"


def sayfayi_getir(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"[{url}] Sayfa getirme hatası: {e}")
        return None


# 1. FESTİVAL KADRO CONTROLÜ
def kadro_kontrol_et():
    soup = sayfayi_getir(FESTIVAL_URL)
    if not soup:
        return

    # Sitedeki dinamik kodları (sayaçlar, scriptler vs.) temizliyoruz ki yanlış alarm vermesin
    for tag in soup(["script", "style", "meta", "noscript"]):
        tag.decompose()

    yeni_icerik = soup.get_text(strip=True)
    yeni_hash = hashlib.md5(yeni_icerik.encode("utf-8")).hexdigest()

    eski_hash = ""
    if os.path.exists(KADRO_HAFIZA):
        with open(KADRO_HAFIZA, "r") as f:
            eski_hash = f.read().strip()

    if eski_hash == "":
        with open(KADRO_HAFIZA, "w") as f:
            f.write(yeni_hash)
        print("[Kadro] İlk durum kaydedildi. Takip aktif.")
    elif yeni_hash != eski_hash:
        print("[Kadro] KADRO/SİTE GÜNCELLENDİ!")
        pb.push_link("🚨 FESTİVAL KADROSU / SİTESİ GÜNCELLENDİ!", FESTIVAL_URL)
        with open(KADRO_HAFIZA, "w") as f:
            f.write(yeni_hash)
    else:
        print("[Kadro] Kadro sayfasında değişiklik yok.")


# 2. BİLET FİYAT / STOK KONTROLÜ
def fiyat_kontrol_et():
    soup = sayfayi_getir(BILET_URL)
    if not soup:
        return

    metin = soup.get_text()

    # Bilet sitesindeki TL / ₺ geçen fiyat ibarelerini bulur
    fiyatlar = re.findall(
        r"\b\d+(?:\.\d+)?\s*(?:TL|₺)\b", metin, flags=re.IGNORECASE
    )

    if not fiyatlar:
        # Alternatif: Fiyatlar özel class içinde yazıyorsa
        fiyat_elementi = soup.select_one(
            ".ticket-price, .price, .bilet-fiyat, .product-price"
        )
        if fiyat_elementi:
            fiyatlar = [fiyat_elementi.get_text(strip=True)]

    if fiyatlar:
        guncel_fiyat = " | ".join(set(fiyatlar))
        print(f"[Bilet] Tespit edilen fiyat/stok: {guncel_fiyat}")

        eski_fiyat = ""
        if os.path.exists(FIYAT_HAFIZA):
            with open(FIYAT_HAFIZA, "r") as f:
                eski_fiyat = f.read().strip()

        if eski_fiyat == "":
            with open(FIYAT_HAFIZA, "w") as f:
                f.write(guncel_fiyat)
            print("[Bilet] İlk bilet durumu kaydedildi.")
        elif guncel_fiyat != eski_fiyat:
            print("[Bilet] BİLET DURUMU/FİYATI DEĞİŞTİ!")
            pb.push_note(
                "🚨 BİLET FİYATI / DURUMU DEĞİŞTİ!",
                f"Yeni Durum: {guncel_fiyat}\nEski Durum: {eski_fiyat}\nLink: {BILET_URL}",
            )
            with open(FIYAT_HAFIZA, "w") as f:
                f.write(guncel_fiyat)
        else:
            print("[Bilet] Bilet sayfasında değişiklik yok.")
    else:
        print("[Bilet] Sayfada belirgin bir bilet fiyatı bulunamadı.")


def main():
    kadro_kontrol_et()
    fiyat_kontrol_et()


if __name__ == "__main__":
    main()