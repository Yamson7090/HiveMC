import yaml
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def load_config():
    try:
        with open('config.yml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        with open('config.yml', 'w', encoding='utf-8') as file:
            with open('defaults/default_config.yml', 'r', encoding='utf-8') as default_file:
                default_config = default_file.read()
            file.write(default_config)
        print("❌ 错误：找不到 config.yml 文件，已重新生成默认配置，请根据文件内容进行修改。")
        exit(1)

def sqlite_ready(db_name='users.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            if_admin INTEGER DEFAULT 0,
            servers TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()
    def add_user(username, password, if_admin=0, db_name='users.db'):
        password_hash = generate_password_hash(password)
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, if_admin) VALUES (?, ?, ?)
            ''', (username, password_hash, if_admin))
            conn.commit()
            print(f"✅ 用户 '{username}' 已添加到数据库")
        except sqlite3.IntegrityError:
            print(f"⚠️ 用户 '{username}' 已存在，无法重复添加")
        finally:
            cursor.close()
            conn.close()


"""MySQL 数据库连接"""
def mysql_ready():
    config = load_config()
    db_user = config['database']['user']
    db_pass = config['database']['password']
    db_host = config['database']['host']
    db_port = config['database']['port']
    db_name = config['database']['name']

    # 拼接连接字符串
    database_uri = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 初始化数据库
    db = SQLAlchemy(app)

    # --- 4. 定义模型 (User) ---
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(50), unique=True, nullable=False)
        password_hash = db.Column(db.String(128), nullable=False)

        def set_password(self, password):
            self.password_hash = generate_password_hash(password)

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)

    # --- 5. 路由与初始化 ---
    def init_db():
        with app.app_context():
            db.create_all()
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin')
                admin.set_password('123456')
                db.session.add(admin)
                db.session.commit()
                print("✅ 数据库已连接并初始化完成")