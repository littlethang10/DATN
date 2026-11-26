https://github.com/ankandrew/fast-plate-ocr
https://github.com/FoundationVision/ByteTrack?utm_source=chatgpt.com

"C:\ffmpeg\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe" -re -stream_loop -1 -i "C:\Users\pc\Downloads\1.mp4" -an -c:v libx264 -preset veryfast -tune zerolatency -pix_fmt yuv420p -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/test




# Khởi động RTSP server
Start-Process -FilePath "C:\THANG2\code\mediamtx\mediamtx.exe" -WorkingDirectory "C:\THANG2\code\mediamtx" -WindowStyle Hidden

# Phát video thứ nhất, lặp vô hạn
Start-Process -FilePath "C:\ffmpeg\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe" -ArgumentList '-re -stream_loop -1 -i "C:\Users\pc\Downloads\Recording 2026-11-03 085654.mp4" -c copy -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/video' -WindowStyle Hidden

# Phát video thứ hai, lặp vô hạn
Start-Process -FilePath "C:\ffmpeg\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe" -ArgumentList '-re -stream_loop -1 -i "C:\Users\pc\Downloads\Recording 2026-11-04 154815.mp4" -c copy -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/video2' -WindowStyle Hidden

# Chạy dự án, sau khi Docker Desktop đã khởi động
Set-Location "C:\THANG2\code"
docker compose up -d