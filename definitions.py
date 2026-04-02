

def load_config():
    try:
        with open('config.yml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print("❌ 错误：找不到 config.yml 文件，已重新生成默认配置。")
        exit(1)