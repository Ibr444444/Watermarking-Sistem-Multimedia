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

## Catatan Teknis

LSB (Least Significant Bit) sangat rentan terhadap kompresi JPEG karena JPEG adalah kompresi **lossy** — bit-bit LSB pada setiap pixel bisa berubah setelah kompresi. Semakin rendah QF, semakin besar distorsi, semakin rusak watermark yang diekstrak.
