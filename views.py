import urllib.request
from tkinter import BOTH, PanedWindow
from tkinter.ttk import Combobox, Style, Button as TtkButton, Entry as TtkEntry, Frame as TtkFrame, Checkbutton as TtkCheckbutton, Label as TtkLabel
from tkinter.simpledialog import Dialog
from PIL import Image
from PIL import ImageTk
from tkinter import LEFT, RIGHT, Scrollbar, Text, Toplevel, Y, messagebox, simpledialog, PhotoImage, Label as TkLabel
import os
import tkinter as tk
import webbrowser
import io
import threading
import datetime

from models import Game

def safe_text(val):
    if isinstance(val, list):
        return ', '.join(str(v).strip() for v in val if str(v).strip()) or 'Không rõ'
    if isinstance(val, str) and val.strip():
        return val.strip()
    return 'Không rõ'

# --- Đảm bảo GameForm được định nghĩa trước khi sử dụng ---
from tkinter.simpledialog import Dialog

class GameForm(Dialog):
    def __init__(self, parent, game=None):
        self.game = game
        super().__init__(parent, title='Form Game')

    def body(self, master):
        self.configure(bg="#23272f")
        master.configure(bg="#23272f")
        style = Style(master)
        style.theme_use('clam')
        style.configure("Card.TFrame", background="#23272f")
        style.configure("Card.TLabel", background="#23272f", foreground="#e0e6f0", font=("Segoe UI", 12, "bold"))
        style.configure("Accent.TButton", background="#2e8fff", foreground="#fff", font=("Segoe UI", 11, "bold"), borderwidth=0)
        style.map("Accent.TButton", background=[('active', '#1e6fdc')])

        fields = [
            'Tên', 'Mô tả', 'Ngày phát hành', 'Nhà phát triển',
            'Thể loại', 'Hệ máy', 'Liên kết chi tiết'
        ]
        self.entries = []

        frm = TtkFrame(master, style="Card.TFrame")
        frm.pack(padx=0, pady=0, fill='both', expand=True)

        for i, label in enumerate(fields):
            TtkLabel(frm, text=f'{label}:', style="Card.TLabel").pack(anchor='w', padx=24, pady=(8 if i == 0 else 2, 2))
            entry = tk.Entry(
                frm,
                font=("Segoe UI", 11),
                width=40,
                bg="#23262e",
                fg="#f5f6fa",
                insertbackground="#4f8cff",
                relief="flat",
                highlightthickness=1,
                highlightbackground="#31343c",
                highlightcolor="#4f8cff",
                borderwidth=0,
                disabledbackground="#23262e",
                disabledforeground="#b0b6c2"
            )
            entry.pack(fill='x', padx=24, pady=2, ipady=6)
            self.entries.append(entry)

        if self.game:
            values = [
                self.game.title or '',
                self.game.description or '',
                self.game.released or '',
                self.game.developers or '',
                self.game.genres or '',
                self.game.platforms or '',
                self.game.site_url or ''
            ]
            for entry, value in zip(self.entries, values):
                entry.insert(0, value)

        self.entries[0].focus_set()
        for i in range(len(self.entries) - 1):
            self.entries[i].bind('<Return>', lambda e, idx=i: self.entries[idx+1].focus_set())
        self.entries[-1].bind('<Return>', lambda e: self.ok())
        return self.entries[0]

    def buttonbox(self):
        box = tk.Frame(self, bg="#23272f")
        style = Style(self)
        style.theme_use('clam')
        style.configure("Accent.TButton", background="#2e8fff", foreground="#fff", font=("Segoe UI", 11, "bold"), borderwidth=0)
        style.map("Accent.TButton", background=[('active', '#1e6fdc')])
        btn_width = 14
        ok_btn = TtkButton(box, text="✔ OK", style="Accent.TButton", width=btn_width, command=self.ok)
        cancel_btn = TtkButton(box, text="✖ Hủy", style="Accent.TButton", width=btn_width, command=self.cancel)
        ok_btn.pack(side=tk.LEFT, padx=(0, 8), pady=10, expand=True, fill='x')
        cancel_btn.pack(side=tk.LEFT, padx=(8, 0), pady=10, expand=True, fill='x')
        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())
        box.pack(pady=(10, 0), fill='x')

    def apply(self):
        self.result = {
            'title': self.entries[0].get(),
            'description': self.entries[1].get(),
            'released': self.entries[2].get(),
            'developers': self.entries[3].get(),
            'genres': self.entries[4].get(),
            'platforms': self.entries[5].get(),
            'site_url': self.entries[6].get()
        }

# ĐẢM BẢO: Sau class GameForm phải có code thân class (không để trống).

