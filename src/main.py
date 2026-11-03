import argparse
import glob
import os
import sys
import time

# Thêm đường dẫn src/ vào hệ thống
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.insert(0, CURRENT_DIR)

from bmp_parser import read_bmp, write_bmp, generate_sample_bmp
from dpcm import dpcm_encode, dpcm_decode
from huffman import compress_payload, decompress_payload


def handle_compress(input_bmp: str, output_huf: str, use_dpcm: bool = True) -> None:
    t0 = time.perf_counter()
    bmp = read_bmp(input_bmp)
    stream = dpcm_encode(bmp.pixels) if use_dpcm else bmp.pixels
    compressed_bytes, stats = compress_payload(bmp.header, stream, use_dpcm=use_dpcm)

    os.makedirs(os.path.dirname(os.path.abspath(output_huf)), exist_ok=True)
    with open(output_huf, "wb") as f:
        f.write(compressed_bytes)
    elapsed = (time.perf_counter() - t0) * 1000

    ratio = (stats["compressed_bytes"] / stats["original_bytes"]) * 100
    saving = 100.0 - ratio

    print("\n" + "=" * 60)
    print(" KẾT QUẢ NÉN ẢNH HUFFMAN + DPCM")
    print("=" * 60)
    print(f" - Tệp đầu vào          : {input_bmp} ({bmp.width}x{bmp.height}, {bmp.bpp}-bit)")
    print(f" - Tệp đầu ra           : {output_huf}")
    print(f" - Tiền xử lý vi sai    : {'Bật (DPCM)' if use_dpcm else 'Tắt (Raw Huffman)'}")
    print(f" - Số ký hiệu phân biệt : K = {stats['distinct_symbols']} / 256")
    print(f" - Entropy Shannon (H)  : {stats['entropy']:.4f} bits/symbol")
    print(f" - Độ dài mã TB (ABL)   : {stats['abl']:.4f} bits/symbol (Thỏa H <= ABL < H + 1)")
    print(f" - Dung lượng gốc       : {stats['original_bytes']:,} bytes")
    print(f" - Dung lượng sau nén   : {stats['compressed_bytes']:,} bytes")
    print(f" - Tỉ lệ nén đạt được   : {ratio:.2f}% (Tiết kiệm {saving:.2f}% dung lượng)")
    print(f" - Thời gian thực thi   : {elapsed:.2f} ms")
    print("=" * 60)


def handle_decompress(input_huf: str, output_bmp: str) -> None:
    t0 = time.perf_counter()
    with open(input_huf, "rb") as f:
        huf_bytes = f.read()

    bmp_header, stream, use_dpcm = decompress_payload(huf_bytes)
    pixels = dpcm_decode(stream) if use_dpcm else stream
    write_bmp(output_bmp, bmp_header, pixels)
    elapsed = (time.perf_counter() - t0) * 1000

    print("\n" + "=" * 60)
    print(" KẾT QUẢ GIẢI NÉN ẢNH HUFFMAN")
    print("=" * 60)
    print(f" - Tệp nén đầu vào      : {input_huf}")
    print(f" - Ảnh khôi phục        : {output_bmp}")
    print(f" - Dung lượng khôi phục : {len(bmp_header) + len(pixels):,} bytes")
    print(f" - Thời gian giải nén   : {elapsed:.2f} ms")
    print("=" * 60)


def list_and_choose_file(pattern: str, title: str, exclude_keyword: str = None) -> str:
    """Quét thư mục và hiển thị danh sách cho người dùng chọn số."""
    data_dir = os.path.join(PROJECT_ROOT, "data")
    search_path = os.path.join(data_dir, pattern)
    files = glob.glob(search_path)

    if exclude_keyword:
        files = [f for f in files if exclude_keyword not in os.path.basename(f).lower()]

    print("\n" + "-" * 60)
    print(f" {title}")
    print("-" * 60)

    if files:
        for idx, f in enumerate(files, start=1):
            rel_path = os.path.relpath(f, PROJECT_ROOT)
            f_size = os.path.getsize(f)
            print(f" [{idx}] {rel_path:<32} ({f_size:,} bytes)")
    else:
        print(" (Không tìm thấy tệp phù hợp trong thư mục data/)")

    print(" [0] Nhập đường dẫn tệp thủ công")
    print("-" * 60)

    while True:
        choice = input("Nhập số thứ tự: ").strip()
        if choice.isdigit():
            c_int = int(choice)
            if 1 <= c_int <= len(files):
                return os.path.relpath(files[c_int - 1], PROJECT_ROOT)
            elif c_int == 0:
                manual = input("Nhập đường dẫn tệp: ").strip()
                return manual
        elif os.path.exists(choice):
            return choice
        print("[!] Lựa chọn không hợp lệ, vui lòng nhập lại.")


