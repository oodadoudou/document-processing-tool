# 📚 Document Processing Tool (文件处理工具)

A multi-functional command-line tool for batch processing various document and file types. This tool simplifies common file management tasks such as renaming, format conversion, PDF manipulation, archiving, and more.

一个多功能的命令行工具，用于批量处理各种文档和文件类型。本工具简化了常见的文件管理任务，例如文件重命名、格式转换、PDF 操作、归档等等。

---

## ⚠️ Important Disclaimer (重要免责声明)

**This tool is developed for personal use and convenience. While tested, any automated file processing carries inherent risks of data loss or corruption if not used correctly.**

**Before using this tool, you are HIGHLY RECOMMENDED to back up all your important files and directories. The developer holds no responsibility for any direct or indirect data loss or damage resulting from the use of this tool.**

**此工具为个人开发和便利而设。尽管经过测试，但任何自动化文件处理如果使用不当，都存在数据丢失或损坏的固有风险。**

**在使用本工具之前，强烈建议您备份所有重要文件和目录。开发者对因使用本工具而造成的任何直接或间接的数据丢失或损坏不承担任何责任。**

---

## ✨ Features (功能特性)

* **Core Operations (核心操作)**:
    * PDF Page Trimming (PDF 页面裁剪)
    * Directory Flattening (目录扁平化)
    * File Combination (文件合并: PDF, TXT, EPUB)
* **File Operations (文件操作)**:
    * Filename Cleanup (文件名清理，支持正则表达式)
    * Add File Prefix (添加文件前缀)
    * Numeric Renaming (数字重命名)
    * Intelligent Renaming (智能重命名)
    * Reverse Renaming (反向重命名)
* **Format Conversion (格式转换)**:
    * EPUB to Plain Text (EPUB 到纯文本)
    * PDF to Editable Text (PDF 到可编辑文本)
    * PDF to Image (PDF 到图片)
    * Image to PDF (图片到 PDF)
    * Image Compression (图片压缩并生成PDF)
* **Security Operations (安全操作)**:
    * PDF Decryption (PDF 解密)
    * PDF Encryption (PDF 加密)
    * Archive Extraction (档案解压)
    * PDF Repair (PDF 修复)
* **Other Utilities (其他实用工具)**:
    * ISO Creator (ISO 镜像创建 - macOS specific)
    * PDF Specific Page Remover (PDF 特定页面删除)
    * File Organizer (文件整理归类)

---

## ⚙️ Prerequisites (先决条件)

* **Python**: Python 3.12+ is recommended.
* **Dependencies**: All Python dependencies are listed in `requirements.txt`.
* **macOS Specific**: For `--iso-creator` (`-ISO`) functionality, `hdiutil` must be available on your system (which is usually pre-installed on macOS).

* **Python**: 推荐使用 Python 3.12+。
* **依赖项**: 所有 Python 依赖项列在 `requirements.txt` 中。
* **macOS 特定**: 对于 `--iso-creator` (`-ISO`) 功能，您的系统上必须安装 `hdiutil`（通常在 macOS 上预装）。

---

## 🚀 Installation (安装)

## 🚀 Installation (安装)

1.  **Clone the repository (克隆仓库)**:
    ```bash
    git clone [https://github.com/oodadoudou/document-processing-tool.git](https://github.com/oodadoudou/document-processing-tool.git)
    cd document-processing-tool
    ```

2.  **Create a virtual environment (创建虚拟环境 - 推荐)**:
    ```bash
    python3 -m venv document_tool_env
    source document_tool_env/bin/activate  # On Windows, use `document_tool_env\Scripts\activate`
    ```

3.  **Install dependencies (安装依赖项)**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execution Location (执行位置)**:
    This script is designed to process files within the **current directory** where the command is executed. Therefore, please navigate to the folder containing the files you wish to process before running the script.
    For convenience, it is highly recommended to set up a shortcut command or add the script's directory to your system's PATH environment variable. This will allow you to run the script from any directory directly.

    本脚本设计为只处理执行命令的**当前目录**下的所有文件。因此，请您在需要处理文件所在的文件夹中执行该脚本。
    为了方便使用，强烈建议您为该脚本设定一个快捷命令，或将其目录添加到您的系统 PATH 环境变量中。这样，您就可以在任何目录下直接运行此脚本。

---

---

## 📝 Usage (使用方法)

The tool is executed via the command line using `python file_process_tools.py [OPTIONS]`.

