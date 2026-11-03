def dpcm_encode(pixels: bytes) -> bytes:
    """
    Biến đổi mảng điểm ảnh P sang mảng sai số vi sai Delta:
    Delta[0] = P[0], Delta[i] = (P[i] - P[i-1]) mod 256.
    """
    if not pixels:
        return b""
    n = len(pixels)
    deltas = bytearray(n)
    deltas[0] = pixels[0]
    for i in range(1, n):
        deltas[i] = (pixels[i] - pixels[i - 1]) & 0xFF
    return bytes(deltas)


def dpcm_decode(deltas: bytes) -> bytes:
    """
    Khôi phục hoàn toàn mảng điểm ảnh gốc P từ mảng vi sai Delta:
    P[0] = Delta[0], P[i] = (P[i-1] + Delta[i]) mod 256.
    """
    if not deltas:
        return b""
    n = len(deltas)
    pixels = bytearray(n)
    pixels[0] = deltas[0]
    for i in range(1, n):
        pixels[i] = (pixels[i - 1] + deltas[i]) & 0xFF
    return bytes(pixels)