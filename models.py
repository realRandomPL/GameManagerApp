import json
import os
import datetime

# --- game.py ---
class Game:
    def __init__(self, title, description, released=None, cover_url=None, developers=None, genres=None, platforms=None, site_url=None, aliases=None, id=None, created_at=None):
        self.id = id
        self.title = title
        self.description = description
        self.released = released
        self.cover_url = cover_url
        self.developers = developers
        self.genres = genres
        self.platforms = platforms
        self.site_url = site_url
        self.aliases = aliases
        self.created_at = created_at

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'released': self.released,
            'cover_url': self.cover_url,
            'developers': self.developers,
            'genres': self.genres,
            'platforms': self.platforms,
            'site_url': self.site_url,
            'aliases': self.aliases
        }


# --- user.py ---
class User:
    def __init__(self, username, password, role='user'):
        self.username = username
        self.password = password  # Trong thực tế, nên lưu hash mật khẩu!
        self.role = role

    def to_dict(self):
        return {'username': self.username, 'password': self.password, 'role': self.role}

# --- game_manager.py ---


class GameManager:
    def __init__(self, path='games.json', username=None):
        # Nếu là admin thì luôn dùng games.json mặc định
        if username == "123":
            self.path = "data/games.json"
        elif username:
            self.path = f"data/games_{username}.json"
        else:
            self.path = path
        self.games = []
        self.load_games()

    def _clean_game_dict(self, g):
        """Làm sạch dữ liệu game dictionary, chuyển string rỗng thành None"""
        
        # Các trường cần làm sạch
        fields = ["developers", "genres", "platforms", "description", 
                  "released", "cover_url", "site_url", "aliases"]
        
        for field in fields:
            value = g.get(field)
            # Chuyển None hoặc chuỗi rỗng thành None
            if not value or (isinstance(value, str) and not value.strip()):
                g[field] = None
        
        return g

    def load_games(self):
        """Tải danh sách games từ file JSON"""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.games = []
                for g in data:
                    # Làm sạch dữ liệu trước khi tạo Game object
                    cleaned_data = self._clean_game_dict(g)
                    try:
                        game = Game(**cleaned_data)
                        self.games.append(game)
                    except Exception as e:
                        print(f"Lỗi tạo game từ dữ liệu {cleaned_data}: {e}")
                        continue
        except FileNotFoundError:
            print(f"File {self.path} không tồn tại. Tạo danh sách trống.")
            self.games = []
        except json.JSONDecodeError as e:
            print(f"Lỗi đọc file JSON {self.path}: {e}")
            self.games = []
        except Exception as e:
            print(f"Lỗi không xác định khi tải games: {e}")
            self.games = []
    
    def next_id(self):
        """Tự động tạo ID tiếp theo"""
        if not self.games:
            return 1
        return max(g.id for g in self.games if g.id is not None) + 1


    def save_games(self):
        """Lưu danh sách games vào file JSON"""
        try:
            data = []
            for game in self.games:
                game_dict = game.to_dict()
                # Làm sạch dữ liệu trước khi lưu
                cleaned_dict = self._clean_game_dict(game_dict)
                # Loại bỏ các trường None để file JSON gọn hơn
                cleaned_dict = {k: v for k, v in cleaned_dict.items() if v is not None}
                data.append(cleaned_dict)
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Đã lưu {len(self.games)} games vào {self.path}")
        except Exception as e:
            print(f"Lỗi lưu file: {e}")
            raise

    def add_game(self, game):
        """Thêm game mới"""
        if not isinstance(game, Game):
            raise ValueError("Tham số phải là instance của Game")
        # Thêm trường created_at nếu chưa có
        if not hasattr(game, "created_at") or not getattr(game, "created_at", None):
            game.created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Kiểm tra trùng lặp ID
        if any(g.id == game.id for g in self.games):
            raise ValueError(f"Game với ID {game.id} đã tồn tại")
        
        self.games.append(game)
        self.save_games()
        print(f"Đã thêm game: {game.title}")

    def update_game(self, game):
        """Cập nhật thông tin game"""
        if not isinstance(game, Game):
            raise ValueError("Tham số phải là instance của Game")
        
        for i, g in enumerate(self.games):
            if g.id == game.id:
                self.games[i] = game
                self.save_games()
                print(f"Đã cập nhật game: {game.title}")
                return
        
        raise ValueError(f"Không tìm thấy game với ID {game.id}")

    def delete_game(self, game_id):
        """Xóa game theo ID"""
        original_count = len(self.games)
        self.games = [g for g in self.games if g.id != game_id]
        
        if len(self.games) < original_count:
            self.save_games()
            print(f"Đã xóa game với ID: {game_id}")
        else:
            raise ValueError(f"Không tìm thấy game với ID {game_id}")

    def find_game_by_id(self, game_id):
        """Tìm game theo ID"""
        for game in self.games:
            if game.id == game_id:
                return game
        return None

    def find_games_by_title(self, title):
        """Tìm games theo tên (không phân biệt hoa thường)"""
        if not title:
            return []
        
        title_lower = title.lower()
        return [game for game in self.games 
                if title_lower in game.title.lower()]

    def find_games_by_developer(self, developer):
        """Tìm games theo nhà phát triển"""
        if not developer:
            return []
        
        developer_lower = developer.lower()
        return [game for game in self.games 
                if game.developers and developer_lower in game.developers.lower()]

    def find_games_by_genre(self, genre):
        """Tìm games theo thể loại"""
        if not genre:
            return []
        
        genre_lower = genre.lower()
        return [game for game in self.games 
                if game.genres and genre_lower in game.genres.lower()]

    def get_all_developers(self):
        """Lấy danh sách tất cả nhà phát triển"""
        developers = set()
        for game in self.games:
            if game.developers:
                # Tách các nhà phát triển bằng dấu phẩy
                dev_list = [d.strip() for d in game.developers.split(',')]
                developers.update(dev_list)
        return sorted(list(developers))

    def get_all_genres(self):
        """Lấy danh sách tất cả thể loại"""
        genres = set()
        for game in self.games:
            if game.genres:
                # Tách các thể loại bằng dấu phẩy
                genre_list = [g.strip() for g in game.genres.split(',')]
                genres.update(genre_list)
        return sorted(list(genres))

    def get_all_platforms(self):
        """Lấy danh sách tất cả nền tảng"""
        platforms = set()
        for game in self.games:
            if game.platforms:
                # Tách các nền tảng bằng dấu phẩy
                platform_list = [p.strip() for p in game.platforms.split(',')]
                platforms.update(platform_list)
        return sorted(list(platforms))

    def get_games_count(self):
        """Lấy số lượng games"""
        return len(self.games)

    def get_games_by_year(self, year):
        """Lấy games theo năm phát hành"""
        if not year:
            return []
        
        year_str = str(year)
        return [game for game in self.games 
                if game.released and year_str in game.released]

    def validate_game_data(self, game_data):
        """Kiểm tra tính hợp lệ của dữ liệu game"""
        required_fields = ['id', 'title']
        
        for field in required_fields:
            if field not in game_data or not game_data[field]:
                raise ValueError(f"Trường {field} là bắt buộc")
        
        # Kiểm tra ID có phải là số không
        try:
            int(game_data['id'])
        except (ValueError, TypeError):
            raise ValueError("ID phải là một số")
        
        return True

    def import_games_from_dict(self, games_data):
        """Import games từ dictionary hoặc list"""
        if not isinstance(games_data, list):
            raise ValueError("Dữ liệu phải là một list")
        
        imported_count = 0
        errors = []
        
        for i, game_data in enumerate(games_data):
            try:
                # Validate dữ liệu
                self.validate_game_data(game_data)
                
                # Làm sạch dữ liệu
                cleaned_data = self._clean_game_dict(game_data.copy())
                
                # Tạo game object
                game = Game(**cleaned_data)
                
                # Kiểm tra trùng lặp
                if not any(g.id == game.id for g in self.games):
                    self.games.append(game)
                    imported_count += 1
                else:
                    errors.append(f"Game {i+1}: ID {game.id} đã tồn tại")
                    
            except Exception as e:
                errors.append(f"Game {i+1}: {str(e)}")
        
        if imported_count > 0:
            self.save_games()
        
        return {
            'imported': imported_count,
            'errors': errors,
            'total': len(games_data)
        }

    def export_games_to_dict(self):
        """Export games thành dictionary"""
        return [game.to_dict() for game in self.games]

    def get_statistics(self):
        """Lấy thống kê về collection"""
        total_games = len(self.games)
        
        # Đếm games theo năm
        years = {}
        for game in self.games:
            if game.released:
                # Lấy năm từ chuỗi released
                year_match = None
                for word in game.released.split():
                    if word.isdigit() and len(word) == 4:
                        year_match = word
                        break
                
                if year_match:
                    years[year_match] = years.get(year_match, 0) + 1
        
        return {
            'total_games': total_games,
            'total_developers': len(self.get_all_developers()),
            'total_genres': len(self.get_all_genres()),
            'total_platforms': len(self.get_all_platforms()),
            'games_by_year': years,
            'games_with_cover': len([g for g in self.games if g.cover_url]),
            'games_with_description': len([g for g in self.games if g.description])
        }

