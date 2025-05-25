📚 Document Processing Tool (文档处理工具)
这是一个多功能的命令行文件批处理系统，旨在简化日常的文档管理和格式转换任务。它支持多种文件类型（如 PDF, TXT, EPUB, 图片, 压缩包）的操作，包括重命名、合并、裁剪、加密、解密、格式转换以及目录整理等。

This is a versatile command-line file batch processing system designed to streamline everyday document management and format conversion tasks. It supports various file types (e.g., PDF, TXT, EPUB, images, archives) and operations including renaming, merging, trimming, encryption, decryption, format conversion, and directory organization.

✨ 主要功能 / ✨ Key Features
压缩包解压 / Archive Extraction: 支持 zip, 7z, rar, tar, gz, bz2, xz, iso 等格式的自动解压，支持密码尝试。
Automatically extracts zip, 7z, rar, tar, gz, bz2, xz, iso formats, with support for password attempts.

目录扁平化 / Directory Flattening: 将子目录中的所有文件提取到根目录，并删除空目录。
Extracts all files from subdirectories to the root directory and deletes empty subdirectories.

PDF 页面操作 / PDF Page Operations:

裁剪页面 / Trim Pages: 删除 PDF 的首页、尾页或指定页数。
Deletes the first, last, or a specified number of pages from PDFs.

加密/解密 / Encrypt/Decrypt: 使用密码对 PDF 文件进行 AES-256 加密或解密。
Encrypts or decrypts PDF files using a password with AES-256 encryption.

修复 / Repair: 尝试通过重新保存来修复损坏或结构异常的 PDF 文件。
Attempts to repair corrupted or structurally problematic PDF files by re-saving them.

文件合并 / File Merging: 合并同类型文件（PDF, TXT）。
Combines files of the same type (PDF, TXT).

文件名处理 / Filename Processing:

删除指定字符 / Delete Characters: 从文件名中删除匹配的字符或正则表达式。
Deletes specific characters or regex patterns from filenames.

添加前缀 / Add Prefix: 为文件或文件夹添加指定前缀（支持智能处理）。
Adds a specified prefix to files or folders (supports smart processing).

数字重命名 / Numeric Renaming: 提取文件名中的数字并重命名文件。
Extracts numbers from filenames and renames files.

智能重命名 / Smart Renaming: 根据文件名首字母（支持中文拼音首字母）进行重命名。
Renames files/folders based on the first letter of their name (supports Chinese Pinyin initials).

反向重命名 / Reverse Renaming: 移除特定格式（X-）的文件名或文件夹前缀。
Removes specific prefixes (e.g., X-) from filenames or folder names.

格式转换 / Format Conversion:

EPUB 到 TXT / EPUB to TXT: 将 EPUB 电子书转换为纯文本。
Converts EPUB e-books to plain text.

PDF 到 TXT / PDF to TXT: 将 PDF 转换为可编辑的纯文本（支持标准、紧凑、清理模式）。
Converts PDFs to editable plain text (supports standard, compact, and clean modes).

PDF 到图片 / PDF to Image: 将 PDF 页面转换为 PNG 或 JPG 格式图片。
Converts PDF pages into PNG or JPG image formats.

图片到 PDF / Image to PDF: 将多张图片合并为 PDF 文档。
Combines multiple images into a single PDF document.

图片处理 / Image Processing:

图片超压缩 / Super Compression: 对图片进行高效压缩并生成 PDF，支持有损/无损模式。
Highly compresses images and generates a PDF, supporting lossy/lossless modes.

🚀 快速开始 / 🚀 Quick Start
1. 克隆仓库 / 1. Clone the Repository
git clone https://github.com/YourUsername/document-processing-tool.git
cd document-processing-tool

2. 安装依赖 / 2. Install Dependencies
本项目依赖一些 Python 库。您可以使用 pip 和提供的 requirements.txt 文件进行安装。

This project relies on several Python libraries. You can install them using pip and the provided requirements.txt file.

pip install -r requirements.txt

3. 运行脚本 / 3. Run the Script
脚本将自动检测并处理其执行目录下的文件。PDF 输出将在当前目录下创建一个名为 processed_pdf 的文件夹。

The script will automatically detect and process files in its execution directory. PDF output will be saved to a folder named processed_pdf created in the current directory.

常用命令示例 / Common Command Examples:
解压所有压缩包： / Extract all archives:

python file_process_tools.py -X

将所有子目录文件扁平化到当前目录： / Flatten all subdirectory files into the current directory:

python file_process_tools.py -F

删除 PDF 文件的首页和尾页： / Delete the first and last pages of PDF files:

python file_process_tools.py -T lf

将当前目录下所有 PDF 合并为 combined_books.pdf： / Merge all PDFs in the current directory into combined_books.pdf:

python file_process_tools.py -C p combined_books

从文件名中删除 _copy 字符串： / Delete the string _copy from filenames:

python file_process_tools.py -D "_copy"

为 PDF 和 TXT 文件添加 REPORT_ 前缀： / Add the prefix REPORT_ to PDF and TXT files:

python file_process_tools.py -P "REPORT_"

对所有文件和文件夹进行智能重命名（根据首字母）： / Perform smart renaming for all files and folders (based on first letter):

python file_process_tools.py -R

将所有 EPUB 文件转换为 TXT 文件： / Convert all EPUB files to TXT files:

python file_process_tools.py --epubTtxt

将 PDF 转换为图片（JPG 格式，DPI 150）： / Convert PDFs to images (JPG format, 150 DPI):

python file_process_tools.py --pdfTimg --img-format jpg --dpi 150

加密 PDF 文件： / Encrypt PDF files:

python file_process_tools.py --encode-pdf YourStrongPassword

修复 PDF 文件： / Repair PDF files:

python file_process_tools.py --repair-pdf

压缩图片并生成 PDF (有损模式)： / Compress images and generate PDF (lossy mode):

python file_process_tools.py --compress-images my_compressed_document.pdf --lossy

查看所有可用参数及详细说明： / To view all available parameters and detailed descriptions:

python file_process_tools.py -h

⚠️ 注意事项 / ⚠️ Important Notes
个人使用工具: 本工具主要为个人方便使用而设计，不保证在所有复杂场景下完美无误。
Personal Use Tool: This tool is primarily designed for personal convenience and does not guarantee flawless operation in all complex scenarios.

备份数据: 在执行任何修改文件的操作前，强烈建议备份您的数据，以防数据丢失。
Backup Data: It is strongly recommended to back up your data before performing any file-modifying operations to prevent data loss.

路径设置: 脚本将处理其执行目录下的文件，所有输出（包括 processed_pdf 文件夹）也将位于此目录下。
Path Settings: The script will process files in its execution directory, and all outputs (including the processed_pdf folder) will also be located in this directory.

不可逆操作: 某些操作（如 flatten-dirs、delete）是不可逆的，请谨慎使用。
Irreversible Operations: Some operations (e.g., flatten-dirs, delete) are irreversible. Please use them with caution.

权限问题: 确保脚本对执行目录及其子目录有读写权限。
Permissions: Ensure the script has read/write permissions for the execution directory and its subdirectories.

🤝 贡献 / 🤝 Contributing
欢迎通过 Pull Request 提交改进和新功能！如果您发现任何 Bug 或有功能建议，请提交 Issue。

Contributions via Pull Requests for improvements and new features are welcome! If you find any bugs or have feature suggestions, please open an Issue.

📄 许可证 / 📄 License
本项目采用 MIT 许可证 发布。

This project is licensed under the MIT License.