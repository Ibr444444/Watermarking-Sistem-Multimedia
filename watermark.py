"""
Digital Watermarking dengan Metode LSB + Evaluasi Kompresi JPEG
================================================================
Implementasi:
1. Generate watermark biner sederhana
2. Sisipkan watermark ke foto menggunakan LSB (Least Significant Bit)
3. Kompres foto dengan JPEG pada berbagai Quality Factor (QF)
4. Ekstrak watermark dari tiap hasil kompresi
5. Evaluasi dengan PSNR, BER, dan NCC
6. Temukan nilai QF minimum agar watermark masih bisa diekstrak
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ─────────────────────────────────────────────
# 1. GENERATE WATERMARK BINER
# ─────────────────────────────────────────────

def generate_binary_watermark(size=(64, 64), text="WM"):
    """
    Buat watermark biner berupa teks hitam-putih.
    Output: array numpy 2D berisi 0 dan 1.
    """
    img = Image.new("L", size, color=0)  # background hitam
    draw = ImageDraw.Draw(img)
    # Coba pakai font default, fallback ke None
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((4, 20), text, fill=255, font=font)
    wm = np.array(img)
    wm = (wm > 128).astype(np.uint8)  # binarisasi
    return wm


def generate_random_watermark(size=(64, 64), seed=42):
    """
    Buat watermark acak (pseudo-random) dari seed tertentu.
    Output: array numpy 2D berisi 0 dan 1.
    """
    rng = np.random.default_rng(seed)
    return rng.integers(0, 2, size=size, dtype=np.uint8)


# ─────────────────────────────────────────────
# 2. EMBED WATERMARK DENGAN LSB
# ─────────────────────────────────────────────

def embed_lsb(image_array, watermark):
    """
    Sisipkan watermark ke channel BIRU gambar menggunakan LSB.
    - image_array : numpy array shape (H, W, 3), dtype uint8
    - watermark   : numpy array 2D berisi 0 dan 1
    Returns: watermarked image sebagai numpy array
    """
    img = image_array.copy()
    wm_flat = watermark.flatten()
    h, w, _ = img.shape

    if len(wm_flat) > h * w:
        raise ValueError(
            f"Watermark ({len(wm_flat)} bit) terlalu besar untuk gambar ({h*w} pixel)."
        )

    # Sisipkan ke channel Biru (index 2), bit LSB
    blue = img[:, :, 2].flatten()
    blue[: len(wm_flat)] = (blue[: len(wm_flat)] & 0xFE) | wm_flat
    img[:, :, 2] = blue.reshape(h, w)
    return img


# ─────────────────────────────────────────────
# 3. KOMPRES DENGAN JPEG
# ─────────────────────────────────────────────

def compress_jpeg(image_array, quality):
    """
    Kompres gambar dengan JPEG pada Quality Factor tertentu.
    Returns: numpy array hasil kompresi (sudah di-decode kembali)
    """
    img_pil = Image.fromarray(image_array.astype(np.uint8))
    buf = io.BytesIO()
    img_pil.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return np.array(Image.open(buf))


# ─────────────────────────────────────────────
# 4. EKSTRAK WATERMARK DARI LSB
# ─────────────────────────────────────────────

def extract_lsb(image_array, watermark_shape):
    """
    Ekstrak watermark dari LSB channel Biru.
    - image_array     : numpy array hasil kompresi
    - watermark_shape : tuple (H, W) ukuran watermark asli
    Returns: numpy array 2D berisi 0 dan 1
    """
    n_bits = watermark_shape[0] * watermark_shape[1]
    blue = image_array[:, :, 2].flatten()
    extracted = (blue[:n_bits] & 1).reshape(watermark_shape)
    return extracted.astype(np.uint8)


# ─────────────────────────────────────────────
# 5. METRIK EVALUASI
# ─────────────────────────────────────────────

def psnr(original, compressed):
    """Peak Signal-to-Noise Ratio (dB). Makin tinggi makin baik."""
    mse = np.mean((original.astype(np.float64) - compressed.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return 10 * np.log10(255**2 / mse)


def ber(wm_original, wm_extracted):
    """
    Bit Error Rate. Range [0, 1].
    0  = identik, 1 = semua bit berbeda.
    Jika BER > 0.3 dianggap watermark tidak bisa diekstrak.
    """
    return np.mean(wm_original.flatten() != wm_extracted.flatten())


def ncc(wm_original, wm_extracted):
    """
    Normalized Cross-Correlation. Range [-1, 1].
    1 = identik, < 0.5 dianggap watermark tidak bisa diekstrak.
    """
    a = wm_original.astype(np.float64) - wm_original.mean()
    b = wm_extracted.astype(np.float64) - wm_extracted.mean()
    denom = np.sqrt(np.sum(a**2) * np.sum(b**2))
    if denom == 0:
        return 0.0
    return float(np.sum(a * b) / denom)


# ─────────────────────────────────────────────
# 6. PIPELINE UTAMA
# ─────────────────────────────────────────────

def run_watermarking_pipeline(
    host_image_path=None,
    watermark_type="binary",  # "binary" atau "random"
    quality_factors=None,
    output_dir="output",
    ber_threshold=0.3,
    ncc_threshold=0.5,
):
    """
    Jalankan seluruh pipeline watermarking dan evaluasi.

    Parameters
    ----------
    host_image_path  : path ke foto host (JPG/PNG). Jika None, buat gambar sintetis.
    watermark_type   : "binary" (teks) atau "random"
    quality_factors  : list nilai QF, default [90, 80, 70, 60, 50, 40, 30, 20, 10]
    output_dir       : folder output
    ber_threshold    : BER di atas nilai ini → watermark gagal diekstrak
    ncc_threshold    : NCC di bawah nilai ini → watermark gagal diekstrak
    """
    if quality_factors is None:
        quality_factors = [90, 80, 70, 60, 50, 40, 30, 20, 10]

    os.makedirs(output_dir, exist_ok=True)

    # ── Load / buat host image ──────────────────────────────────────────
    if host_image_path and os.path.exists(host_image_path):
        host_img = np.array(Image.open(host_image_path).convert("RGB"))
        print(f"[INFO] Host image loaded: {host_image_path} ({host_img.shape})")
    else:
        print("[INFO] Host image tidak ditemukan, membuat gambar sintetis 256×256 ...")
        host_img = _make_synthetic_face(256, 256)

    # ── Buat watermark ─────────────────────────────────────────────────
    wm_size = (64, 64)
    if watermark_type == "random":
        watermark = generate_random_watermark(size=wm_size)
        print("[INFO] Watermark: acak (random)")
    else:
        watermark = generate_binary_watermark(size=wm_size, text="ITB")
        print("[INFO] Watermark: biner (teks 'ITB')")

    # ── Embed watermark ────────────────────────────────────────────────
    watermarked_img = embed_lsb(host_img, watermark)

    # Simpan gambar hasil embed (tanpa kompresi)
    Image.fromarray(watermarked_img).save(os.path.join(output_dir, "watermarked_original.png"))
    print("[INFO] Gambar watermarked disimpan → output/watermarked_original.png")

    # ── Evaluasi per QF ────────────────────────────────────────────────
    results = []
    print("\n" + "=" * 65)
    print(f"{'QF':>5}  {'PSNR (dB)':>12}  {'BER':>8}  {'NCC':>8}  {'Status':>20}")
    print("=" * 65)

    for qf in quality_factors:
        compressed = compress_jpeg(watermarked_img, quality=qf)
        extracted_wm = extract_lsb(compressed, watermark.shape)

        p = psnr(watermarked_img, compressed)
        b = ber(watermark, extracted_wm)
        n = ncc(watermark, extracted_wm)

        can_extract = (b <= ber_threshold) and (n >= ncc_threshold)
        status = "✓ Dapat diekstrak" if can_extract else "✗ Tidak dapat diekstrak"

        results.append(
            {
                "qf": qf,
                "psnr": p,
                "ber": b,
                "ncc": n,
                "can_extract": can_extract,
                "compressed": compressed,
                "extracted_wm": extracted_wm,
            }
        )

        psnr_str = f"{p:.2f}" if p != float("inf") else "∞"
        print(f"{qf:>5}  {psnr_str:>12}  {b:>8.4f}  {n:>8.4f}  {status:>20}")

    print("=" * 65)

    # ── Temukan threshold QF ───────────────────────────────────────────
    fail_qfs = [r["qf"] for r in results if not r["can_extract"]]
    if fail_qfs:
        threshold_qf = max(fail_qfs)
        print(f"\n[HASIL] Watermark TIDAK dapat diekstrak mulai QF ≤ {threshold_qf}")
    else:
        threshold_qf = None
        print("\n[HASIL] Watermark masih dapat diekstrak pada semua QF yang diuji.")

    # ── Simpan gambar kompresi & watermark ter-ekstrak ─────────────────
    for r in results:
        qf = r["qf"]
        Image.fromarray(r["compressed"]).save(
            os.path.join(output_dir, f"compressed_qf{qf}.jpg"), quality=qf
        )
        _save_wm_image(r["extracted_wm"], os.path.join(output_dir, f"extracted_wm_qf{qf}.png"))

    # ── Simpan plot evaluasi ───────────────────────────────────────────
    _plot_evaluation(results, watermark, watermarked_img, output_dir, threshold_qf)

    print(f"\n[INFO] Semua output tersimpan di folder '{output_dir}/'")
    return results, threshold_qf


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def _make_synthetic_face(h, w):
    """Buat gambar sintetis dengan warna-warna untuk simulasi foto wajah."""
    img = np.zeros((h, w, 3), dtype=np.uint8)
    # Background
    img[:, :] = [200, 170, 140]
    # 'Wajah' oval
    cx, cy = w // 2, h // 2
    for y in range(h):
        for x in range(w):
            if ((x - cx) / (w * 0.35)) ** 2 + ((y - cy) / (h * 0.45)) ** 2 < 1:
                img[y, x] = [220, 185, 155]
    # Mata kiri
    img[cy - 30 : cy - 20, cx - 35 : cx - 15] = [50, 30, 20]
    # Mata kanan
    img[cy - 30 : cy - 20, cx + 15 : cx + 35] = [50, 30, 20]
    # Mulut
    img[cy + 30 : cy + 38, cx - 20 : cx + 20] = [160, 80, 80]
    return img


def _save_wm_image(wm_array, path):
    """Simpan array biner sebagai gambar grayscale."""
    img = Image.fromarray((wm_array * 255).astype(np.uint8), mode="L")
    img.save(path)


def _plot_evaluation(results, original_wm, watermarked_img, output_dir, threshold_qf):
    """Buat visualisasi lengkap: grafik metrik + grid watermark ter-ekstrak."""
    qfs = [r["qf"] for r in results]
    psnrs = [r["psnr"] if r["psnr"] != float("inf") else 100 for r in results]
    bers = [r["ber"] for r in results]
    nccs = [r["ncc"] for r in results]

    # ── Plot 1: Grafik Metrik ───────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Evaluasi Watermarking LSB vs Quality Factor JPEG", fontsize=13, fontweight="bold")

    axes[0].plot(qfs, psnrs, "o-", color="steelblue", linewidth=2)
    axes[0].set_title("PSNR (dB)")
    axes[0].set_xlabel("Quality Factor (QF)")
    axes[0].set_ylabel("PSNR (dB)")
    axes[0].invert_xaxis()
    axes[0].grid(True, alpha=0.4)

    axes[1].plot(qfs, bers, "o-", color="tomato", linewidth=2)
    axes[1].axhline(y=0.3, color="gray", linestyle="--", label="Threshold BER=0.3")
    axes[1].set_title("BER (Bit Error Rate)")
    axes[1].set_xlabel("Quality Factor (QF)")
    axes[1].set_ylabel("BER")
    axes[1].invert_xaxis()
    axes[1].legend()
    axes[1].grid(True, alpha=0.4)

    axes[2].plot(qfs, nccs, "o-", color="seagreen", linewidth=2)
    axes[2].axhline(y=0.5, color="gray", linestyle="--", label="Threshold NCC=0.5")
    axes[2].set_title("NCC (Normalized Cross-Correlation)")
    axes[2].set_xlabel("Quality Factor (QF)")
    axes[2].set_ylabel("NCC")
    axes[2].invert_xaxis()
    axes[2].legend()
    axes[2].grid(True, alpha=0.4)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "metrics_plot.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("[INFO] Grafik metrik disimpan → output/metrics_plot.png")

    # ── Plot 2: Grid Watermark yang Diekstrak ───────────────────────────
    n = len(results)
    cols = min(5, n)
    rows = (n + cols - 1) // cols + 1  # +1 untuk baris watermark asli & host

    fig2 = plt.figure(figsize=(cols * 3, rows * 3))
    fig2.suptitle("Watermark Asli vs Watermark Ter-Ekstrak per QF", fontsize=12, fontweight="bold")

    # Baris 0: watermark asli + host image
    ax_wm = fig2.add_subplot(rows, cols, 1)
    ax_wm.imshow(original_wm, cmap="gray", vmin=0, vmax=1)
    ax_wm.set_title("Watermark\nAsli", fontsize=9)
    ax_wm.axis("off")

    ax_host = fig2.add_subplot(rows, cols, 2)
    ax_host.imshow(watermarked_img)
    ax_host.set_title("Foto +\nWatermark", fontsize=9)
    ax_host.axis("off")

    # Baris berikutnya: watermark per QF
    for i, r in enumerate(results):
        ax = fig2.add_subplot(rows, cols, cols + i + 1)
        ax.imshow(r["extracted_wm"], cmap="gray", vmin=0, vmax=1)
        status_sym = "✓" if r["can_extract"] else "✗"
        color = "green" if r["can_extract"] else "red"
        ax.set_title(
            f"QF={r['qf']} {status_sym}\nBER={r['ber']:.3f}",
            fontsize=8,
            color=color,
        )
        ax.axis("off")

    if threshold_qf:
        fig2.text(
            0.5, 0.01,
            f"Watermark tidak dapat diekstrak pada QF ≤ {threshold_qf}",
            ha="center", fontsize=11, color="red", fontweight="bold"
        )

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "watermark_grid.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("[INFO] Grid watermark disimpan → output/watermark_grid.png")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Digital Watermarking LSB + JPEG Evaluation")
    parser.add_argument("--image", type=str, default=None, help="Path foto host (opsional)")
    parser.add_argument(
        "--wm-type", choices=["binary", "random"], default="binary",
        help="Tipe watermark: 'binary' (teks) atau 'random'"
    )
    parser.add_argument(
        "--qf", nargs="+", type=int,
        default=[90, 80, 70, 60, 50, 40, 30, 20, 10],
        help="Daftar Quality Factor JPEG"
    )
    parser.add_argument("--output", type=str, default="output", help="Folder output")
    args = parser.parse_args()

    run_watermarking_pipeline(
        host_image_path=args.image,
        watermark_type=args.wm_type,
        quality_factors=args.qf,
        output_dir=args.output,
    )