# --- user_manager.py ---

class UserManager:
    def __init__(self, path='data/users.json'):
        self.path = path
        self._ensure_file()
        self.users = self._load()

        # Tạo admin mặc định nếu chưa có
        if not any(u.username == "123" for u in self.users):
            print("Khởi tạo admin mặc định: 123/123")
            self.add_user(User("123", "123", "admin"))

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, 'w') as f:
                json.dump([], f)

    def _load(self):
        with open(self.path, 'r') as f:
            data = json.load(f)
        return [User(**u) for u in data]

    def _save(self):
        with open(self.path, 'w') as f:
            json.dump([u.to_dict() for u in self.users], f, indent=2)

    def authenticate(self, username, password):
        """
        Kiểm tra thông tin đăng nhập, trả về User nếu hợp lệ, ngược lại None
        """
        for u in self.users:
            if u.username == username and u.password == password:
                return u
        return None

    def add_user(self, user):
        """Thêm người dùng mới vào hệ thống"""
        self.users.append(user)
        self._save()

    def update_user(self, username, **kwargs):
        for u in self.users:
            if u.username == username and u.username != "123":
                for k, v in kwargs.items():
                    if hasattr(u, k):
                        setattr(u, k, v)
                self._save()
                return True
        return False

    def user_exists(self, username):
        return any(u.username == username for u in self.users)

    def register_user(self, username, password, role='user'):
        role = 'user'  # Ép vai trò luôn là user, không cho phép admin khi đăng ký
        if self.user_exists(username):
            return False  # Username đã tồn tại
        self.add_user(User(username, password, role))
        return True