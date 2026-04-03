import yaml
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from definitions import load_config

# 读取配置文件
config = load_config()

app = Flask(__name__)
app.secret_key = config['server']['secret_key']
server_port = config['server']['port']

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

@app.route('/backend')
def backend():
    # 检查是否登录
    #if 'username' not in session:
    #    flash('请先登录', 'error')
    #    return redirect(url_for('login'))

    # 模拟用户数据
    user = {
        #'username': session['username'],
        'username': 'username',
        'role': '管理员',
        'created_at': '2024-01-01',
        'points': 1000,
        'server_count': 2,
        'total_cost': 500
    }

    # 模拟公告数据
    announcements = [
        {
            'title': '系统维护通知',
            'date': '2024-01-15',
            'content': '系统将于本周六凌晨2:00-4:00进行维护升级，届时服务可能短暂中断，请提前做好准备。'
        },
        {
            'title': '新功能上线',
            'date': '2024-01-10',
            'content': '我们很高兴地宣布，新的服务器控制面板功能已上线！现在您可以更方便地管理您的服务器。'
        }
    ]

    # 模拟用户服务器数据
    user_servers = [
        {
            'name': '阿明的生存服',
            'version': '1.20.1',
            'port': '25565',
            'status': 'running',
            'players': '5/20'
        },
        {
            'name': 'PVP 竞技场',
            'version': '1.19.4',
            'port': '25566',
            'status': 'stopped',
            'players': '0/10'
        }
    ]

    return render_template('backend.html', user=user, announcements=announcements, user_servers=user_servers)

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