本工具通过命令行执行，使用 `python file_process_tools.py [选项]`。

**General Syntax (通用语法)**:
```bash
python file_process_tools.py [COMMAND] [PARAMETERS]
```

**To view all available commands and their descriptions (查看所有可用命令及其描述)**:
```bash
python file_process_tools.py --help
# 或
python file_process_tools.py -h
```

---

## 🚀 Detailed Command Reference (详细命令参考)

This section provides detailed explanations and examples for each command. Remember to replace `python file_process_tools.py` with your actual execution command.

本节提供每个命令的详细说明和示例。请记住，将 `python file_process_tools.py` 替换为您的实际执行命令。

### [Core Operations] (核心操作)

These operations modify file structure and are recommended to execute first.

这些操作会修改文件结构，建议优先执行。

#### 1. PDF Page Cropping (PDF 页面裁剪)

* **Long/Short Arg**: `--trim-pages` / `-TP`
* **Description**: Deletes pages from the beginning or end of PDF files. This is an atomic operation that preserves the original file by creating a new one.
* **用法**:
    * 删除前 N 页: `-TP f [N]` (默认 N=1)
    * 删除后 N 页: `-TP l [N]` (默认 N=1)
    * 删除第一页和最后一页: `-TP lf`
* **Description**: 从 PDF 文件的开头或结尾删除页面。这是一个原子操作，通过创建新文件来保留原始文件。
* **Usage Examples (使用示例)**:
    ```bash
    # Deletes the last 3 pages of all PDFs in the current directory
    # 删除当前目录下所有 PDF 的最后 3 页
    python file_process_tools.py -TP l 3

    # Deletes the first page of all PDFs
    # 删除所有 PDF 的第一页
    python file_process_tools.py --trim-pages f

    # Deletes the first and last page of all PDFs
    # 删除所有 PDF 的第一页和最后一页
    python file_process_tools.py -TP lf
    ```

#### 2. Directory Flattening (目录扁平化)

* **Long/Short Arg**: `--flatten-dirs` / `-FD`
* **Description**: Extracts all files from subdirectories to the input directory, forces deletion of empty directories, and automatically handles filename conflicts. This is an irreversible operation; backup is recommended.
* **Description**: 将所有文件从子目录提取到输入目录，强制删除空目录，并自动处理文件名冲突。此操作不可逆转；建议备份。
* **Usage Examples (使用示例)**:
    ```bash
    # Flattens the directory structure
    # 扁平化目录结构
    python file_process_tools.py -FD
    ```

#### 3. Merge Files Operation (合并文件操作)

* **Long/Short Arg**: `--combine` / `-CB`
* **Description**: Merges multiple files of the same type (PDF, TXT, EPUB) into a single file.
* **Description**: 将多个相同类型的文件（PDF、TXT、EPUB）合并为一个文件。
* **Usage Examples (使用示例)**:
    ```bash
    # Merges all PDF files into 'combined.pdf'
    # 将所有 PDF 文件合并到 'combined.pdf'
    python file_process_tools.py -CB p

    # Merges all EPUB files into 'library.epub'
    # 将所有 EPUB 文件合并到 'library.epub'
    python file_process_tools.py --combine e library
    ```

### [File Operations] (文件操作)

File renaming and batch processing functions.

文件重命名和批量处理功能。

#### 1. Filename Cleanup (文件名清理)

* **Long/Short Arg**: `--delete` / `-DL`
* **Description**: Deletes all matching characters from filenames. Supports regular expressions. Affects both files and directories. Irreversible operation; testing recommended.
* **Description**: 从文件名中删除所有匹配的字符。支持正则表达式。影响文件和目录。操作不可逆；建议测试。
* **Usage Examples (使用示例)**:
    ```bash
    # Deletes "_copy" from filenames
    # 从文件名中删除 "_copy"
    python file_process_tools.py -DL "_copy"

    # Deletes all square brackets "[]" from filenames
    # 从文件名中删除所有方括号 "[]"
    python file_process_tools.py --delete "[\\[\\]]"
    ```

#### 2. Add File Prefix (添加文件前缀)

