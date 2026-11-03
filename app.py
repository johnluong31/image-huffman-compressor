import hashlib
import io
import math
import os
import sys
import time
from collections import Counter
import matplotlib.pyplot as plt
import streamlit as st

# Nạp các module thuật toán từ thư mục src/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from bmp_parser import read_bmp, write_bmp, generate_sample_bmp
from dpcm import dpcm_encode, dpcm_decode
from huffman import compress_payload, decompress_payload

# Cấu hình trang Dashboard
st.set_page_config(
    page_title="Image Huffman Compressor",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🖼️ Nén Tệp Ảnh (.BMP) với Huffman Codes & DPCM")
st.caption(
    "Hệ thống demo thuật toán nén dữ liệu ảnh bảo toàn (Lossless Image Compression) "
    "kết hợp Tiền xử lý vi sai DPCM và Mã tiền tố Huffman tối ưu."
)

# ----------------- SIDEBAR: TÙY CHỌN -----------------
with st.sidebar:
    st.header("⚙️ Thiết lập giải thuật")
    use_dpcm = st.toggle("Kích hoạt Tiền xử lý vi sai (DPCM)", value=True, 
                         help="Gom phân bố điểm ảnh về gần 0 để tối ưu hóa cây Huffman")
    st.divider()
    st.markdown("**Thông tin đồ án:**")
    st.markdown("- **Thuật toán:** Huffman Coding (CLRS Chapter 15)")
    st.markdown("- **Độ phức tạp:** $\\Theta(N + K \\log K) \\equiv \\Theta(N)$")
    st.markdown("- **Bảo toàn:** 100% Lossless (PSNR = $\\infty$)")
    
    st.divider()
    if st.button("Tạo ảnh mẫu chuẩn (landscape.bmp)"):
        sample_path = "data/landscape.bmp"
        generate_sample_bmp(sample_path)
        st.success(f"Đã tạo ảnh mẫu tại `{sample_path}`!")

# ----------------- HÀM TIỆN ÍCH -----------------
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def plot_entropy_chart(orig_pixels: bytes, dpcm_pixels: bytes):
    raw_counts = Counter(orig_pixels)
    dpcm_counts = Counter(dpcm_pixels)
    x_vals = list(range(256))
    y_raw = [raw_counts.get(i, 0) for i in x_vals]
    y_dpcm = [dpcm_counts.get(i, 0) for i in x_vals]

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    axes[0].bar(x_vals, y_raw, color="#2563eb", width=1.0)
    axes[0].set_title("Phân bố Pixel gốc (Entropy cao)", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Giá trị Byte (0 - 255)")
    axes[0].set_ylabel("Tần số")

    axes[1].bar(x_vals, y_dpcm, color="#059669", width=1.0)
    axes[1].set_title("Sau biến đổi DPCM (Tập trung quanh 0)", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Giá trị Vi sai (0 - 255)")
    axes[1].set_ylabel("Tần số")

    plt.tight_layout()
    return fig

# ----------------- GIAO DIỆN CHÍNH (TABS) -----------------
tab_compress, tab_decompress = st.tabs(["📦 1. Nén ảnh (.bmp ➜ .huf)", "🔓 2. Giải nén & Kiểm định (.huf ➜ .bmp)"])

# ----------------- TAB 1: NÉN ẢNH -----------------
with tab_compress:
    col_up, col_info = st.columns([1, 1])

    with col_up:
        uploaded_bmp = st.file_uploader("Tải tệp ảnh Bitmap (.bmp) lên:", type=["bmp"], key="upload_bmp")
        
        # Cho phép dùng nhanh ảnh mẫu nếu không muốn upload
        use_default_sample = st.checkbox("Hoặc sử dụng ảnh mẫu có sẵn: `data/landscape.bmp`", value=False)
        
    bmp_data_bytes = None
    file_display_name = ""

    if uploaded_bmp is not None:
        bmp_data_bytes = uploaded_bmp.read()
        file_display_name = uploaded_bmp.name
    elif use_default_sample and os.path.exists("data/landscape.bmp"):
        with open("data/landscape.bmp", "rb") as f:
            bmp_data_bytes = f.read()
        file_display_name = "landscape.bmp"

    if bmp_data_bytes:
        # Tạm lưu tệp để dùng hàm đọc BMP
        temp_input = "data/_temp_web_input.bmp"
        os.makedirs("data", exist_ok=True)
        with open(temp_input, "wb") as f:
            f.write(bmp_data_bytes)

        try:
            bmp_obj = read_bmp(temp_input)
            
            with col_up:
                st.image(bmp_data_bytes, caption=f"Ảnh đầu vào: {file_display_name} ({bmp_obj.width}x{bmp_obj.height})", use_container_width=True)

            # Thực hiện nén
            t0 = time.perf_counter()
            stream = dpcm_encode(bmp_obj.pixels) if use_dpcm else bmp_obj.pixels
            huf_bytes, stats = compress_payload(bmp_obj.header, stream, use_dpcm=use_dpcm)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            ratio = (stats["compressed_bytes"] / stats["original_bytes"]) * 100
            saving = 100.0 - ratio

            with col_info:
                st.subheader("📊 Kết quả Nén")
                m1, m2, m3 = st.columns(3)
                m1.metric("Kích thước gốc", f"{stats['original_bytes']:,} B")
                m2.metric("Kích thước nén", f"{stats['compressed_bytes']:,} B")
                m3.metric("Tiết kiệm dung lượng", f"{saving:.2f}%", delta=f"-{saving:.2f}%")

                m4, m5, m6 = st.columns(3)
                m4.metric("Entropy Shannon", f"{stats['entropy']:.3f} bit")
                m5.metric("Độ dài mã TB (ABL)", f"{stats['abl']:.3f} bit")
                m6.metric("Thời gian nén", f"{elapsed_ms:.1f} ms")

                st.info(f"💡 **Tính chất lý thuyết:** Độ dài mã trung bình thỏa mãn bất đẳng thức: "
                        f"${stats['entropy']:.3f} \\le {stats['abl']:.3f} < {stats['entropy']+1:.3f}$, khẳng định tính tối ưu của cây Huffman.")

                # Tải file nén về máy
                out_huf_name = os.path.splitext(file_display_name)[0] + ".huf"
                st.download_button(
                    label=f"⬇️ Tải tệp nén nhị phân ({out_huf_name})",
                    data=huf_bytes,
                    file_name=out_huf_name,
                    mime="application/octet-stream",
                    use_container_width=True,
                )

            # Vẽ biểu đồ phân bố tần suất
            st.divider()
            st.subheader("📈 Phân tích Entropy & Hiệu ứng DPCM")
            fig = plot_entropy_chart(bmp_obj.pixels, stream)
            st.pyplot(fig)

        except Exception as e:
            st.error(f"Lỗi đọc ảnh BMP: {str(e)}")

# ----------------- TAB 2: GIẢI NÉN & KIỂM ĐỊNH -----------------
with tab_decompress:
    col_dec_up, col_dec_view = st.columns([1, 1])

    with col_dec_up:
        uploaded_huf = st.file_uploader("Tải tệp nén (.huf) cần giải nén:", type=["huf"], key="upload_huf")

    if uploaded_huf is not None:
        huf_payload = uploaded_huf.read()

        try:
            t0 = time.perf_counter()
            bmp_header, stream, is_dpcm = decompress_payload(huf_payload)
            pixels = dpcm_decode(stream) if is_dpcm else stream
            elapsed_ms = (time.perf_counter() - t0) * 1000

            restored_bytes = bmp_header + pixels
            out_bmp_name = os.path.splitext(uploaded_huf.name)[0] + "_restored.bmp"

            with col_dec_up:
                st.success(f"Giải nén thành công trong **{elapsed_ms:.2f} ms**!")
                st.write(f"- Phương thức nén lưu trong Header: **{'Huffman + DPCM' if is_dpcm else 'Huffman thô'}**")
                st.write(f"- Kích thước khôi phục: **{len(restored_bytes):,} bytes**")

                st.download_button(
                    label=f"⬇️ Tải ảnh đã giải nén ({out_bmp_name})",
                    data=restored_bytes,
                    file_name=out_bmp_name,
                    mime="image/bmp",
                    use_container_width=True,
                )

            with col_dec_view:
                st.image(restored_bytes, caption=f"Ảnh khôi phục: {out_bmp_name}", use_container_width=True)

            # Đối chiếu Lossless nếu có ảnh gốc tương ứng
            st.divider()
            st.subheader("🛡️ Kiểm định Tính Toàn vẹn Tuyệt đối (Lossless Verification)")
            
            ref_bmp_file = st.file_uploader("Tải ảnh gốc ban đầu để đối chiếu bit (tùy chọn):", type=["bmp"], key="ref_bmp")
            if ref_bmp_file:
                orig_bytes = ref_bmp_file.read()
                hash_orig = sha256_bytes(orig_bytes)
                hash_rest = sha256_bytes(restored_bytes)

                c1, c2 = st.columns(2)
                c1.code(f"SHA-256 (Ảnh gốc):\n{hash_orig}")
                c2.code(f"SHA-256 (Khôi phục):\n{hash_rest}")

                if hash_orig == hash_rest:
                    st.success("🎯 **KẾT QUẢ: KHỚP 100% BIT-BY-BIT! (Lossless: MSE = 0.0000, PSNR = ∞ dB)**")
                else:
                    st.error("⚠️ CẢNH BÁO: Mã băm SHA-256 không khớp!")

        except Exception as e:
            st.error(f"Lỗi giải nén: Tệp .huf không hợp lệ ({str(e)})")