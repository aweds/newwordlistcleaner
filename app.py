# -*- coding: utf-8 -*-
"""
Almanca Kelime Listesi — Temizlik, Seviye Ayırma & İndirme
Streamlit Web Uygulaması
"""

import streamlit as st
import json
import io
from collections import Counter, defaultdict
from datetime import datetime

# ============================================================
# SAYFA AYARLARI
# ============================================================
st.set_page_config(
    page_title="Almanca Kelime Temizleyici",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded",
)

LEVEL_PRIORITY = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================
def word_score(word):
    """Kelimenin zenginlik puanı (daha yüksek = daha zengin)."""
    return sum([
        bool(word.get("artikel")),
        bool(word.get("plural")),
        bool(word.get("example_tr")),
        bool(word.get("example_de")),
        bool(word.get("tip")),
        len(word.get("related", [])),
    ])


def merge_word_data(existing, new):
    """İki kelime kaydını birleştir."""
    merged = existing.copy()

    for key in ["artikel", "plural", "example_tr", "example_de", "tip", "type_tr"]:
        if not merged.get(key) and new.get(key):
            merged[key] = new[key]

    # Related birleştir
    existing_related = set(merged.get("related", []))
    new_related = set(new.get("related", []))
    merged["related"] = sorted(existing_related | new_related)

    # En düşük seviyeyi tut
    old_level = merged.get("level", "A1")
    new_level = new.get("level", "A1")
    if LEVEL_PRIORITY.get(new_level, 99) < LEVEL_PRIORITY.get(old_level, 99):
        merged["level"] = new_level

    # Kategori geçmişi
    if "_also_in" not in merged:
        merged["_also_in"] = []
    src = new.get("_source_category")
    if src and src not in merged["_also_in"]:
        merged["_also_in"].append(src)

    return merged


def process_data(data):
    """
    Ana işlem: tekrarları temizle, kategorilere göre yeniden grupla.
    Dönen: (categories, all_words, duplicates_info, level_counts)
    """
    # Tüm kelimeleri düz listeye al
    all_words = []
    for cat in data.get("categories", []):
        for word in cat.get("words", []):
            w = word.copy()
            w["_source_category"] = cat["id"]
            w["_source_category_name"] = cat.get("name", cat["id"])
            w["_source_emoji"] = cat.get("emoji", "📝")
            all_words.append(w)

    # Grupla
    grouped = defaultdict(list)
    for w in all_words:
        key = w["de"].strip().lower()
        grouped[key].append(w)

    # Birleştir
    unique_words = []
    duplicates_info = []

    for key, words in grouped.items():
        if len(words) == 1:
            unique_words.append(words[0])
        else:
            richest = max(words, key=word_score)
            merged = richest
            for other in words:
                if other is not richest:
                    merged = merge_word_data(merged, other)

            unique_words.append(merged)
            duplicates_info.append({
                "de": richest["de"],
                "count": len(words),
                "categories": [w["_source_category"] for w in words],
                "levels": [w.get("level", "?") for w in words],
                "kept_level": merged.get("level", "?"),
                "kept_category": merged["_source_category"],
            })

    # Kategorilere göre yeniden grupla (orijinal kategori id'lerini koru)
    cat_map = {}
    cat_order = []
    for w in unique_words:
        cid = w["_source_category"]
        if cid not in cat_map:
            cat_map[cid] = {
                "id": cid,
                "name": w["_source_category_name"],
                "emoji": w["_source_emoji"],
                "words": [],
            }
            cat_order.append(cid)

        clean_word = {k: v for k, v in w.items() if not k.startswith("_")}
        cat_map[cid]["words"].append(clean_word)

    categories = [cat_map[cid] for cid in cat_order]

    # Seviye dağılımı
    level_counts = Counter(w.get("level", "A1") for w in unique_words)

    return categories, unique_words, duplicates_info, level_counts


def build_output(categories, level_counts):
    """Çıktı JSON'unu oluştur."""
    total = sum(len(c["words"]) for c in categories)
    return {
        "meta": {
            "level": "A1-B1",
            "language_pair": "de-tr",
            "total": total,
            "version": "3.0",
            "description": "Almanca A1-B1 seviye kelime listesi — temizlenmiş, seviye etiketli",
            "level_distribution": dict(level_counts),
            "generated_at": datetime.now().isoformat(),
        },
        "categories": categories,
    }


