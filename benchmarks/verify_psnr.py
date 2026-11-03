import argparse
import glob
import hashlib
import math
import os
import sys
from collections import Counter

# Đưa thư mục src/ vào path để nạp module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from bmp_parser import read_bmp
from dpcm import dpcm_encode


def sha256_file(filepath: str) -> str:
    """Tính mã băm SHA-256 của tệp để kiểm tra tính toàn vẹn 100%."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_mse_psnr(raw1: bytes, raw2: bytes):
    """Tính toán sai số bình phương trung bình (MSE) và tỉ số tín hiệu trên nhiễu (PSNR)."""
    if len(raw1) != len(raw2):
        raise ValueError(
            f"Kích thước dữ liệu 2 ảnh không khớp nhau! ({len(raw1)} vs {len(raw2)} bytes)"
        )
    n = len(raw1)
    mse = sum((a - b) ** 2 for a, b in zip(raw1, raw2)) / n
    psnr = float("inf") if mse == 0 else 10 * math.log10((255.0**2) / mse)
    return mse, psnr


def plot_histogram(pixels: bytes, deltas: bytes, output_plot: str, img_name: str) -> None:
    """Vẽ và xuất biểu đồ so sánh phân bố Entropy."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[!] Chưa cài đặt matplotlib (`pip install matplotlib` để xuất biểu đồ).")
        return

    raw_counts = Counter(pixels)
    dpcm_counts = Counter(deltas)
    x_vals = list(range(256))
    y_raw = [raw_counts.get(i, 0) for i in x_vals]
    y_dpcm = [dpcm_counts.get(i, 0) for i in x_vals]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].bar(x_vals, y_raw, color="#3b82f6", width=1.0)
    axes[0].set_title(f"Phân bố Pixel gốc: {img_name}\n(Entropy cao, phân tán)")
    axes[0].set_xlabel("Giá trị Byte (0 - 255)")
    axes[0].set_ylabel("Tần số xuất hiện")

    axes[1].bar(x_vals, y_dpcm, color="#10b981", width=1.0)
    axes[1].set_title("Phân bố sau DPCM\n(Tập trung quanh 0 -> Tối ưu hóa Huffman)")
    axes[1].set_xlabel("Giá trị Vi sai (0 - 255)")
    axes[1].set_ylabel("Tần số xuất hiện")

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_plot)), exist_ok=True)
    plt.savefig(output_plot, dpi=150)
    plt.close()
    print(f"[+] Đã xuất biểu đồ so sánh phân bố Entropy tại: {output_plot}")


def detect_restored_file(orig_path: str) -> str:
    """Tự động suy đoán tệp khôi phục tương ứng nếu người dùng không chỉ định."""
    dir_name = os.path.dirname(orig_path)
    base_name = os.path.splitext(os.path.basename(orig_path))[0]

    # Các vị trí ưu tiên tìm kiếm
    candidates = [
        os.path.join(dir_name, f"{base_name}_restored.bmp"),
        os.path.join(dir_name, "restored.bmp"),
    ]
    for cand in candidates:
        if os.path.exists(cand):
            return cand
    return candidates[0]


def prompt_select_image() -> str:
    """Quét thư mục data/ và hiển thị menu chọn ảnh tương tác."""
    data_dir = "data"
    all_bmps = glob.glob(os.path.join(data_dir, "*.bmp"))
    # Lọc bỏ các tệp kết quả giải nén để danh sách gọn gàng
    orig_candidates = [
        f for f in all_bmps if not ("restored" in os.path.basename(f).lower())
    ]

    print("\n" + "=" * 60)
    print(" DANH SÁCH ẢNH .BMP TÌM THẤY TRONG THƯ MỤC 'data/':")
    print("=" * 60)

    if orig_candidates:
        for idx, file_path in enumerate(orig_candidates, start=1):
            file_size = os.path.getsize(file_path)
            print(f" [{idx}] {file_path:<30} ({file_size:,} bytes)")
    else:
        print(" (Không tìm thấy ảnh gốc trong thư mục data/)")

    print(" [0] Nhập đường dẫn file thủ công")
    print("=" * 60)

    while True:
        choice = input("Nhập số thứ tự ảnh muốn kiểm tra: ").strip()
        if choice.isdigit():
            c_int = int(choice)
            if 1 <= c_int <= len(orig_candidates):
                return orig_candidates[c_int - 1]
            elif c_int == 0:
                manual_path = input("Nhập đường dẫn tệp ảnh gốc: ").strip()
                return manual_path
        elif os.path.exists(choice):
            return choice

        print("[!] Lựa chọn không hợp lệ, vui lòng thử lại!")


