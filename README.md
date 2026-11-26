<div align="center">

# 🚗 GateView

### Hệ thống giám sát xe ra vào

Theo dõi camera, nhận diện biển số và quản lý lịch sử ra vào trên một giao diện.

**Python** · **Docker** · **RTSP** · **YOLO** · **OCR** · **ByteTrack**

</div>

---

## Tổng quan

GateView kết hợp giao diện web, dịch vụ lưu trữ dữ liệu và bộ xử lý nhận diện để hỗ trợ giám sát phương tiện tại cổng. Hệ thống lấy hình ảnh từ camera RTSP, theo dõi phương tiện và ghi nhận thông tin phục vụ tra cứu, thống kê.

### Chức năng chính

- 📹 Quản lý camera ra/vào và xem luồng RTSP.
- 🎯 Cấu hình vùng quan tâm (ROI) cho từng camera.
- 🔎 Nhận diện phương tiện, đọc biển số và theo dõi đối tượng.
- 🕘 Xem lịch sử lượt xe, tìm kiếm và kiểm tra thông tin nhận diện.
- 📊 Theo dõi thống kê và xuất báo cáo Excel.

## Cấu trúc dự án

```text
├── be/                 # Backend, xử lý nhận diện và xuất báo cáo
├── fe/                 # Giao diện web và cấu hình Nginx
├── model/              # Các mô hình nhận diện
├── mediamtx/           # MediaMTX và cấu hình luồng
├── fast-plate-ocr/     # Mã nguồn OCR
├── fast-plate-ocr-src/ # Ứng dụng và mã nguồn OCR
├── docs/               # Tài liệu và nguồn tham khảo
├── tracking.json       # Cấu hình theo dõi
└── compose.yaml        # Cấu hình Docker Compose
```

## Bắt đầu nhanh

### Yêu cầu

- [Git](https://git-scm.com/) và [Git LFS](https://git-lfs.com/) để tải đầy đủ các tệp mô hình.
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) hoặc Docker Engine có Docker Compose.
- Camera có luồng RTSP hoặc nguồn video RTSP tương thích nếu muốn xem camera.

### 1. Tải dự án

```bash
git lfs install
git clone https://github.com/littlethang10/DATN.git
cd DATN
git lfs pull
```

### 2. Khởi động giao diện và backend

```bash
docker compose up -d --build
```

Mở **http://localhost:8080** trong trình duyệt. Dữ liệu backend được lưu trong Docker volume `gateview-data`.

```bash
# Xem trạng thái và nhật ký
docker compose ps
docker compose logs -f

# Dừng các dịch vụ
docker compose down
```

### 3. Thêm camera

Trong giao diện, vào mục quản lý camera để thêm tên, mã camera, chiều xe và địa chỉ RTSP. Cấu hình ROI theo khu vực cần nhận diện. Nếu nguồn RTSP chạy trên máy cài Docker, địa chỉ camera phải có thể truy cập từ container; trên Docker Desktop có thể dùng `host.docker.internal` thay cho `localhost` khi phù hợp.

## Nhận diện tự động

Docker Compose khởi động **giao diện và backend**; bộ xử lý nhận diện `be/recognize.py` chạy riêng trên máy chủ. Bộ xử lý sử dụng mô hình `model/best_640x640.pt`, cấu hình `tracking.json` và kết nối đến ứng dụng tại `http://127.0.0.1:8080`.

Mã nhận diện cần môi trường Python với OpenCV, PyTorch, NumPy, FastALPR và Ultralytics; cấu hình hiện tại hướng đến GPU NVIDIA/CUDA. Các phụ thuộc này không nằm trong `be/requirements.txt` của container backend và cần được cài riêng phù hợp với máy. Xem thêm [hướng dẫn ứng dụng OCR](fast-plate-ocr-src/APP_README.md).

## Công nghệ

| Thành phần | Công nghệ |
| --- | --- |
| Giao diện | HTML, CSS, JavaScript, Nginx |
| Backend và dữ liệu | Python, SQLite |
| Video | RTSP, FFmpeg, MediaMTX |
| Nhận diện và theo dõi | YOLO, FastALPR, OCR, ByteTrack |
| Triển khai | Docker Compose, Git LFS |

## Tham khảo

- [fast-plate-ocr](https://github.com/ankandrew/fast-plate-ocr)
- [ByteTrack](https://github.com/FoundationVision/ByteTrack)
