def dpcm_encode(pixels: bytes) -> bytes:
    """Biến đổi vi sai độc lập trên từng kênh màu (BGR) với bước nhảy stride = 3."""
    if not pixels:
        return b""
    n = len(pixels)
    deltas = bytearray(n)
    
    # 3 byte đầu tiên (B0, G0, R0) giữ nguyên làm mốc
    stride = 3 if n >= 3 else 1
    for c in range(min(stride, n)):
        deltas[c] = pixels[c]
        
    # Tính sai số: pixel màu này trừ pixel cùng màu ngay trước nó
    for i in range(stride, n):
        deltas[i] = (pixels[i] - pixels[i - stride]) & 0xFF
    return bytes(deltas)


def dpcm_decode(deltas: bytes) -> bytes:
    """Khôi phục mảng điểm ảnh theo từng kênh màu độc lập."""
    if not deltas:
        return b""
    n = len(deltas)
    pixels = bytearray(n)
    
    stride = 3 if n >= 3 else 1
    for c in range(min(stride, n)):
        pixels[c] = deltas[c]
        
    for i in range(stride, n):
        pixels[i] = (pixels[i - stride] + deltas[i]) & 0xFF
    return bytes(pixels)