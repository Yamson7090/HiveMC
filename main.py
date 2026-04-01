import flask

app = flask.Flask(__name__)
server_port = 5000

@app.route("/")
def home():
    return flask.render_template('welcome.html')

# 这里预留一个登录页面的路由，后续可以实现登录逻辑
@app.route('/login')
def login():
    return "登录页面开发中..."

@app.route("/status")
def status():
    return "Server is running!"

def main():
    print("启动服务器，监听端口",server_port,"...")
    app.run(host='0.0.0.0', port=server_port, debug=False)

if __name__ == "__main__":
    main()