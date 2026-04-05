import yaml
import sqlite3
import pymysql
import json
import os
import subprocess
import threading
import queue
import time
from werkzeug.security import generate_password_hash, check_password_hash

mc_process = None
output_queue = queue.Queue() # 用于暂存控制台输出的队列

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

ANNOUNCE_FILE = 'announcements.json'
def load_announcements():
    """加载公告数据"""
    if os.path.exists(ANNOUNCE_FILE):
        try:
            with open(ANNOUNCE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取公告文件错误: {e}")
            # 如果文件损坏或为空，返回一个空列表
            return []
    else:
        # 如果文件不存在，返回一个示例公告（或者空列表）
        with open(ANNOUNCE_FILE, 'w', encoding='utf-8') as file:
            with open('defaults/default_announcements.json', 'r', encoding='utf-8') as default_file:
                default_announcements = default_file.read()
            file.write(default_announcements)
        print("❌ 错误：找不到 announcements.json 文件，已重新生成默认配置，请根据文件内容进行修改。")
        return load_announcements()


# --- 全局变量 ---
mc_process = None
output_queue = queue.Queue() # 用于暂存控制台输出的队列

def read_mc_output():
    """后台线程：持续读取 Minecraft 的输出并放入队列"""
    global mc_process
    if mc_process:
        # 逐行读取标准输出
        for line in mc_process.stdout:
            if line:
                decoded_line = line.strip()
                output_queue.put(decoded_line)
        
        # 进程结束后的处理
        output_queue.put("[系统] Minecraft 服务端已关闭。")

def start_server(MC_START_CMD, server_id):
    """启动 Minecraft 服务端"""
    global mc_process
    if mc_process and mc_process.poll() is None:
        return "服务端已经在运行中！"
    
    try:
        # 启动进程，捕获 stdout 和 stdin
        # text=True 表示以文本模式运行，方便处理字符串
        mc_process = subprocess.Popen(
            MC_START_CMD, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, # 将错误输出也合并到标准输出
            cwd=os.path.join(os.getcwd(), "servers", server_id),
            bufsize=1,
            text=True,
            encoding='utf-8'
        )
        
        # 启动读取线程
        thread = threading.Thread(target=read_mc_output, daemon=True)
        thread.start()
        return mc_process.pid
    except Exception as e:
        return f"启动失败: {str(e)}"

config = load_config()

# 根据配置文件选择数据库类型并导入相关函数
if config['database']['type'] == 'sqlite':
    db_path = config['database']['sqlite']['db_path']
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

    def add_user(username, password, if_admin=0, db_name=db_path):
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
    

    def login(username, password, db_name=db_path):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username=?', (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result and check_password_hash(result[0], password):
            return True
        else:
            return False

elif config['database']['type'] == 'mysql':
    """MySQL 数据库连接"""
    config = load_config()
    db_user = config['database']['mysql']['user']
    db_pass = config['database']['mysql']['password']
    db_host = config['database']['mysql']['host']
    db_port = config['database']['mysql']['port']
    db_name = config['database']['mysql']['name']

    def add_user(username, password, if_admin=0):
        password_hash = generate_password_hash(password)
        conn = pymysql.connect(host=db_host, port=db_port, user=db_user, password=db_pass, database=db_name)
        cursor = conn.cursor()
        try:
            sql_insert = "INSERT INTO users (username, password_hash, if_admin) VALUES (%s, %s, %s)"
            cursor.execute(sql_insert, (username, password_hash, if_admin))
            conn.commit()
            print(f"✅ 用户 '{username}' 已添加到数据库")
        except pymysql.err.IntegrityError:
            print(f"⚠️ 用户 '{username}' 已存在")
        finally:
            cursor.close()
            conn.close()

    def mysql_ready():
        conn = pymysql.connect(host=db_host, port=db_port, user=db_user, password=db_pass)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
        conn.select_db(db_name)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                if_admin TINYINT(1) DEFAULT 0,
                servers TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        ''')
        # 检查 admin 用户是否存在
        sql_check = "SELECT id FROM users WHERE username = %s"
        cursor.execute(sql_check, ('admin',))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if not result:
            add_user('admin', '123456', if_admin=1)
    
    def login(username, password):
        conn = pymysql.connect(host=db_host, port=db_port, user=db_user, password=db_pass, database=db_name)
        cursor = conn.cursor()
        sql_select = "SELECT password_hash FROM users WHERE username = %s"
        cursor.execute(sql_select, (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result and check_password_hash(result[0], password):
            return True
        else:
            return False

else:
    print("❌ 错误：不支持的数据库类型，请检查配置文件中的 database.type 设置。")
    exit(1)