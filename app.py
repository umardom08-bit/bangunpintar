import io
import math
import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.patches import Rectangle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ---------------------------------------------------------------
# 1. KONFIGURASI HALAMAN & CUSTOM CSS (TEMA MERAH - KUNING - PUTIH)
# ---------------------------------------------------------------
st.set_page_config(
    page_title="BangunPintar - Aplikasi Web RAB Rumah Otomatis",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Fondasi Terang & Bersih (Putih Dominan 60%) */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #0F172A !important;
    }
    .stApp {
        background-color: #F8FAFC !important;
    }

    /* Paksa Semua Judul, Label Input & Caption di Area Utama Berwarna Gelap */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6,
    .main p, .main span, .main label, .main div[data-testid="stCaptionContainer"] {
        color: #0F172A !important;
    }

    /* Styling Kotak Input Angka & Teks Agar Terang */
    .main input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
    }
    .main div[data-baseweb="input"], .main div[data-baseweb="base-input"] {
        background-color: #FFFFFF !important;
        border-color: #CBD5E1 !important;
    }
    .main button[data-testid="stNumberInputStepDown"],
    .main button[data-testid="stNumberInputStepUp"] {
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
    }

    /* Sidebar Styling Gelap Elegan */
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #F8FAFC !important;
    }

    /* Kartu Metrik (Putih bersih + Aksen Border Kuning/Merah) */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 2px solid #FACC15 !important;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        color: #475569 !important;
    }
    div[data-testid="stMetricValue"] div {
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        color: #DC2626 !important;
    }

    /* Kontainer Kartu */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 14px !important;
        padding: 20px !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
    }

    /* Tombol Aksi Utama (Merah Menyala ala Red Tape) */
    .stButton > button {
        border-radius: 8px;
        font-weight: 700;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"] {
        background-color: #DC2626 !important;
        border-color: #DC2626 !important;
        color: #FFFFFF !important;
    }
    .stButton > button[kind="primary"] p {
        color: #FFFFFF !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #B91C1C !important;
        border-color: #B91C1C !important;
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
    }
    .stButton > button[kind="secondary"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        color: #1E293B !important;
    }

    /* Header Banner Estetik (Kombinasi Putih, Kuning & Garis Merah) */
    .app-header {
        background: linear-gradient(135deg, #FEF08A 0%, #FEF9C3 100%);
        border-left: 6px solid #DC2626;
        border-radius: 12px;
        padding: 22px 26px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .app-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A !important;
        margin: 0;
    }
    .app-subtitle {
        font-size: 0.95rem;
        font-weight: 600;
        color: #334155 !important;
        margin-top: 6px;
        margin-bottom: 0;
    }
</style>
""", unsafe_allow_html=True)

FOLDER = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------
# 2. FUNGSI BANTU & LOGIKA PERHITUNGAN
# ---------------------------------------------------------------
@st.cache_data
def baca_csv(nama_file):
    return pd.read_csv(os.path.join(FOLDER, nama_file), encoding="utf-8-sig")


def rp(x):
    return "Rp " + f"{x:,.0f}".replace(",", ".")


def gabung_segmen(segmen):
    if not segmen:
        return []
    segmen = sorted(segmen)
    hasil = []
    awal, akhir = segmen[0]
    for a, b in segmen[1:]:
        if a <= akhir + 1e-9:
            akhir = max(akhir, b)
        else:
            hasil.append((awal, akhir))
            awal, akhir = a, b
    hasil.append((awal, akhir))
    return hasil


def kumpulkan_dinding_koordinat(posisi_ruang):
    horizontal, vertikal = {}, {}
    for item in posisi_ruang:
        x, y = item["Posisi X (m)"], item["Posisi Y (m)"]
        p, l = item["Panjang X (m)"], item["Lebar Y (m)"]

        for yy in (y, y + l):
            horizontal.setdefault(round(yy, 3), []).append((x, x + p))
        for xx in (x, x + p):
            vertikal.setdefault(round(xx, 3), []).append((y, y + l))

    dinding_h = [(yy, a, b) for yy, s in horizontal.items() for a, b in gabung_segmen(s)]
    dinding_v = [(xx, a, b) for xx, s in vertikal.items() for a, b in gabung_segmen(s)]
    return dinding_h, dinding_v


def panjang_dinding_koordinat(posisi_ruang):
    dinding_h, dinding_v = kumpulkan_dinding_koordinat(posisi_ruang)
    return sum(b - a for _, a, b in dinding_h) + sum(b - a for _, a, b in dinding_v)


def hitung_kolom_koordinat(posisi_ruang, jarak_maks):
    if not posisi_ruang:
        return 0, 0
    dinding_h, dinding_v = kumpulkan_dinding_koordinat(posisi_ruang)

    titik = set()
    for yy, a, b in dinding_h:
        titik.add((round(a, 3), yy))
        titik.add((round(b, 3), yy))
    for xx, a, b in dinding_v:
        titik.add((xx, round(a, 3)))
        titik.add((xx, round(b, 3)))
    for yy, x1, x2 in dinding_h:
        for xx, y1, y2 in dinding_v:
            if x1 - 1e-9 <= xx <= x2 + 1e-9 and y1 - 1e-9 <= yy <= y2 + 1e-9:
                titik.add((xx, yy))

    tambahan = 0
    for yy, x1, x2 in dinding_h:
        pos = sorted(t[0] for t in titik if t[1] == yy and x1 - 1e-9 <= t[0] <= x2 + 1e-9)
        for a, b in zip(pos, pos[1:]):
            tambahan += max(math.ceil((b - a) / jarak_maks - 1e-9) - 1, 0)
    for xx, y1, y2 in dinding_v:
        pos = sorted(t[1] for t in titik if t[0] == xx and y1 - 1e-9 <= t[1] <= y2 + 1e-9)
        for a, b in zip(pos, pos[1:]):
            tambahan += max(math.ceil((b - a) / jarak_maks - 1e-9) - 1, 0)
    return len(titik), tambahan


# ---------------------------------------------------------------
# 3. INISIALISASI SESSION STATE
# ---------------------------------------------------------------
if "ruang" not in st.session_state:
    st.session_state.ruang = []

if "step" not in st.session_state:
    st.session_state.step = 1

defaults = {
    "tinggi_dinding": 3.0,
    "hitung_otomatis": True,
    "panjang_dinding_kustom": 0.0,
    "jml_pintu": 3,
    "luas_pintu": 1.9,
    "jml_jendela": 4,
    "luas_jendela": 1.2,
    "sudut_atap": 30,
    "galian_lebar": 0.6,
    "galian_dalam": 0.7,
    "pondasi_lebar": 0.4,
    "pondasi_tinggi": 0.6,
    "sloof_lebar": 0.15,
    "sloof_tinggi": 0.20,
    "kolom_b": 0.15,
    "kolom_h": 0.15,
    "jarak_kolom": 3.0,
    "ring_b": 0.15,
    "ring_h": 0.20,
    "besi_sloof": 225.0,
    "besi_kb": 160.0,
    "jml_pekerja": 4,
    "jml_mandor": 1,
    "jam_kerja": 8,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def next_step():
    if st.session_state.step < 6:
        st.session_state.step += 1


def prev_step():
    if st.session_state.step > 1:
        st.session_state.step -= 1


# ---------------------------------------------------------------
# 4. SIDEBAR: PENGATURAN FINANSIAL & HARGA
# ---------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Pengaturan Global")
    st.caption("Konfigurasi finansial dan harga satuan.")

    with st.container(border=True):
        st.markdown("**💰 Parameter Finansial**")
        op = st.number_input("Overhead & Profit (%)", min_value=0.0, max_value=30.0, value=10.0, step=0.5)
        ppn = st.number_input("PPN (%)", min_value=0.0, max_value=15.0, value=11.0, step=0.5)

    with st.expander("💵 Edit Database Harga", expanded=False):
        if os.path.exists(os.path.join(FOLDER, "harga.csv")):
            harga_awal = baca_csv("harga.csv")
            harga_edit = st.data_editor(
                harga_awal[["komponen", "jenis", "satuan", "harga"]],
                hide_index=True,
                disabled=["komponen", "jenis", "satuan"],
                key="editor_harga",
            )
            harga_map = dict(zip(harga_edit["komponen"], harga_edit["harga"]))
        else:
            harga_map = {}
            st.warning("File harga.csv tidak ditemukan.")


# ---------------------------------------------------------------
# 5. KALKULASI GLOBAL REAL-TIME
# ---------------------------------------------------------------
has_ruang = len(st.session_state.ruang) > 0
has_ahsp = os.path.exists(os.path.join(FOLDER, "ahsp.csv"))

if has_ruang:
    total_luas = sum(r["Panjang X (m)"] * r["Lebar Y (m)"] for r in st.session_state.ruang)
    dinding_otomatis = panjang_dinding_koordinat(st.session_state.ruang)
    panjang_dinding = dinding_otomatis if st.session_state.hitung_otomatis else st.session_state.panjang_dinding_kustom

    luas_dinding_bruto = panjang_dinding * st.session_state.tinggi_dinding
    luas_bukaan = (st.session_state.jml_pintu * st.session_state.luas_pintu) + (st.session_state.jml_jendela * st.session_state.luas_jendela)
    luas_dinding_netto = max(luas_dinding_bruto - luas_bukaan, 0.0)
    luas_atap = total_luas / math.cos(math.radians(st.session_state.sudut_atap))

    n_titik, n_tambahan = hitung_kolom_koordinat(st.session_state.ruang, st.session_state.jarak_kolom)
    n_kolom = n_titik + n_tambahan

    vol_sloof = panjang_dinding * st.session_state.sloof_lebar * st.session_state.sloof_tinggi
    vol_kolom = n_kolom * st.session_state.kolom_b * st.session_state.kolom_h * st.session_state.tinggi_dinding
    vol_ring = panjang_dinding * st.session_state.ring_b * st.session_state.ring_h

    bek_sloof = panjang_dinding * st.session_state.sloof_tinggi * 2
    bek_kolom = n_kolom * 2 * (st.session_state.kolom_b + st.session_state.kolom_h) * st.session_state.tinggi_dinding
    bek_ring = panjang_dinding * (st.session_state.ring_b + 2 * st.session_state.ring_h)

    besi_sloof_total = vol_sloof * st.session_state.besi_sloof
    besi_kolom_total = vol_kolom * st.session_state.besi_kb
    besi_ring_total = vol_ring * st.session_state.besi_kb

    total_vol_beton = vol_sloof + vol_kolom + vol_ring
    total_besi = besi_sloof_total + besi_kolom_total + besi_ring_total

    detail_pekerjaan = [
        {"Kategori": "A. Pekerjaan Tanah & Pondasi", "Pekerjaan": "Galian Tanah Pondasi", "Volume": panjang_dinding * st.session_state.galian_lebar * st.session_state.galian_dalam, "Satuan": "m³", "AHSP_Key": "galian_tanah"},
        {"Kategori": "A. Pekerjaan Tanah & Pondasi", "Pekerjaan": "Pondasi Batu Kali / Belah", "Volume": panjang_dinding * st.session_state.pondasi_lebar * st.session_state.pondasi_tinggi, "Satuan": "m³", "AHSP_Key": "pondasi_batu_belah"},
        {"Kategori": "B. Pekerjaan Struktur Beton", "Pekerjaan": "Beton Sloof K-250", "Volume": vol_sloof, "Satuan": "m³", "AHSP_Key": "beton_k250"},
        {"Kategori": "B. Pekerjaan Struktur Beton", "Pekerjaan": "Pembesian Sloof", "Volume": besi_sloof_total, "Satuan": "kg", "AHSP_Key": "pembesian"},
        {"Kategori": "B. Pekerjaan Struktur Beton", "Pekerjaan": "Bekisting Sloof", "Volume": bek_sloof, "Satuan": "m²", "AHSP_Key": "bekisting_sloof"},
        {"Kategori": "B. Pekerjaan Struktur Beton", "Pekerjaan": "Beton Kolom Praktis K-250", "Volume": vol_kolom, "Satuan": "m³", "AHSP_Key": "beton_k250"},
        {"Kategori": "B. Pekerjaan Struktur Beton", "Pekerjaan": "Pembesian Kolom Praktis", "Volume": besi_kolom_total, "Satuan": "kg", "AHSP_Key": "pembesian"},
        {"Kategori": "B. Pekerjaan Struktur Beton", "Pekerjaan": "Bekisting Kolom Praktis", "Volume": bek_kolom, "Satuan": "m²", "AHSP_Key": "bekisting_sloof"},
        {"Kategori": "B. Pekerjaan Struktur Beton", "Pekerjaan": "Beton Ring Balok K-250", "Volume": vol_ring, "Satuan": "m³", "AHSP_Key": "beton_k250"},
        {"Kategori": "B. Pekerjaan Struktur Beton", "Pekerjaan": "Pembesian Ring Balok", "Volume": besi_ring_total, "Satuan": "kg", "AHSP_Key": "pembesian"},
        {"Kategori": "B. Pekerjaan Struktur Beton", "Pekerjaan": "Bekisting Ring Balok", "Volume": bek_ring, "Satuan": "m²", "AHSP_Key": "bekisting_sloof"},
        {"Kategori": "C. Pekerjaan Dinding & Finis", "Pekerjaan": "Pasangan Dinding Bata 1/2 Bata", "Volume": luas_dinding_netto, "Satuan": "m²", "AHSP_Key": "pasangan_bata_1/2"},
        {"Kategori": "C. Pekerjaan Dinding & Finis", "Pekerjaan": "Plesteran Tebal 15 mm (2 sisi)", "Volume": luas_dinding_netto * 2, "Satuan": "m²", "AHSP_Key": "plesteran_1pc8ps_15mm"},
        {"Kategori": "C. Pekerjaan Dinding & Finis", "Pekerjaan": "Acian Dinding (2 sisi)", "Volume": luas_dinding_netto * 2, "Satuan": "m²", "AHSP_Key": "acian"},
        {"Kategori": "C. Pekerjaan Dinding & Finis", "Pekerjaan": "Pengecatan Tembok Interior", "Volume": luas_dinding_netto * 2, "Satuan": "m²", "AHSP_Key": "cat_tembok_interior"},
        {"Kategori": "D. Pekerjaan Lantai & Plafon", "Pekerjaan": "Penutup Lantai Keramik 40x40", "Volume": total_luas, "Satuan": "m²", "AHSP_Key": "lantai_keramik_40x40"},
        {"Kategori": "D. Pekerjaan Lantai & Plafon", "Pekerjaan": "Rangka Plafon Hollow", "Volume": total_luas, "Satuan": "m²", "AHSP_Key": "rangka_plafon_hollow"},
        {"Kategori": "D. Pekerjaan Lantai & Plafon", "Pekerjaan": "Plafon PVC", "Volume": total_luas, "Satuan": "m²", "AHSP_Key": "plafon_pvc"},
        {"Kategori": "E. Pekerjaan Atap", "Pekerjaan": "Rangka Atap Baja Ringan", "Volume": luas_atap, "Satuan": "m²", "AHSP_Key": "rangka_atap_baja_ringan"},
        {"Kategori": "E. Pekerjaan Atap", "Pekerjaan": "Penutup Atap Genteng Press", "Volume": luas_atap, "Satuan": "m²", "AHSP_Key": "penutup_atap_genteng_press"},
    ]

    if has_ahsp:
        ahsp = baca_csv("ahsp.csv")
        kebutuhan = {}
        baris_rab = []
        for no, row in enumerate(detail_pekerjaan, start=1):
            komponen = ahsp[ahsp["kunci"] == row["AHSP_Key"]]
            biaya_dasar = 0.0
            for k in komponen.itertuples():
                kunci_k = (k.komponen, k.jenis, k.satuan)
                kebutuhan[kunci_k] = kebutuhan.get(kunci_k, 0) + k.koefisien * row["Volume"]
                biaya_dasar += k.koefisien * harga_map.get(k.komponen, 0)

            harga_satuan = biaya_dasar * (1 + op / 100)
            jumlah_harga = harga_satuan * row["Volume"]
            baris_rab.append([
                no, row["Kategori"], row["Pekerjaan"], round(row["Volume"], 2), row["Satuan"],
                round(harga_satuan), round(jumlah_harga)
            ])

        rab = pd.DataFrame(baris_rab, columns=["No", "Kategori", "Pekerjaan", "Volume", "Satuan", "Harga Satuan (Rp)", "Jumlah (Rp)"])
        subtotal = rab["Jumlah (Rp)"].sum()
        nilai_ppn = subtotal * ppn / 100
        total_rab = subtotal + nilai_ppn
        biaya_per_m2 = total_rab / total_luas if total_luas > 0 else 0
        total_oh_pekerja = sum([j for k, j in kebutuhan.items() if k[1] == "upah"])
        estimasi_hari = math.ceil(total_oh_pekerja / st.session_state.jml_pekerja)
    else:
        total_rab = 0
        estimasi_hari = 0
else:
    total_luas = 0.0
    dinding_otomatis = 0.0
    panjang_dinding = 0.0
    total_rab = 0
    estimasi_hari = 0


# ---------------------------------------------------------------
# 6. HEADER APLIKASI & INDIKATOR PROGRES BERSIH
# ---------------------------------------------------------------
st.markdown("""
<div class="app-header">
    <p class="app-title">🏡 BangunPintar</p>
    <p class="app-subtitle">Aplikasi web RAB rumah otomatis — Perencanaan Denah, Struktur, Material & Anggaran Biaya</p>
</div>
""", unsafe_allow_html=True)

# Nama-nama tahap aktif
step_titles = [
    "Langkah 1: Perencanaan Geometri & Denah Ruang",
    "Langkah 2: Spesifikasi Teknis & Dimensi Struktur",
    "Langkah 3: Rekapitulasi Volume Pekerjaan Fisik",
    "Langkah 4: Logistik Material & Simulasi Durasi",
    "Langkah 5: Rencana Anggaran Biaya (RAB) & Penawaran",
    "Langkah 6: Cetak Dokumen Laporan Terpadu (PDF)"
]

st.markdown(f"### **{step_titles[st.session_state.step - 1]}**")
st.progress(st.session_state.step / 6)
st.write("")


# ===============================================================
# LAYAR 1: INPUT KOORDINAT, RINGKASAN METRIK & PREVIEW DENAH
# ===============================================================
if st.session_state.step == 1:
    if has_ruang:
        m1, m2, m3 = st.columns(3, gap="medium")
        m1.metric("Total Luas Bangunan", f"{total_luas:.2f} m²", f"{len(st.session_state.ruang)} Ruangan")
        m2.metric("Estimasi Total RAB", rp(total_rab), f"± {rp(biaya_per_m2)} / m²")
        m3.metric("Estimasi Durasi Proyek", f"± {estimasi_hari} Hari", f"Asumsi {st.session_state.jml_pekerja} Pekerja")
        st.write("")

    c_left, c_right = st.columns([1.05, 0.95], gap="large")

    with c_left:
        with st.container(border=True):
            st.markdown("#### ➕ Tambah Tata Letak Ruangan")
            st.caption("Masukkan koordinat sudut kiri-bawah (X, Y) serta dimensi panjang & lebar.")

            with st.form("form_ruang", clear_on_submit=True):
                nama = st.text_input("Nama Ruang", placeholder="Contoh: Ruang Tamu, Kamar Tidur")
                cx, cy = st.columns(2)
                x_in = cx.number_input("Posisi X (m)", min_value=0.0, value=0.0, step=0.5)
                y_in = cy.number_input("Posisi Y (m)", min_value=0.0, value=0.0, step=0.5)

                cp, cl = st.columns(2)
                p_in = cp.number_input("Panjang X (m)", min_value=0.1, value=3.0, step=0.1)
                l_in = cl.number_input("Lebar Y (m)", min_value=0.1, value=3.0, step=0.1)

                submitted = st.form_submit_button("➕ Tambahkan ke Denah", type="primary", use_container_width=True)
                if submitted:
                    if nama.strip() == "":
                        st.error("Nama ruang tidak boleh kosong.")
                    else:
                        st.session_state.ruang.append({
                            "Nama Ruang": nama.strip(),
                            "Posisi X (m)": x_in,
                            "Posisi Y (m)": y_in,
                            "Panjang X (m)": p_in,
                            "Lebar Y (m)": l_in,
                        })
                        st.rerun()

        if has_ruang:
            with st.container(border=True):
                st.markdown("#### 📋 Daftar Ruangan Terdaftar")
                df_r = pd.DataFrame(st.session_state.ruang)
                df_r["Luas (m²)"] = df_r["Panjang X (m)"] * df_r["Lebar Y (m)"]
                st.dataframe(df_r, use_container_width=True, hide_index=True)

                cb1, cb2 = st.columns(2)
                if cb1.button("🗑️ Hapus Terakhir", use_container_width=True):
                    st.session_state.ruang.pop()
                    st.rerun()
                if cb2.button("⚠️ Reset Semua", use_container_width=True):
                    st.session_state.ruang = []
                    st.rerun()

    with c_right:
        with st.container(border=True):
            st.markdown("#### 🖼️ Preview Denah Bangunan")
            st.caption("Visualisasi denah otomatis berdasarkan koordinat.")

            if has_ruang:
                plt.clf()
                plt.close("all")
                fig, ax = plt.subplots(figsize=(5.5, 5.2))
                for r in st.session_state.ruang:
                    rx, ry = r["Posisi X (m)"], r["Posisi Y (m)"]
                    rp_val, rl_val = r["Panjang X (m)"], r["Lebar Y (m)"]
                    ax.add_patch(Rectangle((rx, ry), rp_val, rl_val, facecolor="#FEF9C3", edgecolor="#DC2626", linewidth=2))
                    ax.text(
                        rx + rp_val / 2, ry + rl_val / 2,
                        f"{r['Nama Ruang']}\n({rp_val}x{rl_val}m)",
                        ha="center", va="center", fontsize=8.5, fontweight="bold", color="#0F172A"
                    )

                max_x = max(r["Posisi X (m)"] + r["Panjang X (m)"] for r in st.session_state.ruang)
                max_y = max(r["Posisi Y (m)"] + r["Lebar Y (m)"] for r in st.session_state.ruang)

                ax.set_xlim(-0.5, max_x + 1.0)
                ax.set_ylim(-0.5, max_y + 1.0)
                ax.set_aspect("equal")
                ax.grid(True, linestyle="--", alpha=0.4, color="#CBD5E1")
                ax.set_xlabel("Sumbu X (m)", fontsize=9, color="#475569")
                ax.set_ylabel("Sumbu Y (m)", fontsize=9, color="#475569")
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info("👈 Tambahkan ruangan pertama di form sebelah kiri untuk melihat sketsa denah dan estimasi biaya secara instan.")


# ===============================================================
# LAYAR 2: PARAMETER & STRUKTUR BANGUNAN
# ===============================================================
elif st.session_state.step == 2:
    if not has_ruang:
        st.warning("⚠️ Silakan masukkan minimal satu ruangan pada **Layar 1** terlebih dahulu.")
    else:
        k1, k2, k3 = st.columns(3)
        k1.metric("Luas Lantai Dasar", f"{total_luas:.2f} m²")
        k2.metric("Panjang Dinding Terhitung", f"{panjang_dinding:.2f} m")
        k3.metric("Estimasi Biaya Terkini", rp(total_rab))
        st.write("")

        col_arch, col_struct = st.columns(2, gap="large")

        with col_arch:
            with st.container(border=True):
                st.markdown("#### 🚪 Arsitektur, Dinding & Atap")
                st.caption("Atur ketinggian dinding, bukaan, dan kemiringan atap.")

                st.session_state.tinggi_dinding = st.number_input(
                    "Tinggi Dinding (m)", min_value=2.0, value=st.session_state.tinggi_dinding, step=0.1
                )

                st.session_state.hitung_otomatis = st.toggle(
                    "Hitung panjang dinding otomatis dari koordinat", value=st.session_state.hitung_otomatis
                )
                if st.session_state.hitung_otomatis:
                    st.info(f"Panjang dinding otomatis: **{dinding_otomatis:.2f} m**")
                else:
                    st.session_state.panjang_dinding_kustom = st.number_input(
                        "Panjang Dinding Total Kustom (m)", min_value=0.0, value=float(dinding_otomatis), step=0.5
                    )

                st.markdown("**Bukaan Pintu & Jendela**")
                cp1, cp2 = st.columns(2)
                st.session_state.jml_pintu = cp1.number_input("Jumlah Pintu", min_value=0, value=st.session_state.jml_pintu, step=1)
                st.session_state.luas_pintu = cp2.number_input("Luas 1 Pintu (m²)", min_value=0.0, value=st.session_state.luas_pintu, step=0.1)

                cj1, cj2 = st.columns(2)
                st.session_state.jml_jendela = cj1.number_input("Jumlah Jendela", min_value=0, value=st.session_state.jml_jendela, step=1)
                st.session_state.luas_jendela = cj2.number_input("Luas 1 Jendela (m²)", min_value=0.0, value=st.session_state.luas_jendela, step=0.1)

                st.session_state.sudut_atap = st.slider(
                    "Kemiringan Atap (derajat)", 15, 45, st.session_state.sudut_atap
                )

        with col_struct:
            with st.container(border=True):
                st.markdown("#### 🏗️ Dimensi Struktur & Pembesian")
                st.caption("Sesuaikan dimensi galian, pondasi, sloof, kolom, dan ring balok.")

                sub_tab1, sub_tab2, sub_tab3 = st.tabs(["1. Pondasi & Sloof", "2. Kolom & Ring Balok", "3. Rasio Pembesian"])

                with sub_tab1:
                    st.write("")
                    sd1, sd2 = st.columns(2)
                    st.session_state.galian_lebar = sd1.number_input("Lebar Galian (m)", min_value=0.1, value=st.session_state.galian_lebar, step=0.05)
                    st.session_state.galian_dalam = sd2.number_input("Kedalaman Galian (m)", min_value=0.1, value=st.session_state.galian_dalam, step=0.05)

                    sd3, sd4 = st.columns(2)
                    st.session_state.pondasi_lebar = sd3.number_input("Lebar Pondasi Batu Kali (m)", min_value=0.1, value=st.session_state.pondasi_lebar, step=0.05)
                    st.session_state.pondasi_tinggi = sd4.number_input("Tinggi Pondasi Batu Kali (m)", min_value=0.1, value=st.session_state.pondasi_tinggi, step=0.05)

                    sd5, sd6 = st.columns(2)
                    st.session_state.sloof_lebar = sd5.number_input("Lebar Sloof Beton (m)", min_value=0.05, value=st.session_state.sloof_lebar, step=0.01)
                    st.session_state.sloof_tinggi = sd6.number_input("Tinggi Sloof Beton (m)", min_value=0.05, value=st.session_state.sloof_tinggi, step=0.01)

                with sub_tab2:
                    st.write("")
                    sk1, sk2, sk3 = st.columns(3)
                    st.session_state.kolom_b = sk1.number_input("Lebar Kolom (m)", min_value=0.05, value=st.session_state.kolom_b, step=0.01)
                    st.session_state.kolom_h = sk2.number_input("Panjang Kolom (m)", min_value=0.05, value=st.session_state.kolom_h, step=0.01)
                    st.session_state.jarak_kolom = sk3.number_input("Jarak Maks Kolom (m)", min_value=1.0, value=st.session_state.jarak_kolom, step=0.5)

                    sr1, sr2 = st.columns(2)
                    st.session_state.ring_b = sr1.number_input("Lebar Ring Balok (m)", min_value=0.05, value=st.session_state.ring_b, step=0.01)
                    st.session_state.ring_h = sr2.number_input("Tinggi Ring Balok (m)", min_value=0.05, value=st.session_state.ring_h, step=0.01)

                with sub_tab3:
                    st.write("")
                    sb1, sb2 = st.columns(2)
                    st.session_state.besi_sloof = sb1.number_input("Rasio Besi Sloof (kg/m³)", min_value=0.0, value=st.session_state.besi_sloof, step=5.0)
                    st.session_state.besi_kb = sb2.number_input("Rasio Besi Kolom/Ring (kg/m³)", min_value=0.0, value=st.session_state.besi_kb, step=5.0)


# ===============================================================
# LAYAR 3: VOLUME PEKERJAAN RINCI
# ===============================================================
elif st.session_state.step == 3:
    if not has_ruang:
        st.warning("⚠️ Silakan lengkapi data denah di **Layar 1** terlebih dahulu.")
    else:
        mv1, mv2, mv3, mv4 = st.columns(4)
        mv1.metric("Luas Bangunan", f"{total_luas:.2f} m²")
        mv2.metric("Panjang Dinding", f"{panjang_dinding:.2f} m")
        mv3.metric("Total Beton", f"{total_vol_beton:.2f} m³")
        mv4.metric("Total Pembesian", f"{total_besi:.1f} kg")
        st.write("")

        with st.container(border=True):
            st.markdown("#### 📋 Rekapitulasi Volume Pekerjaan Fisik")
            df_vol = pd.DataFrame(detail_pekerjaan)
            df_vol["Volume (Dibulatkan)"] = df_vol["Volume"].round(2)

            t_sub1, t_sub2 = st.tabs(["📑 Tabel Keseluruhan", "🔍 Filter per Kategori"])
            with t_sub1:
                st.dataframe(df_vol[["Kategori", "Pekerjaan", "Volume (Dibulatkan)", "Satuan"]], use_container_width=True, hide_index=True)
            with t_sub2:
                kat_pilih = st.selectbox("Pilih Kategori Pekerjaan:", df_vol["Kategori"].unique())
                st.dataframe(df_vol[df_vol["Kategori"] == kat_pilih][["Pekerjaan", "Volume (Dibulatkan)", "Satuan"]], use_container_width=True, hide_index=True)


# ===============================================================
# LAYAR 4: MATERIAL & DURASI PROYEK
# ===============================================================
elif st.session_state.step == 4:
    if not (has_ruang and has_ahsp):
        st.warning("⚠️ Pastikan data ruang terisi dan file `ahsp.csv` tersedia.")
    else:
        semen_kg = kebutuhan.get(("Semen Portland", "bahan", "kg"), 0)
        pasir_m3 = kebutuhan.get(("Pasir pasang", "bahan", "m3"), 0)
        bata_pcs = sum([j for k, j in kebutuhan.items() if "Bata" in k[0]])
        besi_kg = sum([j for k, j in kebutuhan.items() if "Besi" in k[0]])
        besi_batang = math.ceil(besi_kg / 7.4)

        cm1, cm2, cm3, cm4 = st.columns(4)
        cm1.metric("Semen Portland", f"{semen_kg:,.0f} kg", f"≈ {semen_kg/50:,.1f} zak")
        cm2.metric("Pasir Pasang", f"{pasir_m3:,.2f} m³")
        cm3.metric("Bata Merah", f"{bata_pcs:,.0f} bh")
        cm4.metric("Total Besi", f"{besi_kg:,.1f} kg", f"≈ {besi_batang:,} btg (12m)")
        st.write("")

        with st.container(border=True):
            t_mat1, t_mat2, t_mat3 = st.tabs(["🧱 Kebutuhan Bahan", "👷 Rincian Tenaga Kerja", "⏱️ Simulasi Durasi Proyek"])

            with t_mat1:
                bahan_list = [[k[0], k[2], round(j, 2)] for k, j in kebutuhan.items() if k[1] == "bahan"]
                df_bahan = pd.DataFrame(bahan_list, columns=["Nama Bahan", "Satuan", "Jumlah Kebutuhan"])
                st.dataframe(df_bahan, use_container_width=True, hide_index=True)

            with t_mat2:
                upah_list = [[k[0], round(j, 1)] for k, j in kebutuhan.items() if k[1] == "upah"]
                df_upah = pd.DataFrame(upah_list, columns=["Jenis Tenaga Kerja", "Jumlah Total Orang-Hari (OH)"])
                st.dataframe(df_upah, use_container_width=True, hide_index=True)

            with t_mat3:
                st.markdown("#### ⏱️ Simulasi Durasi Pengerjaan Lapangan")
                cs1, cs2, cs3 = st.columns(3)
                st.session_state.jml_pekerja = cs1.number_input("Jumlah Pekerja Harian", min_value=1, value=st.session_state.jml_pekerja, step=1)
                st.session_state.jml_mandor = cs2.number_input("Jumlah Mandor", min_value=1, value=st.session_state.jml_mandor, step=1)
                st.session_state.jam_kerja = cs3.selectbox("Jam Kerja per Hari", [7, 8], index=1)

                hari_baru = math.ceil(total_oh_pekerja / st.session_state.jml_pekerja)
                bulan_baru = hari_baru / 30.0

                st.write("")
                r1, r2, r3 = st.columns(3)
                r1.metric("Total Beban Kerja", f"{total_oh_pekerja:,.1f} OH")
                r2.metric("Estimasi Hari Kerja", f"± {hari_baru} Hari")
                r3.metric("Estimasi Bulan", f"± {bulan_baru:.1f} Bulan")


# ===============================================================
# LAYAR 5: RAB & PENAWARAN KLIEN
# ===============================================================
elif st.session_state.step == 5:
    if not (has_ruang and has_ahsp):
        st.warning("⚠️ Silakan lengkapi data denah di **Layar 1** terlebih dahulu.")
    else:
        mr1, mr2, mr3, mr4 = st.columns(4)
        mr1.metric("Subtotal Pekerjaan", rp(subtotal))
        mr2.metric(f"PPN ({ppn:g}%)", rp(nilai_ppn))
        mr3.metric("Grand Total RAB", rp(total_rab))
        mr4.metric("Biaya per m²", rp(biaya_per_m2))
        st.write("")

        with st.container(border=True):
            tr1, tr2, tr3 = st.tabs(["🤝 Penawaran Klien (Ringkas)", "📑 RAB Rinci Lengkap", "📊 Grafik Komposisi Biaya"])

            with tr1:
                df_klien = rab[["No", "Kategori", "Pekerjaan", "Volume", "Satuan", "Jumlah (Rp)"]].copy()
                df_klien["Jumlah (Rp)"] = df_klien["Jumlah (Rp)"].apply(rp)
                st.dataframe(df_klien, hide_index=True, use_container_width=True)

                csv_export = rab.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="📥 Unduh Rincian Penawaran (CSV/Excel)",
                    data=csv_export,
                    file_name="RAB_Penawaran_BangunPintar.csv",
                    mime="text/csv",
                    type="primary"
                )

            with tr2:
                st.dataframe(rab, hide_index=True, use_container_width=True)

            with tr3:
                st.bar_chart(rab.set_index("Pekerjaan")["Jumlah (Rp)"])


# ===============================================================
# LAYAR 6: CETAK DOKUMEN LAPORAN TERPADU (PDF & SKETSA DENAH)
# ===============================================================
elif st.session_state.step == 6:
    if not (has_ruang and has_ahsp):
        st.warning("⚠️ Silakan lengkapi data denah di **Layar 1** terlebih dahulu.")
    else:
        semen_kg = kebutuhan.get(("Semen Portland", "bahan", "kg"), 0)
        pasir_m3 = kebutuhan.get(("Pasir pasang", "bahan", "m3"), 0)
        bata_pcs = sum([j for k, j in kebutuhan.items() if "Bata" in k[0]])
        besi_kg = sum([j for k, j in kebutuhan.items() if "Besi" in k[0]])
        besi_batang = math.ceil(besi_kg / 7.4)

        def generate_denah_img_buffer():
            fig_pdf, ax_pdf = plt.subplots(figsize=(4.5, 4))
            for r in st.session_state.ruang:
                rx, ry = r["Posisi X (m)"], r["Posisi Y (m)"]
                rp_val, rl_val = r["Panjang X (m)"], r["Lebar Y (m)"]
                ax_pdf.add_patch(Rectangle((rx, ry), rp_val, rl_val, facecolor="#FEF9C3", edgecolor="#DC2626", linewidth=2))
                ax_pdf.text(rx + rp_val / 2, ry + rl_val / 2, f"{r['Nama Ruang']}\n{rp_val}x{rl_val}m",
                            ha="center", va="center", fontsize=7, fontweight="bold", color="#0F172A")

            max_x = max(r["Posisi X (m)"] + r["Panjang X (m)"] for r in st.session_state.ruang)
            max_y = max(r["Posisi Y (m)"] + r["Lebar Y (m)"] for r in st.session_state.ruang)
            ax_pdf.set_xlim(-0.5, max_x + 0.5)
            ax_pdf.set_ylim(-0.5, max_y + 0.5)
            ax_pdf.set_aspect("equal")
            ax_pdf.grid(True, linestyle="--", alpha=0.5)

            img_buf = io.BytesIO()
            plt.savefig(img_buf, format="png", bbox_inches="tight", dpi=100)
            plt.close(fig_pdf)
            img_buf.seek(0)
            return img_buf

        def buat_pdf_laporan():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle("DocTitle", parent=styles["Heading1"], fontSize=14, textColor=colors.HexColor("#0F172A"), spaceAfter=4)
            section_style = ParagraphStyle("SectionTitle", parent=styles["Heading2"], fontSize=11, textColor=colors.HexColor("#DC2626"), spaceBefore=10, spaceAfter=4)
            normal_style = ParagraphStyle("NormalText", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#334155"))

            story = []
            story.append(Paragraph("<b>LAPORAN RESMI PERENCANAAN & RAB</b>", title_style))
            story.append(Paragraph("<b>Aplikasi BangunPintar - Aplikasi Web RAB Rumah Otomatis</b>", normal_style))
            story.append(Spacer(1, 10))

            story.append(Paragraph("<b>1. RINGKASAN GEOMETRI & SKETSA DENAH BANGUNAN</b>", section_style))
            ruang_data = [["Nama Ruang", "Pos X", "Pos Y", "Pjg X", "Lbr Y", "Luas"]]
            for r in st.session_state.ruang:
                ruang_data.append([
                    r["Nama Ruang"], f"{r['Posisi X (m)']}m", f"{r['Posisi Y (m)']}m",
                    f"{r['Panjang X (m)']}m", f"{r['Lebar Y (m)']}m", f"{r['Panjang X (m)'] * r['Lebar Y (m)']:.2f}m²"
                ])

            t_ruang = Table(ruang_data, colWidths=[85, 40, 40, 40, 40, 50])
            t_ruang.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))

            img_buffer = generate_denah_img_buffer()
            denah_image = RLImage(img_buffer, width=190, height=170)

            tabel_layout_denah = Table([[t_ruang, denah_image]], colWidths=[305, 200])
            tabel_layout_denah.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
            story.append(tabel_layout_denah)
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<b>Total Luas Bangunan:</b> {total_luas:.2f} m² | <b>Panjang Dinding:</b> {panjang_dinding:.2f} m | <b>Kolom Praktis:</b> {n_kolom} titik", normal_style))
            story.append(Spacer(1, 8))

            story.append(Paragraph("<b>2. KEBUTUHAN LOGISTIK & DURASI PROYEK</b>", section_style))
            log_data = [
                ["Material Utama", "Jumlah Kebutuhan"],
                ["Semen Portland", f"{semen_kg:,.0f} kg (≈ {semen_kg/50:,.1f} zak)"],
                ["Pasir Pasang", f"{pasir_m3:,.2f} m³"],
                ["Bata Merah", f"{bata_pcs:,.0f} buah"],
                ["Besi Beton (12m)", f"{besi_batang:,} batang (≈ {besi_kg:,.0f} kg)"],
                ["Estimasi Waktu", f"± {estimasi_hari} Hari Kerja (asumsi {st.session_state.jml_pekerja} pekerja)"]
            ]
            t_log = Table(log_data, colWidths=[180, 325])
            t_log.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DC2626")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t_log)
            story.append(Spacer(1, 8))

            story.append(Paragraph("<b>3. RENCANA ANGGARAN BIAYA (RAB) PENAWARAN</b>", section_style))
            rab_pdf_data = [["No", "Kategori", "Pekerjaan", "Vol", "Sat", "Jumlah (Rp)"]]
            for r in baris_rab:
                rab_pdf_data.append([str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), rp(r[6])])

            t_rab = Table(rab_pdf_data, colWidths=[25, 125, 185, 45, 35, 90])
            t_rab.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(t_rab)
            story.append(Spacer(1, 8))

            story.append(Paragraph(f"<b>Subtotal Pekerjaan:</b> {rp(subtotal)}", normal_style))
            story.append(Paragraph(f"<b>PPN ({ppn:g}%):</b> {rp(nilai_ppn)}", normal_style))
            story.append(Paragraph(f"<b>GRAND TOTAL BIAYA: {rp(total_rab)}</b>", ParagraphStyle("GrandTotal", parent=normal_style, fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#DC2626"))))
            story.append(Paragraph(f"<b>Estimasi Biaya per m²:</b> {rp(biaya_per_m2)} / m²", normal_style))

            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()

        with st.container(border=True):
            st.markdown("#### 📄 Laporan Hasil Perencanaan Terpadu (PDF + Sketsa Denah)")
            st.caption("Unduh dokumen penawaran dan perhitungan teknis resmi dalam satu file PDF siap cetak.")

            m_pdf1, m_pdf2, m_pdf3 = st.columns(3)
            m_pdf1.metric("Total Luas Bangunan", f"{total_luas:.2f} m²")
            m_pdf2.metric("Grand Total RAB", rp(total_rab))
            m_pdf3.metric("Estimasi Biaya / m²", rp(biaya_per_m2))

            st.write("")
            pdf_bytes = buat_pdf_laporan()
            st.download_button(
                label="📥 Unduh Laporan PDF + Sketsa Denah Otomatis",
                data=pdf_bytes,
                file_name="Laporan_RAB_BangunPintar.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )


# ---------------------------------------------------------------
# 7. TOMBOL NAVIGASI BAWAH (KEMBALI & SELANJUTNYA)
# ---------------------------------------------------------------
st.write("")
st.markdown("---")
col_prev, col_spacer, col_next = st.columns([1.2, 2.6, 1.2])

with col_prev:
    if st.session_state.step > 1:
        st.button("⬅️ Kembali", on_click=prev_step, use_container_width=True)

with col_next:
    if st.session_state.step < 6:
        st.button("Selanjutnya ➡️", on_click=next_step, type="primary", use_container_width=True)
