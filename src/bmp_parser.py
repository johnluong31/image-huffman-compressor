import struct
import os
import math


class BMPImage:
    """Cấu trúc lưu trữ thông tin Header và mảng Pixel của tệp BMP."""
    def __init__(self, header: bytes, pixels: bytes, width: int, height: int, bpp: int):
        self.header = header
        self.pixels = pixels
        self.width = width
        self.height = height
        self.bpp = bpp


def read_bmp(filepath: str) -> BMPImage:
    """Đọc tệp BMP nhị phân, tách riêng phần Header (54+ bytes) và mảng Pixel."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Không tìm thấy tệp ảnh: {filepath}")

    with open(filepath, "rb") as f:
        data = f.read()

    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError("Tệp không đúng định dạng chuẩn Bitmap (.bmp)!")

    # Byte 10..14 trong BMP File Header lưu vị trí bắt đầu của Pixel Data (thường là 54)
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    width, height = struct.unpack_from("<ii", data, 18)
    bpp = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]

    if compression != 0:
        raise ValueError("Chỉ hỗ trợ tệp BMP không nén (BI_RGB = 0).")

    header = data[:pixel_offset]
    pixels = data[pixel_offset:]
    return BMPImage(header, pixels, width, abs(height), bpp)


def write_bmp(filepath: str, header: bytes, pixels: bytes) -> None:
    """Ghi ghép lại phần Header nguyên bản và mảng Pixel đã giải nén ra tệp .bmp."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(header)
        f.write(pixels)


def generate_sample_bmp(filepath: str, width: int = 256, height: int = 256) -> None:
    """
    Tự động tạo một bức ảnh phong cảnh (bầu trời chuyển sắc, mặt trời, dãy núi)
    chuẩn BMP 24-bit (Header đúng 54 bytes) để chạy thực nghiệm ngay lập tức.
    """
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    row_stride = (width * 3 + 3) & ~3
    padding = row_stride - width * 3
    pixel_data_size = row_stride * height
    file_size = 54 + pixel_data_size

    # Tạo 14 bytes Bitmap File Header + 40 bytes DIB Header = 54 bytes
    bmp_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, 54)
    dib_header = struct.pack(
        "<IiiHHIIiiII",
        40, width, height, 1, 24, 0, pixel_data_size, 2835, 2835, 0, 0
    )

    pixels = bytearray()
    for y in range(height):
        # Đảo chiều y để vẽ từ dưới lên theo chuẩn lưu trữ của BMP
        mountain_h1 = int(height * 0.35 + 25 * math.sin(y * 0.05))
        for x in range(width):
            m1 = int(height * 0.32 + 28 * math.sin(x * 0.04) + 12 * math.cos(x * 0.11))
            m2 = int(height * 0.48 + 20 * math.cos(x * 0.03 + 1.2))
            dist_sun = math.hypot(x - width * 0.75, y - height * 0.72)

            if y < m1:
                # Tiền cảnh: Đồi cỏ xanh đậm
                r, g, b = 34, 110 + (y % 15), 45
            elif y < m2:
                # Trung cảnh: Dãy núi đá xanh lam
                r, g, b = 70, 95, 130
            elif dist_sun < 28:
                # Mặt trời vàng rực
                r, g, b = 255, 220, 60
            else:
                # Bầu trời chuyển sắc mượt mà (Gradient)
                ratio = y / height
                r = int(135 + 80 * (1 - ratio))
                g = int(190 + 40 * (1 - ratio))
                b = 245

            pixels.extend((b, g, r))  # Chuẩn BMP lưu theo thứ tự BGR
        pixels.extend(b"\x00" * padding)

    write_bmp(filepath, bmp_header + dib_header, bytes(pixels))