from tkinter import Tk, Toplevel, StringVar, CENTER, PhotoImage, Label as TkLabel
from tkinter import messagebox
import os  # Đảm bảo chỉ có 1 dòng import os ở đầu file, KHÔNG import os trong bất kỳ hàm nào bên dưới
import requests
import threading
from models import GameManager, UserManager
from views import MainView
from tkinter.ttk import Frame, Label, Button, Entry, Style
import io
from PIL import Image, ImageDraw, ImageTk
import tkinter as tk
import datetime
import json

# --- app_controller.py ---


class GameApp:
    def __init__(self, user, root, on_logout=None):
        self.user = user
        self.root = root
        self.on_logout = on_logout
        self.root.title("Ứng dụng quản lý game cá nhân")
        self.manager = GameManager(username=self.user.username)
        self.api = GiantBombClient()
        self.is_admin = self.user.role == "admin"
        self.view = MainView(self.root, self.manager, self.user, api_client=self.api, is_admin=self.is_admin, on_logout=self.logout, admin_manage_users_callback=self.admin_manage_users if self.is_admin else None)

    def logout(self):
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc chắn muốn đăng xuất?"):
            self.root.withdraw()
            if self.on_logout:
                self.on_logout()

    def run(self):
        # Chỉ deiconify, không gọi mainloop ở đây
        self.root.deiconify()

    def admin_manage_users(self):
        dialog = Toplevel(self.root)
        dialog.title("Quản lý tài khoản")
        dialog.configure(bg="#23272f")
        self._center_dialog(dialog, 600, 420)
        dialog.grab_set()
        dialog.focus_force()
        style = Style(dialog)
        style.theme_use('clam')
        style.configure("Card.TFrame", background="#23272f")
        style.configure("Card.TLabel", background="#23272f", foreground="#e0e6f0", font=("Segoe UI", 12, "bold"))
        style.configure("Accent.TButton", background="#2e8fff", foreground="#fff", font=("Segoe UI", 11, "bold"), borderwidth=0)
        style.map("Accent.TButton", background=[('active', '#1e6fdc')])

        frm = Frame(dialog, style="Card.TFrame")
        frm.pack(fill='both', expand=True, padx=20, pady=20)

        Label(frm, text="Danh sách tài khoản", style="Card.TLabel").pack(anchor='w', pady=(0, 8))
        user_manager = UserManager()
        current_username = self.user.username
        users = [u for u in user_manager.users if u.username != "123"]
        from tkinter import Listbox, END, SINGLE
        lb = Listbox(frm, selectmode=SINGLE, font=("Segoe UI", 11), bg="#23262e", fg="#e0e6f0", width=32)
        for u in users:
            lb.insert(END, f"{u.username} - {'Admin' if u.role == 'admin' else 'User'}")
        lb.pack(fill='x', pady=(0, 8))

        def set_role_admin():
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning("Chưa chọn", "Chọn tài khoản để nâng quyền")
                return
            idx = sel[0]
            user = users[idx]
            if user.username == "123":
                messagebox.showwarning("Không thể thay đổi", "Không thể thay đổi quyền admin gốc!")
                return
            if user.username == current_username:
                messagebox.showwarning("Không thể thao tác", "Không thể thao tác trên chính tài khoản của bạn!")
                return
            user.role = "admin"
            user_manager._save()
            lb.delete(idx)
            lb.insert(idx, f"{user.username} - Admin")
            messagebox.showinfo("Thành công", f"Đã nâng {user.username} thành admin")

        def set_role_user():
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning("Chưa chọn", "Chọn tài khoản để hạ quyền")
                return
            idx = sel[0]
            user = users[idx]
            if user.username == "123":
                messagebox.showwarning("Không thể thay đổi", "Không thể thay đổi quyền admin gốc!")
                return
            if user.username == current_username:
                messagebox.showwarning("Không thể thao tác", "Không thể thao tác trên chính tài khoản của bạn!")
                return
            user.role = "user"
            user_manager._save()
            lb.delete(idx)
            lb.insert(idx, f"{user.username} - User")
            messagebox.showinfo("Thành công", f"Đã hạ quyền {user.username} thành user")

        def delete_user():
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning("Chưa chọn", "Chọn tài khoản để xóa")
                return
            idx = sel[0]
            user = users[idx]
            if user.username == "123":
                messagebox.showwarning("Không thể xóa", "Không thể xóa tài khoản admin gốc!")
                return
            if user.username == current_username:
                messagebox.showwarning("Không thể thao tác", "Không thể thao tác trên chính tài khoản của bạn!")
                return
            if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa tài khoản {user.username}?\nTất cả dữ liệu liên quan sẽ bị xóa vĩnh viễn!"):
                # Xóa user khỏi danh sách và file
                del users[idx]
                user_manager.users = [u for u in user_manager.users if u.username != user.username]
                user_manager._save()
                lb.delete(idx)
                # XÓA TOÀN BỘ DỮ LIỆU GAME, JSON LIÊN QUAN ĐẾN USER
                try:
                    game_json = os.path.join(os.path.dirname(__file__), "data", f"games_{user.username}.json")
                    if os.path.exists(game_json):
                        os.remove(game_json)
                except Exception:
                    pass
                # Nếu có thể có các file khác liên quan user, xóa thêm ở đây
                messagebox.showinfo("Thành công", f"Đã xóa tài khoản {user.username} và toàn bộ dữ liệu liên quan.")

        btn_frame = Frame(frm, style="Card.TFrame")
        btn_frame.pack(pady=8)
        Button(btn_frame, text="Nâng quyền Admin", style="Accent.TButton", command=set_role_admin).pack(side="left", padx=5)
        Button(btn_frame, text="Hạ quyền User", style="Accent.TButton", command=set_role_user).pack(side="left", padx=5)
        Button(btn_frame, text="Xóa tài khoản", style="Accent.TButton", command=delete_user).pack(side="left", padx=5)
        Button(btn_frame, text="Đóng", style="Accent.TButton", command=dialog.destroy).pack(side="left", padx=5)

        dialog.wait_window()

    def _center_dialog(self, dialog, width=480, height=320):
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _show_mode_dialog(self, parent):
        dialog_width = 540
        dialog_height = 420
        dialog = tk.Toplevel(parent)
        dialog.withdraw()
        self._set_dialog_appearance(dialog, width=dialog_width, height=dialog_height, title="Chào mừng!")
        dialog.configure(bg="#23272f")
        # Cho phép thu nhỏ (minimize) và giữ nút minimize trên titlebar
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.focus_force()
        dialog.lift()
        dialog.grab_set()
        # Đảm bảo cửa sổ có nút minimize trên mọi Windows
        try:
            dialog.overrideredirect(False)
        except Exception:
            pass

        frm = tk.Frame(dialog, bg="#23272f")
        frm.place(relx=0.5, rely=0.5, anchor='center', width=dialog_width-40, height=dialog_height-40)

        # Logo + tên app + chào mừng (CĂN GIỮA)
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "data", "icon.png")
            logo_img = Image.open(logo_path).resize((48, 48))
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(frm, image=logo_photo, bg="#23272f")
            logo_label.image = logo_photo
            logo_label.pack(pady=(24, 8))
        except Exception:
            tk.Label(frm, text="🎮", font=("Segoe UI", 32), bg="#23272f", fg="#fff").pack(pady=(24, 8))
        tk.Label(frm, text="GAME COLLECTION", font=("Segoe UI", 16, "bold"), bg="#23272f", fg="#fff", anchor="center", justify="center").pack(pady=(0, 4), fill='x')
        tk.Label(
            frm,
            text="Chào mừng bạn đến với ứng dụng quản lý game cá nhân!",
            font=("Segoe UI", 11),
            bg="#23272f",
            fg="#b0b6c2",
            anchor="center",
            justify="center"
        ).pack(pady=(2, 18), fill='x')

        # Nút chọn chế độ (CĂN GIỮA)
        btn_style = {"font": ("Segoe UI", 12, "bold"), "bg": "#2196f3", "fg": "#fff", "activebackground": "#1976d2", "activeforeground": "#fff", "bd": 0, "relief": "flat", "cursor": "hand2", "height": 1}
        def make_btn(text, command):
            btn = tk.Button(frm, text=text, command=command, **btn_style)
            btn.pack(fill='x', padx=64, pady=7, ipady=4)
            btn.bind("<Enter>", lambda e: btn.config(bg="#1976d2"))
            btn.bind("<Leave>", lambda e: btn.config(bg="#2196f3"))
            return btn

        result = {"mode": None}
        def set_mode_and_close(m):
            result["mode"] = m
            dialog.destroy()

        make_btn("Đăng nhập", lambda: set_mode_and_close("login"))
        make_btn("Đăng ký", lambda: set_mode_and_close("register"))
        tk.Button(frm, text="Thoát", command=lambda: set_mode_and_close("quit"),
                  font=("Segoe UI", 11, "bold"), bg="#bdbdbd", fg="#222", activebackground="#888", activeforeground="#fff",
                  bd=0, relief="flat", cursor="hand2", height=1).pack(fill='x', padx=64, pady=(7, 16), ipady=4)

        def close():
            result["mode"] = None
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", close)
        dialog.deiconify()
        dialog.lift()
        dialog.grab_set()
        dialog.focus_force()
        dialog.wait_window()
        return result["mode"]

    def _show_login_dialog(self, parent):
        dialog_width = 540
        dialog_height = 520
        dialog = tk.Toplevel(parent)
        dialog.withdraw()
        self._set_dialog_appearance(dialog, width=dialog_width, height=dialog_height, title="Đăng nhập")
        dialog.configure(bg="#23272f")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.focus_force()
        dialog.lift()
        dialog.grab_set()
        try:
            dialog.overrideredirect(False)
        except Exception:
            pass
        frm = tk.Frame(dialog, bg="#23272f")
        frm.place(relx=0.5, rely=0.5, anchor='center', width=dialog_width-40, height=dialog_height-40)

        # Logo + tiêu đề (CĂN GIỮA)
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "data", "icon.png")
            logo_img = Image.open(logo_path).resize((48, 48))
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(frm, image=logo_photo, bg="#23272f")
            logo_label.image = logo_photo
            logo_label.pack(pady=(24, 8))
        except Exception:
            tk.Label(frm, text="🎮", font=("Segoe UI", 32), bg="#23272f", fg="#fff").pack(pady=(24, 8))
        tk.Label(frm, text="ĐĂNG NHẬP", font=("Segoe UI", 15, "bold"), bg="#23272f", fg="#fff").pack(pady=(0, 2), fill='x')
        tk.Label(frm, text="Đăng nhập bằng tài khoản của bạn", font=("Segoe UI", 10), bg="#23272f", fg="#b0b6c2").pack(pady=(2, 18), fill='x')

        # Form (CĂN GIỮA)
        tk.Label(frm, text="TÊN ĐĂNG NHẬP", font=("Segoe UI", 10, "bold"), bg="#23272f", fg="#b0b6c2", anchor='center').pack(anchor='center', padx=48, pady=(0, 2))
        username_var = tk.StringVar()
        username_entry = tk.Entry(frm, textvariable=username_var, font=("Segoe UI", 12), bg="#23262e", fg="#fff", insertbackground="#4f8cff", relief="flat", highlightthickness=1, highlightbackground="#31343c", highlightcolor="#4f8cff", justify='center')
        username_entry.pack(fill='x', padx=64, pady=(0, 12), ipady=6)

        tk.Label(frm, text="MẬT KHẨU", font=("Segoe UI", 10, "bold"), bg="#23272f", fg="#b0b6c2", anchor='center').pack(anchor='center', padx=48, pady=(0, 2))
        password_var = tk.StringVar()
        password_entry = tk.Entry(frm, textvariable=password_var, font=("Segoe UI", 12), bg="#23262e", fg="#fff", show="*", insertbackground="#4f8cff", relief="flat", highlightthickness=1, highlightbackground="#31343c", highlightcolor="#4f8cff", justify='center')
        password_entry.pack(fill='x', padx=64, pady=(0, 6), ipady=6)

        # Hiện/ẩn mật khẩu & Ghi nhớ tôi (căn đều nhau)
        checkbox_frame = tk.Frame(frm, bg="#23272f")
        checkbox_frame.pack(fill='x', padx=64, pady=(0, 8))
        show_pw_var = tk.BooleanVar(value=False)
        def toggle_pw():
            password_entry.config(show="" if show_pw_var.get() else "*")
        show_pw_cb = tk.Checkbutton(checkbox_frame, text="Hiện mật khẩu", variable=show_pw_var, command=toggle_pw, bg="#23272f", fg="#b0b6c2", activebackground="#23272f", activeforeground="#4f8cff", selectcolor="#23262e", font=("Segoe UI", 10))
        show_pw_cb.pack(side=tk.LEFT, expand=True, anchor='center')
        remember_var = tk.BooleanVar(value=False)
        remember_cb = tk.Checkbutton(checkbox_frame, text="Ghi nhớ tôi", variable=remember_var, bg="#23272f", fg="#b0b6c2", activebackground="#23272f", activeforeground="#4f8cff", selectcolor="#23262e", font=("Segoe UI", 10))
        remember_cb.pack(side=tk.LEFT, expand=True, anchor='center')

        REMEMBER_FILE = os.path.join(os.path.dirname(__file__), "data", "remembered.json")

        def load_remembered():
            if os.path.exists(REMEMBER_FILE):
                try:
                    with open(REMEMBER_FILE, "r", encoding="utf-8") as f:
                        self._remembered = json.load(f)
                except Exception:
                    self._remembered = {}
            else:
                self._remembered = {}

        def save_remembered():
            try:
                with open(REMEMBER_FILE, "w", encoding="utf-8") as f:
                    json.dump(self._remembered, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        load_remembered()

        def on_username_change(*args):
            uname = username_var.get()
            if uname in self._remembered:
                password_var.set(self._remembered[uname])
                remember_var.set(True)
            else:
                password_var.set("")
                remember_var.set(False)
        username_var.trace_add("write", lambda *a: on_username_change())

        popup_ref = {"popup": None}
        def show_remembered_popup(event):
            uname = username_var.get()
            if len(uname) < 2:
                if popup_ref["popup"]:
                    popup_ref["popup"].destroy()
                    popup_ref["popup"] = None
                return
            matches = [u for u in self._remembered if uname.lower() in u.lower()]
            if not matches:
                if popup_ref["popup"]:
                    popup_ref["popup"].destroy()
                    popup_ref["popup"] = None
                return
            if popup_ref["popup"]:
                popup_ref["popup"].destroy()
            popup = tk.Toplevel(dialog)
            popup_ref["popup"] = popup
            popup.wm_overrideredirect(True)
            popup.configure(bg="#31343c")
            x = dialog.winfo_rootx() + username_entry.winfo_x()
            y = dialog.winfo_rooty() + username_entry.winfo_y() + username_entry.winfo_height()
            popup.geometry(f"220x{min(120, 28*len(matches))}+{x}+{y}")

            def fill_and_close(u):
                username_var.set(u)
                password_var.set(self._remembered[u])
                remember_var.set(True)
                popup.destroy()
                popup_ref["popup"] = None
                password_entry.focus_set()

            for i, u in enumerate(matches):
                btn = tk.Button(popup, text=u, anchor="w", font=("Segoe UI", 11), bg="#31343c", fg="#fff", bd=0, relief="flat", activebackground="#4f8cff", activeforeground="#fff", cursor="hand2", command=lambda u=u: fill_and_close(u))
                btn.pack(fill='x')
            def close_popup(event=None):
                if popup.winfo_exists():
                    popup.destroy()
                    popup_ref["popup"] = None
            popup.bind("<FocusOut>", close_popup)
        username_entry.bind("<KeyRelease>", show_remembered_popup)

        def on_remember_change(*args):
            uname = username_var.get()
            if not remember_var.get() and uname in self._remembered:
                del self._remembered[uname]
                save_remembered()
        remember_var.trace_add("write", lambda *a: on_remember_change())

        result = {"creds": None, "retry": False}
        def submit(event=None):
            self._dialog_zoomed = dialog.state() == 'zoomed'
            if remember_var.get():
                self._remembered[username_var.get()] = password_var.get()
                save_remembered()
            else:
                uname = username_var.get()
                if uname in self._remembered:
                    del self._remembered[uname]
                    save_remembered()
            result["creds"] = {'username': username_var.get(), 'password': password_var.get()}
            dialog.destroy()
        def go_back():
            self._dialog_zoomed = dialog.state() == 'zoomed'
            result["creds"] = "back"
            dialog.destroy()

        login_btn = tk.Button(
            frm, text="Đăng nhập",
            font=("Segoe UI", 12, "bold"),
            bg="#2196f3", fg="#fff",
            activebackground="#1976d2", activeforeground="#fff",
            bd=0, relief="flat", cursor="hand2", height=1,
            command=submit
        )
        login_btn.pack(fill='x', padx=64, pady=(12, 8), ipady=4)

        # Nút quay lại (thêm dưới nút đăng nhập)
        back_btn = tk.Button(
            frm, text="Quay lại",
            font=("Segoe UI", 12, "bold"),
            bg="#23272f", fg="#b0b6c2",
            activebackground="#31343c", activeforeground="#fff",
            bd=0, relief="flat", cursor="hand2", height=1,
            command=go_back,
            highlightthickness=1, highlightbackground="#bdbdbd"
        )
        back_btn.pack(fill='x', padx=64, pady=(0, 16), ipady=4)
        back_btn.update_idletasks()
        back_btn.configure(
            highlightthickness=2,
            highlightbackground="#bdbdbd",
            highlightcolor="#bdbdbd"
        )

        def close():
            result["creds"] = "back"
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", close)
        username_entry.focus_set()
        username_entry.bind('<Return>', lambda e: password_entry.focus_set())
        password_entry.bind('<Return>', lambda e: submit())
        dialog.deiconify()
        dialog.lift()
        dialog.grab_set()
        dialog.focus_force()
        dialog.wait_window()
        return result.get("creds", None)

    def _show_register_dialog(self, parent):
        dialog_width = 540
        dialog_height = 570
        dialog = tk.Toplevel(parent)
        dialog.withdraw()
        self._set_dialog_appearance(dialog, width=dialog_width, height=dialog_height, title="Đăng ký tài khoản")
        dialog.configure(bg="#23272f")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.focus_force()
        dialog.lift()
        dialog.grab_set()
        try:
            dialog.overrideredirect(False)
        except Exception:
            pass
        frm = tk.Frame(dialog, bg="#23272f")
        frm.place(relx=0.5, rely=0.5, anchor='center', width=dialog_width-40, height=dialog_height-40)

        # Logo + tiêu đề (CĂN GIỮA)
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "data", "icon.png")
            logo_img = Image.open(logo_path).resize((48, 48))
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(frm, image=logo_photo, bg="#23272f")
            logo_label.image = logo_photo
            logo_label.pack(pady=(24, 8))
        except Exception:
            tk.Label(frm, text="🎮", font=("Segoe UI", 32), bg="#23272f", fg="#fff").pack(pady=(24, 8))
        tk.Label(frm, text="ĐĂNG KÝ TÀI KHOẢN", font=("Segoe UI", 15, "bold"), bg="#23272f", fg="#fff").pack(pady=(0, 2), fill='x')
        tk.Label(frm, text="Tạo tài khoản mới để bắt đầu quản lý game của bạn", font=("Segoe UI", 10), bg="#23272f", fg="#b0b6c2").pack(pady=(2, 18), fill='x')

        # Form đăng ký (CĂN GIỮA)
        tk.Label(frm, text="TÊN ĐĂNG NHẬP", font=("Segoe UI", 10, "bold"), bg="#23272f", fg="#b0b6c2", anchor='center').pack(anchor='center', padx=48, pady=(0, 2))
        reg_username_var = StringVar()
        reg_username_entry = tk.Entry(frm, textvariable=reg_username_var, font=("Segoe UI", 12), bg="#23262e", fg="#fff", insertbackground="#4f8cff", relief="flat", highlightthickness=1, highlightbackground="#31343c", highlightcolor="#4f8cff", justify='center')
        reg_username_entry.pack(fill='x', padx=64, pady=(0, 12), ipady=6)

        tk.Label(frm, text="MẬT KHẨU", font=("Segoe UI", 10, "bold"), bg="#23272f", fg="#b0b6c2", anchor='center').pack(anchor='center', padx=48, pady=(0, 2))
        reg_password_var = StringVar()
        reg_password_entry = tk.Entry(frm, textvariable=reg_password_var, font=("Segoe UI", 12), bg="#23262e", fg="#fff", show="*", insertbackground="#4f8cff", relief="flat", highlightthickness=1, highlightbackground="#31343c", highlightcolor="#4f8cff", justify='center')
        reg_password_entry.pack(fill='x', padx=64, pady=(0, 6), ipady=6)

        tk.Label(frm, text="XÁC NHẬN MẬT KHẨU", font=("Segoe UI", 10, "bold"), bg="#23272f", fg="#b0b6c2", anchor='center').pack(anchor='center', padx=48, pady=(0, 2))
        reg_confirm_password_var = StringVar()
        reg_confirm_password_entry = tk.Entry(frm, textvariable=reg_confirm_password_var, font=("Segoe UI", 12), bg="#23262e", fg="#fff", show="*", insertbackground="#4f8cff", relief="flat", highlightthickness=1, highlightbackground="#31343c", highlightcolor="#4f8cff", justify='center')
        reg_confirm_password_entry.pack(fill='x', padx=64, pady=(0, 12), ipady=6)

        # Hiện/ẩn mật khẩu
        show_reg_pw_var = tk.BooleanVar(value=False)
        def toggle_reg_pw():
            reg_password_entry.config(show="" if show_reg_pw_var.get() else "*")
            reg_confirm_password_entry.config(show="" if show_reg_pw_var.get() else "*")
        show_reg_pw_cb = tk.Checkbutton(frm, text="Hiện mật khẩu", variable=show_reg_pw_var, command=toggle_reg_pw, bg="#23272f", fg="#b0b6c2", activebackground="#23272f", activeforeground="#4f8cff", selectcolor="#23262e", font=("Segoe UI", 10))
        show_reg_pw_cb.pack(anchor='center', padx=64, pady=(0, 0))

        # Nút đăng ký
        result = {"creds": None}
        def submit_reg(event=None):
            username = reg_username_var.get().strip()
            password = reg_password_var.get()
            confirm_password = reg_confirm_password_var.get()
            if not username or not password or not confirm_password:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng điền đầy đủ thông tin đăng ký.", parent=dialog)
                return
            if password != confirm_password:
                messagebox.showwarning("Mật khẩu không khớp", "Vui lòng xác nhận đúng mật khẩu.", parent=dialog)
                return
            if len(username) < 3 or not username.isalnum():
                messagebox.showwarning("Tên đăng nhập không hợp lệ", "Tên đăng nhập phải có ít nhất 3 ký tự và không chứa ký tự đặc biệt.", parent=dialog)
                return
            if not self.user_manager.register_user(username, password, role="user"):
                messagebox.showwarning("Tên đăng nhập đã tồn tại", "Vui lòng chọn tên đăng nhập khác.", parent=dialog)
                return
            messagebox.showinfo("Đăng ký thành công", "Bạn đã đăng ký tài khoản thành công! Bạn có thể đăng nhập ngay bây giờ.", parent=dialog)
            result["creds"] = {'username': username, 'password': password}
            dialog.destroy()

        reg_btn = tk.Button(
            frm, text="Đăng ký",
            font=("Segoe UI", 12, "bold"),
            bg="#2e8fff", fg="#fff",
            activebackground="#1e6fdc", activeforeground="#fff",
            bd=0, relief="flat", cursor="hand2", height=1,
            command=submit_reg
        )
        reg_btn.pack(fill='x', padx=64, pady=(12, 8), ipady=4)

        # Đảm bảo nút quay lại luôn hiển thị: đặt riêng một frame ở dưới cùng
        bottom_frame = tk.Frame(frm, bg="#23272f")
        bottom_frame.pack(side=tk.BOTTOM, fill='x', padx=0, pady=(0, 8))
        back_btn = tk.Button(
            bottom_frame, text="Quay lại",
            font=("Segoe UI", 12, "bold"),
            bg="#23272f", fg="#b0b6c2",
            activebackground="#31343c", activeforeground="#fff",
            bd=0, relief="flat", cursor="hand2", height=1,
            command=lambda: dialog.destroy(),
            highlightthickness=1, highlightbackground="#bdbdbd"
        )
        back_btn.pack(fill='x', padx=64, ipady=4)
        back_btn.update_idletasks()
        back_btn.configure(
            highlightthickness=2,
            highlightbackground="#bdbdbd",
            highlightcolor="#bdbdbd"
        )

        def close():
            result["creds"] = "back"
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", close)
        reg_username_entry.focus_set()
        reg_username_entry.bind('<Return>', lambda e: reg_password_entry.focus_set())
        reg_password_entry.bind('<Return>', lambda e: reg_confirm_password_entry.focus_set())
        reg_confirm_password_entry.bind('<Return>', lambda e: submit_reg())
        dialog.deiconify()
        dialog.lift()  # Đảm bảo cửa sổ hiện lên trên cùng
        dialog.grab_set()
        dialog.focus_force()
        dialog.wait_window()
        return result["creds"]

    def _set_dialog_appearance(self, dialog, width=480, height=320, title=""):
        dialog.title(title)
        dialog.configure(bg="#23272f")
        # Thêm hiệu ứng fade-in mượt mà cho dialog
        try:
            dialog.attributes('-alpha', 0.0)
        except Exception:
            pass
        self._center_dialog(dialog, width, height)
        dialog.update_idletasks()
        # Fade-in hiệu ứng
        try:
            for i in range(0, 21):
                alpha = i / 20.0
                dialog.attributes('-alpha', alpha)
                dialog.update()
                dialog.after(8)
        except Exception:
            pass
        # KHÔNG dùng overrideredirect, KHÔNG custom border để cửa sổ nét, có titlebar chuẩn

    def _fade_in(self, dialog, duration=180):
        # Không dùng hiệu ứng fade-in để tránh nhấp nháy hoặc load chậm
        pass

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
                # ...existing code...
            elif mode == 'login':
                while True:
                    login_result = self._show_login_dialog(parent)
                    if login_result == "back":
                        break
                    creds = login_result
                    if creds:
                        user = self.user_manager.authenticate(creds['username'], creds['password'])
                        if user:
                            return user
                        else:
                            messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu.", parent=parent)
                            continue
                    else:
                        break
            elif mode == 'quit':
                return None

