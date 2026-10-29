import math
import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.patches import Rectangle

st.set_page_config(
    page_title="BangunPintar - Estimasi Denah & RAB",
    page_icon="🏠",
    layout="wide"
)

FOLDER = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------
# Fungsi Bantu
# ---------------------------------------------------------------
@st.cache_data
def baca_csv(nama_file):
    return pd.read_csv(os.path.join(FOLDER, nama_file), encoding="utf-8-sig")


def rp(x):
    """Format angka ke Rupiah, contoh: Rp 1.250.000"""
    return "Rp " + f"{x:,.0f}".replace(",", ".")


def gabung_segmen(segmen):
    """Gabungkan ruas garis yang bertumpuk pada satu garis lurus."""
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
    """Menghitung dinding dari daftar ruang koordinat (x, y, panjang, lebar)."""
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
    total = sum(b - a for _, a, b in dinding_h) + sum(b - a for _, a, b in dinding_v)
    return total


def hitung_kolom_koordinat(posisi_ruang, jarak_maks):
    """Menghitung titik kolom praktis berdasarkan koordinat denah."""
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
# Inisialisasi State Ruang
# ---------------------------------------------------------------
if "ruang" not in st.session_state:
    st.session_state.ruang = []


# ---------------------------------------------------------------
# SIDEBAR: Pengaturan Harga & Finansial Global
# ---------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Pengaturan Global")
    st.caption("Pengaturan finansial dan database harga lokal.")

    st.markdown("---")
    st.markdown("##### 💰 Finansial Proyek")
    op = st.number_input("Overhead & Profit (%)", min_value=0.0, max_value=30.0, value=10.0, step=0.5)
    ppn = st.number_input("PPN (%)", min_value=0.0, max_value=15.0, value=11.0, step=0.5)

    st.markdown("---")
    st.markdown("##### 💵 Database Harga Satuan")
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
# HEADER UTAMA
# ---------------------------------------------------------------
st.title("🏡 BangunPintar")
st.markdown("##### *Aplikasi Web Estimasi Denah, Volume, Material, dan RAB Profesional*")
st.markdown("---")


# ---------------------------------------------------------------
# NAVIGASI UTAMA BERBASIS 5 LAYAR (TABS)
# ---------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ Layar 1: Denah & Koordinat",
    "📐 Layar 2: Parameter & Struktur",
    "📋 Layar 3: Volume Pekerjaan",
    "🧱 Layar 4: Material & Tukang",
    "💰 Layar 5: RAB & Penawaran Klien"
])


# ===============================================================
# LAYAR 1: INPUT KOORDINAT & PREVIEW DENAH
# ===============================================================
with tab1:
    st.subheader("Layar 1: Perencanaan Geometri & Tata Letak Ruangan")
    st.caption("Masukkan data ruang berdasarkan titik koordinat (X, Y) sudut kiri-bawah serta dimensi panjang dan lebarnya.")

    c_f1, c_f2 = st.columns([1.1, 0.9], gap="large")

    with c_f1:
        st.markdown("##### ➕ Form Tambah Ruang")
        with st.form("form_ruang", clear_on_submit=True):
            nama = st.text_input("Nama Ruang", "Ruang Tamu")
            cx, cy = st.columns(2)
            x_in = cx.number_input("Posisi X (m)", min_value=0.0, value=0.0, step=0.5)
            y_in = cy.number_input("Posisi Y (m)", min_value=0.0, value=0.0, step=0.5)
            
            cp, cl = st.columns(2)
            p_in = cp.number_input("Panjang X (m)", min_value=0.1, value=3.0, step=0.1)
            l_in = cl.number_input("Lebar Y (m)", min_value=0.1, value=3.0, step=0.1)

            submitted = st.form_submit_button("Tambah Ruang", use_container_width=True)
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

        st.markdown("##### 📋 Daftar Ruang")
        if st.session_state.ruang:
            df_r = pd.DataFrame(st.session_state.ruang)
            df_r["Luas (m²)"] = df_r["Panjang X (m)"] * df_r["Lebar Y (m)"]
            st.dataframe(df_r, use_container_width=True, hide_index=True)
            st.info(f"**Total Luas Bangunan:** {df_r['Luas (m²)'].sum():.2f} m²")

            cb1, cb2 = st.columns(2)
            if cb1.button("🗑️ Hapus Terakhir", use_container_width=True):
                st.session_state.ruang.pop()
                st.rerun()
            if cb2.button("⚠️ Reset Semua", use_container_width=True):
                st.session_state.ruang = []
                st.rerun()
        else:
            st.warning("Belum ada ruang yang dimasukkan.")

    with c_f2:
        st.markdown("##### 🖼️ Preview Gambar Denah")
        if st.session_state.ruang:
            fig, ax = plt.subplots(figsize=(5.5, 5))
            for r in st.session_state.ruang:
                rx, ry = r["Posisi X (m)"], r["Posisi Y (m)"]
                rp_val, rl_val = r["Panjang X (m)"], r["Lebar Y (m)"]
                ax.add_patch(Rectangle((rx, ry), rp_val, rl_val, facecolor="#eaf2fb", edgecolor="#1e3a8a", linewidth=2))
                ax.text(rx + rp_val / 2, ry + rl_val / 2, f"{r['Nama Ruang']}\n{rp_val}x{rl_val}m",
                        ha="center", va="center", fontsize=8, fontweight="bold", color="#0f172a")

            max_x = max(r["Posisi X (m)"] + r["Panjang X (m)"] for r in st.session_state.ruang)
            max_y = max(r["Posisi Y (m)"] + r["Lebar Y (m)"] for r in st.session_state.ruang)
            ax.set_xlim(-0.5, max_x + 0.5)
            ax.set_ylim(-0.5, max_y + 0.5)
            ax.set_aspect("equal")
            ax.grid(True, linestyle="--", alpha=0.5)
            ax.set_xlabel("Sumbu X (m)")
            ax.set_ylabel("Sumbu Y (m)")
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("Denah akan muncul otomatis setelah ruang ditambahkan.")


