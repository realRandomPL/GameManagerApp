import urllib.request
from tkinter import BOTH
from tkinter.ttk import Combobox, Style, Button as TtkButton, Entry as TtkEntry, Frame as TtkFrame, Checkbutton as TtkCheckbutton, Label as TtkLabel
from tkinter.simpledialog import Dialog
from PIL import Image
from PIL import ImageTk
from tkinter import LEFT, RIGHT, Scrollbar, Text, Toplevel, Y, messagebox, simpledialog, PhotoImage, Label as TkLabel
import os
import tkinter as tk
import webbrowser
import io

from models import Game

def safe_text(val):
    if isinstance(val, list):
        return ', '.join(str(v).strip() for v in val if str(v).strip()) or 'Không rõ'
    if isinstance(val, str) and val.strip():
        return val.strip()
    return 'Không rõ'

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
        # Sửa style cho Checkbutton để khi hover sẽ đổi màu nền/viền cho dễ nhìn
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
        # ...existing code...

    def __init__(self, master, manager, user, api_client=None, is_admin=False, on_logout=None):
        self.master = master
        self.manager = manager
        self.user = user
        self.api = api_client
        self.is_admin = is_admin
        self.on_logout = on_logout

        self._setup_style()
        self.genre_filter = ""
        self.dev_filter = ""
        self._original_order = None  # Lưu thứ tự gốc ban đầu (list các id)
        self._original_id_map = {}   # Lưu mapping id -> số thứ tự gốc

        self.master.configure(bg="#181a20")

        # --- Thêm canvas cuộn cho toàn bộ giao diện ---
        self.canvas = tk.Canvas(master, bg="#181a20", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar = Scrollbar(master, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # --- Sửa: Sử dụng pack(fill='both', expand=True) cho content_frame để tự động giãn ---
        self.content_frame = TtkFrame(self.canvas, style="Card.TFrame")
        self.content_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        self.content_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        # --- Luôn bind mousewheel cho canvas khi không hover listbox/info_text ---
        self._canvas_mousewheel_enabled = True
        self.canvas.bind("<Enter>", lambda e: self._enable_canvas_mousewheel())
        self.canvas.bind("<Leave>", lambda e: self._disable_canvas_mousewheel())

        # --- Các thành phần giao diện đặt vào content_frame ---
        filter_frame = TtkFrame(self.content_frame, style="Card.TFrame")
        filter_frame.pack(padx=20, pady=15, fill='x')

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

        # --- Sửa lại: chỉ tích mặc định từ A-Z, logic cũ cho các trường khác ---
        self.sort_order = tk.BooleanVar(value=True)
        TtkCheckbutton(filter_frame, text="Tăng dần A->Z", variable=self.sort_order, style="Modern.TCheckbutton").pack(side=tk.LEFT, padx=10)
        self.sort_order.trace('w', self.on_sort_change)

        # Đăng xuất
        if self.on_logout:
            self._modern_button(filter_frame, 'Đăng xuất', self.on_logout).pack(side=tk.RIGHT, padx=5)

        list_frame = TtkFrame(self.content_frame, style="Card.TFrame")
        list_frame.pack(padx=20, pady=10, fill='both', expand=True)  # expand=True

        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(list_frame, width=50, yscrollcommand=scrollbar.set,
                                  font=("Segoe UI", 12), bg="#23262e", fg="#f5f6fa",
                                  selectbackground="#4f8cff", selectforeground="#fff",
                                  highlightthickness=0, bd=0, relief="flat", activestyle='none')
        self.listbox.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 10), pady=5)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.listbox.bind("<Enter>", lambda e: self._disable_canvas_mousewheel())
        self.listbox.bind("<Leave>", lambda e: self._enable_canvas_mousewheel())
        self.listbox.bind("<Enter>", lambda e: self._handle_listbox_mousewheel_bind())
        self.listbox.bind("<Leave>", lambda e: self._handle_listbox_mousewheel_unbind())

        btn_frame = TtkFrame(self.content_frame, style="Card.TFrame")
        btn_frame.pack(padx=20, pady=8)

        self._modern_button(btn_frame, 'Thêm', self.add).pack(side=tk.LEFT, padx=5)
        self._modern_button(btn_frame, 'Sửa', self.edit).pack(side=tk.LEFT, padx=5)
        self._modern_button(btn_frame, 'Xóa', self.delete).pack(side=tk.LEFT, padx=5)
        self._modern_button(btn_frame, 'Tìm API', self.search_api).pack(side=tk.LEFT, padx=5)
        self._modern_button(btn_frame, 'Xem JSON', self.show_json).pack(side=tk.LEFT, padx=5)

        # --- Hình nền cho vùng thông tin khi chưa chọn game ---
        self.bg_image = None
        self.bg_label = None

        self.cover_label = TtkLabel(self.content_frame, style="Card.TLabel")
        self.cover_label.pack(padx=20, pady=10)

        info_frame = TtkFrame(self.content_frame, style="Card.TFrame")
        info_frame.pack(padx=20, pady=5, fill='x')

        self.info_text = Text(info_frame, height=10, wrap='word', font=("Segoe UI", 11),
                              bg="#23262e", fg="#f5f6fa", bd=0, relief="flat", highlightthickness=0)
        self.info_text.pack(side=tk.LEFT, fill='x', expand=True)
        self.info_text.config(state='disabled')

        # --- Không còn label hình nền phía dưới info_text ---
        # self.bg_label = None

        self.link_button = TtkButton(self.content_frame, text='Mở liên kết chi tiết', command=self.open_site,
                                     style="Accent.TButton", state='disabled', cursor="hand2")
        self.link_button.pack(pady=(0, 15))

        self.selected_game = None

        self.update_genre_combobox()
        self.refresh_list()

    def _modern_button(self, parent, text, command):
        return TtkButton(parent, text=text, command=command, style="Modern.TButton", cursor="hand2")

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        # Lưu thứ tự gốc ban đầu nếu chưa có
        if self._original_order is None:
            self._original_order = sorted([g.id for g in self.manager.games], key=lambda x: x)
        # Luôn lấy danh sách games đúng thứ tự gốc ban đầu (id tăng dần)
        all_games = sorted(self.manager.games, key=lambda g: self._original_order.index(g.id) if g.id in self._original_order else 1e9)
        games = all_games

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

        self.update_genre_combobox()
        self.cover_label.config(image='', text='')
        self.cover_label.image = None
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        self.info_text.config(state='disabled')
        self.link_button.config(state='disabled')
        self.selected_game = None

        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

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
                cover_url=None,  # Không nhập cover_url, aliases
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
            # Không sửa cover_url, aliases
            self.manager.update_game(game)
            self.update_genre_combobox()
            self.refresh_list()

    def delete(self):
        if not self.is_admin:
            messagebox.showwarning('Không đủ quyền', 'Chỉ admin mới có thể xóa game')
            return
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning('Chưa chọn game', 'Vui lòng chọn game để xóa')
            return
        index = sel[0]
        game = self.sorted_games[index] if hasattr(self, 'sorted_games') else self.manager.games[index]
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
            dialog.title("Tìm trên API")
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

                lb = tk.Listbox(content_frame, width=50, selectmode=tk.SINGLE, font=("Segoe UI", 11), bg="#23272f", fg="#e0e6f0", selectbackground="#3a3f4b", highlightthickness=0, bd=0, relief="flat")
                lb.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 10), pady=0)
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
        txt = Text(top, wrap='none', font=("Consolas", 11), bg="#23272f", fg="#e0e6f0", bd=0, relief="flat", highlightthickness=0)
        txt.pack(side=LEFT, fill=BOTH, expand=True)
        scroll = Scrollbar(top, command=txt.yview)
        scroll.pack(side=RIGHT, fill=Y)
        txt.config(yscrollcommand=scroll.set)
        with open(self.manager.path, 'r', encoding='utf-8') as f:
            data = f.read()
        txt.insert('1.0', data)

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
                try:
                    with urllib.request.urlopen(url) as u:
                        raw_data = u.read()
                    im = Image.open(io.BytesIO(raw_data))
                    im = im.resize((150, 200))
                    photo = ImageTk.PhotoImage(im)
                    self.cover_label.config(image=photo, text='')
                    self.cover_label.image = photo
                except Exception as e:
                    self.cover_label.config(image='', text='Không tải được ảnh')
                    self.cover_label.image = None
            else:
                self.cover_label.config(image='', text='Không có ảnh')
                self.cover_label.image = None
            # Hiện thông tin game (không hiện url bìa)
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
        else:
            # ...existing code...
            pass

    def open_site(self):
        if self.selected_game and self.selected_game.site_url:
            webbrowser.open(self.selected_game.site_url)

    def _on_canvas_configure(self, event):
        # Đảm bảo content_frame luôn rộng bằng canvas khi thay đổi kích thước
        self.canvas.itemconfig(self.content_window, width=event.width)

    def _handle_listbox_mousewheel_bind(self):
        # Nếu listbox có thể cuộn (nhiều item, xuất hiện thanh cuộn), chỉ bind mousewheel cho listbox
        if self.listbox.yview()[1] - self.listbox.yview()[0] < 1.0:
            self._disable_canvas_mousewheel()
            self.listbox.bind("<MouseWheel>", self._on_listbox_mousewheel)
        else:
            # Nếu không thể cuộn, để canvas nhận mousewheel
            self._enable_canvas_mousewheel()
            self.listbox.unbind("<MouseWheel>")

    def _handle_listbox_mousewheel_unbind(self):
        self.listbox.unbind("<MouseWheel>")
        self._enable_canvas_mousewheel()

    def _handle_info_mousewheel_bind(self):
        # Nếu info_text có thể cuộn (nội dung dài), chỉ bind mousewheel cho info_text
        # Nếu không thể cuộn (nội dung vừa đủ hoặc trống), để canvas nhận mousewheel
        if self.info_text.yview()[1] - self.info_text.yview()[0] < 1.0:
            self._disable_canvas_mousewheel()
            self.info_text.bind("<MouseWheel>", self._on_info_mousewheel)
        else:
            self._enable_canvas_mousewheel()
            self.info_text.unbind("<MouseWheel>")

    def _handle_info_mousewheel_unbind(self):
        self.info_text.unbind("<MouseWheel>")
        self._enable_canvas_mousewheel()

    def _enable_canvas_mousewheel(self):
        if not self._canvas_mousewheel_enabled:
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
            self._canvas_mousewheel_enabled = True

    def _disable_canvas_mousewheel(self):
        if self._canvas_mousewheel_enabled:
            self.canvas.unbind_all("<MouseWheel>")
            self._canvas_mousewheel_enabled = False

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_listbox_mousewheel(self, event):
        self.listbox.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _on_info_mousewheel(self, event):
        self.info_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _bind_canvas_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_canvas_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")

    def _bind_info_mousewheel(self):
        self.info_text.bind_all("<MouseWheel>", self._on_info_mousewheel)

    def _unbind_info_mousewheel(self):
        self.info_text.unbind_all("<MouseWheel>")

    def _sort_and_reindex_games(self):
        # Sắp xếp games theo chữ cái đầu của title (A-Z, không phân biệt hoa thường)
        self.manager.games.sort(key=lambda g: (g.title or '').lower())
        # Đánh lại id theo thứ tự mới
        for idx, game in enumerate(self.manager.games, 1):
            game.id = idx
        self.manager.save_games()

