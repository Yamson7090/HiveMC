from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime

import definitions
from definitions import load_config, load_announcements, start_server, read_mc_output

# 读取配置文件
config = load_config()

if config['database']['type'] == 'sqlite':
    from definitions import sqlite_ready, login, add_user
    sqlite_ready()
elif config['database']['type'] == 'mysql':
    from definitions import mysql_ready, login, add_user
    mysql_ready()
else:
    print("❌ 错误：不支持的数据库类型，请检查配置文件中的 database.type 设置。")
    exit(1)

app = Flask(__name__)
app.secret_key = config['server']['secret_key']
server_port = config['server']['port']

@app.route("/")
def index():
    # 检查是否登录
    current_user = session.get('username')
    if current_user:
        flash(f"欢迎回来，{current_user}！", 'success')
    elif current_user is None:
        flash("欢迎访问 Minecraft 服务器控制面板！请登录以管理您的服务器。", 'info')
    
    '''
    # 模拟服务器列表
    active_servers = [
        {"name": "阿明的生存服", "owner": "阿明", "status": "running"},
        {"name": "PVP 竞技场", "owner": "大神K", "status": "stopped"},
    ]'''
    return render_template('index.html', user=current_user, info=None)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if login(username, password):
            session['username'] = username
            flash('登录成功！', 'success')
            return redirect(url_for('backend'))
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # 验证输入
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('密码长度至少为6位', 'error')
            return render_template('register.html')

        # 添加用户到数据库
        try:
            add_user(username, password)
            flash('注册成功！请登录', 'success')
            return redirect(url_for('login_page'))
        except Exception as e:
            flash('注册失败，用户名可能已存在', 'error')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/backend')
def backend():
    # 检查是否登录
    if session.get('username') is None:
        flash('请先登录', 'error')
        return redirect(url_for('login_page'))
    else :
        user = {'username': session['username']}

    # 公告
    announcements = load_announcements()[:3]
    # 模拟用户服务器数据
    user_servers = [
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

@app.route('/api/start', methods=['POST'])
def api_start():
    # 启动服务端接口
    msg = start_server()
    return jsonify({'status': 'success', 'msg': msg})

@app.route('/api/console', methods=['GET'])
def get_console_logs():
    """获取最新 的控制台日志 (AJAX 轮询)"""
    logs = []
    # 尝试从队列中取出所有积压的日志
    while not output_queue.empty():
        logs.append(output_queue.get())
    return jsonify({'logs': logs})

@app.route('/api/command', methods=['POST'])
def send_command():
    """发送指令到 Minecraft"""
    global mc_process
    cmd = request.json.get('command')
    
    if not cmd:
        return jsonify({'status': 'error', 'msg': '指令为空'})
    
    if mc_process and mc_process.poll() is None:
        try:
            # 将指令写入标准输入，并加上换行符模拟回车
            mc_process.stdin.write((cmd + "\n").encode('utf-8'))
            mc_process.stdin.flush()
            return jsonify({'status': 'success', 'msg': '指令已发送'})
        except Exception as e:
            return jsonify({'status': 'error', 'msg': str(e)})
    else:
        return jsonify({'status': 'error', 'msg': '服务端未运行，无法发送指令'})

def main():
    print("启动服务器，监听端口",server_port,"...")
    app.run(host='0.0.0.0', port=server_port, debug=False)

if __name__ == "__main__":
    main()