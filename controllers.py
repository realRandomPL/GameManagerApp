from tkinter import Tk, Toplevel, StringVar, CENTER, PhotoImage, Label as TkLabel
from tkinter import messagebox
import os
import requests
from models import GameManager, UserManager
from views import MainView  # Xóa LoginView nếu không dùng
from tkinter.ttk import Frame, Label, Button, Entry, Style

# --- app_controller.py ---


class GameApp:
    def __init__(self, user, root, on_logout=None):
        self.user = user
        self.root = root
        self.on_logout = on_logout
        self.root.title("Ứng dụng quản lý game cá nhân")
        self.manager = GameManager(username=self.user.username)  # games riêng cho từng user, admin dùng chung
        self.api = GiantBombClient()

        self.is_admin = self.user.role == "admin"
        self.view = MainView(self.root, self.manager, self.user, api_client=self.api, is_admin=self.is_admin, on_logout=self.logout)

    def logout(self):
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc chắn muốn đăng xuất?"):
            self.root.destroy()
            if self.on_logout:
                self.on_logout()

    def run(self):
        self.root.mainloop()


# --- auth_controller.py ---

class AuthController:
    def __init__(self, root):
        self.user_manager = UserManager()
        self.root = root
        self._dialog_zoomed = False  # nhớ trạng thái maximize của dialog

    def launch(self):
        parent = self.root
        while True:
            mode = self._show_mode_dialog(parent)
            if mode is None:
                return None
            if mode == 'register':
                reg_result = self._show_register_dialog(parent)
                if reg_result == "back" or reg_result is None:
                    continue
                # Sửa: kiểm tra reg_result là tuple trước khi unpack
                if not isinstance(reg_result, tuple) or len(reg_result) != 2:
                    messagebox.showerror("Lỗi", "Thông tin không hợp lệ.", parent=parent)
                    continue
                username, password = reg_result
                if not username or not password:
                    messagebox.showerror("Lỗi", "Thông tin không hợp lệ.", parent=parent)
                    continue
                if self.user_manager.register_user(username, password):
                    messagebox.showinfo("Thành công", "Đăng ký thành công! Vui lòng đăng nhập.", parent=parent)
                    continue
                else:
                    messagebox.showerror("Thất bại", "Tên đăng nhập đã tồn tại.", parent=parent)
                    continue
            elif mode == 'login':
                login_result = self._show_login_dialog(parent)
                if login_result == "back":
                    continue
                creds = login_result
                if creds:
                    user = self.user_manager.authenticate(creds['username'], creds['password'])
                    if user:
                        return user
                    else:
                        messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu.", parent=parent)
                        continue
            elif mode == 'quit':
                return None

    def _center_dialog(self, dialog, width=480, height=320):
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _apply_zoom_state(self, dialog):
        if self._dialog_zoomed:
            dialog.state('zoomed')

    def _show_mode_dialog(self, parent):
        dialog = Toplevel(parent)
        dialog.title("Chọn chế độ")
        dialog.configure(bg="#23272f")
        self._center_dialog(dialog, 480, 360)
        dialog.minsize(400, 260)
        dialog.resizable(True, True)
        self._apply_zoom_state(dialog)
        dialog.grab_set()
        dialog.focus_force()

        style = Style(dialog)
        style.theme_use('clam')
        style.configure("Card.TFrame", background="#23272f")
        style.configure("Card.TLabel", background="#23272f", foreground="#e0e6f0", font=("Segoe UI", 13, "bold"))
        style.configure("Accent.TButton", background="#2e8fff", foreground="#fff", font=("Segoe UI", 12, "bold"), borderwidth=0)
        style.map("Accent.TButton", background=[('active', '#1e6fdc')])

        frm = Frame(dialog, style="Card.TFrame")
        frm.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.8)

        Label(frm, text="Chọn chế độ đăng nhập", style="Card.TLabel", anchor=CENTER).pack(pady=(0, 15))

        mode_var = StringVar(value="login")
        result = {"mode": None}

        def set_mode_and_close(m):
            self._dialog_zoomed = dialog.state() == 'zoomed'
            result["mode"] = m
            dialog.destroy()

        btn_login = Button(frm, text="Đăng nhập", style="Accent.TButton", command=lambda: set_mode_and_close("login"))
        btn_login.pack(fill='x', pady=5)
        btn_register = Button(frm, text="Đăng ký", style="Accent.TButton", command=lambda: set_mode_and_close("register"))
        btn_register.pack(fill='x', pady=5)
        btn_quit = Button(frm, text="Thoát", style="Accent.TButton", command=lambda: set_mode_and_close("quit"))
        btn_quit.pack(fill='x', pady=5)

        def on_resize(event):
            frm.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.8)
        dialog.bind("<Configure>", on_resize)

        dialog.bind('<Escape>', lambda e: set_mode_and_close("quit"))
        btn_login.focus_set()
        dialog.wait_window()
        return result["mode"]

    def _show_login_dialog(self, parent):
        dialog = Toplevel(parent)
        dialog.title("Đăng nhập")
        dialog.configure(bg="#23262e")
        self._center_dialog(dialog, 480, 360)
        dialog.minsize(400, 260)
        dialog.resizable(True, True)
        self._apply_zoom_state(dialog)
        dialog.grab_set()
        dialog.focus_force()

        style = Style(dialog)
        style.theme_use('clam')
        style.configure("Card.TLabel", background="#23262e", foreground="#f5f6fa", font=("Segoe UI", 12, "bold"))
        style.configure("Accent.TButton", background="#4f8cff", foreground="#fff", font=("Segoe UI", 12, "bold"), borderwidth=0)
        style.map("Accent.TButton", background=[('active', '#3766b1')])

        frm = Frame(dialog, style="Card.TFrame")
        frm.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.8)

        Label(frm, text="Tên đăng nhập:", style="Card.TLabel").grid(row=1, column=0, sticky='e', pady=8, padx=5)
        Label(frm, text="Mật khẩu:", style="Card.TLabel").grid(row=2, column=0, sticky='e', pady=8, padx=5)
        username_var = StringVar()
        password_var = StringVar()
        entry1 = Entry(frm, textvariable=username_var, font=("Segoe UI", 12))
        entry2 = Entry(frm, textvariable=password_var, show="*", font=("Segoe UI", 12))
        entry1.grid(row=1, column=1, pady=8, padx=5, sticky='ew')
        entry2.grid(row=2, column=1, pady=8, padx=5, sticky='ew')

        frm.columnconfigure(0, weight=1)
        frm.columnconfigure(1, weight=2)

        result = {"creds": None}

        def submit(event=None):
            self._dialog_zoomed = dialog.state() == 'zoomed'
            result["creds"] = {'username': username_var.get(), 'password': password_var.get()}
            dialog.destroy()

        def go_back():
            self._dialog_zoomed = dialog.state() == 'zoomed'
            result["creds"] = "back"
            dialog.destroy()

        btn = Button(frm, text="Đăng nhập", style="Accent.TButton", command=submit)
        btn.grid(row=3, column=0, columnspan=2, pady=12, sticky='ew')
        btn_back = Button(frm, text="Quay lại", style="Accent.TButton", command=go_back)
        btn_back.grid(row=4, column=0, columnspan=2, pady=5, sticky='ew')

        def on_resize(event):
            frm.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.8)
        dialog.bind("<Configure>", on_resize)

        entry1.focus_set()
        entry1.bind('<Return>', lambda e: entry2.focus_set())
        entry2.bind('<Return>', lambda e: submit())
        dialog.wait_window()
        return result["creds"]

    def _show_register_dialog(self, parent):
        dialog = Toplevel(parent)
        dialog.title("Đăng ký tài khoản")
        dialog.configure(bg="#23262e")
        self._center_dialog(dialog, 480, 360)
        dialog.minsize(400, 260)
        dialog.resizable(True, True)
        self._apply_zoom_state(dialog)
        dialog.grab_set()
        dialog.focus_force()

        style = Style(dialog)
        style.theme_use('clam')
        style.configure("Card.TLabel", background="#23262e", foreground="#f5f6fa", font=("Segoe UI", 12, "bold"))
        style.configure("Accent.TButton", background="#4f8cff", foreground="#fff", font=("Segoe UI", 12, "bold"), borderwidth=0)
        style.map("Accent.TButton", background=[('active', '#3766b1')])

        frm = Frame(dialog, style="Card.TFrame")
        frm.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.8)

        Label(frm, text="Tên đăng nhập:", style="Card.TLabel").grid(row=1, column=0, sticky='e', pady=8, padx=5)
        Label(frm, text="Mật khẩu:", style="Card.TLabel").grid(row=2, column=0, sticky='e', pady=8, padx=5)
        username_var = StringVar()
        password_var = StringVar()
        entry1 = Entry(frm, textvariable=username_var, font=("Segoe UI", 12))
        entry2 = Entry(frm, textvariable=password_var, show="*", font=("Segoe UI", 12))
        entry1.grid(row=1, column=1, pady=8, padx=5, sticky='ew')
        entry2.grid(row=2, column=1, pady=8, padx=5, sticky='ew')

        frm.columnconfigure(0, weight=1)
        frm.columnconfigure(1, weight=2)

        result = {"creds": None}

        def submit(event=None):
            self._dialog_zoomed = dialog.state() == 'zoomed'
            result["creds"] = (username_var.get(), password_var.get())
            dialog.destroy()

        def go_back():
            self._dialog_zoomed = dialog.state() == 'zoomed'
            result["creds"] = "back"
            dialog.destroy()

        btn = Button(frm, text="Đăng ký", style="Accent.TButton", command=submit)
        btn.grid(row=3, column=0, columnspan=2, pady=12, sticky='ew')
        btn_back = Button(frm, text="Quay lại", style="Accent.TButton", command=go_back)
        btn_back.grid(row=4, column=0, columnspan=2, pady=5, sticky='ew')

        def on_resize(event):
            frm.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.8)
        dialog.bind("<Configure>", on_resize)

        entry1.focus_set()
        entry1.bind('<Return>', lambda e: entry2.focus_set())
        entry2.bind('<Return>', lambda e: submit())
        dialog.wait_window()
        return result["creds"]