* **Long/Short Arg**: `--add-prefix` / `-AP`
* **Description**: Adds a specified prefix to PDF/TXT filenames. Automatically skips files that already have the prefix. Supports secondary processing (e.g., with numeric renaming).
* **Description**: 为 PDF/TXT 文件名添加指定前缀。自动跳过已包含前缀的文件。支持二次处理（例如与数字重命名结合使用）。
* **Usage Examples (使用示例)**:
    ```bash
    # Adds "2024Q1_" as a prefix
    # 添加 "2024Q1_" 作为前缀
    python file_process_tools.py -AP "2024Q1_"

    # Adds "FINAL_" as a prefix
    # 添加 "FINAL_" 作为前缀
    python file_process_tools.py --add-prefix "FINAL_"
    ```

#### 3. Numeric Renaming (数字重命名)

* **Long/Short Arg**: `--extract-numbers` / `-EN`
* **Description**: Extracts numbers and hyphens (`-`, `.`) from filenames for renaming.
* **Description**: 从文件名中提取数字和连字符（`-`、`.`）进行重命名。
* **Usage Examples (使用示例)**:
    ```bash
    # Renames files based on extracted numbers
    # 根据提取的数字重命名文件
    python file_process_tools.py -EN
    ```

#### 4. Rename Operation (重命名操作)

* **Long/Short Arg**: `--rename` / `-RN`
* **Description**: Processes both directories and files, or only folders/files based on the mode.
* **Description**: 根据模式处理目录和文件，或仅处理文件夹/文件。
* **Usage Examples (使用示例)**:
    ```bash
    # Processes both directories and files
    # 处理目录和文件
    python file_process_tools.py -RN

    # Renames files only
    # 仅重命名文件
    python file_process_tools.py --rename files
    ```

#### 5. Reverse Renaming (反向重命名)

* **Long/Short Arg**: `--reverse-rename` / `-RR`
* **Description**: Removes prefixes in the format `X-xxxx` from filenames and folder names. Automatically handles name conflicts.
* **Description**: 从文件名和文件夹名中移除 `X-xxxx` 格式的前缀。自动处理名称冲突。
* **Usage Examples (使用示例)**:
    ```bash
    # Renames 'B-Report.pdf' to 'Report.pdf', 'D-Data/' to 'Data/'
    # 将 'B-Report.pdf' 重命名为 'Report.pdf'，将 'D-Data/' 重命名为 'Data/'
    python file_process_tools.py -RR
    ```

#### 6. Encode Folders (编码文件夹)

* **Long/Short Arg**: `--encode-folders` / `-EF`
* **Description**: Encodes and double-compresses subfolders into `.z删ip` files. Optionally provide a password for 7z encryption (default: 1111).
* **Description**: 将子文件夹双重压缩并编码为 `.z删ip` 文件。可选地提供一个密码用于 7z 加密（默认密码为 `1111`）。
* **Usage Examples (使用示例)**:
    ```bash
    # Encodes folders with the default password (1111)
    # 使用默认密码 (1111) 编码文件夹
    python file_process_tools.py -EF

    # Encodes folders with a custom password 'my_password'
    # 使用自定义密码 'my_password' 编码文件夹
    python file_process_tools.py -EF my_password
    ```

#### 7. Decode Folders (解码文件夹)

* **Long/Short Arg**: `--decode-folders` / `-DF`
* **Description**: Decodes and double-decompresses `.z删ip` files into original folders. Optionally provide a password for 7z decryption (default: 1111).
* **Description**: 将 `.z删ip` 文件双重解压并解码回原始文件夹结构。可选地提供一个密码用于 7z 解密（默认密码为 `1111`）。
* **Usage Examples (使用示例)**:
    ```bash
    # Decodes folders with the default password (1111)
    # 使用默认密码 (1111) 解码文件夹
    python file_process_tools.py -DF

    # Decodes folders with a custom password 'my_password'
    # 使用自定义密码 'my_password' 解码文件夹
    python file_process_tools.py -DF my_password
    ```

### [Format Conversion] (格式转换)

Document format conversion functions.

文档格式转换功能。

#### 1. EPUB to Plain Text (EPUB 到纯文本)

* **Long/Short Arg**: `--epubTtxt` / `-ET`
* **Description**: Converts EPUB files to plain text, retaining chapter structure and filtering empty paragraphs.
* **Description**: 将 EPUB 文件转换为纯文本，保留章节结构并过滤空段落。
* **Usage Examples (使用示例)**:
    ```bash
    # Converts all EPUBs to TXT files
    # 将所有 EPUB 转换为 TXT 文件
    python file_process_tools.py -ET
    ```

#### 2. PDF to Editable Text (PDF 到可编辑文本)

