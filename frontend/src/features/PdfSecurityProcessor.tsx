import React, { useState } from 'react';
import { formatDetails } from '../utils/formatDetails';

interface PdfSecurityProcessorProps {
  inputDir: string;
  onLog: (log: string) => void;
}

/**
 * PDF安全处理组件：包含PDF加密和解密功能，参数与后端接口严格一致。
 */
const PdfSecurityProcessor: React.FC<PdfSecurityProcessorProps> = ({ inputDir, onLog }) => {
  // 加密相关状态
  const [encodePassword, setEncodePassword] = useState<string>('');
  const [encodeError, setEncodeError] = useState<string | null>(null);
  const [encodeLoading, setEncodeLoading] = useState(false);

  // 解密相关状态
  const [decodePassword, setDecodePassword] = useState<string>('');
  const [decodeError, setDecodeError] = useState<string | null>(null);
  const [decodeLoading, setDecodeLoading] = useState(false);

  // 自动输出目录
  const outputDir = inputDir ? `${inputDir.replace(/\/$/, '')}/processed_files` : '';

  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5001';

  // PDF加密提交
  const handleEncode = async (e: React.FormEvent) => {
    e.preventDefault();
    setEncodeError(null);
    if (!inputDir || inputDir.trim() === '') {
      setEncodeError('请先选择操作目录');
      return;
    }
    if (!encodePassword) {
      setEncodeError('请输入加密密码');
      return;
    }
    setEncodeLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/pdf/encode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          output_dir: outputDir,
          password: encodePassword,
        }),
      });
      const data = await res.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (err) {
      onLog(`PDF加密失败: ${err}`);
    } finally {
      setEncodeLoading(false);
    }
  };

  // PDF解密提交
  const handleDecode = async (e: React.FormEvent) => {
    e.preventDefault();
    setDecodeError(null);
    if (!inputDir || inputDir.trim() === '') {
      setDecodeError('请先选择操作目录');
      return;
    }
    if (!decodePassword) {
      setDecodeError('请输入解密密码');
      return;
    }
    setDecodeLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/pdf/decode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          password: decodePassword,
        }),
      });
      const data = await res.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (err) {
      onLog(`PDF解密失败: ${err}`);
    } finally {
      setDecodeLoading(false);
    }
  };

  // inputDir 为空时的提示
  if (!inputDir || inputDir.trim() === '') {
    return (
      <div className="pixelated-border" style={{ padding: 32, textAlign: 'center', color: '#b6c6e3' }}>
        请选择操作目录后使用 PDF 安全功能
      </div>
    );
  }

  return (
    <div className="pixelated-border" style={{ padding: 24 }}>
      <h2 className="pixel-main-title">PDF安全</h2>
      {/* PDF加密 */}
      <div className="pixelated-border" style={{ marginBottom: 32, padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>PDF加密</h3>
        <form onSubmit={handleEncode}>
          <div style={{ marginBottom: 8 }}>
            <label>加密密码：</label>
            <input
              type="password"
              value={encodePassword}
              onChange={e => setEncodePassword(e.target.value)}
              className="pixelated-input"
              placeholder="请输入加密密码"
              autoComplete="new-password"
            />
          </div>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
            输出目录：<span style={{ color: '#fff' }}>{outputDir}</span>
          </div>
          {encodeError && <div className="pixel-error">{encodeError}</div>}
          <button
            type="submit"
            className="pixelated-button"
            style={{ width: '100%', marginTop: 8 }}
            disabled={encodeLoading}
          >
            {encodeLoading ? '加密中...' : 'PDF加密'}
          </button>
        </form>
      </div>
      {/* PDF解密 */}
      <div className="pixelated-border" style={{ padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>PDF解密</h3>
        <form onSubmit={handleDecode}>
          <div style={{ marginBottom: 8 }}>
            <label>解密密码：</label>
            <input
              type="password"
              value={decodePassword}
              onChange={e => setDecodePassword(e.target.value)}
              className="pixelated-input"
              placeholder="请输入解密密码"
              autoComplete="current-password"
            />
          </div>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
            输出目录：<span style={{ color: '#fff' }}>{outputDir}</span>
          </div>
          {decodeError && <div className="pixel-error">{decodeError}</div>}
          <button
            type="submit"
            className="pixelated-button"
            style={{ width: '100%', marginTop: 8 }}
            disabled={decodeLoading}
          >
            {decodeLoading ? '解密中...' : 'PDF解密'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default PdfSecurityProcessor;