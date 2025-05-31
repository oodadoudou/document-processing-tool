# File Process Tools | 文件处理工具

[English](#english) | [中文](#chinese)

<a name="english"></a>
# File Process Tools

A powerful file processing toolkit that provides PDF processing, file compression, file conversion, and other functionalities.

## Features

**PDF Processing**
* **PDF Merge**: Combine multiple PDF files into a single PDF document.
* **PDF Page Processing**: Support deleting first page, last page, first and last pages, or specific single/multiple pages from PDF files.
* **PDF to Image**: Convert each page of a PDF file into separate image files (PNG, JPG formats).
* **PDF Text Extraction**: Extract text content from PDF files and save as TXT files, supporting multiple output formats.
* **PDF Encryption/Decryption**: Set password protection for PDF files or decrypt encrypted PDF files.
* **PDF File Repair**: Attempt to repair damaged or unopenable PDF files.
* **Images to PDF**: Merge multiple image files into a PDF document, with options to adjust image size, DPI, and compression during conversion.

**File and Folder Management**
* **Batch Filename Processing**:
    * Add prefix/suffix to filenames.
    * Remove specified characters or pattern matches from filenames.
    * Rename items based on specified patterns (files, folders, or both).
    * Extract number sequences from filenames.
    * Support undoing the last rename operation (if recorded).
* **Folder Flattening**: Move all files from subfolders to the parent folder's root directory.
* **Folder Encryption/Decryption**: Encrypt and compress folders and their contents, with corresponding decrypt and decompress operations.
* **Create ISO from Subfolders**: Create separate ISO image files for each subfolder under a specified parent directory.
* **File Type Organization**: Automatically organize files into corresponding subfolders based on their extensions (e.g., .pdf, .epub, .txt).

**File Conversion and Merging**
* **EPUB to TXT**: Convert EPUB format ebooks to plain text TXT files.
* **TXT File Merging**: Combine multiple TXT files into a single TXT file.

## Download and Installation

1. Download the latest `File Process Tools Setup.exe` from the [Releases](../../releases) page
2. Double-click the installer
3. Follow the installation wizard
4. Launch the program from the Start menu or desktop shortcut

## System Requirements

- Windows 10/11 64-bit

## Usage Instructions

1. After launching the program, select the desired function from the left menu
2. Drag and drop or select files according to the interface prompts
3. Set the appropriate parameters
4. Click the process button to start the operation

## Development

### Tech Stack
- Frontend: React + TypeScript + Electron
- Backend: Python + Flask
- Packaging: electron-builder + PyInstaller

### Local Development
```bash
# Frontend Development
cd frontend
yarn install
yarn start

# Backend Development
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## FAQ

1. Program won't start
   - Ensure running as administrator
   - Check if antivirus is blocking
   - Verify Windows Defender isn't blocking the program

2. File processing fails
   - Ensure files aren't in use by other programs
   - Check file read/write permissions
   - Verify sufficient disk space

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Submit a Pull Request

## License

MIT License - See [LICENSE](LICENSE) file

---

<a name="chinese"></a>
# 文件处理工具

一个强大的文件处理工具集，提供PDF处理、文件压缩、文件转换等功能。

## 功能特点

**PDF 处理**
* **PDF 合并**: 将多个 PDF 文件合并成一个单一的 PDF 文档。
* **PDF 页面处理**: 支持删除 PDF 文件的首页、末页、首末页，或删除指定的单个/多个页面。
* **PDF 转图片**: 将 PDF 文件的每一页转换为独立的图片文件（如 PNG, JPG 格式）。
* **PDF 文本提取**: 从 PDF 文件中提取文本内容并保存为 TXT 文件，支持多种输出格式。
* **PDF 加密与解密**: 为 PDF 文件设置密码进行加密，或对已加密的 PDF 文件进行解密。
* **PDF 文件修复**: 尝试修复损坏或无法打开的 PDF 文件。
* **图片文件转 PDF**: 将多个图片文件合并并转换为一个 PDF 文档，支持在转换过程中调整图片尺寸和 DPI，并可对图片进行压缩。

**文件与文件夹管理**
* **文件名批量处理**:
    * 添加文件名前缀/后缀。
    * 删除文件名中的指定字符或匹配模式的字符。
    * 根据指定模式（文件、文件夹或两者）统一重命名项目。
    * 提取文件名中的数字序列。
    * 支持撤销上一次的重命名操作（若有记录）。
* **文件夹层级展平**: 将指定文件夹内所有子文件夹中的文件移动到该父文件夹的根目录。
* **文件夹加密压缩/解压缩**: 对文件夹及其内容进行加密压缩处理，并支持对应的解密解压缩操作。
* **从子文件夹创建 ISO 镜像**: 将指定父目录下的各个子文件夹分别创建为独立的 ISO 镜像文件。
* **文件按类型分组整理**: 根据文件的扩展名（如 .pdf, .epub, .txt 等），自动将文件整理到相应的子文件夹中。

**文件转换与合并**
* **EPUB 转 TXT**: 将 EPUB 格式的电子书文件转换为纯文本 TXT 文件。
* **TXT 文件合并**: 将多个 TXT 文本文件合并成一个单一的 TXT 文件。

## 下载和安装

1. 从 [Releases](../../releases) 页面下载最新的 `File Process Tools Setup.exe`
2. 双击安装程序
3. 按照安装向导完成安装
4. 从开始菜单或桌面快捷方式启动程序

## 系统要求

- Windows 10/11 64位

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

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件 