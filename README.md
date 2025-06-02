# Hướng dẫn sử dụng ứng dụng Quản lý bộ sưu tập game

## 1. Cài đặt để chạy file code
- Tải file .exe bên release 

## 2. Đăng nhập / Đăng ký
- **Admin mặc định:**  
  - Tài khoản: `123`  
  - Mật khẩu: `123`
- Người dùng mới có thể đăng ký tài khoản.

## 3. Chức năng chính
- **Admin:**
  - Thêm game
  - Sửa game
  - Xóa game
  - Tìm kiếm/thêm game qua API
  - Xem dữ liệu JSON
- **User thường:**
  - Xóa game
  - Tìm kiếm/thêm game qua API
  - Xem dữ liệu JSON

## 4. Lưu trữ dữ liệu
- Dữ liệu game và người dùng lưu trong thư mục `data/` dưới dạng file JSON:
  - `data/games.json`: Dữ liệu game chung cho admin.
  - `data/games_<username>.json`: Dữ liệu game riêng cho từng user.
  - `data/users.json`: Danh sách tài khoản người dùng.

## 5. Một số lưu ý
- Khi thêm game từ API, nên kiểm tra và chỉnh sửa lại thông tin trước khi lưu.
- Nếu gặp lỗi file JSON, kiểm tra quyền ghi file hoặc xóa file lỗi để chương trình tự tạo lại.
- Ảnh bìa game sẽ tự động lấy từ API hoặc nhập thủ công (nếu có).

## 6. Hướng dẫn sử dụng nhanh
- Chạy `python main.py`
- Đăng nhập bằng tài khoản admin hoặc đăng ký tài khoản mới.
- Sử dụng các chức năng trên giao diện theo quyền của bạn.

---

**Mọi thắc mắc, lỗi do sai sót của dev chưa đủ kiến thức, mong bỏ qua!**
