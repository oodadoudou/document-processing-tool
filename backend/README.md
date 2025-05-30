# Backend (Flask)

## 1. 安装 Python

### macOS / Linux 推荐

使用 pyenv 或 Anaconda：

```bash
# pyenv 安装
curl https://pyenv.run | bash
# 安装 Python 3.10 及以上
pyenv install 3.10.14
pyenv global 3.10.14
python --version
```

### Windows 推荐

- 访问 [Python 官网](https://www.python.org/downloads/) 下载并安装。
- 安装时勾选"Add Python to PATH"。
- 命令行输入：

```powershell
python --version
```

## 2. 创建并激活虚拟环境

### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows
```powershell
python -m venv venv
.\venv\Scripts\activate
```

## 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 4. 启动后端 Server

```bash
python app.py
```

## 5. 说明
- 开发模式：直接运行 `python app.py`，支持热重载（如需可用 Flask 的 debug 模式）。
- 生产模式：建议用 gunicorn/uwsgi 等部署，或用 PyInstaller 打包为可执行文件。 