# ===============================================================
# GLOBAL VARIABLES FOR CALCULATION ACROSS TABS
# ===============================================================
if st.session_state.ruang:
    total_luas = sum(r["Panjang X (m)"] * r["Lebar Y (m)"] for r in st.session_state.ruang)
    dinding_otomatis = panjang_dinding_koordinat(st.session_state.ruang)
else:
    total_luas = 0.0
    dinding_otomatis = 0.0


# ===============================================================
# LAYAR 2: PARAMETER & STRUKTUR BANGUNAN
# ===============================================================
with tab2:
    st.subheader("Layar 2: Spesifikasi Teknis & Dimensi Struktur")
    st.caption("Atur parameter tinggi bangunan, bukaan arsitektural, serta dimensi elemen struktur beton bertulang.")

    p_s1, p_s2 = st.columns(2)
    with p_s1:
        st.markdown("##### 🚪 Dinding, Bukaan & Atap")
        tinggi_dinding = st.number_input("Tinggi Dinding (m)", min_value=2.0, value=3.0, step=0.1)
        
        hitung_otomatis = st.checkbox("Hitung panjang dinding otomatis dari koordinat", value=True)
        if hitung_otomatis:
            panjang_dinding = dinding_otomatis
            st.caption(f"Panjang dinding total: **{panjang_dinding:.2f} m**.")
        else:
            panjang_dinding = st.number_input("Panjang Dinding Total Kustom (m)", min_value=0.0, value=float(dinding_otomatis), step=0.5)

        c_p1, c_p2 = st.columns(2)
        jml_pintu = c_p1.number_input("Jumlah Pintu", min_value=0, value=3, step=1)
        luas_pintu = c_p2.number_input("Luas 1 Pintu (m²)", min_value=0.0, value=1.9, step=0.1)
        
        c_j1, c_j2 = st.columns(2)
        jml_jendela = c_j1.number_input("Jumlah Jendela", min_value=0, value=4, step=1)
        luas_jendela = c_j2.number_input("Luas 1 Jendela (m²)", min_value=0.0, value=1.2, step=0.1)
        
        sudut_atap = st.slider("Kemiringan Atap (derajat)", 15, 45, 30)

    with p_s2:
        st.markdown("##### 🏗️ Dimensi Struktur & Pembesian")
        st_d1, st_d2 = st.columns(2)
        galian_lebar = st_d1.number_input("Lebar Galian (m)", min_value=0.1, value=0.6, step=0.05)
        galian_dalam = st_d2.number_input("Kedalaman Galian (m)", min_value=0.1, value=0.7, step=0.05)
        
        st_d3, st_d4 = st.columns(2)
        pondasi_lebar = st_d3.number_input("Lebar Pondasi Batu Kali (m)", min_value=0.1, value=0.4, step=0.05)
        pondasi_tinggi = st_d4.number_input("Tinggi Pondasi Batu Kali (m)", min_value=0.1, value=0.6, step=0.05)
        
        st_d5, st_d6 = st.columns(2)
        sloof_lebar = st_d5.number_input("Lebar Sloof Beton (m)", min_value=0.05, value=0.15, step=0.01)
        sloof_tinggi = st_d6.number_input("Tinggi Sloof Beton (m)", min_value=0.05, value=0.20, step=0.01)

        st_k1, st_k2, st_k3 = st.columns(3)
        kolom_b = st_k1.number_input("Lebar Kolom (m)", min_value=0.05, value=0.15, step=0.01)
        kolom_h = st_k2.number_input("Tebal Kolom (m)", min_value=0.05, value=0.15, step=0.01)
        jarak_kolom = st_k3.number_input("Jarak Maks Kolom (m)", min_value=1.0, value=3.0, step=0.5)

        st_r1, st_r2 = st.columns(2)
        ring_b = st_r1.number_input("Lebar Ring Balok (m)", min_value=0.05, value=0.15, step=0.01)
        ring_h = st_r2.number_input("Tinggi Ring Balok (m)", min_value=0.05, value=0.20, step=0.01)

        st_b1, st_b2 = st.columns(2)
        besi_sloof = st_b1.number_input("Rasio Besi Sloof (kg/m³)", min_value=0.0, value=225.0, step=5.0)
        besi_kb = st_b2.number_input("Rasio Besi Kolom/Ring (kg/m³)", min_value=0.0, value=160.0, step=5.0)


