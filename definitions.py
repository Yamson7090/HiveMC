import yaml
import sqlite3
import pymysql
from sqlalchemy import Column, Integer, String
from flask_sqlalchemy import SQLAlchemy
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

config = load_config()

if config['database']['type'] == 'sqlite':

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
        if not cursor.execute("SELECT * FROM users WHERE username='admin'").fetchone():
            add_user('admin', '123456', if_admin=1, db_name=db_name)
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
    

    def login(username, password, db_name='users.db'):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username=?', (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result and check_password_hash(result[0], password):
            return True
        return False

elif config['database']['type'] == 'mysql':
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
        engine = SQLAlchemy.create_engine(database_uri, pool_pre_ping=True, echo=False)
        Session = SQLAlchemy.orm.sessionmaker(bind=engine)
        db_session = SQLAlchemy.orm.scoped_session(Session)
        Base = SQLAlchemy.ext.declarative.declarative_base()
        Base.query = db_session.query_property() # 为 Base 添加 query 属性，方便查询

        return db_session, engine, Base
else:
    print("❌ 错误：不支持的数据库类型，请检查配置文件中的 database.type 设置。")
    exit(1)