import yaml
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 读取配置文件
with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

app = Flask(__name__)
app.secret_key = 'sjhkSBVDhzsdgvilasyglvaughr'  # 用于会话加密
server_port = 5000

@app.route("/")
def home():
    # 检查是否登录
    current_user = session.get('username')
    
    # 模拟服务器列表
    active_servers = [
        {"name": "阿明的生存服", "owner": "阿明", "status": "running"},
        {"name": "PVP 竞技场", "owner": "大神K", "status": "stopped"},
    ]
    return render_template('index.html', servers=active_servers, user=current_user, info=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 1. 检查用户是否存在
        if username in users_db:
            # 2. 验证密码哈希
            if check_password_hash(users_db[username], password):
                session['username'] = username
                flash('登录成功！欢迎回来，' + username, 'success')
                return redirect(url_for('index'))
            else:
                flash('密码错误', 'error')
        else:
            flash('用户不存在', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('已退出登录', 'info')
    return redirect(url_for('index'))

@app.route("/status")
def status():
    return "Server is running!"

def main():
    print("启动服务器，监听端口",server_port,"...")
    app.run(host='0.0.0.0', port=server_port, debug=False)

if __name__ == "__main__":
    main()