# ===============================================================
# CALCULATIONS LOGIC (SHARED ACROSS TABS 3, 4, 5)
# ===============================================================
if st.session_state.ruang:
    luas_dinding_bruto = panjang_dinding * tinggi_dinding
    luas_bukaan = (jml_pintu * luas_pintu) + (jml_jendela * luas_jendela)
    luas_dinding_netto = max(luas_dinding_bruto - luas_bukaan, 0.0)
    luas_atap = total_luas / math.cos(math.radians(sudut_atap))

    n_titik, n_tambahan = hitung_kolom_koordinat(st.session_state.ruang, jarak_kolom)
    n_kolom = n_titik + n_tambahan

    vol_sloof = panjang_dinding * sloof_lebar * sloof_tinggi
    vol_kolom = n_kolom * kolom_b * kolom_h * tinggi_dinding
    vol_ring = panjang_dinding * ring_b * ring_h

    bek_sloof = panjang_dinding * sloof_tinggi * 2
    bek_kolom = n_kolom * 2 * (kolom_b + kolom_h) * tinggi_dinding
    bek_ring = panjang_dinding * (ring_b + 2 * ring_h)

    besi_sloof_total = vol_sloof * besi_sloof
    besi_kolom_total = vol_kolom * besi_kb
    besi_ring_total = vol_ring * besi_kb

    total_vol_beton = vol_sloof + vol_kolom + vol_ring
    total_besi = besi_sloof_total + besi_kolom_total + besi_ring_total

    detail_pekerjaan = [
        {"Kategori": "A. Pekerjaan Tanah & Pondasi", "Pekerjaan": "Galian Tanah Pondasi", "Volume": panjang_dinding * galian_lebar * galian_dalam, "Satuan": "m³", "AHSP_Key": "galian_tanah"},
        {"Kategori": "A. Pekerjaan Tanah & Pondasi", "Pekerjaan": "Pondasi Batu Kali / Belah", "Volume": panjang_dinding * pondasi_lebar * pondasi_tinggi, "Satuan": "m³", "AHSP_Key": "pondasi_batu_belah"},
        
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


# ===============================================================
# LAYAR 3: VOLUME PEKERJAAN RINCI
# ===============================================================
with tab3:
    st.subheader("Layar 3: Rekapitulasi Volume Pekerjaan Fisik")
    st.caption("Rincian volume pekerjaan struktur dan arsitektur berdasarkan geometri bangunan.")

    if st.session_state.ruang:
        m_v1, m_v2, m_v3, m_v4 = st.columns(4)
        m_v1.metric("Luas Bangunan", f"{total_luas:.2f} m²")
        m_v2.metric("Panjang Dinding", f"{panjang_dinding:.2f} m")
        m_v3.metric("Total Beton", f"{total_vol_beton:.2f} m³")
        m_v4.metric("Total Pembesian", f"{total_besi:.1f} kg")

        df_vol = pd.DataFrame(detail_pekerjaan)
        df_vol["Volume (Dibulatkan)"] = df_vol["Volume"].round(2)

        t_sub1, t_sub2 = st.tabs(["Tabel Keseluruhan", "Filter per Kategori"])
        with t_sub1:
            st.dataframe(df_vol[["Kategori", "Pekerjaan", "Volume (Dibulatkan)", "Satuan"]], use_container_width=True, hide_index=True)
        with t_sub2:
            kat_pilih = st.selectbox("Pilih Kategori:", df_vol["Kategori"].unique())
            st.dataframe(df_vol[df_vol["Kategori"] == kat_pilih][["Pekerjaan", "Volume (Dibulatkan)", "Satuan"]], use_container_width=True, hide_index=True)
    else:
        st.info("Silakan isi data ruang di Layar 1 terlebih dahulu.")


# ===============================================================
# LAYAR 4: MATERIAL & TENAGA KERJA (DENGAN SIMULASI DURASI PROYEK)
# ===============================================================
with tab4:
    st.subheader("Layar 4: Rekapitulasi Material & Tenaga Kerja")
    st.caption("Konversi volume pekerjaan ke kebutuhan logistik toko bangunan dan simulasi durasi pengerjaan proyek.")

    if st.session_state.ruang and os.path.exists(os.path.join(FOLDER, "ahsp.csv")):
        ahsp = baca_csv("ahsp.csv")
        kebutuhan = {}
        for row in detail_pekerjaan:
            komponen = ahsp[ahsp["kunci"] == row["AHSP_Key"]]
            for k in komponen.itertuples():
                kunci_k = (k.komponen, k.jenis, k.satuan)
                kebutuhan[kunci_k] = kebutuhan.get(kunci_k, 0) + k.koefisien * row["Volume"]

        t_mat1, t_mat2, t_mat3 = st.tabs(["🧱 Kebutuhan Bahan", "👷 Rincian Tenaga Kerja", "⏱️ Simulasi Durasi Proyek"])
        
        with t_mat1:
            bahan_list = [[k[0], k[2], round(j, 2)] for k, j in kebutuhan.items() if k[1] == "bahan"]
            df_bahan = pd.DataFrame(bahan_list, columns=["Nama Bahan", "Satuan", "Jumlah Kebutuhan"])
            st.dataframe(df_bahan, use_container_width=True, hide_index=True)

            semen_kg = kebutuhan.get(("Semen Portland", "bahan", "kg"), 0)
            pasir_m3 = kebutuhan.get(("Pasir pasang", "bahan", "m3"), 0)
            
            # Perbaikan pengambilan Bata Merah (mencari komponen bata merah di dalam kamus kebutuhan)
            bata_pcs = 0.0
            for k, j in kebutuhan.items():
                if "Bata" in k[0]:
                    bata_pcs = j
                    break

            besi_kg = sum([j for k, j in kebutuhan.items() if "Besi" in k[0]])

            st.markdown("##### 📌 Logistik Utama Lapangan:")
            cm1, cm2, cm3, cm4 = st.columns(4)
            cm1.metric("Semen Portland", f"{semen_kg:,.0f} kg", f"≈ {semen_kg/50:,.1f} zak")
            cm2.metric("Pasir Pasang", f"{pasir_m3:,.2f} m³")
            cm3.metric("Bata Merah", f"{bata_pcs:,.0f} bh")
            cm4.metric("Total Besi", f"{besi_kg:,.1f} kg")

        with t_mat2:
            upah_list = [[k[0], round(j, 1)] for k, j in kebutuhan.items() if k[1] == "upah"]
            df_upah = pd.DataFrame(upah_list, columns=["Jenis Tenaga Kerja", "Jumlah Total Orang-Hari (OH)"])
            st.dataframe(df_upah, use_container_width=True, hide_index=True)

        with t_mat3:
            st.markdown("#### ⏱️ Kalkulator & Simulasi Durasi Proyek Lapangan")
            st.caption("Atur jumlah pekerja dan mandor harian untuk melihat estimasi hari/bulan penyelesaian proyek secara otomatis.")

            # Hitung total Orang-Hari (OH) untuk Pekerja dan Tukang
            total_oh_pekerja = sum([j for k, j in kebutuhan.items() if k[1] == "upah"])

            c_sim1, c_sim2, c_sim3 = st.columns(3)
            jml_pekerja_lapangan = c_sim1.number_input("Jumlah Pekerja / Tukang Harian", min_value=1, value=4, step=1)
            jml_mandor_lapangan = c_sim2.number_input("Jumlah Mandor / Pengawas", min_value=1, value=1, step=1)
            jam_kerja_per_hari = c_sim3.selectbox("Jam Kerja per Hari", [7, 8], index=1)

            # Asumsi produktivitas tim (total OH dibagi jumlah pekerja aktif)
            estimasi_hari = math.ceil(total_oh_pekerja / jml_pekerja_lapangan)
            estimasi_bulan = estimasi_hari / 30.0

            st.markdown("---")
            res1, res2, res3 = st.columns(3)
            res1.metric("Total Kebutuhan Tenaga", f"{total_oh_pekerja:,.1f} Orang-Hari (OH)")
            res2.metric("Estimasi Durasi Hari Kerja", f"± {estimasi_hari} Hari Kalender")
            res3.metric("Estimasi Waktu Selesai", f"± {estimasi_bulan:.1f} Bulan")

            if estimasi_hari > 365:
                st.warning("⚠️ Perhatian: Durasi proyek memakan waktu lebih dari 1 tahun. Tambahkan jumlah pekerja harian di atas jika ingin mempercepat progres pembangunan.")
            else:
                st.success(f"✅ Dengan kekuatan {jml_pekerja_lapangan} orang pekerja/tukang dan {jml_mandor_lapangan} mandor, proyek diperkirakan selesai dalam **{estimasi_hari} hari**.")
    else:
        st.info("Pastikan data ruang sudah terisi dan file ahsp.csv tersedia.")


# ===============================================================
# LAYAR 5: RAB & PENAWARAN KLIEN
# ===============================================================
with tab5:
    st.subheader("Layar 5: Rencana Anggaran Biaya (RAB) & Penawaran Klien")
    st.caption("Kalkulasi finansial total biaya bangunan dan tabel penawaran harga siap cetak.")

    if st.session_state.ruang and os.path.exists(os.path.join(FOLDER, "ahsp.csv")):
        ahsp = baca_csv("ahsp.csv")
        baris_rab = []
        for no, row in enumerate(detail_pekerjaan, start=1):
            komponen = ahsp[ahsp["kunci"] == row["AHSP_Key"]]
            biaya_dasar = 0.0
            for k in komponen.itertuples():
                harga_k = harga_map.get(k.komponen, 0)
                biaya_dasar += k.koefisien * harga_k
            
            harga_satuan = biaya_dasar * (1 + op / 100)
            jumlah_harga = harga_satuan * row["Volume"]
            baris_rab.append([
                no, row["Kategori"], row["Pekerjaan"], round(row["Volume"], 2), row["Satuan"],
                round(harga_satuan), round(jumlah_harga)
            ])

        rab = pd.DataFrame(baris_rab, columns=[
            "No", "Kategori", "Pekerjaan", "Volume", "Satuan", "Harga Satuan (Rp)", "Jumlah (Rp)"
        ])

        subtotal = rab["Jumlah (Rp)"].sum()
        nilai_ppn = subtotal * ppn / 100
        total = subtotal + nilai_ppn
        biaya_per_m2 = total / total_luas

        t_r1, t_r2 = st.tabs(["📄 Penawaran Klien (Ringkas)", "📑 RAB Rinci Lengkap"])
        with t_r1:
            st.markdown("#### 🤝 Ringkasan Penawaran Harga untuk Klien")
            df_klien = rab[["No", "Kategori", "Pekerjaan", "Volume", "Satuan", "Jumlah (Rp)"]].copy()
            df_klien["Jumlah (Rp)"] = df_klien["Jumlah (Rp)"].apply(rp)
            st.dataframe(df_klien, hide_index=True, use_container_width=True)

            st.markdown("---")
            cr1, cr2 = st.columns(2)
            with cr1:
                st.metric("Subtotal Pekerjaan", rp(subtotal))
                st.metric(f"PPN ({ppn:g}%)", rp(nilai_ppn))
            with cr2:
                st.metric("Total Estimasi Biaya", rp(total))
                st.metric("Estimasi Biaya per m²", rp(biaya_per_m2))

            csv_export = rab.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Unduh Rincian Penawaran (CSV/Excel)",
                data=csv_export,
                file_name="RAB_Penawaran_Rumah.csv",
                mime="text/csv"
            )

        with t_r2:
            st.markdown("#### 📑 Rencana Anggaran Biaya (RAB) Lengkap")
            st.dataframe(rab, hide_index=True, use_container_width=True)
            st.success(f"**Total Akhir RAB:** {rp(total)}  |  **Biaya per m²:** {rp(biaya_per_m2)}")

        st.markdown("---")
        st.markdown("##### 📊 Komposisi Grafik Biaya Pekerjaan")
        st.bar_chart(rab.set_index("Pekerjaan")["Jumlah (Rp)"])
    else:
        st.info("Silakan lengkapi data pada Layar 1 terlebih dahulu.")