* **Long/Short Arg**: `--pdfTtxt` / `-PT`
* **Description**: Converts PDF files to editable plain text. Additional parameters for text format (`--txt-format` / `-TF`).
* **Description**: 将 PDF 文件转换为可编辑的纯文本。文本格式的附加参数（`--txt-format` / `-TF`）。
* **Usage Examples (使用示例)**:
    ```bash
    # Converts all PDFs to TXT in standard format
    # 将所有 PDF 以标准格式转换为 TXT
    python file_process_tools.py -PT

    # Converts all PDFs to TXT in compact format
    # 将所有 PDF 以紧凑格式转换为 TXT
    python file_process_tools.py --pdfTtxt --txt-format compact
    # 或
    python file_process_tools.py -PT -TF compact
    ```

#### 3. PDF to Image (PDF 到图片)

* **Long/Short Arg**: `--pdfTimg` / `-PI`
* **Description**: Converts PDF pages to images. Additional parameters for image format (`--img-format` / `-IF`) and resolution (`--dpi` / `-DP`). Creates a separate directory for each PDF.
* **Description**: 将 PDF 页面转换为图片。图片格式（`--img-format` / `-IF`）和分辨率（`--dpi` / `-DP`）的附加参数。每个 PDF 会创建一个单独的目录。
* **Usage Examples (使用示例)**:
    ```bash
    # Converts all PDFs to PNG images with 300 DPI
    # 将所有 PDF 转换为 300 DPI 的 PNG 图片
    python file_process_tools.py -PI

    # Converts all PDFs to JPG images with 150 DPI
    # 将所有 PDF 转换为 150 DPI 的 JPG 图片
    python file_process_tools.py --pdfTimg --img-format jpg --dpi 150
    # 或
    python file_process_tools.py -PI -IF jpg -DP 150
    ```

#### 4. Image to PDF (图片到 PDF)

* **Long/Short Arg**: `--imgTpdf` / `-IP`
* **Description**: Combines images into a single PDF file. Additional parameters for PDF page width (`--pdf-width` / `-PW`) and DPI (`--pdf-dpi` / `-PD`).
* **Description**: 将图片合并为单个 PDF 文件。PDF 页面宽度（`--pdf-width` / `-PW`）和 DPI（`--pdf-dpi` / `-PD`）的附加参数。
* **Usage Examples (使用示例)**:
    ```bash
    # Converts all images in the current directory to 'combined_images.pdf'
    # 将当前目录下所有图片转换为 'combined_images.pdf'
    python file_process_tools.py -IP

    # Converts images to PDF with a page width of 1200px and 200 DPI
    # 将图片转换为 PDF，页面宽度为 1200 像素，200 DPI
    python file_process_tools.py --imgTpdf --pdf-width 1200 --pdf-dpi 200
    # 或
    python file_process_tools.py -IP -PW 1200 -PD 200
    ```

#### 5. Text Conversion Format (文本转换格式)

* **Long/Short Arg**: `--txt-format` / `-TF`
* **Description**: Sets the output format for text conversions (e.g., from PDF to TXT).
* **Options**: `standard`, `compact`, `clean`
* **Description**: 设置文本转换（例如从 PDF 到 TXT）的输出格式。
* **选项**: `standard`（标准）、`compact`（紧凑）、`clean`（清理）
* **Usage Examples (使用示例)**: (See `pdfTtxt` examples above)
* **使用示例**: （请参阅上面的 `pdfTtxt` 示例）

#### 6. Image Output Format (图片输出格式)

* **Long/Short Arg**: `--img-format` / `-IF`
* **Description**: Sets the output format for image conversions (e.g., from PDF to Image).
* **Options**: `png`, `jpg`
* **Description**: 设置图片转换（例如从 PDF 到图片）的输出格式。
* **选项**: `png`, `jpg`
* **Usage Examples (使用示例)**: (See `pdfTimg` examples above)
* **使用示例**: （请参阅上面的 `pdfTimg` 示例）

#### 7. Image Output Resolution (图片输出分辨率)

* **Long/Short Arg**: `--dpi` / `-DP`
* **Description**: Sets the DPI (dots per inch) for image output.
* **Type**: `int` (default: 300)
* **Description**: 设置图片输出的 DPI（每英寸点数）。
* **类型**: `int` (默认: 300)
* **Usage Examples (使用示例)**: (See `pdfTimg` examples above)
* **使用示例**: （请参阅上面的 `pdfTimg` 示例）