class MainView:
    def _setup_style(self):
        style = Style()
        style.theme_use('clam')
        # Màu nền và card
        style.configure("Card.TFrame", background="#23262e")
        style.configure("Card.TLabel", background="#23262e", foreground="#f5f6fa", font=("Segoe UI", 11, "bold"))
        # Combobox hiện đại
        style.configure("Modern.TCombobox",
                        fieldbackground="#23262e", background="#23262e",
                        foreground="#f5f6fa", font=("Segoe UI", 11),
                        bordercolor="#31343c", lightcolor="#31343c", darkcolor="#31343c")
        style.map("Modern.TCombobox",
                  fieldbackground=[('readonly', '#23262e')],
                  background=[('readonly', '#23262e')],
                  foreground=[('readonly', '#f5f6fa')])
        # Checkbutton
        style.configure("Modern.TCheckbutton",
                        background="#23262e", foreground="#b0b6c2", font=("Segoe UI", 11),
                        indicatorcolor="#4f8cff", indicatordiameter=16)
        style.map("Modern.TCheckbutton",
                  background=[('active', '#31343c'), ('!active', '#23262e')],
                  foreground=[('active', '#4f8cff'), ('!active', '#b0b6c2')],
                  indicatorcolor=[('selected', '#4f8cff'), ('!selected', '#b0b6c2')],
                  indicatordiameter=[('selected', 16), ('!selected', 16)])
        # Button chính
        style.configure("Accent.TButton",
                        background="#4f8cff", foreground="#fff",
                        font=("Segoe UI", 11, "bold"), borderwidth=0, focusthickness=2, focuscolor="#4f8cff")
        style.map("Accent.TButton",
                  background=[('active', '#3766b1'), ('disabled', '#444')],
                  foreground=[('disabled', '#aaa')])
        # Button phụ
        style.configure("Modern.TButton",
                        background="#31343c", foreground="#f5f6fa",
                        font=("Segoe UI", 11, "bold"), borderwidth=0)
        style.map("Modern.TButton",
                  background=[('active', '#4f8cff'), ('disabled', '#444')],
                  foreground=[('disabled', '#aaa')])
        # Entry
        style.configure("TEntry",
                        fieldbackground="#23262e", background="#23262e",
                        foreground="#f5f6fa", bordercolor="#4f8cff", lightcolor="#31343c", darkcolor="#31343c")
        # Listbox (set ở nơi tạo)
        # Đảm bảo đồng bộ màu nền, border, font với dialog chọn chế độ
        style.configure("MainBG.TFrame", background="#23272f")
        style.configure("MainTitle.TLabel", background="#23272f", foreground="#e0e6f0", font=("Segoe UI", 16, "bold"))
        style.configure("Section.TLabel", background="#23272f", foreground="#4f8cff", font=("Segoe UI", 13, "bold"))

    def __init__(self, master, manager, user, api_client=None, is_admin=False, on_logout=None, admin_manage_users_callback=None):
        self.master = master
        self.manager = manager
        self.user = user
        self.api = api_client
        self.is_admin = is_admin
        self.on_logout = on_logout
        self.admin_manage_users_callback = admin_manage_users_callback

        self._setup_style()
        self.genre_filter = ""
        self.dev_filter = ""
        self._original_order = None
        self._original_id_map = {}

        # --- Giao diện đồng bộ với dialog chọn chế độ ---
        self.master.configure(bg="#23272f")
        self.master.minsize(900, 600)
        self.master.update_idletasks()
        self.master.resizable(True, True)
        self.master.bind("<Configure>", self._on_resize_main)

        # --- Ảnh nền phủ toàn bộ
        self.bg_label = None
        try:
            from PIL import Image, ImageTk, ImageEnhance, ImageFilter
            bg_path = os.path.join(os.path.dirname(__file__), "data", "background.jpg")
            if os.path.exists(bg_path):
                bg_img = Image.open(bg_path)
                # Resize ảnh nền về đúng kích thước màn hình 1 lần duy nhất
                screen_w = master.winfo_screenwidth()
                screen_h = master.winfo_screenheight()
                bg_img = bg_img.resize((screen_w, screen_h))
                # Làm mờ và tối ảnh nền
                bg_img = bg_img.filter(ImageFilter.GaussianBlur(6))
                enhancer = ImageEnhance.Brightness(bg_img)
                bg_img = enhancer.enhance(0.5)
                self.bg_photo = ImageTk.PhotoImage(bg_img)
                self.bg_label = tk.Label(master, image=self.bg_photo)
                self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
            else:
                master.configure(bg="#23272f")
        except Exception:
            master.configure(bg="#23272f")
            self.bg_label = None

        # --- Sidebar trái
        self.sidebar = tk.Frame(master, bg="#1a1d26", width=210)
        self.sidebar.place(relx=0, rely=0, relheight=1)
        # Avatar + tên user
        try:
            avatar_path = os.path.join(os.path.dirname(__file__), "data", "avatar.png")
            avatar_img = Image.open(avatar_path).resize((64, 64))
            self.avatar_photo = ImageTk.PhotoImage(avatar_img)
            avatar_label = tk.Label(self.sidebar, image=self.avatar_photo, bg="#1a1d26")
            avatar_label.pack(pady=(24, 8))
        except Exception:
            avatar_label = tk.Label(self.sidebar, text="🙂", font=("Segoe UI", 32), bg="#1a1d26", fg="#fff")
            avatar_label.pack(pady=(24, 8))
        tk.Label(self.sidebar, text=user.username, font=("Segoe UI", 14, "bold"), bg="#1a1d26", fg="#fff").pack(pady=(0, 24))

        # Menu sidebar
        menu_items = [
            ("Home", lambda: None),
            ("Catalogue", lambda: None),
            ("Downloads", lambda: None),
            ("Settings", lambda: None),
        ]
        for text, cmd in menu_items:
            btn = tk.Button(self.sidebar, text=text, font=("Segoe UI", 12, "bold"),
                            bg="#23262e", fg="#fff", bd=0, relief="flat", activebackground="#31343c",
                            activeforeground="#4f8cff", cursor="hand2", command=cmd)
            btn.pack(fill='x', padx=16, pady=6, ipady=6)

        # --- Main frame ---
        self.main_frame = TtkFrame(master, style="MainBG.TFrame")
        self.main_frame.pack(fill='both', expand=True)

        # --- Tiêu đề chính ---
        TtkLabel(self.main_frame, text="BỘ SƯU TẬP GAME", style="MainTitle.TLabel", anchor="center").pack(pady=(18, 8))

        # --- Hiển thị ngày giờ hiện tại ở góc trên phải ---
        self.datetime_label = TtkLabel(self.main_frame, text="", style="Card.TLabel", anchor="e")
        self.datetime_label.pack(anchor="ne", padx=24, pady=(0, 0))
        self._update_datetime_label()

        # --- Thoát/Đăng xuất ---
        top_btn_frame = TtkFrame(self.main_frame, style="MainBG.TFrame")
        top_btn_frame.pack(fill='x', padx=24)
        if self.on_logout:
            self._modern_button(top_btn_frame, 'Đăng xuất', self.on_logout).pack(side=tk.RIGHT, padx=5)
        # Thêm nút quản lý tài khoản cho admin
        if self.is_admin and self.admin_manage_users_callback:
            self._modern_button(top_btn_frame, 'Quản lý tài khoản', self.admin_manage_users_callback).pack(side=tk.RIGHT, padx=5)

        # --- Chọn tài khoản user để thao tác (chỉ admin) ---
        if self.is_admin:
            from models import UserManager
            user_manager = UserManager()
            # Lấy danh sách user không trùng lặp, không lặp lại user hiện tại
            self.usernames = [u.username for u in user_manager.users if u.username != "123" and u.username != user.username]
            self.selected_username = tk.StringVar(value=self.user.username)
            user_select_frame = TtkFrame(self.main_frame, style="MainBG.TFrame")
            user_select_frame.pack(fill='x', padx=24, pady=(0, 8))
            TtkLabel(user_select_frame, text="Chọn tài khoản thao tác:", style="Card.TLabel").pack(side=tk.LEFT, padx=(0, 5))
            self.user_combobox = Combobox(user_select_frame, textvariable=self.selected_username, state="readonly", width=18, style="Modern.TCombobox")
            self.user_combobox['values'] = [self.user.username] + self.usernames
            self.user_combobox.current(0)
            self.user_combobox.pack(side=tk.LEFT, padx=5)
            self.user_combobox.bind("<<ComboboxSelected>>", self.on_user_change)

        # --- Thanh filter/sort ---
        filter_frame = TtkFrame(self.main_frame, style="MainBG.TFrame")
        filter_frame.pack(padx=24, pady=8, fill='x')

        TtkLabel(filter_frame, text="Thể loại:", style="Card.TLabel").pack(side=tk.LEFT, padx=(0, 5))
        self.genre_var = tk.StringVar()
        self.genre_combobox = Combobox(filter_frame, textvariable=self.genre_var, state="readonly", width=18, style="Modern.TCombobox")
        self.genre_combobox.pack(side=tk.LEFT, padx=5)
        self.genre_combobox.bind("<<ComboboxSelected>>", self.on_filter_change)

        TtkLabel(filter_frame, text="Sắp xếp:", style="Card.TLabel").pack(side=tk.LEFT, padx=(20, 5))
        self.sort_var = tk.StringVar()
        self.sort_combobox = Combobox(filter_frame, textvariable=self.sort_var, state="readonly", width=18, style="Modern.TCombobox")
        self.sort_combobox['values'] = ["", "Tên", "Ngày phát hành"]
        self.sort_combobox.current(0)
        self.sort_combobox.pack(side=tk.LEFT, padx=5)
        self.sort_combobox.bind("<<ComboboxSelected>>", self.on_sort_change)

        self.sort_order = tk.BooleanVar(value=True)
        TtkCheckbutton(filter_frame, text="Tăng dần A->Z", variable=self.sort_order, style="Modern.TCheckbutton").pack(side=tk.LEFT, padx=10)
        self.sort_order.trace('w', self.on_sort_change)

        # --- Nội dung chính: chia 2 cột bằng PanedWindow ---
        paned = PanedWindow(self.main_frame, orient=tk.HORIZONTAL, sashrelief='flat', bg="#23272f", bd=0, sashwidth=6)
        paned.pack(fill='both', expand=True, padx=24, pady=(0, 12))

        left_frame = TtkFrame(paned, style="MainBG.TFrame")
        right_frame = TtkFrame(paned, style="MainBG.TFrame")
        paned.add(left_frame, minsize=220)
        paned.add(right_frame, minsize=320)

        self._paned = paned
        self._left_frame = left_frame
        self._right_frame = right_frame

        self._default_pane_ratio = 0.5
        self._pane_initialized = False
        self.master.after(100, self._set_default_pane_size)
        paned.bind('<Configure>', self._on_pane_configure)

        # --- Cột trái: danh sách game ---
        # Tiêu đề danh sách game + thanh tìm kiếm
        title_search_frame = TtkFrame(left_frame, style="MainBG.TFrame")
        title_search_frame.pack(anchor='w', fill='x', pady=(0, 4), padx=0)

        TtkLabel(title_search_frame, text="Danh sách game", style="Section.TLabel", anchor="w").pack(side=tk.LEFT, pady=0, padx=(0, 6))

        # Thêm Entry tìm kiếm và nút search
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            title_search_frame, textvariable=self.search_var, font=("Segoe UI", 11),
            width=18, bg="#23262e", fg="#f5f6fa", insertbackground="#4f8cff",
            relief="flat", highlightthickness=1, highlightbackground="#31343c", highlightcolor="#4f8cff"
        )
        search_entry.pack(side=tk.LEFT, padx=(0, 2), ipady=4)
        search_entry.bind('<Return>', lambda e: self.on_search())
        # Thêm dòng này để tự động lọc khi nhập/xóa ký tự
        search_entry.bind('<KeyRelease>', lambda e: self.refresh_list())

        # Nút search (icon kính lúp)
        search_btn = tk.Button(
            title_search_frame, text="🔍", font=("Segoe UI", 11), width=2,
            bg="#23262e", fg="#4f8cff", bd=0, relief="flat", activebackground="#31343c",
            activeforeground="#4f8cff", cursor="hand2", command=self.on_search
        )
        search_btn.pack(side=tk.LEFT, padx=(0, 0), ipady=0)

        # --- Listbox + scrollbar dọc ---
        listbox_frame = TtkFrame(left_frame, style="MainBG.TFrame")
        listbox_frame.pack(fill='both', expand=True)

        self.listbox = tk.Listbox(listbox_frame, width=50, font=("Segoe UI", 12), bg="#23262e", fg="#f5f6fa",
                                  selectbackground="#4f8cff", selectforeground="#fff",
                                  highlightthickness=0, bd=0, relief="flat", activestyle='none')
        self.listbox.pack(side=tk.LEFT, fill='both', expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.listbox.bind("<Enter>", lambda e: self._handle_listbox_mousewheel_bind())
        self.listbox.bind("<Leave>", lambda e: self._handle_listbox_mousewheel_unbind())

        self.scrollbar_v = Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        # KHÔNG pack scrollbar_v ở đây, để pack/remove động trong refresh_list

        # --- Nút chức năng ---
        btn_frame = TtkFrame(left_frame, style="MainBG.TFrame")
        btn_frame.pack(pady=8)
        self._modern_button(btn_frame, 'Thêm', self.add).pack(side=tk.LEFT, padx=5)
        self._modern_button(btn_frame, 'Sửa', self.edit).pack(side=tk.LEFT, padx=5)
        self._modern_button(btn_frame, 'Xóa', self.delete).pack(side=tk.LEFT, padx=5)
        self._modern_button(btn_frame, 'Tìm API', self.search_api).pack(side=tk.LEFT, padx=5)
        self._modern_button(btn_frame, 'Xem JSON', self.show_json).pack(side=tk.LEFT, padx=5)

        # --- Cột phải: thông tin game ---
        # right_frame = TtkFrame(content_frame, style="MainBG.TFrame")
        # right_frame.pack(side=tk.LEFT, fill='both', expand=True)

        # --- Thay đổi: Tạo frame mới chứa tiêu đề và ảnh bìa ---
        info_header_frame = TtkFrame(right_frame, style="MainBG.TFrame")
        info_header_frame.pack(pady=(0, 8))

        # Tiêu đề canh giữa phía trên ảnh bìa
        TtkLabel(info_header_frame, text="Thông tin game", style="Section.TLabel").pack(anchor='center')

        # Ảnh bìa (cover)
        self.cover_label = TtkLabel(info_header_frame, style="Card.TLabel")
        self.cover_label.pack(pady=(4, 0))

        # Info text + scrollbar dọc/ngang
        info_frame = TtkFrame(right_frame, style="MainBG.TFrame")
        info_frame.pack(fill='both', expand=True)

        self.info_text = Text(info_frame, height=12, wrap='none', font=("Segoe UI", 11),
                              bg="#23262e", fg="#f5f6fa", bd=0, relief="flat", highlightthickness=0)
        self.info_text.grid(row=0, column=0, sticky='nsew')
        self.info_scrollbar_v = Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        # KHÔNG grid scrollbar_v ở đây, để grid/remove động trong _update_info_scrollbar_visibility
        self.info_scrollbar_h = Scrollbar(info_frame, orient=tk.HORIZONTAL, command=self.info_text.xview)
        self.info_scrollbar_h.grid(row=1, column=0, sticky='ew')
        self.info_text.config(yscrollcommand=self._on_info_scroll, xscrollcommand=self.info_scrollbar_h.set)
        info_frame.rowconfigure(0, weight=1)
        info_frame.columnconfigure(0, weight=1)
        self.info_text.config(state='disabled')

        self.info_text.bind("<Enter>", lambda e: self._handle_info_mousewheel_bind())
        self.info_text.bind("<Leave>", lambda e: self._handle_info_mousewheel_unbind())

        # Nút mở liên kết
        self.link_button = TtkButton(right_frame, text='Mở liên kết chi tiết', command=self.open_site,
                                     style="Accent.TButton", state='disabled', cursor="hand2")
        self.link_button.pack(pady=(8, 0))

        self.selected_game = None

        self.update_genre_combobox()
        self.refresh_list()

        self.info_text.bind("<Configure>", lambda e: self._update_info_scrollbar_visibility())
        self.info_text.bind("<Expose>", lambda e: self._update_info_scrollbar_visibility())

    def _on_resize_main(self, event):
        # Đảm bảo các frame con luôn fill hết cửa sổ khi phóng to/thu nhỏ
        self.main_frame.pack(fill='both', expand=True)
        # ...các frame con đã dùng fill/expand nên không cần xử lý thêm...

    def _modern_button(self, parent, text, command):
        return TtkButton(parent, text=text, command=command, style="Modern.TButton", cursor="hand2")

    def on_search(self):
        # Khi nhấn Enter hoặc nút search, lọc danh sách game theo tên
        self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        # Lưu thứ tự gốc ban đầu nếu chưa có
        if self._original_order is None:
            self._original_order = sorted([g.id for g in self.manager.games], key=lambda x: x)
        # Luôn lấy danh sách games đúng thứ tự gốc ban đầu (id tăng dần)
        all_games = sorted(self.manager.games, key=lambda g: self._original_order.index(g.id) if g.id in self._original_order else 1e9)
        games = all_games

        # --- Áp dụng filter tìm kiếm theo tên ---
        search_text = self.search_var.get().strip().lower()
        if search_text:
            games = [g for g in games if search_text in (g.title or '').lower()]

        # Apply filters
        if self.genre_filter:
            # Lọc từ all_games để giữ đúng thứ tự thêm vào
            games = [g for g in all_games if self.genre_filter in (g.genres or "").lower()]

        sort_options = {"Tên": "title", "Ngày phát hành": "released"}
        sort_field = sort_options.get(self.sort_var.get(), None)
        is_az = self.sort_order.get()  # True: tích A-Z, False: bỏ tích

        if sort_field == "title":
            games_sorted = sorted(games, key=lambda g: g.title or "", reverse=not is_az)
            for idx, game in enumerate(games_sorted, 1):
                game._display_index = idx
            self.sorted_games = games_sorted
            for game in games_sorted:
                self.listbox.insert(tk.END, f"{game._display_index}: {game.title}")
        elif sort_field == "released":
            games_sorted = sorted(games, key=lambda g: g.released or "", reverse=is_az)
            for idx, game in enumerate(games_sorted, 1):
                game._display_index = idx
            self.sorted_games = games_sorted
            for game in games_sorted:
                self.listbox.insert(tk.END, f"{game._display_index}: {game.title}")
        else:
            # Mặc định: giữ nguyên thứ tự gốc ban đầu (id tăng dần), chỉ đảo chiều hiển thị nếu bỏ tích
            if is_az:
                games_show = games
            else:
                games_show = list(reversed(games))
            self.sorted_games = games_show
            for game in games_show:
                self.listbox.insert(tk.END, f"{game.id}: {game.title}")

        # Tự động bật/tắt thanh cuộn dọc/ngang
        self.listbox.update_idletasks()
        if self.listbox.size() > 0 and self.listbox.winfo_height() < self.listbox.size() * 24:
            self.scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.scrollbar_v.pack_forget()
        # XÓA HOÀN TOÀN các dòng sau:
        # max_len = max((len(self.listbox.get(i)) for i in range(self.listbox.size())), default=0)
        # if max_len > 40:
        #     self.scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        # else:
        #     self.scrollbar_h.pack_forget()

        self.update_genre_combobox()
        self.cover_label.config(image='', text='')
        self.cover_label.image = None
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        self.info_text.config(state='disabled')
        self.link_button.config(state='disabled')
        self.selected_game = None

        # ẨN/HIỆN thanh cuộn dọc/ngang info_text tùy nội dung
        self._update_info_scrollbar_visibility()

    def update_genre_combobox(self):
        genre_set = set()
        for g in self.manager.games:
            if g.genres:
                for genre in map(str.strip, (g.genres or "").split(",")):
                    if genre:
                        genre_set.add(genre.lower())
        # Đảm bảo giữ nguyên giá trị đang chọn nếu có
        current = self.genre_var.get()
        values = [""] + sorted({g.capitalize() for g in genre_set})
        self.genre_combobox['values'] = values
        # Nếu giá trị hiện tại không còn trong danh sách thì reset về ""
        if current not in values:
            self.genre_var.set("")

    def on_filter_change(self, event=None):
        # Lấy đúng giá trị genre (không lower nữa)
        self.genre_filter = self.genre_var.get().lower()
        self.refresh_list()

    def on_sort_change(self, *args):
        self.refresh_list()

    def add(self):
        if not self.is_admin:
            messagebox.showwarning('Không đủ quyền', 'Chỉ admin mới có thể thêm game')
            return
        form = GameForm(self.master)
        data = form.result
        if data:
            new_game = Game(
                title=data['title'],
                description=data['description'],
                released=data['released'],
                developers=data['developers'],
                genres=data['genres'],
                platforms=data['platforms'],
                site_url=data['site_url'],
                cover_url=None,
                aliases=None
            )
            new_game.id = self.manager.next_id()
            self.manager.add_game(new_game)
            self.update_genre_combobox()
            self.refresh_list()

    def edit(self):
        if not self.is_admin:
            messagebox.showwarning('Không đủ quyền', 'Chỉ admin mới có thể sửa game')
            return
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning('Chưa chọn game', 'Vui lòng chọn game để sửa')
            return
        index = sel[0]
        game = self.sorted_games[index] if hasattr(self, 'sorted_games') else self.manager.games[index]
        form = GameForm(self.master, game)
        data = form.result
        if data:
            game.title = data['title']
            game.description = data['description']
            game.released = data['released']
            game.developers = data['developers']
            game.genres = data['genres']
            game.platforms = data['platforms']
            game.site_url = data['site_url']
            self.manager.update_game(game)
            self.update_genre_combobox()
            self.refresh_list()

    def delete(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning('Chưa chọn game', 'Vui lòng chọn game để xóa')
            return
        index = sel[0]
        game = self.sorted_games[index] if hasattr(self, 'sorted_games') else self.manager.games[index]
        if not self.is_admin:
            pass
        if messagebox.askyesno('Xác nhận', f'Bạn có chắc muốn xóa game "{game.title}" không?'):
            self.manager.delete_game(game.id)
            self.update_genre_combobox()
            self.refresh_list()

    def search_api(self):
        if not self.api:
            messagebox.showerror('Lỗi', 'API client chưa khởi tạo')
            return

        def center_window(window, width=700, height=400):
            window.update_idletasks()
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            window.geometry(f"{width}x{height}+{x}+{y}")

        def ask_game_name(parent):
            dialog = Toplevel(parent)
            dialog.title("Tìm game bằng API")
            dialog.configure(bg="#23272f")
            dialog.resizable(False, False)
            center_window(dialog, 600, 180)
            dialog.grab_set()
            dialog.focus_force()
            dialog.transient(parent)

            style = Style(dialog)
            style.theme_use('clam')
            style.configure("Card.TLabel", background="#23272f", foreground="#e0e6f0", font=("Segoe UI", 12, "bold"))
            style.configure("Accent.TButton", background="#2e8fff", foreground="#fff", font=("Segoe UI", 11, "bold"), borderwidth=0)
            style.map("Accent.TButton", background=[('active', '#1e6fdc')])

            frm = TtkFrame(dialog, style="Card.TFrame")
            frm.pack(padx=24, pady=18, fill='both', expand=True)

            TtkLabel(frm, text="Nhập tên game:", style="Card.TLabel").pack(pady=(0, 8))
            name_var = tk.StringVar()
            entry = tk.Entry(frm, textvariable=name_var, font=("Segoe UI", 12), width=32, bg="#23262e", fg="#f5f6fa", insertbackground="#4f8cff", relief="flat", highlightthickness=1, highlightbackground="#31343c", highlightcolor="#4f8cff")
            entry.pack(pady=(0, 12))
            entry.focus_set()

            result = {"value": None, "back": False}

            def do_search(event=None):
                result["value"] = name_var.get()
                dialog.destroy()

            def cancel(event=None):
                result["value"] = None
                dialog.destroy()

            def go_back(event=None):
                result["back"] = True
                dialog.destroy()

            btn_frame = TtkFrame(frm, style="Card.TFrame")
            btn_frame.pack(pady=(0, 0), fill='x')

            btn_width = 14
            search_btn = TtkButton(btn_frame, text="🔍 Tìm kiếm", style="Accent.TButton", command=do_search, width=btn_width)
            cancel_btn = TtkButton(btn_frame, text="Hủy", style="Accent.TButton", command=cancel, width=btn_width)
            search_btn.pack(side=tk.LEFT, padx=(0, 8), pady=0, expand=True, fill='x')
            cancel_btn.pack(side=tk.LEFT, padx=(8, 0), pady=0, expand=True, fill='x')

            entry.bind('<Return>', do_search)
            dialog.bind('<Escape>', cancel)
            search_btn.bind('<Return>', do_search)
            dialog.wait_window()
            if result.get("back"):
                return "back"
            return result["value"]

        while True:
            query = ask_game_name(self.master)
            if query == "back" or not query:
                return

            try:
                results = self.api.search_games(query)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi khi tìm kiếm API: {e}")
                return

            def show_result_window():
                top = Toplevel(self.master)
                top.title("Chọn game từ kết quả API")
                top.configure(bg="#23272f")
                top.transient(self.master)
                top.grab_set()
                top.focus_force()
                top.lift()
                center_window(top, 700, 400)

                content_frame = TtkFrame(top, style="Card.TFrame")
                content_frame.pack(fill='both', expand=True, padx=10, pady=10)

                lb_scroll = Scrollbar(content_frame)
                lb_scroll.pack(side=tk.RIGHT, fill=tk.Y)
                
                lb = tk.Listbox(content_frame, width=50, selectmode=tk.SINGLE, font=("Segoe UI", 11), bg="#23272f", fg="#e0e6f0", selectbackground="#3a3f4b", highlightthickness=0, bd=0, relief="flat")
                lb.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 10), pady=0)
                
                lb_scroll.config(command=lb.yview)
                lb.config(yscrollcommand=lb_scroll.set)

                # --- Thêm hỗ trợ cuộn chuột ---
                def on_mousewheel(event):
                    if lb.winfo_height() < lb.size() * 24:
                        lb.yview_scroll(int(-1 * (event.delta / 120)), "units")
                        return "break"
                lb.bind("<MouseWheel>", on_mousewheel)
                # Đảm bảo cuộn được cả khi chuột ở trên scrollbar
                lb_scroll.bind("<MouseWheel>", on_mousewheel)

                for idx, r in enumerate(results):
                    lb.insert(tk.END, f"{r.get('name')} - {r.get('original_release_date') or 'Không rõ'}")

                cover_label = TtkLabel(content_frame, style="Card.TLabel")
                cover_label.pack(side=tk.LEFT, padx=(0, 0), pady=0)
                cover_label.image = None

                def show_cover(event=None):
                    sel = lb.curselection()
                    if not sel:
                        cover_label.config(image='', text='')
                        cover_label.image = None
                        return
                    idx = sel[0]
                    game = results[idx]
                    url = None
                    image_data = game.get('image')
                    if isinstance(image_data, dict):
                        url = image_data.get('medium_url')
                    if not url:
                        cover_label.config(image='', text='Không có ảnh')
                        cover_label.image = None
                        return
                    try:
                        with urllib.request.urlopen(url) as u:
                            raw_data = u.read()
                        im = Image.open(io.BytesIO(raw_data))
                        im = im.resize((150, 200))
                        photo = ImageTk.PhotoImage(im)
                        cover_label.config(image=photo, text='')
                        cover_label.image = photo
                    except Exception as e:
                        cover_label.config(image='', text='Không tải được ảnh')
                        cover_label.image = None

                lb.bind('<<ListboxSelect>>', show_cover)
                if results:
                    lb.selection_set(0)
                    show_cover()

                def on_confirm(event=None):
                    sels = lb.curselection()
                    if not sels:
                        messagebox.showwarning("Chưa chọn", "Vui lòng chọn ít nhất một game")
                        return

                    added = False
                    for idx in sels:
                        selected = results[idx]
                        guid = selected.get('guid')
                        if not guid:
                            continue

                        try:
                            selected = self.api.get_game_details(guid)
                        except Exception as e:
                            messagebox.showerror("Lỗi", f"Không lấy được chi tiết game: {e}")
                            continue

                        def extract_names(data):
                            if isinstance(data, list):
                                return ', '.join(item.get('name', '') for item in data if isinstance(item, dict) and 'name' in item)
                            elif isinstance(data, str):
                                return data
                            return ''

                        developers_str = extract_names(selected.get('developers'))
                        genres_str = extract_names(selected.get('genres'))
                        platforms_str = extract_names(selected.get('platforms'))

                        data = {
                            'title': selected.get('name', ''),
                            'description': selected.get('deck', ''),
                            'released': selected.get('original_release_date', ''),
                            'cover_url': (selected.get('image') or {}).get('medium_url', ''),
                            'developers': developers_str,
                            'genres': genres_str,
                            'platforms': platforms_str,
                            'site_url': selected.get('site_detail_url', ''),
                            'aliases': None
                        }

                        form_data = {
                            'title': data['title'],
                            'description': data['description'],
                            'released': data['released'],
                            'developers': data['developers'],
                            'genres': data['genres'],
                            'platforms': data['platforms'],
                            'site_url': data['site_url']
                        }
                        form = GameForm(self.master, Game(**form_data))
                        filled = form.result
                        if filled:
                            new_game = Game(
                                title=filled['title'],
                                description=filled['description'],
                                released=filled['released'],
                                developers=filled['developers'],
                                genres=filled['genres'],
                                platforms=filled['platforms'],
                                site_url=filled['site_url'],
                                cover_url=data['cover_url'],
                                aliases=None
                            )
                            if not new_game.id:
                                new_game.id = self.manager.next_id()
                            self.manager.add_game(new_game)
                            added = True

                    if added:
                        self.update_genre_combobox()
                        self.refresh_list()
                    # KHÔNG đóng cửa sổ, cho phép chọn tiếp

                def on_back():
                    top.destroy()

                btn_frame = TtkFrame(top, style="Card.TFrame")
                btn_frame.pack(pady=10)
                btn_confirm = TtkButton(btn_frame, text='Xác nhận', command=on_confirm, style="Accent.TButton")
                btn_confirm.pack(side=tk.LEFT, padx=(0, 8), ipadx=10)
                btn_back = TtkButton(btn_frame, text='Quay lại', command=on_back, style="Accent.TButton")
                btn_back.pack(side=tk.LEFT, padx=(8, 0), ipadx=10)

                top.bind('<Return>', on_confirm)
                top.bind('<Escape>', lambda e: on_back())

                # Đảm bảo khi đóng cửa sổ bằng nút X cũng chỉ đóng cửa sổ này
                top.protocol("WM_DELETE_WINDOW", on_back)

                top.wait_window()

            show_result_window()
    # ...existing code...

    def show_json(self):
        top = Toplevel(self.master)
        top.title('Dữ liệu JSON')
        top.configure(bg="#23272f")
        # Frame để chứa text và scrollbars
        frame = TtkFrame(top, style="Card.TFrame")
        frame.pack(fill=BOTH, expand=True)
        txt = Text(frame, wrap='none', font=("Consolas", 11), bg="#23272f", fg="#e0e6f0", bd=0, relief="flat", highlightthickness=0)
        txt.grid(row=0, column=0, sticky='nsew')
        scroll_y = Scrollbar(frame, command=txt.yview)
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x = Scrollbar(frame, orient=tk.HORIZONTAL, command=txt.xview)
        scroll_x.grid(row=1, column=0, sticky='ew')
        txt.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        # Sửa đoạn này: tạo file nếu chưa tồn tại
        path = self.manager.path
        if not os.path.exists(path):
            messagebox.showinfo("Thông báo", f"Chưa có dữ liệu cho tài khoản này.\nFile {path} chưa tồn tại.")
            top.destroy()
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = f.read()
        txt.insert('1.0', data)

    def open_site(self):
        if self.selected_game and self.selected_game.site_url:
            webbrowser.open(self.selected_game.site_url)

    def on_select(self, event):
        selection = event.widget.curselection()
        # Nếu đã chọn game này rồi và lại click vào nó nữa thì reset về mặc định
        if selection:
            index = selection[0]
            game = self.sorted_games[index]
            # Nếu đã chọn rồi và click lại vào chính nó
            if self.selected_game is not None and self.selected_game == game:
                # Reset về mặc định
                self.listbox.selection_clear(0, tk.END)
                self.cover_label.config(image='', text='')
                self.cover_label.image = None
                self.info_text.config(state='normal')
                self.info_text.delete('1.0', tk.END)
                self.info_text.config(state='disabled')
                self.link_button.config(state='disabled')
                self.selected_game = None
                # Ẩn thanh cuộn ngang khi không chọn game
                self.info_scrollbar_h.grid_remove()
                self.info_scrollbar_v.grid_remove()
                return
            # Lưu lại game đang chọn
            self.selected_game = game
            # Lấy số thứ tự hiển thị đúng cho từng chế độ
            if hasattr(game, "_display_index"):
                display_index = game._display_index
            else:
                display_index = game.id
            # Hiện ảnh bìa nếu có
            url = game.cover_url
            if url:
                # Tải ảnh bìa bằng threading để không block UI
                def load_cover():
                    try:
                        with urllib.request.urlopen(url) as u:
                            raw_data = u.read()
                        im = Image.open(io.BytesIO(raw_data))
                        im = im.resize((200, 270))
                        photo = ImageTk.PhotoImage(im)
                        self.cover_label.config(image=photo, text='')
                        self.cover_label.image = photo
                    except Exception as e:
                        self.cover_label.config(image='', text='Không tải được ảnh')
                        self.cover_label.image = None
                threading.Thread(target=load_cover, daemon=True).start()
            else:
                self.cover_label.config(image='', text='Không có ảnh')
                self.cover_label.image = None
            # Hiện thông tin game (có thêm ngày giờ tạo nếu có)
            info = f"""
Tên: {safe_text(game.title)}
Mô tả: {safe_text(game.description)}
Ngày phát hành: {safe_text(game.released)}
Nhà phát triển: {safe_text(game.developers)}
Thể loại: {safe_text(game.genres)}
Hệ máy: {safe_text(game.platforms)}
Liên kết chi tiết: {safe_text(game.site_url)}
""".strip()
            self.info_text.config(state='normal')
            self.info_text.delete('1.0', tk.END)
            self.info_text.insert(tk.END, info.strip())
            self.info_text.config(state='disabled')
            self.link_button.config(state='normal' if game.site_url else 'disabled')
            # ẨN/HIỆN thanh cuộn dọc/ngang info_text tùy nội dung
            self._update_info_scrollbar_visibility()
        else:
            # Không chọn game nào: ẩn thanh cuộn ngang/dọc
            self.info_scrollbar_h.grid_remove()
            self.info_scrollbar_v.grid_remove()
            self._update_info_scrollbar_visibility()

    def _update_datetime_label(self):
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.datetime_label.config(text=f"🕒 {now}")
        self.datetime_label.after(1000, self._update_datetime_label)

    def _update_info_scrollbar_visibility(self):
        # Kiểm tra nếu nội dung info_text đủ dài để cuộn thì hiện, ngược lại ẩn
        self.info_text.update_idletasks()
        first_y, last_y = self.info_text.yview()
        first_x, last_x = self.info_text.xview()
        content = self.info_text.get('1.0', 'end-1c').strip()
        # Thanh cuộn dọc
        if last_y - first_y < 1.0 and content:
            if not self.info_scrollbar_v.winfo_ismapped():
                self.info_scrollbar_v.grid(row=0, column=1, sticky='ns')
        else:
            if self.info_scrollbar_v.winfo_ismapped():
                self.info_scrollbar_v.grid_remove()
        # Thanh cuộn ngang
        if last_x - first_x < 1.0 and content:
            if not self.info_scrollbar_h.winfo_ismapped():
                self.info_scrollbar_h.grid(row=1, column=0, sticky='ew')
        else:
            if self.info_scrollbar_h.winfo_ismapped():
                self.info_scrollbar_h.grid_remove()

        # Nếu đã hiện thanh cuộn ngang mà sau khi kéo giãn đủ rộng thì ẩn ngay lập tức
        self.info_text.after(50, self._auto_hide_info_scrollbar_h)

    def _auto_hide_info_scrollbar_h(self):
        # Tự động ẩn thanh cuộn ngang nếu không còn cần thiết (sau khi kéo giãn)
        self.info_text.update_idletasks()
        first_x, last_x = self.info_text.xview()
        content = self.info_text.get('1.0', 'end-1c').strip()
        if last_x - first_x >= 1.0 or not content:
            if self.info_scrollbar_h.winfo_ismapped():
                self.info_scrollbar_h.grid_remove()

    def _on_listbox_scroll(self, *args):
        self.scrollbar_v.set(*args)
        # Ẩn/hiện scrollbar_v động
        self.listbox.update_idletasks()
        first, last = self.listbox.yview()
        if last - first < 1.0:
            if not self.scrollbar_v.winfo_ismapped():
                self.scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            if self.scrollbar_v.winfo_ismapped():
                self.scrollbar_v.pack_forget()

    def _on_info_scroll(self, *args):
        self.info_scrollbar_v.set(*args)
        # Ẩn/hiện scrollbar_v động
        self.info_text.update_idletasks()
        first, last = self.info_text.yview()
        if last - first < 1.0:
            if not self.info_scrollbar_v.winfo_ismapped():
                self.info_scrollbar_v.grid(row=0, column=1, sticky='ns')
        else:
            if self.info_scrollbar_v.winfo_ismapped():
                self.info_scrollbar_v.grid_remove()

    def _handle_listbox_mousewheel_bind(self):
        # Chỉ bind mousewheel nếu có thể cuộn
        if self.listbox.yview()[1] - self.listbox.yview()[0] < 1.0:
            self.listbox.bind("<MouseWheel>", self._on_listbox_mousewheel)
        else:
            self.listbox.unbind("<MouseWheel>")

    def _handle_listbox_mousewheel_unbind(self):
        self.listbox.unbind("<MouseWheel>")

    def _handle_info_mousewheel_bind(self):
        # Chỉ bind mousewheel nếu có thể cuộn
        if self.info_text.yview()[1] - self.info_text.yview()[0] < 1.0:
            self.info_text.bind("<MouseWheel>", self._on_info_mousewheel)
        else:
            self.info_text.unbind("<MouseWheel>")

    def _handle_info_mousewheel_unbind(self):
        self.info_text.unbind("<MouseWheel>")

    # --- THÊM HÀM NÀY để tránh lỗi AttributeError ---
    def _on_info_mousewheel(self, event):
        # Cho phép cuộn nội dung info_text bằng chuột
        if event.delta:
            self.info_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _set_default_pane_size(self):
        paned = self._paned
        total = paned.winfo_width()
        if total <= 1:
            self.master.after(100, self._set_default_pane_size)
            return
        left_size = int(total * self._default_pane_ratio)
        try:
            paned.sashpos(0, left_size)
            self._pane_initialized = True
        except Exception:
            pass

    def _reset_pane_size(self, event=None):
        # Đặt lại tỷ lệ mặc định khi double click vào sash
        self._set_default_pane_size()

    def _on_pane_configure(self, event=None):
        # Nếu chưa từng set mặc định, set lại khi lần đầu render
        if not self._pane_initialized:
            self._set_default_pane_size()
        # ...nếu đã set rồi thì không làm gì, tránh nhảy sash khi resize bình thường...

    def on_user_change(self, event=None):
        # Khi admin chọn user khác, load lại manager cho user đó
        username = self.selected_username.get()
        from models import GameManager
        self.manager = GameManager(username=username)
        self._original_order = None  # Reset lại thứ tự gốc
        self.refresh_list()