def main():
    parser = argparse.ArgumentParser(
        description="Kiểm định chất lượng ảnh nén Huffman (Lossless PSNR & SHA-256)"
    )
    parser.add_argument(
        "-i", "--input", help="Đường dẫn ảnh gốc (.bmp)", default=None
    )
    parser.add_argument(
        "-r", "--restored", help="Đường dẫn ảnh khôi phục (.bmp)", default=None
    )
    parser.add_argument(
        "-p", "--plot", help="Đường dẫn lưu biểu đồ histogram (.png)", default=None
    )
    args = parser.parse_args()

    # 1. Xác định tệp ảnh gốc
    orig_path = args.input
    if not orig_path:
        orig_path = prompt_select_image()

    if not os.path.exists(orig_path):
        print(f"[x] Lỗi: Không tìm thấy tệp ảnh gốc tại '{orig_path}'")
        return

    # 2. Xác định tệp ảnh đã giải nén
    rest_path = args.restored or detect_restored_file(orig_path)
    if not os.path.exists(rest_path):
        print(f"[x] Lỗi: Không tìm thấy tệp ảnh giải nén tại '{rest_path}'!")
        print(f"    Gợi ý: Hãy chạy lệnh giải nén trước:")
        print(f"    python src/main.py decompress <file_nen.huf> -o {rest_path}")
        return

    # 3. Đặt tên biểu đồ theo tên file để không bị ghi đè lẫn nhau
    base_name = os.path.splitext(os.path.basename(orig_path))[0]
    plot_path = args.plot or f"benchmarks/histogram_{base_name}.png"

    # 4. Đọc ảnh và tính toán chỉ số
    bmp_orig = read_bmp(orig_path)
    bmp_rest = read_bmp(rest_path)

    hash_orig = sha256_file(orig_path)
    hash_rest = sha256_file(rest_path)
    mse, psnr = compute_mse_psnr(bmp_orig.pixels, bmp_rest.pixels)

    print("\n" + "=" * 65)
    print(" BÁO CÁO KIỂM ĐỊNH CHẤT LƯỢNG NÉN BẢO TOÀN (LOSSLESS VERIFICATION)")
    print("=" * 65)
    print(f" - Ảnh gốc (.bmp)          : {orig_path} ({bmp_orig.width}x{bmp_orig.height})")
    print(f" - Ảnh khôi phục (.bmp)    : {rest_path}")
    print(f" - SHA-256 (Gốc)           : {hash_orig}")
    print(f" - SHA-256 (Khôi phục)     : {hash_rest}")
    print(f" - Trạng thái toàn vẹn bit : {'KHỚP TUYỆT ĐỐI 100% (LOSSLESS)' if hash_orig == hash_rest else 'LỖI: SAI LỆCH DỮ LIỆU!'}")
    print(f" - Sai số bình phương (MSE): {mse:.6f}")
    print(f" - Tỉ số tín hiệu (PSNR)   : {psnr} dB")
    print("=" * 65)

    # 5. Vẽ và xuất biểu đồ
    deltas = dpcm_encode(bmp_orig.pixels)
    plot_histogram(bmp_orig.pixels, deltas, plot_path, os.path.basename(orig_path))


if __name__ == "__main__":
    main()