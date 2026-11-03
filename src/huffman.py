import heapq
import struct
import math
from collections import Counter
from typing import Dict, Optional, Tuple


class HuffmanNode:
    """Nút của Cây nhị phân Huffman."""
    def __init__(self, symbol: Optional[int], freq: int, left=None, right=None):
        self.symbol = symbol
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other: "HuffmanNode") -> bool:
        # So sánh ưu tiên theo tần số nhỏ hơn; nếu bằng nhau thì ưu tiên symbol nhỏ hơn để cây cố định
        if self.freq != other.freq:
            return self.freq < other.freq
        s1 = self.symbol if self.symbol is not None else 256
        s2 = other.symbol if other.symbol is not None else 256
        return s1 < s2


def build_huffman_tree(freq_map: Dict[int, int]) -> Optional[HuffmanNode]:
    """Xây dựng cây Huffman từ bảng tần số bằng Min-Heap với độ phức tạp O(K log K)."""
    if not freq_map:
        return None

    min_heap = [HuffmanNode(sym, freq) for sym, freq in sorted(freq_map.items())]
    heapq.heapify(min_heap)  # BUILD-MIN-HEAP trong thời gian O(K)

    if len(min_heap) == 1:
        # Trường hợp đặc biệt ảnh chỉ có 1 giá trị duy nhất
        only_node = heapq.heappop(min_heap)
        return HuffmanNode(None, only_node.freq, left=only_node)

    while len(min_heap) > 1:
        x = heapq.heappop(min_heap)  # EXTRACT-MIN thứ 1
        y = heapq.heappop(min_heap)  # EXTRACT-MIN thứ 2
        z = HuffmanNode(None, x.freq + y.freq, left=x, right=y)
        heapq.heappush(min_heap, z)  # INSERT nút cha

    return heapq.heappop(min_heap)


def generate_codes(root: Optional[HuffmanNode]) -> Dict[int, str]:
    """Duyệt cây Huffman (DFS) để sinh bảng mã tiền tố nhị phân cho từng ký hiệu."""
    codes: Dict[int, str] = {}

    def _dfs(node: Optional[HuffmanNode], current_bits: str):
        if node is None:
            return
        if node.symbol is not None:
            codes[node.symbol] = current_bits or "0"
            return
        _dfs(node.left, current_bits + "0")
        _dfs(node.right, current_bits + "1")

    _dfs(root, "")
    return codes


def pack_bits(bit_string: str) -> Tuple[bytes, int]:
    """Gom chuỗi bit '0'/'1' thành mảng byte vật lý, trả về (mảng_byte, số_bit_bù_padding)."""
    padding = (8 - len(bit_string) % 8) % 8
    if padding > 0:
        bit_string += "0" * padding

    packed = bytearray(len(bit_string) // 8)
    for i in range(0, len(bit_string), 8):
        packed[i // 8] = int(bit_string[i : i + 8], 2)
    return bytes(packed), padding


def unpack_bits(packed_bytes: bytes, padding: int) -> str:
    """Giải nén mảng byte vật lý thành chuỗi bit và cắt bỏ phần bit padding."""
    bit_chunks = [f"{byte:08b}" for byte in packed_bytes]
    bit_string = "".join(bit_chunks)
    if padding > 0:
        bit_string = bit_string[:-padding]
    return bit_string


def compress_payload(bmp_header: bytes, data_stream: bytes, use_dpcm: bool = True) -> Tuple[bytes, dict]:
    """
    Đóng gói toàn bộ dữ liệu nén ra định dạng nhị phân .huf độc lập:
    [4B Magic 'HUF1'][1B Flag DPCM][1B Padding][2B K][4B HeaderLen][4B DataLen][BMP Header][FreqTable][PackedBits]
    """
    freq_map = dict(Counter(data_stream))
    root = build_huffman_tree(freq_map)
    codes = generate_codes(root)

    encoded_bits = "".join(codes[b] for b in data_stream)
    packed_stream, padding = pack_bits(encoded_bits)

    # Tính toán các chỉ số học thuật: Entropy Shannon (H) và Độ dài từ mã trung bình (ABL)
    total_symbols = len(data_stream)
    entropy = -sum((f / total_symbols) * math.log2(f / total_symbols) for f in freq_map.values())
    abl = sum((freq_map[sym] / total_symbols) * len(codes[sym]) for sym in freq_map)

    k = len(freq_map)
    file_header = struct.pack(
        "<4sBBHII",
        b"HUF1",
        1 if use_dpcm else 0,
        padding,
        k,
        len(bmp_header),
        total_symbols,
    )

    freq_table_bytes = bytearray()
    for sym, freq in sorted(freq_map.items()):
        freq_table_bytes.extend(struct.pack("<BI", sym, freq))

    full_binary = file_header + bmp_header + bytes(freq_table_bytes) + packed_stream
    stats = {
        "distinct_symbols": k,
        "entropy": entropy,
        "abl": abl,
        "original_bytes": len(bmp_header) + total_symbols,
        "compressed_bytes": len(full_binary),
    }
    return full_binary, stats


def decompress_payload(huf_bytes: bytes) -> Tuple[bytes, bytes, bool]:
    """Giải mã tệp nhị phân .huf độc lập, trả về (bmp_header, data_stream, use_dpcm)."""
    magic, dpcm_flag, padding, k, header_len, total_symbols = struct.unpack_from("<4sBBHII", huf_bytes, 0)
    if magic != b"HUF1":
        raise ValueError("Tệp không đúng định dạng nén .huf hợp lệ!")

    offset = 16
    bmp_header = huf_bytes[offset : offset + header_len]
    offset += header_len

    freq_map: Dict[int, int] = {}
    for _ in range(k):
        sym, freq = struct.unpack_from("<BI", huf_bytes, offset)
        freq_map[sym] = freq
        offset += 5

    packed_stream = huf_bytes[offset:]
    root = build_huffman_tree(freq_map)
    bit_string = unpack_bits(packed_stream, padding)

    decoded = bytearray()
    curr = root
    for bit in bit_string:
        curr = curr.left if bit == "0" else curr.right
        if curr.symbol is not None:
            decoded.append(curr.symbol)
            curr = root
            if len(decoded) == total_symbols:
                break

    return bmp_header, bytes(decoded), bool(dpcm_flag)