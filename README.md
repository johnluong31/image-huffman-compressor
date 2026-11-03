# 🖼️ Lossless Image Compression using Huffman Coding & DPCM

Hệ thống nén dữ liệu tệp ảnh Bitmap (`.bmp`) không mất mát (Lossless Data Compression) vận dụng thuật toán kinh điển **Huffman Codes** (CLRS Chapter 15) kết hợp kỹ thuật tiền xử lý vi sai **DPCM (Differential Pulse Code Modulation)**. Dự án tích hợp đầy đủ giao diện dòng lệnh tương tác (Interactive CLI) và bảng điều khiển trực quan hiện đại bằng **Streamlit Web Dashboard**.

---

## 📌 Tính năng nổi bật

- **Nén nhị phân thực thụ (True Bit-Packing):** Đóng gói tuần tự từng bit mã hóa thành các byte vật lý (`wb`), xử lý padding bits ở byte cuối cùng chuẩn xác, không dùng kỹ thuật nén giả bằng chuỗi ký tự `'0'`/`'1'`.
- **Tệp nén độc lập (Self-contained Archive):** Định dạng nhị phân `.huf` tự lưu trữ cấu trúc Header và bảng tần số thu gọn, có thể mang sang bất kỳ máy tính nào giải nén độc lập mà không cần phụ thuộc vào cây dữ liệu lưu trong bộ nhớ RAM.
- **Tiền xử lý vi sai DPCM (Differential Encoding):** Khai thác tính tương quan không gian (Spatial Redundancy) của ảnh tự nhiên. Thay vì lưu trực tiếp giá trị pixel, thuật toán lưu sai số vi sai giữa hai điểm ảnh liền kề $\Delta[i] = (P[i] - P[i-1]) \bmod 256$. Phân bố vi sai tập trung đậm đặc quanh giá trị $0$, giúp tối ưu hóa chiều dài từ mã Huffman và tăng tỉ lệ tiết kiệm dung lượng từ $25\% - 50\%$.
- **Bảo toàn chất lượng ảnh 100% (Lossless Verification):** Kiểm định chất lượng khôi phục tuyệt đối với $\text{MSE} = 0.0000$, $\text{PSNR} = \infty\text{ dB}$ và đối chiếu mã băm **SHA-256** khớp chính xác từng bit so với ảnh gốc.
- **Giao diện Web Streamlit hiện đại:** Hỗ trợ kéo-thả tải ảnh trực quan, đo lường Entropy Shannon, thời gian thực thi (ms) và vẽ biểu đồ so sánh phổ tần suất trước và sau khi biến đổi DPCM.

---

## 📂 Cấu trúc thư mục dự án

```text
image-huffman-compressor/
├── app.py                  # Giao diện Web tương tác (Streamlit Dashboard)
├── src/
│   ├── bmp_parser.py       # Đọc/ghi cấu trúc Header BMP 54 bytes & sinh ảnh mẫu
│   ├── dpcm.py             # Thuật toán mã hóa/giải mã sai phân DPCM
│   ├── huffman.py          # Min-Heap, Cây nhị phân Huffman & Bit-packing nhị phân
│   └── main.py             # CLI điều khiển (hỗ trợ Interactive Menu & Headless CLI)
├── data/
│   ├── landscape.bmp       # Ảnh mẫu đầu vào chuẩn 24-bit RGB
│   ├── compressed.huf      # Tệp nhị phân sau nén (chứa Header độc lập)
│   └── restored.bmp        # Ảnh khôi phục hoàn chỉnh sau khi giải nén
├── benchmarks/
│   ├── verify_psnr.py      # Script kiểm định SHA-256, PSNR, MSE & xuất Histogram
│   └── histogram_plot.png  # Biểu đồ so sánh phân bố Entropy trước/sau DPCM
├── .gitignore              # Bộ lọc tệp tạm và cache Python
└── README.md
```

---

## ⚙️ Cài đặt môi trường

Yêu cầu máy tính đã cài đặt Python 3.9 trở lên. Cài đặt các thư viện cần thiết qua terminal:

```bash
pip install streamlit matplotlib
```

---

## 🚀 Hướng dẫn sử dụng

### 1. Khởi chạy Giao diện Web (Khuyến nghị để demo trực quan)
Khởi động ứng dụng Dashboard kéo-thả:
```bash
streamlit run app.py
```
Trình duyệt web sẽ tự động mở tại địa chỉ `http://localhost:8501`:
* **Tab 1 - Nén ảnh:** Kéo thả tệp `.bmp` bất kỳ (hoặc dùng ảnh mẫu có sẵn), xem dung lượng nén, Entropy, thời gian thực thi và tải file `.huf` về máy.
* **Tab 2 - Giải nén:** Tải tệp `.huf` lên để khôi phục ảnh `.bmp`, tải ảnh về và kiểm tra đối chiếu mã SHA-256 trực tiếp trên giao diện.

### 2. Sử dụng Menu dòng lệnh tương tác (Interactive CLI)
Chạy lệnh trực tiếp không cần nhớ cú pháp tham số dài dòng:
```bash
python src/main.py
```
Hệ thống hiển thị menu đánh số `[1], [2], [3]...` để bạn chọn tệp ảnh trong thư mục `data/` và thực hiện nén/giải nén nhanh chóng.