#### 8. PDF Page Width (PDF 页面宽度)

* **Long/Short Arg**: `--pdf-width` / `-PW`
* **Description**: Sets the width in pixels for PDF pages when converting from images to PDF.
* **Type**: `int` (default: 1500)
* **Description**: 设置从图片转换为 PDF 时，PDF 页面的宽度（以像素为单位）。
* **类型**: `int` (默认: 1500)
* **Usage Examples (使用示例)**: (See `imgTpdf` examples above)
* **使用示例**: （请参阅上面的 `imgTpdf` 示例）

#### 9. PDF Output DPI (PDF 输出 DPI)

* **Long/Short Arg**: `--pdf-dpi` / `-PD`
* **Description**: Sets the DPI for the output PDF when converting from images to PDF.
* **Type**: `int` (default: 300)
* **Description**: 设置从图片转换为 PDF 时，输出 PDF 的 DPI。
* **类型**: `int` (默认: 300)
* **Usage Examples (使用示例)**: (See `imgTpdf` examples above)
* **使用示例**: （请参阅上面的 `imgTpdf` 示例）

### [Security Operations] (安全操作)

#### 1. Decrypts PDF Files (解密 PDF 文件)

* **Long/Short Arg**: `--decode-pdf` / `-DCP`
* **Description**: Decrypts PDF files using the specified password.
* **Description**: 使用指定密码解密 PDF 文件。
* **Usage Examples (使用示例)**:
    ```bash
    # Decrypts PDFs with password "mysecret"
    # 使用密码 "mysecret" 解密 PDF
    python file_process_tools.py -DCP "mysecret"
    ```

#### 2. Encrypts PDF Files (加密 PDF 文件)

* **Long/Short Arg**: `--encode-pdf` / `-ECP`
* **Description**: Encrypts PDF files using the specified password. Encrypted files will have restrictions on printing, copying, and modification.
* **Description**: 使用指定密码加密 PDF 文件。加密文件将限制打印、复制和修改权限。
* **Usage Examples (使用示例)**:
    ```bash
    # Encrypts PDFs with password "securepass"
    # 使用密码 "securepass" 加密 PDF
    python file_process_tools.py --encode-pdf "securepass"
    # 或
    python file_process_tools.py -ECP "securepass"
    ```

#### 3. Extracts Archive Files (解压档案文件)

* **Long/Short Arg**: `--extract-archives` / `-XA`
* **Description**: Extracts various archive file types (zip, 7z, rar, tar, gz, bz2, xz, iso). Default password for archives is `1111`.
* **Description**: 解压各种档案文件类型（zip, 7z, rar, tar, gz, bz2, xz, iso）。默认档案密码为 `1111`。
* **Usage Examples (使用示例)**:
    ```bash
    # Extracts all supported archives in the current directory
    # 解压当前目录下所有支持的档案
    python file_process_tools.py -XA
    ```

#### 4. Repairs PDF Files (修复 PDF 文件)

* **Long/Short Arg**: `--repair-pdf` / `-RPDF`
* **Description**: Attempts to repair PDF internal structure by re-saving, which can resolve merging or processing issues.
* **Description**: 尝试通过重新保存来修复 PDF 内部结构，这可以解决合并或处理问题。
* **Usage Examples (使用示例)**:
    ```bash
    # Repairs all PDFs in the current directory
    # 修复当前目录下所有 PDF
    python file_process_tools.py -RPDF
    ```

### [Other Operations] (其他操作)

#### 1. Compresses Images and Generates PDF (压缩图片并生成 PDF)

* **Long/Short Arg**: `--compress-images` / `-CI`
* **Description**: Compresses images and combines them into a PDF. Default is lossless compression. Can be combined with `--lossy` for lossy compression.
* **Description**: 压缩图片并将其合并到 PDF 中。默认为无损压缩。可与 `--lossy` 结合使用以进行有损压缩。
* **Usage Examples (使用示例)**:
    ```bash
    # Lossless compression of images into 'output.pdf'
    # 将图片无损压缩到 'output.pdf'
    python file_process_tools.py -CI output.pdf

    # Lossy compression of images into 'report.pdf'
    # 将图片有损压缩到 'report.pdf'
    python file_process_tools.py --compress-images report.pdf --lossy
    # 或
    python file_process_tools.py -CI report.pdf -LSS
    ```

#### 2. Enables Lossy Compression Mode (启用有损压缩模式)

