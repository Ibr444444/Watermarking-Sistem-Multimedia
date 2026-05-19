# Digital Watermarking — LSB + Evaluasi Kompresi JPEG

Implementasi tugas watermarking untuk mata kuliah Multimedia (ITB).

## Isi File

| File | Keterangan |
|------|------------|
| `watermark.py` | Script Python utama (bisa dijalankan langsung) |
| `watermarking_colab.ipynb` | Notebook Jupyter / Google Colab (direkomendasikan) |
| `requirements.txt` | Dependensi Python |

## Cara Pakai

### A. Google Colab (Direkomendasikan)
1. Buka [Google Colab](https://colab.research.google.com/)
2. Upload file `watermarking_colab.ipynb`
3. Jalankan sel satu per satu dari atas ke bawah
4. Di sel **Upload Foto**, upload foto wajah kamu (JPG/PNG)
   - Jika di-skip, sistem akan membuat gambar sintetis otomatis

### B. Lokal / Terminal
```bash
pip install -r requirements.txt

# Pakai gambar sintetis (tanpa foto):
python watermark.py

# Pakai foto sendiri:
python watermark.py --image foto_wajah.jpg

# Pilih tipe watermark (binary / random):
python watermark.py --image foto_wajah.jpg --wm-type random

# Tentukan Quality Factor sendiri:
python watermark.py --image foto_wajah.jpg --qf 95 80 60 40 20
```

## Konsep

```
Foto Wajah
    │
    ▼
[Embed LSB] ← Watermark Biner (64×64 bit)
    │
    ▼
Foto + Watermark (tidak terlihat secara visual)
    │
    ├──── Kompres QF=90 → Ekstrak → Evaluasi PSNR / BER / NCC
    ├──── Kompres QF=70 → Ekstrak → Evaluasi
    ├──── Kompres QF=50 → Ekstrak → Evaluasi
    ├──── Kompres QF=30 → Ekstrak → Evaluasi
    └──── Kompres QF=10 → Ekstrak → Evaluasi
                                         │
                                         ▼
                              Temukan threshold QF
```

## Metrik Evaluasi

| Metrik | Keterangan | Threshold Gagal |
|--------|------------|-----------------|
| **PSNR** | Kualitas gambar (dB), makin tinggi makin baik | — |
| **BER** | Bit Error Rate, rasio bit yang salah [0–1] | BER > 0.3 |
| **NCC** | Normalized Cross-Correlation [-1 s/d 1] | NCC < 0.5 |

## Output

Semua hasil disimpan di folder `output/`:
- `watermarked_original.png` — Foto setelah embed watermark
- `compressed_qfXX.jpg` — Foto setelah kompresi JPEG per QF
- `extracted_wm_qfXX.png` — Watermark yang berhasil/gagal diekstrak
- `metrics_plot.png` — Grafik PSNR, BER, NCC vs QF
- `watermark_grid.png` — Grid perbandingan watermark per QF

---

## Contoh Output

### 1. Foto Host & Watermark Asli

Foto wajah yang digunakan sebagai host image (kiri) dan watermark biner teks "ITB" berukuran 64×64 piksel yang akan disisipkan (kanan).

![Foto Host dan Watermark Asli](output/1.png)

---

### 2. Perbandingan Foto Asli vs Foto Setelah Embed Watermark

Foto asli (kiri), foto setelah watermark disisipkan menggunakan metode LSB (tengah), dan peta perbedaan piksel yang diperbesar (kanan). PSNR embed = **80.35 dB**, menunjukkan watermark tidak terlihat secara visual.

![Embed Watermark](output/2.png)

---

### 3. Hasil Evaluasi per Quality Factor JPEG

Tabel hasil evaluasi PSNR, BER, dan NCC untuk setiap nilai QF yang diuji:

| QF | PSNR (dB) | BER | NCC | Status |
|----|-----------|-----|-----|--------|
| 90 | 48.21 | 0.5254 | -0.0099 | ✗ Tidak dapat diekstrak |
| 80 | 45.61 | 0.5310 |  0.0079 | ✗ Tidak dapat diekstrak |
| 70 | 44.00 | 0.5415 |  0.0132 | ✗ Tidak dapat diekstrak |
| 60 | 38.52 | 0.5227 |  0.0334 | ✗ Tidak dapat diekstrak |
| 50 | 35.08 | 0.6328 | -0.0428 | ✗ Tidak dapat diekstrak |
| 40 | 34.68 | 0.3635 |  0.0387 | ✗ Tidak dapat diekstrak |
| 30 | 33.68 | 0.5925 |  0.0002 | ✗ Tidak dapat diekstrak |
| 20 | 31.75 | 0.5149 |  0.0112 | ✗ Tidak dapat diekstrak |
| 10 | 28.53 | 0.9187 | -0.0268 | ✗ Tidak dapat diekstrak |

> 🔴 **Watermark TIDAK dapat diekstrak pada QF ≤ 90**

---

### 4. Grafik Metrik Evaluasi (PSNR / BER / NCC vs QF)

Grafik berikut menunjukkan tren ketiga metrik seiring menurunnya Quality Factor. Garis putus-putus menunjukkan threshold keberhasilan ekstraksi watermark.

![Grafik Metrik](output/3.png)

---

### 5. Grid Watermark Ter-Ekstrak per QF

Perbandingan watermark asli (kiri atas) dengan watermark hasil ekstraksi dari setiap versi foto yang dikompres JPEG pada berbagai QF. Seluruh hasil menunjukkan pola noise yang mengkonfirmasi kegagalan ekstraksi.

![Grid Watermark](output/4.png)

---

## Catatan Teknis

LSB (Least Significant Bit) sangat rentan terhadap kompresi JPEG karena JPEG adalah kompresi **lossy** — bit-bit LSB pada setiap pixel bisa berubah setelah kompresi. Semakin rendah QF, semakin besar distorsi, semakin rusak watermark yang diekstrak.

Untuk aplikasi yang membutuhkan ketahanan watermark terhadap JPEG, disarankan menggunakan metode berbasis domain frekuensi seperti **DCT watermarking** atau **DWT+SVD watermarking**.