# --- auth_controller.py ---

class AuthController:
    def __init__(self, root, user_manager):
        self.root = root
        self.user_manager = user_manager
        self._remembered = {}
        self._dialog_zoomed = False

    def _set_dialog_appearance(self, dialog, width=480, height=320, title=""):
        dialog.title(title)
        dialog.configure(bg="#23272f")
        # Thêm hiệu ứng fade-in mượt mà cho dialog
        try:
            dialog.attributes('-alpha', 0.0)
        except Exception:
            pass
        self._center_dialog(dialog, width, height)
        dialog.update_idletasks()
        # Fade-in hiệu ứng
        try:
            for i in range(0, 21):
                alpha = i / 20.0
                dialog.attributes('-alpha', alpha)
                dialog.update()
                dialog.after(8)
        except Exception:
            pass
        # KHÔNG dùng overrideredirect, KHÔNG custom border để cửa sổ nét, có titlebar chuẩn

    def _show_mode_dialog(self, parent):
        dialog_width = 540
        dialog_height = 420
        dialog = tk.Toplevel(parent)
        dialog.withdraw()
        self._set_dialog_appearance(dialog, width=dialog_width, height=dialog_height, title="Chào mừng!")
        dialog.configure(bg="#23272f")
        # Cho phép thu nhỏ (minimize) và giữ nút minimize trên titlebar
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.focus_force()
        dialog.lift()
        dialog.grab_set()
        # Đảm bảo cửa sổ có nút minimize trên mọi Windows
        try:
            dialog.overrideredirect(False)
        except Exception:
            pass

        frm = tk.Frame(dialog, bg="#23272f")
        frm.place(relx=0.5, rely=0.5, anchor='center', width=dialog_width-40, height=dialog_height-40)

        # Logo + tên app + chào mừng (CĂN GIỮA)
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "data", "icon.png")
            logo_img = Image.open(logo_path).resize((48, 48))
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(frm, image=logo_photo, bg="#23272f")
            logo_label.image = logo_photo
            logo_label.pack(pady=(24, 8))
        except Exception:
            tk.Label(frm, text="🎮", font=("Segoe UI", 32), bg="#23272f", fg="#fff").pack(pady=(24, 8))
        tk.Label(frm, text="GAME COLLECTION", font=("Segoe UI", 16, "bold"), bg="#23272f", fg="#fff", anchor="center", justify="center").pack(pady=(0, 4), fill='x')
        tk.Label(
            frm,
            text="Chào mừng bạn đến với ứng dụng quản lý game cá nhân!",
            font=("Segoe UI", 11),
            bg="#23272f",
            fg="#b0b6c2",
            anchor="center",
            justify="center"
        ).pack(pady=(2, 18), fill='x')

        # Nút chọn chế độ (CĂN GIỮA)
        btn_style = {"font": ("Segoe UI", 12, "bold"), "bg": "#2196f3", "fg": "#fff", "activebackground": "#1976d2", "activeforeground": "#fff", "bd": 0, "relief": "flat", "cursor": "hand2", "height": 1}
        def make_btn(text, command):
            btn = tk.Button(frm, text=text, command=command, **btn_style)
            btn.pack(fill='x', padx=64, pady=7, ipady=4)
            btn.bind("<Enter>", lambda e: btn.config(bg="#1976d2"))
            btn.bind("<Leave>", lambda e: btn.config(bg="#2196f3"))
            return btn

        result = {"mode": None}
        def set_mode_and_close(m):
            result["mode"] = m
            dialog.destroy()

        make_btn("Đăng nhập", lambda: set_mode_and_close("login"))
        make_btn("Đăng ký", lambda: set_mode_and_close("register"))
        tk.Button(frm, text="Thoát", command=lambda: set_mode_and_close("quit"),
                  font=("Segoe UI", 11, "bold"), bg="#bdbdbd", fg="#222", activebackground="#888", activeforeground="#fff",
                  bd=0, relief="flat", cursor="hand2", height=1).pack(fill='x', padx=64, pady=(7, 16), ipady=4)

        def close():
            result["mode"] = None
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", close)
        dialog.deiconify()
        dialog.lift()
        dialog.grab_set()
        dialog.focus_force()
        dialog.wait_window()
        return result["mode"]

    def _show_login_dialog(self, parent):
        dialog_width = 540
        dialog_height = 520
        dialog = tk.Toplevel(parent)
        dialog.withdraw()
        self._set_dialog_appearance(dialog, width=dialog_width, height=dialog_height, title="Đăng nhập")
        dialog.configure(bg="#23272f")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.focus_force()
        dialog.lift()
        dialog.grab_set()
        try:
            dialog.overrideredirect(False)
        except Exception:
            pass
        frm = tk.Frame(dialog, bg="#23272f")
        frm.place(relx=0.5, rely=0.5, anchor='center', width=dialog_width-40, height=dialog_height-40)

        # Logo + tiêu đề (CĂN GIỮA)
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "data", "icon.png")
            logo_img = Image.open(logo_path).resize((48, 48))
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(frm, image=logo_photo, bg="#23272f")
            logo_label.image = logo_photo
            logo_label.pack(pady=(24, 8))
        except Exception:
            tk.Label(frm, text="🎮", font=("Segoe UI", 32), bg="#23272f", fg="#fff").pack(pady=(24, 8))
        tk.Label(frm, text="ĐĂNG NHẬP", font=("Segoe UI", 15, "bold"), bg="#23272f", fg="#fff").pack(pady=(0, 2), fill='x')
        tk.Label(frm, text="Đăng nhập bằng tài khoản của bạn", font=("Segoe UI", 10), bg="#23272f", fg="#b0b6c2").pack(pady=(2, 18), fill='x')

        # Form (CĂN GIỮA)
        tk.Label(frm, text="TÊN ĐĂNG NHẬP", font=("Segoe UI", 10, "bold"), bg="#23272f", fg="#b0b6c2", anchor='center').pack(anchor='center', padx=48, pady=(0, 2))
        username_var = tk.StringVar()
        username_entry = tk.Entry(frm, textvariable=username_var, font=("Segoe UI", 12), bg="#23262e", fg="#fff", insertbackground="#4f8cff", relief="flat", highlightthickness=1, highlightbackground="#31343c", highlightcolor="#4f8cff", justify='center')
        username_entry.pack(fill='x', padx=64, pady=(0, 12), ipady=6)

        tk.Label(frm, text="MẬT KHẨU", font=("Segoe UI", 10, "bold"), bg="#23272f", fg="#b0b6c2", anchor='center').pack(anchor='center', padx=48, pady=(0, 2))
        password_var = tk.StringVar()
        password_entry = tk.Entry(frm, textvariable=password_var, font=("Segoe UI", 12), bg="#23262e", fg="#fff", show="*", insertbackground="#4f8cff", relief="flat", highlightthickness=1, highlightbackground="#31343c", highlightcolor="#4f8cff", justify='center')
        password_entry.pack(fill='x', padx=64, pady=(0, 6), ipady=6)

        # Hiện/ẩn mật khẩu & Ghi nhớ tôi (căn đều nhau)
        checkbox_frame = tk.Frame(frm, bg="#23272f")
        checkbox_frame.pack(fill='x', padx=64, pady=(0, 8))
        show_pw_var = tk.BooleanVar(value=False)
        def toggle_pw():
            password_entry.config(show="" if show_pw_var.get() else "*")
        show_pw_cb = tk.Checkbutton(checkbox_frame, text="Hiện mật khẩu", variable=show_pw_var, command=toggle_pw, bg="#23272f", fg="#b0b6c2", activebackground="#23272f", activeforeground="#4f8cff", selectcolor="#23262e", font=("Segoe UI", 10))
        show_pw_cb.pack(side=tk.LEFT, expand=True, anchor='center')
        remember_var = tk.BooleanVar(value=False)
        remember_cb = tk.Checkbutton(checkbox_frame, text="Ghi nhớ tôi", variable=remember_var, bg="#23272f", fg="#b0b6c2", activebackground="#23272f", activeforeground="#4f8cff", selectcolor="#23262e", font=("Segoe UI", 10))
        remember_cb.pack(side=tk.LEFT, expand=True, anchor='center')

        REMEMBER_FILE = os.path.join(os.path.dirname(__file__), "data", "remembered.json")

        def load_remembered():
            if os.path.exists(REMEMBER_FILE):
                try:
                    with open(REMEMBER_FILE, "r", encoding="utf-8") as f:
                        self._remembered = json.load(f)
                except Exception:
                    self._remembered = {}
            else:
                self._remembered = {}

        def save_remembered():
            try:
                with open(REMEMBER_FILE, "w", encoding="utf-8") as f:
                    json.dump(self._remembered, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        load_remembered()

        def on_username_change(*args):
            uname = username_var.get()
            if uname in self._remembered:
                password_var.set(self._remembered[uname])
                remember_var.set(True)
            else:
                password_var.set("")
                remember_var.set(False)
        username_var.trace_add("write", lambda *a: on_username_change())

        popup_ref = {"popup": None}
        def show_remembered_popup(event):
            uname = username_var.get()
            if len(uname) < 2:
                if popup_ref["popup"]:
                    popup_ref["popup"].destroy()
                    popup_ref["popup"] = None
                return
            matches = [u for u in self._remembered if uname.lower() in u.lower()]
            if not matches:
                if popup_ref["popup"]:
                    popup_ref["popup"].destroy()
                    popup_ref["popup"] = None
                return
            if popup_ref["popup"]:
                popup_ref["popup"].destroy()
            popup = tk.Toplevel(dialog)
            popup_ref["popup"] = popup
            popup.wm_overrideredirect(True)
            popup.configure(bg="#31343c")
            x = dialog.winfo_rootx() + username_entry.winfo_x()
            y = dialog.winfo_rooty() + username_entry.winfo_y() + username_entry.winfo_height()
            popup.geometry(f"220x{min(120, 28*len(matches))}+{x}+{y}")

            def fill_and_close(u):
                username_var.set(u)
                password_var.set(self._remembered[u])
                remember_var.set(True)
                popup.destroy()
                popup_ref["popup"] = None
                password_entry.focus_set()

            for i, u in enumerate(matches):
                btn = tk.Button(popup, text=u, anchor="w", font=("Segoe UI", 11), bg="#31343c", fg="#fff", bd=0, relief="flat", activebackground="#4f8cff", activeforeground="#fff", cursor="hand2", command=lambda u=u: fill_and_close(u))
                btn.pack(fill='x')
            def close_popup(event=None):
                if popup.winfo_exists():
                    popup.destroy()
                    popup_ref["popup"] = None
            popup.bind("<FocusOut>", close_popup)
        username_entry.bind("<KeyRelease>", show_remembered_popup)

        def on_remember_change(*args):
            uname = username_var.get()
            if not remember_var.get() and uname in self._remembered:
                del self._remembered[uname]
                save_remembered()
        remember_var.trace_add("write", lambda *a: on_remember_change())

        result = {"creds": None, "retry": False}
        def submit(event=None):
            self._dialog_zoomed = dialog.state() == 'zoomed'
            if remember_var.get():
                self._remembered[username_var.get()] = password_var.get()
                save_remembered()
            else:
                uname = username_var.get()
                if uname in self._remembered:
                    del self._remembered[uname]
                    save_remembered()
            result["creds"] = {'username': username_var.get(), 'password': password_var.get()}
            dialog.destroy()
        def go_back():
            self._dialog_zoomed = dialog.state() == 'zoomed'
            result["creds"] = "back"
            dialog.destroy()

        login_btn = tk.Button(
            frm, text="Đăng nhập",
            font=("Segoe UI", 12, "bold"),
            bg="#2196f3", fg="#fff",
            activebackground="#1976d2", activeforeground="#fff",
            bd=0, relief="flat", cursor="hand2", height=1,
            command=submit
        )
        login_btn.pack(fill='x', padx=64, pady=(12, 8), ipady=4)

        # Nút quay lại (thêm dưới nút đăng nhập)
        back_btn = tk.Button(
            frm, text="Quay lại",
            font=("Segoe UI", 12, "bold"),
            bg="#23272f", fg="#b0b6c2",
            activebackground="#31343c", activeforeground="#fff",
            bd=0, relief="flat", cursor="hand2", height=1,
            command=go_back,
            highlightthickness=1, highlightbackground="#bdbdbd"
        )
        back_btn.pack(fill='x', padx=64, pady=(0, 16), ipady=4)
        back_btn.update_idletasks()
        back_btn.configure(
            highlightthickness=2,
            highlightbackground="#bdbdbd",
            highlightcolor="#bdbdbd"
        )

        def close():
            result["creds"] = "back"
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", close)
        username_entry.focus_set()
        username_entry.bind('<Return>', lambda e: password_entry.focus_set())
        password_entry.bind('<Return>', lambda e: submit())
        dialog.deiconify()
        dialog.lift()
        dialog.grab_set()
        dialog.focus_force()
        dialog.wait_window()
        return result.get("creds", None)

    def _show_register_dialog(self, parent):
        dialog_width = 540
        dialog_height = 570
        dialog = tk.Toplevel(parent)
        dialog.withdraw()
        self._set_dialog_appearance(dialog, width=dialog_width, height=dialog_height, title="Đăng ký tài khoản")
        dialog.configure(bg="#23272f")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.focus_force()
        dialog.lift()
        dialog.grab_set()
        try:
            dialog.overrideredirect(False)
        except Exception:
            pass
        frm = tk.Frame(dialog, bg="#23272f")
        frm.place(relx=0.5, rely=0.5, anchor='center', width=dialog_width-40, height=dialog_height-40)

        # Logo + tiêu đề (CĂN GIỮA)
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "data", "icon.png")
            logo_img = Image.open(logo_path).resize((48, 48))
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(frm, image=logo_photo, bg="#23272f")
            logo_label.image = logo_photo
            logo_label.pack(pady=(24, 8))
        except Exception:
            tk.Label(frm, text="🎮", font=("Segoe UI", 32), bg="#23272f", fg="#fff").pack(pady=(24, 8))
        tk.Label(frm, text="ĐĂNG KÝ TÀI KHOẢN", font=("Segoe UI", 15, "bold"), bg="#23272f", fg="#fff").pack(pady=(0, 2), fill='x')
        tk.Label(frm, text="Tạo tài khoản mới để bắt đầu quản lý game của bạn", font=("Segoe UI", 10), bg="#23272f", fg="#b0b6c2").pack(pady=(2, 18), fill='x')

        # Form đăng ký (CĂN GIỮA)
        tk.Label(frm, text="TÊN ĐĂNG NHẬP", font=("Segoe UI", 10, "bold"), bg="#23272f", fg="#b0b6c2", anchor='center').pack(anchor='center', padx=48, pady=(0, 2))
        reg_username_var = StringVar()
        reg_username_entry = tk.Entry(frm, textvariable=reg_username_var, font=("Segoe UI", 12), bg="#23262e", fg="#fff", insertbackground="#4f8cff", relief="flat", highlightthickness=1, highlightbackground="#31343c", highlightcolor="#4f8cff", justify='center')
        reg_username_entry.pack(fill='x', padx=64, pady=(0, 12), ipady=6)

        tk.Label(frm, text="MẬT KHẨU", font=("Segoe UI", 10, "bold"), bg="#23272f", fg="#b0b6c2", anchor='center').pack(anchor='center', padx=48, pady=(0, 2))
        reg_password_var = StringVar()
        reg_password_entry = tk.Entry(frm, textvariable=reg_password_var, font=("Segoe UI", 12), bg="#23262e", fg="#fff", show="*", insertbackground="#4f8cff", relief="flat", highlightthickness=1, highlightbackground="#31343c", highlightcolor="#4f8cff", justify='center')
        reg_password_entry.pack(fill='x', padx=64, pady=(0, 6), ipady=6)

        tk.Label(frm, text="XÁC NHẬN MẬT KHẨU", font=("Segoe UI", 10, "bold"), bg="#23272f", fg="#b0b6c2", anchor='center').pack(anchor='center', padx=48, pady=(0, 2))
        reg_confirm_password_var = StringVar()
        reg_confirm_password_entry = tk.Entry(frm, textvariable=reg_confirm_password_var, font=("Segoe UI", 12), bg="#23262e", fg="#fff", show="*", insertbackground="#4f8cff", relief="flat", highlightthickness=1, highlightbackground="#31343c", highlightcolor="#4f8cff", justify='center')
        reg_confirm_password_entry.pack(fill='x', padx=64, pady=(0, 12), ipady=6)

        # Hiện/ẩn mật khẩu
        show_reg_pw_var = tk.BooleanVar(value=False)
        def toggle_reg_pw():
            reg_password_entry.config(show="" if show_reg_pw_var.get() else "*")
            reg_confirm_password_entry.config(show="" if show_reg_pw_var.get() else "*")
        show_reg_pw_cb = tk.Checkbutton(frm, text="Hiện mật khẩu", variable=show_reg_pw_var, command=toggle_reg_pw, bg="#23272f", fg="#b0b6c2", activebackground="#23272f", activeforeground="#4f8cff", selectcolor="#23262e", font=("Segoe UI", 10))
        show_reg_pw_cb.pack(anchor='center', padx=64, pady=(0, 0))

        # Nút đăng ký
        result = {"creds": None}
        def submit_reg(event=None):
            username = reg_username_var.get().strip()
            password = reg_password_var.get()
            confirm_password = reg_confirm_password_var.get()
            if not username or not password or not confirm_password:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng điền đầy đủ thông tin đăng ký.", parent=dialog)
                return
            if password != confirm_password:
                messagebox.showwarning("Mật khẩu không khớp", "Vui lòng xác nhận đúng mật khẩu.", parent=dialog)
                return
            if len(username) < 3 or not username.isalnum():
                messagebox.showwarning("Tên đăng nhập không hợp lệ", "Tên đăng nhập phải có ít nhất 3 ký tự và không chứa ký tự đặc biệt.", parent=dialog)
                return
            if not self.user_manager.register_user(username, password, role="user"):
                messagebox.showwarning("Tên đăng nhập đã tồn tại", "Vui lòng chọn tên đăng nhập khác.", parent=dialog)
                return
            messagebox.showinfo("Đăng ký thành công", "Bạn đã đăng ký tài khoản thành công! Bạn có thể đăng nhập ngay bây giờ.", parent=dialog)
            result["creds"] = {'username': username, 'password': password}
            dialog.destroy()

        reg_btn = tk.Button(
            frm, text="Đăng ký",
            font=("Segoe UI", 12, "bold"),
            bg="#2e8fff", fg="#fff",
            activebackground="#1e6fdc", activeforeground="#fff",
            bd=0, relief="flat", cursor="hand2", height=1,
            command=submit_reg
        )
        reg_btn.pack(fill='x', padx=64, pady=(12, 8), ipady=4)

        # Đảm bảo nút quay lại luôn hiển thị: đặt riêng một frame ở dưới cùng
        bottom_frame = tk.Frame(frm, bg="#23272f")
        bottom_frame.pack(side=tk.BOTTOM, fill='x', padx=0, pady=(0, 8))
        back_btn = tk.Button(
            bottom_frame, text="Quay lại",
            font=("Segoe UI", 12, "bold"),
            bg="#23272f", fg="#b0b6c2",
            activebackground="#31343c", activeforeground="#fff",
            bd=0, relief="flat", cursor="hand2", height=1,
            command=lambda: dialog.destroy(),
            highlightthickness=1, highlightbackground="#bdbdbd"
        )
        back_btn.pack(fill='x', padx=64, ipady=4)
        back_btn.update_idletasks()
        back_btn.configure(
            highlightthickness=2,
            highlightbackground="#bdbdbd",
            highlightcolor="#bdbdbd"
        )

        def close():
            result["creds"] = "back"
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", close)
        reg_username_entry.focus_set()
        reg_username_entry.bind('<Return>', lambda e: reg_password_entry.focus_set())
        reg_password_entry.bind('<Return>', lambda e: reg_confirm_password_entry.focus_set())
        reg_confirm_password_entry.bind('<Return>', lambda e: submit_reg())
        dialog.deiconify()
        dialog.lift()  # Đảm bảo cửa sổ hiện lên trên cùng
        dialog.grab_set()
        dialog.focus_force()
        dialog.wait_window()
        return result["creds"]

    def _center_dialog(self, dialog, width=480, height=320):
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _fade_in(self, dialog, duration=180):
        # Không dùng hiệu ứng fade-in để tránh nhấp nháy hoặc load chậm
        pass

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
                # ...existing code...
            elif mode == 'login':
                while True:
                    login_result = self._show_login_dialog(parent)
                    if login_result == "back":
                        break
                    creds = login_result
                    if creds:
                        user = self.user_manager.authenticate(creds['username'], creds['password'])
                        if user:
                            return user
                        else:
                            messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu.", parent=parent)
                            continue
                    else:
                        break
            elif mode == 'quit':
                return None