### 3. Sử dụng tham số dòng lệnh (Headless CLI)
Dành cho việc kiểm thử tự động hoặc chạy batch:
```bash
# 1. Tạo tệp ảnh mẫu chuẩn BMP 24-bit (nếu chưa có ảnh):
python src/main.py generate-sample -o data/landscape.bmp

# 2. Thực hiện nén ảnh sang định dạng .huf:
python src/main.py compress data/landscape.bmp -o data/compressed.huf

# 3. Giải nén tệp .huf khôi phục lại ảnh .bmp:
python src/main.py decompress data/compressed.huf -o data/restored.bmp

# 4. Kiểm định toàn vẹn bit (SHA-256, PSNR) và xuất biểu đồ Histogram:
python benchmarks/verify_psnr.py
```

---

## 📊 Phân tích Độ phức tạp Thuật toán ($O, \Omega, \Theta$)

Đặt:
- $N = W \times H \times C$ là tổng số bytes dữ liệu điểm ảnh (Pixel Data payload).
- $K$ là số ký hiệu vi sai phân biệt ($1 \le K \le 256$ đối với dữ liệu biểu diễn ở mức byte).

| Giai đoạn | Thao tác giải thuật | Độ phức tạp thời gian | Độ phức tạp không gian | Giải thích chi tiết |
| :--- | :--- | :---: | :---: | :--- |
| **1. Biến đổi DPCM** | $\Delta[i] = (P[i] - P[i-1]) \bmod 256$ | $\Theta(N)$ | $\Theta(N)$ | Duyệt tuần tự qua mảng $N$ bytes ảnh đúng 1 lần |
| **2. Đếm tần số** | Quét mảng vi sai và cập nhật mảng đếm | $\Theta(N)$ | $\Theta(K) \equiv O(1)$ | Truy cập mảng đếm tần suất với chi phí $O(1)$ mỗi phần tử |
| **3. Dựng cây Huffman** | `BUILD-MIN-HEAP` và lặp gộp $K-1$ lần | $\Theta(K \log K)$ | $\Theta(K) \equiv O(1)$ | Khởi tạo Heap $\Theta(K)$ và $K-1$ lần ghép mất $\Theta(K \log K)$ ($K \le 256$ là hằng số) |
| **4. Sinh bảng mã tiền tố** | Duyệt DFS toàn bộ $2K-1$ nút cây | $\Theta(K) \equiv O(1)$ | $\Theta(K) \equiv O(1)$ | Cây nhị phân đầy đủ có tối đa 511 nút |
| **5. Đóng gói bit (Encode)** | Tra bảng mã và ghép bit nhị phân | $\Theta(N)$ | $\Theta(N)$ | Chi phí tra bảng băm $O(1)$, tổng độ dài bit xuất ra tỉ lệ thuận với $N$ |
| **6. Giải nén luồng bit** | Duyệt luồng bit trên cây nhị phân | $\Theta(N)$ | $\Theta(N)$ | Mỗi bit di chuyển 1 cạnh, gặp nút lá khôi phục 1 byte |
| **7. Nghịch đảo DPCM** | $P[i] = (P[i-1] + \Delta[i]) \bmod 256$ | $\Theta(N)$ | $\Theta(N)$ | Phép cộng tích lũy tuần tự khôi phục mảng điểm ảnh ban đầu |

### Tổng kết độ phức tạp tiệm cận:
- **Thời gian (Time Complexity):** $T(N, K) = \Theta(N + K \log K) \equiv \Theta(N)$ (Tuyến tính tuyệt đối theo kích thước dữ liệu ảnh).
- **Bộ nhớ (Space Complexity):** $S(N, K) = \Theta(N + K) \equiv \Theta(N)$ (Bộ đệm dữ liệu điểm ảnh trong bộ nhớ RAM).

---

## 📈 Kết quả Thực nghiệm & Kiểm định

Thực nghiệm trên tệp ảnh 24-bit RGB (`data/landscape.bmp`, độ phân giải $256 \times 256$):
- **Dung lượng ảnh gốc:** $196,662$ bytes
- **Dung lượng sau nén:** $147,210$ bytes
- **Tỉ lệ tiết kiệm không gian:** $25.15\%$
- **Entropy Shannon ($H$):** $5.937$ bits/symbol
- **Độ dài từ mã trung bình ($ABL$):** $5.964$ bits/symbol (Thỏa mãn bất đẳng thức tối ưu $H \le ABL < H + 1$)
- **Kiểm định tính toàn vẹn Lossless:**
  - Sai số bình phương trung bình: $\text{MSE} = 0.000000$
  - Tỉ số tín hiệu trên nhiễu cực đại: $\text{PSNR} = \infty\text{ dB}$
  - Mã băm SHA-256 ảnh gốc và ảnh sau giải nén trùng khớp hoàn toàn ($100\%$ Bit-by-bit).

---

## 👤 Tác giả
- GitHub: [@johnluong31](https://github.com/johnluong31)