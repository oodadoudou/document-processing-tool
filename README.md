# File Process Tools

一个强大的文件处理工具集，提供PDF处理、文件压缩、文件转换等功能。

## 功能特点

- PDF处理
  - PDF合并
  - PDF拆分
  - PDF转图片
  - PDF提取文本
- 文件压缩
  - 7z压缩/解压
  - 图片压缩
- 文件转换
  - Word转PDF
  - 图片格式转换
- 中文文件名处理
  - 拼音转换
  - 繁简转换

## 下载和安装

1. 从 [Releases](../../releases) 页面下载最新的 `File Process Tools Setup.exe`
2. 双击安装程序
3. 按照安装向导完成安装
4. 从开始菜单或桌面快捷方式启动程序

## 系统要求

- Windows 10/11 64位
- 4GB RAM 或以上
- 500MB 可用磁盘空间

## 使用说明

1. 启动程序后，从左侧菜单选择所需功能
2. 根据界面提示拖拽文件或选择文件
3. 设置相应参数
4. 点击处理按钮开始操作

## 开发相关

### 技术栈
- 前端：React + TypeScript + Electron
- 后端：Python + Flask
- 打包：electron-builder + PyInstaller

### 本地开发
```bash
# 前端开发
cd frontend
yarn install
yarn start

# 后端开发
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## 常见问题

1. 程序无法启动
   - 确保以管理员身份运行
   - 检查杀毒软件是否拦截
   - 确保Windows Defender未阻止程序运行

2. 文件处理失败
   - 确保文件未被其他程序占用
   - 检查文件是否有读写权限
   - 确保磁盘有足够空间

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

## 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## License

MIT License - 详见 [LICENSE](LICENSE) 文件 