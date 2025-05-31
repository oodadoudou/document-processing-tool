# Releases Directory | 发布目录

[English](#english) | [中文](#chinese)

<a name="english"></a>
# Releases Directory

This directory contains the latest release builds of the File Process Tools application.

## Structure

- `latest/` - Contains the most recent release build
  - Format: `File-Process-Tools-Setup-vX.Y.Z.exe`

## Release Process

1. Build the application
2. Move the built file to `releases/latest/` with the correct version naming
3. Create a Git tag for the version
4. Push changes and tag to GitHub

Previous versions can be found in the GitHub Releases section of the repository.

## File Naming Convention

Release files should follow this naming pattern:
- Windows: `File-Process-Tools-Setup-vX.Y.Z.exe`
- macOS: `File-Process-Tools-Setup-vX.Y.Z.dmg`
- Linux: `File-Process-Tools-Setup-vX.Y.Z.AppImage`

Where X.Y.Z represents the semantic version number (e.g., v1.0.0, v1.0.1, etc.)

## Git LFS

This directory is managed by Git LFS (Large File Storage). The following file types are automatically tracked:
- *.exe (Windows installers)
- *.dmg (macOS disk images)
- *.zip (Archive files)
- *.msi (Windows installers)

## Usage

1. Build your release artifacts
2. Place them in the appropriate directory (latest/ or archive/)
3. Commit and push - Git LFS will handle the large files automatically

## Notes

- Keep only necessary release files
- Move older versions to the archive/ directory
- Update version numbers in filenames to match release tags

---

<a name="chinese"></a>
# 发布目录

本目录包含文件处理工具应用程序的最新发布版本。

## 目录结构

- `latest/` - 包含最新的发布版本
  - 格式：`File-Process-Tools-Setup-vX.Y.Z.exe`

## 发布流程

1. 构建应用程序
2. 将构建文件移动到 `releases/latest/` 并使用正确的版本命名
3. 创建对应版本的 Git 标签
4. 将更改和标签推送到 GitHub

历史版本可在仓库的 GitHub Releases 部分找到。

## 文件命名规范

发布文件应遵循以下命名模式：
- Windows: `File-Process-Tools-Setup-vX.Y.Z.exe`
- macOS: `File-Process-Tools-Setup-vX.Y.Z.dmg`
- Linux: `File-Process-Tools-Setup-vX.Y.Z.AppImage`

其中 X.Y.Z 表示语义版本号（例如：v1.0.0、v1.0.1 等）

## Git LFS

本目录由 Git LFS（大文件存储）管理。以下文件类型会自动被追踪：
- *.exe (Windows 安装程序)
- *.dmg (macOS 磁盘镜像)
- *.zip (压缩文件)
- *.msi (Windows 安装程序)

## Usage

1. Build your release artifacts
2. Place them in the appropriate directory (latest/ or archive/)
3. Commit and push - Git LFS will handle the large files automatically

## Notes

- Keep only necessary release files
- Move older versions to the archive/ directory
- Update version numbers in filenames to match release tags 