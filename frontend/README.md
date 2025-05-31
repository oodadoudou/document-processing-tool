# Frontend (React)

[English](#english) | [中文](#chinese)

<a name="english"></a>
# Frontend (React)

## 1. Install Node.js and npm

### macOS / Linux Recommended

Using nvm (Node Version Manager):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# After reopening terminal
nvm install --lts
nvm use --lts
```

### Windows Recommended

Download installer from [Node.js Official Website](https://nodejs.org/) or use [nodist](https://github.com/nullivex/nodist):

```powershell
# After installing, in command line:
node -v
npm -v
```

## 2. Install Dependencies

```bash
npm install
```

## 3. Start Development Server

```bash
npm start
```
- Default access: http://localhost:3000
- Supports hot reload for development.

## 4. Build Production Static Files

```bash
npm run build
```
- Generated static files in `build/` directory, ready for Electron or web server deployment.

## 5. Notes
- Development mode (`npm start`): Local debugging with auto-refresh.
- Production mode (`npm run build`): Generate optimized static assets for release.

---

<a name="chinese"></a>
# 前端 (React)

## 1. 安装 Node.js 和 npm

### macOS / Linux 推荐

使用 nvm（Node Version Manager）：

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# 重新打开终端后
nvm install --lts
nvm use --lts
```

### Windows 推荐

使用 [Node.js 官网](https://nodejs.org/)下载安装包，或用 [nodist](https://github.com/nullivex/nodist)：

```powershell
# 下载安装包后，命令行输入
node -v
npm -v
```

## 2. 安装依赖

```bash
npm install
```

## 3. 启动开发服务器

```bash
npm start
```
- 默认访问：http://localhost:3000
- 支持热更新，适合开发调试。

## 4. 构建生产环境静态文件

```bash
npm run build
```
- 生成的静态文件在 `build/` 目录下，可用于 Electron 或部署到 Web 服务器。

## 5. 说明
- 开发模式（`npm start`）：本地调试，自动刷新。
- 生产模式（`npm run build`）：生成优化后的静态资源，适合发布。
