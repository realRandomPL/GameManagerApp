import sys
import tkinter as tk
from controllers import AuthController, GameApp

def center_window(window, width=900, height=600):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

def main():
    while True:
        root = tk.Tk()
        root.withdraw()  # Ẩn hoàn toàn root, không bao giờ hiện cửa sổ trắng
        auth = AuthController(root)
        user = auth.launch()
        root.destroy()  # Đóng root ngay sau khi dialog đóng
        if user is None:
            break
        # Đăng nhập thành công, tạo root mới cho giao diện chính
        root2 = tk.Tk()
        root2.title("Bộ sưu tập game")
        center_window(root2, 900, 600)  # căn giữa cửa sổ chính
        app = GameApp(user, root2, on_logout=main)
        app.run()
        break

if __name__ == '__main__':
    main()