def run_interactive_menu():
    """Menu tương tác chính khi chạy lệnh `python src/main.py` không kèm tham số."""
    while True:
        print("\n" + "=" * 60)
        print(" CHƯƠNG TRÌNH NÉN ẢNH HUFFMAN CODES & DPCM (TIỆN ÍCH)")
        print("=" * 60)
        print(" [1] Nén tệp ảnh (.bmp -> .huf)")
        print(" [2] Giải nén tệp (.huf -> .bmp)")
        print(" [3] Tạo ảnh mẫu BMP chuẩn (data/landscape.bmp)")
        print(" [4] Chạy kiểm định toàn vẹn Lossless (PSNR & Histogram)")
        print(" [0] Thoát chương trình")
        print("=" * 60)

        opt = input("Chọn chức năng (0-4): ").strip()

        if opt == "1":
            input_file = list_and_choose_file("*.bmp", "DANH SÁCH ẢNH .BMP CẦN NÉN:", exclude_keyword="restored")
            if not os.path.exists(input_file):
                print(f"[x] Không tìm thấy tệp: {input_file}")
                continue

            base_name = os.path.splitext(os.path.basename(input_file))[0]
            default_out = os.path.join("data", f"{base_name}.huf")
            custom_out = input(f"Đường dẫn file sau nén [mặc định: {default_out}]: ").strip()
            out_file = custom_out if custom_out else default_out

            handle_compress(input_file, out_file, use_dpcm=True)

        elif opt == "2":
            input_file = list_and_choose_file("*.huf", "DANH SÁCH TỆP NÉN .HUF CẦN GIẢI NÉN:")
            if not os.path.exists(input_file):
                print(f"[x] Không tìm thấy tệp: {input_file}")
                continue

            base_name = os.path.splitext(os.path.basename(input_file))[0]
            default_out = os.path.join("data", f"{base_name}_restored.bmp")
            custom_out = input(f"Đường dẫn ảnh khôi phục [mặc định: {default_out}]: ").strip()
            out_file = custom_out if custom_out else default_out

            handle_decompress(input_file, out_file)

        elif opt == "3":
            sample_path = os.path.join("data", "landscape.bmp")
            generate_sample_bmp(sample_path)
            print(f"[+] Đã tạo ảnh mẫu thành công tại: {sample_path}")

        elif opt == "4":
            verify_script = os.path.join(PROJECT_ROOT, "benchmarks", "verify_psnr.py")
            if os.path.exists(verify_script):
                os.system(f'"{sys.executable}" "{verify_script}"')
            else:
                print("[x] Không tìm thấy tệp benchmarks/verify_psnr.py!")

        elif opt == "0":
            print("Đã thoát chương trình. Tạm biệt!")
            break
        else:
            print("[!] Lựa chọn không hợp lệ!")


def main():
    parser = argparse.ArgumentParser(description="Chương trình nén tệp ảnh .BMP bằng Huffman Codes & DPCM")
    subparsers = parser.add_subparsers(dest="command", required=False)

    # Subcommand: generate-sample
    gen_parser = subparsers.add_parser("generate-sample", help="Tạo tệp ảnh mẫu data/landscape.bmp")
    gen_parser.add_argument("-o", "--output", default="data/landscape.bmp", help="Đường dẫn ảnh mẫu")

    # Subcommand: compress
    comp_parser = subparsers.add_parser("compress", help="Nén tệp ảnh .bmp sang .huf")
    comp_parser.add_argument("input", help="Đường dẫn tệp ảnh .bmp đầu vào")
    comp_parser.add_argument("-o", "--output", default="data/compressed.huf", help="Đường dẫn tệp .huf đầu ra")
    comp_parser.add_argument("--no-dpcm", action="store_true", help="Tắt biến đổi vi sai DPCM")

    # Subcommand: decompress
    decomp_parser = subparsers.add_parser("decompress", help="Giải nén tệp .huf về lại .bmp")
    decomp_parser.add_argument("input", help="Đường dẫn tệp .huf đầu vào")
    decomp_parser.add_argument("-o", "--output", default="data/restored.bmp", help="Đường dẫn ảnh .bmp khôi phục")

    # Nếu người dùng không gõ tham số nào -> Bật Menu tương tác
    if len(sys.argv) == 1:
        run_interactive_menu()
        return

    args = parser.parse_args()
    if args.command == "generate-sample":
        generate_sample_bmp(args.output)
        print(f"[+] Đã tạo tệp ảnh mẫu chuẩn 24-bit BMP tại: {args.output}")
    elif args.command == "compress":
        handle_compress(args.input, args.output, use_dpcm=not args.no_dpcm)
    elif args.command == "decompress":
        handle_decompress(args.input, args.output)


if __name__ == "__main__":
    main()