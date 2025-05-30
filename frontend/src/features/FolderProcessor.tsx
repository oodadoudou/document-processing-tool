import React, { useState } from 'react';
import { formatDetails } from '../utils/formatDetails';

interface FolderProcessorProps {
  inputDir: string;
  onLog: (log: string) => void;
}

const FolderProcessor: React.FC<FolderProcessorProps> = ({ inputDir, onLog }) => {
  // --- Encode Folders ---
  const [encodePassword, setEncodePassword] = useState<string>('1111');
  const [encodeError, setEncodeError] = useState<string | null>(null);

  // --- Decode Folders ---
  const [decodePassword, setDecodePassword] = useState<string>('1111');
  const [decodeError, setDecodeError] = useState<string | null>(null);

  const outputDir = inputDir ? `${inputDir.replace(/\/$/, '')}/processed_files` : '';

  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5001';

  // --- Handlers ---
  // 1. Encode Folders
  const handleEncodeFolders = async (e: React.FormEvent) => {
    e.preventDefault();
    setEncodeError(null);
    if (!inputDir || inputDir.trim() === '') {
      setEncodeError('操作目录不能为空');
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/folder/encode_double_compress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          password: encodePassword,
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`文件夹加密失败: ${error}`);
    }
  };

  // 2. Decode Folders
  const handleDecodeFolders = async (e: React.FormEvent) => {
    e.preventDefault();
    setDecodeError(null);
    if (!inputDir || inputDir.trim() === '') {
      setDecodeError('操作目录不能为空');
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/folder/decode_double_decompress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          password: decodePassword,
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`文件夹解密失败: ${error}`);
    }
  };

  return (
    <div className="pixelated-border" style={{ padding: 24 }}>
      <h2 className="pixel-main-title">文件夹处理</h2>
      {/* Encode Folders */}
      <div className="pixelated-border" style={{ marginBottom: 32, padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>文件夹加密</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>将目录下所有文件夹加密并双重压缩。</div>
        <form onSubmit={handleEncodeFolders}>
          <div style={{ marginBottom: 8 }}>
            <label>密码（可选）：</label>
            <input type="text" value={encodePassword} onChange={e => setEncodePassword(e.target.value)} className="pixelated-input" />
          </div>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>输出目录：<span style={{ color: '#fff' }}>{outputDir}</span></div>
          {encodeError && <div className="pixel-error">{encodeError}</div>}
          <button type="submit" className="pixelated-button" style={{ width: '100%', marginTop: 8 }}>文件夹加密</button>
        </form>
      </div>
      {/* Decode Folders */}
      <div className="pixelated-border" style={{ padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>文件夹解密</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>将目录下所有加密文件夹解密并双重解压。</div>
        <form onSubmit={handleDecodeFolders}>
          <div style={{ marginBottom: 8 }}>
            <label>密码（可选）：</label>
            <input type="text" value={decodePassword} onChange={e => setDecodePassword(e.target.value)} className="pixelated-input" />
          </div>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>输出目录：<span style={{ color: '#fff' }}>{outputDir}</span></div>
          {decodeError && <div className="pixel-error">{decodeError}</div>}
          <button type="submit" className="pixelated-button" style={{ width: '100%', marginTop: 8 }}>文件夹解密</button>
        </form>
      </div>
    </div>
  );
};

export default FolderProcessor; 