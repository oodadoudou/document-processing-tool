const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webSecurity: false
    }
  });

  // 加载前端页面
  const indexPath = path.join(__dirname, 'index.html');
  console.log('Looking for index.html at:', indexPath);
  
  if (fs.existsSync(indexPath)) {
    win.loadFile(indexPath);
    console.log('Successfully found index.html');
  } else {
    console.error('index.html not found at:', indexPath);
    // 尝试加载备用路径
    const altPath = path.join(process.resourcesPath, 'app.asar', 'build', 'index.html');
    console.log('Trying alternative path:', altPath);
    if (fs.existsSync(altPath)) {
      win.loadFile(altPath);
      console.log('Successfully loaded from alternative path');
    } else {
      console.error('Failed to find index.html in alternative path');
    }
  }

  // 打开开发者工具以便调试
  win.webContents.openDevTools();
}

app.whenReady().then(() => {
  createWindow();

  // 启动后端服务
  const backendExePath = path.join(process.resourcesPath, 'backend/file_process_backend.exe');
  console.log('Looking for backend at:', backendExePath);
  
  if (fs.existsSync(backendExePath)) {
    console.log('Found backend executable');
    const backendProcess = spawn(backendExePath);

    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend stdout: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`Backend stderr: ${data}`);
    });

    backendProcess.on('error', (error) => {
      console.error('Failed to start backend:', error);
    });
  } else {
    console.error('Backend executable not found at:', backendExePath);
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
}); 