* **Long/Short Arg**: `--lossy` / `-LSS`
* **Description**: When used with `--compress-images`, enables lossy compression. JPEG quality is set to 85, and PNG enables lossy compression. File size can be reduced significantly.
* **Description**: 与 `--compress-images` 结合使用时，启用有损压缩模式。JPEG 质量设置为 85，PNG 启用有损压缩。文件大小可显著减小。
* **Usage Examples (使用示例)**: (See `compress-images` examples above)
* **使用示例**: （请参阅上面的 `compress-images` 示例）

#### 3. Creates ISO Files (创建 ISO 文件)

* **Long/Short Arg**: `--iso-creator` / `-ISO`
* **Description**: Creates ISO files from subfolders in the current directory. This function is specific to macOS and requires `hdiutil`.
* **Description**: 从当前目录中的子文件夹创建 ISO 文件。此功能特定于 macOS，需要 `hdiutil`。
* **Usage Examples (使用示例)**:
    ```bash
    # Creates ISOs from subfolders
    # 从子文件夹创建 ISO
    python file_process_tools.py -ISO
    ```

#### 4. Removes Specific Pages from PDFs (从 PDF 中移除特定页面)

* **Long/Short Arg**: `--pdf-page-remover` / `-PPR`
* **Description**: Removes specific pages from PDFs. Provide 1-indexed page numbers separated by spaces.
* **Description**: 从 PDF 中移除特定页面。提供以空格分隔的 1-indexed 页码。
* **Usage Examples (使用示例)**:
    ```bash
    # Removes the 1st, 3rd, and 5th pages from all PDFs
    # 从所有 PDF 中移除第 1、3、5 页
    python file_process_tools.py -PPR 1 3 5
    ```

#### 5. Organizes Files (整理文件)

* **Long/Short Arg**: `--file-organizer` / `-FO`
* **Description**: Organizes files in the current directory into subfolders based on common substrings in their filenames. Targets PDF, EPUB, and TXT files by default.
* **Description**: 根据文件名中的共同子字符串，将当前目录中的文件整理到子文件夹中。默认目标是 PDF、EPUB 和 TXT 文件。
* **Usage Examples (使用示例)**:
    ```bash
    # Organizes files by common names
    # 按通用名称整理文件
    python file_process_tools.py -FO
    ```

---

## ✨ GUI 版本更新 - 现已支持 Windows！

我们很高兴地宣布，本工具现已提供图形用户界面 (GUI) 版本，并全面支持 **Windows 操作系统**！

现在，您可以更直观、便捷地使用各项文件处理功能，无需记忆复杂的命令行参数。

### ⚠️ 注意事项与功能限制：

虽然 GUI 版本提供了极大的便利，但有部分功能和操作在 Windows 环境下或 GUI 中需要额外注意：

* **`ISO` 创建功能 (Create ISO from Folders)**:
    * 此功能**仅在 macOS 系统上可用**。由于其依赖 `hdiutil` 工具，这是 macOS 特有的，因此在 Windows 或其他操作系统上无法使用。

* **`encode_folders` 功能 (文件夹压缩)**:
    * 为了在 Windows 上正常使用此功能，您需要进行额外的环境配置：
        * **安装 7-Zip**: 请从 [https://www.7-zip.org/](https://www.7-zip.org/) 下载并安装 7-Zip。安装后，务必将 7-Zip 的安装目录（例如，`C:\Program Files\7-Zip`）添加到您的系统 `PATH` 环境变量中。
        * **安装 `zip` 命令**: `zip` 命令在 Windows 上通常不自带。您可以选择以下任一方式安装：
            * **Git Bash**: 安装 Git for Windows 通常会包含 `zip` 命令。
            * **Windows Subsystem for Linux (WSL)**: 在 WSL 中安装一个 Linux 发行版，并在其内部安装 `zip` 工具。
            * **Chocolatey**: 如果您使用 Chocolatey 包管理器，可以通过运行 `choco install zip` 来安装。
    * **重要提示**: 如果未正确安装并配置上述外部工具，`encode_folders` 功能将无法正常工作，并可能在日志中显示“命令未找到”的错误信息。

我们致力于提供最佳的用户体验。如果您在使用过程中遇到任何问题，请随时提出！

---

## 📞 Contact (联系方式)

如果您在使用本工具时遇到任何问题或有任何建议，欢迎通过 GitHub Issues 反馈。

If you encounter any issues or have any suggestions while using this tool, feel free to submit them via GitHub Issues.