# --- giantbomb_client.py ---

class GiantBombClient:
    BASE_URL = 'https://www.giantbomb.com/api'
    DEFAULT_API_KEY = '30382badcce6403d0e4329e8df393a72d6366c47'

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GIANTBOMB_API_KEY') or self.DEFAULT_API_KEY
        self.session = requests.Session()
        self._search_cache = {}
        self._details_cache = {}

    def search_games(self, query, limit=50):
        cache_key = (query.lower(), limit)
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]

        params = {
            'api_key': self.api_key,
            'format': 'json',
            'query': query,
            'resources': 'game',
            'limit': limit
        }
        headers = {'User-Agent': 'GameCollectionApp'}
        try:
            resp = self.session.get(f"{self.BASE_URL}/search/", params=params, headers=headers, timeout=10)
            data = resp.json()
        except Exception as e:
            raise RuntimeError(f"Lỗi khi truy vấn API tìm kiếm: {e}")

        if data.get('status_code') != 1:
            raise RuntimeError(f"Lỗi API GiantBomb: {data.get('error')}")

        results = data.get('results', [])
        self._search_cache[cache_key] = results
        return results

    def get_game_details(self, guid):
        if guid in self._details_cache:
            return self._details_cache[guid]

        params = {
            'api_key': self.api_key,
            'format': 'json',
            'field_list': 'name,deck,developers,genres,platforms,aliases,image,original_release_date,site_detail_url'
        }
        headers = {'User-Agent': 'GameCollectionApp'}
        url = f"{self.BASE_URL}/game/{guid}/"
        try:
            resp = self.session.get(url, params=params, headers=headers, timeout=10)
            data = resp.json()
        except Exception as e:
            raise RuntimeError(f"Lỗi khi truy vấn chi tiết game: {e}")

        if data.get('status_code') != 1:
            raise RuntimeError(f"API error: {data.get('error')}")

        result = data.get('results')
        self._details_cache[guid] = result
        return result

# Sử dụng threading tải ảnh bìa
from PIL import Image, ImageTk
import urllib.request
import io

def load_image_async(url, label):
    def task():
        try:
            label.config(text="Đang tải ảnh...")
            with urllib.request.urlopen(url) as u:
                raw_data = u.read()
            im = Image.open(io.BytesIO(raw_data))
            im = im.resize((200, 270))
            photo = ImageTk.PhotoImage(im)
            label.config(image=photo, text='')
            label.image = photo
        except Exception as e:
            label.config(image='', text='Không tải được ảnh')
            label.image = None

    threading.Thread(target=task, daemon=True).start()

# Đảm bảo các class AuthController và GameApp được định nghĩa trước khi sử dụng
# Không có lệnh import hoặc định nghĩa nào bị lỗi hoặc bị lồng nhau

# Đảm bảo KHÔNG có dòng nào như:
# if __name__ == '__main__': hoặc các lệnh chạy thử ở cuối file này