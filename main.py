import tkinter as tk
from controllers import AuthController, GameApp
import os
import sys

def center_window(window, width=900, height=600):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

def launch_app(root):
    print("DEBUG: launch_app start")
    from models import UserManager
    user_manager = UserManager()
    auth = AuthController(root, user_manager)
    user = auth.launch()
    print(f"DEBUG: auth.launch() returned: {user}")
    if user is None:
        print("DEBUG: No user, destroying root")
        root.destroy()
        return
    root.title("Ứng dụng quản lý game cá nhân")
    root.configure(bg="#23272f")
    root.minsize(900, 600)
    root.state('zoomed') 
    root.deiconify()  # Đảm bảo hiện cửa sổ chính sau đăng nhập
    center_window(root, 900, 600)
    app = GameApp(user, root, on_logout=lambda: restart_app(root))
    app.run()

def restart_app(root):
    # Đóng tất cả cửa sổ con nếu còn sót lại
    for w in root.winfo_children():
        try:
            w.destroy()
        except Exception:
            pass
    root.withdraw()
    launch_app(root)

def resource_path(relative_path):
    """Lấy đường dẫn tuyệt đối đến resource, dùng được cả khi chạy exe và chạy code."""
    if hasattr(sys, '_MEIPASS'):
        # Khi chạy bằng PyInstaller
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

def ensure_data_folder_and_images():
    # Đảm bảo thư mục data nằm cùng thư mục với file exe hoặc main.py
    base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    # Copy toàn bộ file từ resource data sang data nếu chưa có
    def copy_default(filename):
        # Ưu tiên lấy file gốc cạnh exe (PyInstaller sẽ giải nén vào _MEIPASS)
        src = resource_path(f"data/{filename}")
        dst = os.path.join(data_dir, filename)
        if not os.path.exists(dst):
            try:
                import shutil
                # Nếu chạy exe, src có thể nằm trong _MEIPASS (bên trong exe)
                if os.path.exists(src):
                    shutil.copyfile(src, dst)
                else:
                    # Nếu không tìm thấy file, thử lấy từ thư mục gốc code (dành cho dev)
                    alt_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", filename)
                    if os.path.exists(alt_src):
                        shutil.copyfile(alt_src, dst)
            except Exception as e:
                print(f"Lỗi copy file {filename}: {e}")
    # Danh sách file mặc định cần copy
    default_files = [
        "dialog_bg.jpg",
        "icon.png",
        "avatar.png",
        "games.json",
        "users.json"
    ]
    for fname in default_files:
        copy_default(fname)
    # Nếu muốn copy thêm các file khác trong data (ví dụ ảnh, json...), chỉ cần thêm vào default_files

if __name__ == "__main__":
    ensure_data_folder_and_images()
    root = tk.Tk()
    root.withdraw()
    # Đặt icon cho cửa sổ (tương thích Win 7/10/11)
    try:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        icon_path = os.path.join(data_dir, "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
            if sys.platform == "win32":
                import ctypes
                app_id = u"game.collection.app"
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass
    launch_app(root)
    root.mainloop()