def filter_by_level(categories, target_level):
    """Belirli seviyedeki kelimeleri içeren kategorileri döndür."""
    result = []
    for cat in categories:
        level_words = [w for w in cat["words"] if w.get("level") == target_level]
        if level_words:
            result.append({
                "id": cat["id"],
                "name": cat["name"],
                "emoji": cat.get("emoji", ""),
                "words": level_words,
            })
    return result


def to_json_bytes(data):
    """JSON'u indirilebilir byte'a çevir."""
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/germany.png", width=80)
    st.title("🧹 Almanca Kelime")
    st.caption("Temizlik & Seviye Ayırma Aracı")

    st.divider()

    st.markdown("### 📖 Nasıl Kullanılır?")
    st.markdown("""
    1. **words.json** dosyanızı yükleyin
    2. **İşle** butonuna basın
    3. Sonuçları önizleyin
    4. Seviye bazında indirin
    """)

    st.divider()

    st.markdown("### ⚙️ Seviye Sistemi")
    st.markdown("""
    - 🟢 **A1** — Başlangıç
    - 🟡 **A2** — Temel
    - 🔴 **B1** — Orta
    """)

    st.divider()
    st.caption("© 2026 — Streamlit Cloud")


# ============================================================
# ANA SAYFA
# ============================================================
st.title("🧹 Almanca Kelime Listesi — Temizlik & Seviye Ayırma")
st.markdown(
    "**words.json** dosyanızı yükleyin, tekrarları otomatik temizleyin "
    "ve A1/A2/B1 seviyelerine ayırın."
)

# --- Dosya Yükleme ---
uploaded_file = st.file_uploader(
    "📤 words.json dosyasını yükleyin",
    type=["json"],
    help="Streamlit Cloud'da dosya yükleme 200 MB'a kadar destekler",
)

if uploaded_file is None:
    st.info("👆 Başlamak için bir **words.json** dosyası yükleyin.")

    with st.expander("📋 Beklenen JSON Formatı (örnek)"):
        st.code("""{
  "meta": { "level": "A1", "language_pair": "de-tr" },
  "categories": [
    {
      "id": "selamlasma",
      "name": "Selamlaşma",
      "emoji": "👋",
      "words": [
        {
          "de": "Hallo",
          "tr": "Merhaba",
          "artikel": null,
          "plural": null,
          "type": "ausruf",
          "type_tr": "ünlem",
          "level": "A1",
          "example_tr": "Merhaba!",
          "example_de": "Hallo!",
          "tip": "...",
          "related": ["Hi"]
        }
      ]
    }
  ]
}""", language="json")
    st.stop()

# --- Yükleme başarılı ---
try:
    data = json.load(uploaded_file)
except json.JSONDecodeError as e:
    st.error(f"❌ JSON hatası: {e}")
    st.stop()

if "categories" not in data:
    st.error("❌ Geçersiz format: 'categories' anahtarı yok.")
    st.stop()

original_total = sum(len(c.get("words", [])) for c in data["categories"])

# --- Bilgi kartları ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📁 Kategori", len(data["categories"]))
with col2:
    st.metric("📖 Orijinal Kelime", original_total)
with col3:
    st.metric("📄 Dosya", uploaded_file.name)

st.divider()

# --- İşleme butonu ---
if st.button("🚀 İşle ve Temizle", type="primary", use_container_width=True):

    with st.spinner("🔄 İşleniyor..."):
        categories, unique_words, duplicates_info, level_counts = process_data(data)

    # Session state'e kaydet
    st.session_state["processed"] = {
        "categories": categories,
        "unique_words": unique_words,
        "duplicates_info": duplicates_info,
        "level_counts": level_counts,
        "original_total": original_total,
    }

    st.success(f"✅ İşlem tamamlandı! **{original_total - len(unique_words)}** tekrar silindi.")
    st.rerun()