# --- giantbomb_client.py ---

class GiantBombClient:
    BASE_URL = 'https://www.giantbomb.com/api'
    DEFAULT_API_KEY = '30382badcce6403d0e4329e8df393a72d6366c47'

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GIANTBOMB_API_KEY') or self.DEFAULT_API_KEY

    def search_games(self, query, limit=5):
        params = {
            'api_key': self.api_key,
            'format': 'json',
            'query': query,
            'resources': 'game',
            'limit': limit
        }
        headers = {'User-Agent': 'GameCollectionApp'}
        resp = requests.get(f"{self.BASE_URL}/search/", params=params, headers=headers)
        try:
            data = resp.json()
        except ValueError:
            raise ValueError("Phản hồi từ API GiantBomb không phải là JSON hợp lệ.")

        status_code = data.get('status_code')
        error_msg = data.get('error', 'Lỗi không xác định')
        if status_code != 1:
            raise RuntimeError(f"Lỗi API GiantBomb (mã {status_code}): {error_msg}")

        return data.get('results', [])

    def get_game_details(self, guid):
        params = {
            'api_key': self.api_key,
            'format': 'json',
            'field_list': 'name,deck,developers,genres,platforms,aliases,image,original_release_date,site_detail_url'
        }
        headers = {'User-Agent': 'GameCollectionApp'}
        url = f"{self.BASE_URL}/game/{guid}/"
        resp = requests.get(url, params=params, headers=headers)
        try:
            data = resp.json()
        except ValueError:
            raise ValueError("Phản hồi chi tiết từ API không hợp lệ.")

        if data.get('status_code') != 1:
            raise RuntimeError(f"API error: {data.get('error')}")

        return data.get('results')