# --- login_view.py ---

class LoginView(Dialog):
    def body(self, master):
        self.winfo_toplevel().title("Đăng nhập")
        master.configure(bg="#23272f")
        tk.Label(master, text='Tên đăng nhập:', bg="#23272f", fg="#e6e6f0", font=("Segoe UI", 11)).grid(row=0, sticky='e')
        tk.Label(master, text='Mật khẩu:', bg="#23272f", fg="#e6e6f0", font=("Segoe UI", 11)).grid(row=1, sticky='e')

        self.e1 = TtkEntry(master, font=("Segoe UI", 11))
        self.e2 = TtkEntry(master, show='*', font=("Segoe UI", 11))

        self.e1.grid(row=0, column=1, padx=5, pady=5)
        self.e2.grid(row=1, column=1, padx=5, pady=5)
        self.e1.focus_set()
        self.e1.configure(insertbackground="#4f8cff")
        self.e2.configure(insertbackground="#4f8cff")
        self.e1.bind('<Return>', lambda e: self.e2.focus_set())
        self.e2.bind('<Return>', lambda e: self.ok())
        return self.e1

    def apply(self):
        self.result = {'username': self.e1.get(), 'password': self.e2.get()}

# --- game_form.py ---

class GameForm(Dialog):
    def __init__(self, parent, game=None):
        self.game = game
        super().__init__(parent, title='Form Game')

    def body(self, master):
        # Đổi màu nền toàn bộ dialog, loại bỏ viền trắng xung quanh, đồng bộ với app
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
        frm.pack(padx=0, pady=0, fill='both', expand=True)  # Không padding để sát viền

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

        # Gán giá trị nếu sửa
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
        # Sử dụng pack thay cho grid để tránh lỗi, đồng bộ màu sắc
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