# --- Sonuçları göster ---
if "processed" in st.session_state:
    p = st.session_state["processed"]
    categories = p["categories"]
    unique_words = p["unique_words"]
    duplicates_info = p["duplicates_info"]
    level_counts = p["level_counts"]
    original_total = p["original_total"]

    st.divider()
    st.header("📊 Sonuçlar")

    # --- Metrikler ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Orijinal", original_total)
    with col2:
        st.metric("Temizlenmiş", len(unique_words),
                  delta=f"-{original_total - len(unique_words)}")
    with col3:
        st.metric("Kategori", len(categories))
    with col4:
        st.metric("Tekrar Grubu", len(duplicates_info))

    # --- Seviye dağılımı ---
    st.subheader("📈 Seviye Dağılımı")

    col1, col2, col3 = st.columns(3)
    total_clean = len(unique_words)

    with col1:
        a1 = level_counts.get("A1", 0)
        st.metric("🟢 A1", a1, delta=f"{a1 / total_clean * 100:.1f}%" if total_clean else "0%")
    with col2:
        a2 = level_counts.get("A2", 0)
        st.metric("🟡 A2", a2, delta=f"{a2 / total_clean * 100:.1f}%" if total_clean else "0%")
    with col3:
        b1 = level_counts.get("B1", 0)
        st.metric("🔴 B1", b1, delta=f"{b1 / total_clean * 100:.1f}%" if total_clean else "0%")

    # Bar chart
    import pandas as pd
    chart_data = pd.DataFrame({
        "Seviye": ["A1", "A2", "B1"],
        "Kelime": [level_counts.get("A1", 0),
                   level_counts.get("A2", 0),
                   level_counts.get("B1", 0)]
    })
    st.bar_chart(chart_data.set_index("Seviye"), color="#4CAF50")

    # --- Sekmeler ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Tekrarlar",
        "📖 Kelimeleri Gez",
        "📥 İndir",
        "ℹ️ Rapor",
    ])

    # === TAB 1: Tekrarlar ===
    with tab1:
        st.subheader(f"🔄 Bulunan {len(duplicates_info)} Tekrar Grubu")

        if not duplicates_info:
            st.success("🎉 Hiç tekrar bulunmadı!")
        else:
            # DataFrame olarak göster
            df = pd.DataFrame([
                {
                    "Kelime": d["de"],
                    "Kaç kez": d["count"],
                    "Kategoriler": ", ".join(d["categories"]),
                    "Seviyeler": ", ".join(d["levels"]),
                    "Tutulan": d["kept_level"],
                }
                for d in duplicates_info
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Arama
            search = st.text_input("🔎 Tekrar ara", placeholder="örn: halb")
            if search:
                filtered = df[df["Kelime"].str.contains(search, case=False, na=False)]
                st.dataframe(filtered, use_container_width=True, hide_index=True)

    # === TAB 2: Kelimeleri Gez ===
    with tab2:
        st.subheader("📖 Kelimeleri İncele")

        col1, col2, col3 = st.columns(3)
        with col1:
            level_filter = st.selectbox(
                "Seviye",
                ["Tümü", "A1", "A2", "B1"],
                key="browse_level"
            )
        with col2:
            cat_options = ["Tümü"] + [c["name"] for c in categories]
            cat_filter = st.selectbox("Kategori", cat_options, key="browse_cat")
        with col3:
            search_text = st.text_input("Ara", placeholder="Almanca veya Türkçe...")

        # Filtrele
        filtered_words = []
        for cat in categories:
            if cat_filter != "Tümü" and cat["name"] != cat_filter:
                continue
            for w in cat["words"]:
                if level_filter != "Tümü" and w.get("level") != level_filter:
                    continue
                if search_text:
                    needle = search_text.lower()
                    if needle not in w["de"].lower() and needle not in w["tr"].lower():
                        continue
                filtered_words.append({
                    "Kategori": cat["name"],
                    "Almanca": w["de"],
                    "Türkçe": w["tr"],
                    "Art.": w.get("artikel") or "—",
                    "Çoğul": w.get("plural") or "—",
                    "Seviye": w.get("level", "?"),
                    "Tip": w.get("type_tr", w.get("type", "")),
                    "Örnek (DE)": w.get("example_de", ""),
                    "Örnek (TR)": w.get("example_tr", ""),
                })

        st.caption(f"**{len(filtered_words)}** kelime gösteriliyor")
        if filtered_words:
            st.dataframe(
                pd.DataFrame(filtered_words),
                use_container_width=True,
                hide_index=True,
                height=500,
            )
        else:
            st.info("Filtreye uyan kelime bulunamadı.")

    # === TAB 3: İndir ===
    with tab3:
        st.subheader("📥 Dosyaları İndir")

        # Master (tüm seviyeler)
        master_data = build_output(categories, level_counts)
        st.download_button(
            "📦 **words_master.json** — Tüm kelimeler (temizlenmiş)",
            data=to_json_bytes(master_data),
            file_name="words_master.json",
            mime="application/json",
            use_container_width=True,
            type="primary",
        )

        st.divider()

        # A1
        a1_cats = filter_by_level(categories, "A1")
        a1_data = build_output(a1_cats, {"A1": level_counts.get("A1", 0)})
        a1_data["meta"]["level"] = "A1"
        a1_data["meta"]["description"] = "Almanca A1 seviye kelime listesi"
        st.download_button(
            f"🟢 **words_a1.json** — {level_counts.get('A1', 0)} kelime",
            data=to_json_bytes(a1_data),
            file_name="words_a1.json",
            mime="application/json",
            use_container_width=True,
        )

        # A2
        a2_cats = filter_by_level(categories, "A2")
        a2_data = build_output(a2_cats, {"A2": level_counts.get("A2", 0)})
        a2_data["meta"]["level"] = "A2"
        a2_data["meta"]["description"] = "Almanca A2 seviye kelime listesi"
        st.download_button(
            f"🟡 **words_a2.json** — {level_counts.get('A2', 0)} kelime",
            data=to_json_bytes(a2_data),
            file_name="words_a2.json",
            mime="application/json",
            use_container_width=True,
        )

        # B1
        b1_cats = filter_by_level(categories, "B1")
        b1_data = build_output(b1_cats, {"B1": level_counts.get("B1", 0)})
        b1_data["meta"]["level"] = "B1"
        b1_data["meta"]["description"] = "Almanca B1 seviye kelime listesi"
        st.download_button(
            f"🔴 **words_b1.json** — {level_counts.get('B1', 0)} kelime",
            data=to_json_bytes(b1_data),
            file_name="words_b1.json",
            mime="application/json",
            use_container_width=True,
        )

        st.divider()

        # CSV (Anki)
        csv_lines = ["Almanca;Türkçe;Seviye;Kategori;Örnek"]
        for cat in categories:
            for w in cat["words"]:
                de = w["de"].replace(";", ",")
                tr = w["tr"].replace(";", ",")
                ex = w.get("example_de", "").replace(";", ",")
                csv_lines.append(
                    f"{de};{tr};{w.get('level', '?')};{cat['name']};{ex}"
                )
        csv_bytes = "\ufeff".join(csv_lines).encode("utf-8")  # BOM for Excel

        st.download_button(
            "📊 **anki_deck.csv** — Anki/Excel için (noktalı virgülle ayrılmış)",
            data=csv_bytes,
            file_name="anki_deck.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.caption("💡 Anki'de içe aktarırken ayırıcı olarak **;** seçin.")

    # === TAB 4: Rapor ===
    with tab4:
        st.subheader("ℹ️ Detaylı Rapor")

        # Kategori bazlı seviye dağılımı
        st.markdown("### 📁 Kategori Bazlı Seviye Dağılımı")

        cat_rows = []
        for cat in categories:
            levels_in_cat = Counter(w.get("level", "?") for w in cat["words"])
            cat_rows.append({
                "Kategori": f"{cat.get('emoji', '')} {cat['name']}",
                "Toplam": len(cat["words"]),
                "A1": levels_in_cat.get("A1", 0),
                "A2": levels_in_cat.get("A2", 0),
                "B1": levels_in_cat.get("B1", 0),
            })

        df_cat = pd.DataFrame(cat_rows).sort_values("Toplam", ascending=False)
        st.dataframe(df_cat, use_container_width=True, hide_index=True, height=400)

        st.divider()

        # Kelime tipi dağılımı
        st.markdown("### 📚 Kelime Tipi Dağılımı")
        type_counts = Counter(w.get("type", "?") for w in unique_words)
        df_type = pd.DataFrame(
            [{"Tip": k, "Sayı": v} for k, v in type_counts.most_common()]
        )
        st.dataframe(df_type, use_container_width=True, hide_index=True)

        st.divider()

        # Ham JSON raporu
        st.markdown("### 🗂️ Ham Rapor (JSON)")
        report = {
            "total_words": len(unique_words),
            "by_level": dict(level_counts),
            "by_type": dict(type_counts),
            "duplicates_removed": len(duplicates_info),
            "generated_at": datetime.now().isoformat(),
        }
        st.json(report)

        st.download_button(
            "📥 report.json indir",
            data=to_json_bytes(report),
            file_name="report.json",
            mime="application/json",
        )

else:
    # Henüz işlenmemiş
    st.divider()
    st.info("👆 Yukarıdaki **🚀 İşle ve Temizle** butonuna basın.")


# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(
    "🧹 **Almanca Kelime Temizleyici** — "
    "Streamlit ile yapılmıştır | "
    "GitHub'da açık kaynak"
)
