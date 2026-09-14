# 🧹 Almanca Kelime Temizleyici

Almanca A1-B1 kelime listelerini temizleyen, tekrarları kaldıran ve seviyelere ayıran Streamlit uygulaması.

## ✨ Özellikler

- 📤 **JSON dosyası yükle** (words.json)
- 🔄 **Tekrarları otomatik temizle** — aynı Almanca kelime birden fazla kategoride varsa birleştirir
- 📊 **Seviye dağılımı** (A1 / A2 / B1) — görsel grafiklerle
- 🔍 **Kelime tarama** — seviye, kategori ve metin filtresiyle
- 📥 **Ayrı dosyalar indir**:
  - `words_master.json` — hepsi bir arada
  - `words_a1.json` — sadece A1
  - `words_a2.json` — sadece A2
  - `words_b1.json` — sadece B1
  - `anki_deck.csv` — Anki/Excel için
  - `report.json` — istatistikler

## 🚀 Canlı Demo

**[Streamlit Cloud'da aç](https://share.streamlit.io)** — kendi hesabınıza deploy edin

## 📦 Yerel Kurulum

```bash
# Depoyu klonla
git clone https://github.com/KULLANICI_ADI/almanca-kelime-temizleyici.git
cd almanca-kelime-temizleyici

# Sanal ortam oluştur (opsiyonel)
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt

# Çalıştır
streamlit run app.py
