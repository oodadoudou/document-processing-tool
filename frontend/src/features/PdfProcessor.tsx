import React, { useState } from 'react';
import { formatDetails } from '../utils/formatDetails';

interface PdfSecurityProcessorProps {
  inputDir: string;
  onLog: (log: string) => void;
}

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5001';

const PdfProcessor: React.FC<PdfSecurityProcessorProps> = ({ inputDir, onLog }) => {
  // --- Page Processing States ---
  const [trimType, setTrimType] = useState<string>('f');
  const [numPages, setNumPages] = useState<string>('1');
  const [trimError, setTrimError] = useState<string | null>(null);
  const [trimLoading, setTrimLoading] = useState<boolean>(false);

  const [pagesToDelete, setPagesToDelete] = useState<string>('');
  const [deletePagesError, setDeletePagesError] = useState<string | null>(null);
  const [deletePagesLoading, setDeletePagesLoading] = useState<boolean>(false);

  const [repairError, setRepairError] = useState<string | null>(null);
  const [repairLoading, setRepairLoading] = useState<boolean>(false);

  // --- Encode PDFs ---
  const [encodePassword, setEncodePassword] = useState<string>('1111');
  const [encodeError, setEncodeError] = useState<string | null>(null);
  const [encodeLoading, setEncodeLoading] = useState<boolean>(false);

  // --- Decode PDFs ---
  const [decodePassword, setDecodePassword] = useState<string>('1111');
  const [decodeError, setDecodeError] = useState<string | null>(null);
  const [decodeLoading, setDecodeLoading] = useState<boolean>(false);

  const outputDir = inputDir ? `${inputDir.replace(/\/$/, '')}/processed_files` : '';

  // --- Handlers ---
  // 1. Trim PDF Pages
  const handleTrimPages = async (e: React.FormEvent) => {
    e.preventDefault();
    setTrimError(null);
    if (!inputDir || inputDir.trim() === '') {
      setTrimError('操作目录不能为空');
      return;
    }
    try {
      setTrimLoading(true);
      const response = await fetch(`${API_BASE}/api/pdf/trim_pages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          output_dir: outputDir,
          trim_type: trimType,
          num_pages: numPages,
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`PDF页面修剪失败: ${error}`);
    } finally {
      setTrimLoading(false);
    }
  };

  // 2. Remove Specific Pages
  const handleRemoveSpecificPages = async (e: React.FormEvent) => {
    e.preventDefault();
    setDeletePagesError(null);
    if (!inputDir || inputDir.trim() === '') {
      setDeletePagesError('操作目录不能为空');
      return;
    }
    try {
      setDeletePagesLoading(true);
      const response = await fetch(`${API_BASE}/api/pdf/remove_specific_pages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          output_dir: outputDir,
          pages_to_delete_str: pagesToDelete,
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`PDF页面删除失败: ${error}`);
    } finally {
      setDeletePagesLoading(false);
    }
  };

  // 3. Repair PDFs
  const handleRepairPdfs = async (e: React.FormEvent) => {
    e.preventDefault();
    setRepairError(null);
    if (!inputDir || inputDir.trim() === '') {
      setRepairError('操作目录不能为空');
      return;
    }
    try {
      setRepairLoading(true);
      const response = await fetch(`${API_BASE}/api/pdf/repair`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          output_dir: outputDir,
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`PDF修复失败: ${error}`);
    } finally {
      setRepairLoading(false);
    }
  };

  // 4. Encode PDFs
  const handleEncodePdfs = async (e: React.FormEvent) => {
    e.preventDefault();
    setEncodeError(null);
    if (!inputDir || inputDir.trim() === '') {
      setEncodeError('操作目录不能为空');
      return;
    }
    try {
      setEncodeLoading(true);
      const response = await fetch(`${API_BASE}/api/pdf/encode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          output_dir: outputDir,
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
      onLog(`PDF加密失败: ${error}`);
    } finally {
      setEncodeLoading(false);
    }
  };

  // 5. Decode PDFs
  const handleDecodePdfs = async (e: React.FormEvent) => {
    e.preventDefault();
    setDecodeError(null);
    if (!inputDir || inputDir.trim() === '') {
      setDecodeError('操作目录不能为空');
      return;
    }
    try {
      setDecodeLoading(true);
      const response = await fetch(`${API_BASE}/api/pdf/decode`, {
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
      onLog(`PDF解密失败: ${error}`);
    } finally {
      setDecodeLoading(false);
    }
  };

  return (
    <div className="pixelated-border" style={{ padding: 24 }}>
      <h2 className="pixel-main-title">PDF处理工具</h2>

      {/* PDF页面处理 */}
      <div className="pixelated-border" style={{ marginBottom: 32, padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>PDF页面处理</h3>
        
        {/* 修剪页面 */}
        <div className="pixelated-border" style={{ marginBottom: 24, padding: 16 }}>
          <h4 style={{ color: '#b6c6e3', marginBottom: 8 }}>修剪页面</h4>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>从PDF文件的开头或结尾删除指定数量的页面。</div>
          <form onSubmit={handleTrimPages}>
            <div style={{ marginBottom: 8 }}>
              <label>修剪类型：</label>
              <select 
                value={trimType} 
                onChange={e => setTrimType(e.target.value)}
                className="pixelated-input"
                style={{ marginLeft: 8 }}
              >
                <option value="f">从开头删除</option>
                <option value="l">从结尾删除</option>
                <option value="lf">删除首尾页</option>
              </select>
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>删除页数：</label>
              <input
                type="number"
                value={numPages}
                onChange={e => setNumPages(e.target.value)}
                className="pixelated-input"
                min="0"
                style={{ marginLeft: 8, width: '100px' }}
              />
            </div>
            <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
              输出目录：<span style={{ color: '#fff' }}>{outputDir}</span>
            </div>
            {trimError && <div className="pixel-error">{trimError}</div>}
            <button
              type="submit"
              className="pixelated-button"
              style={{ width: '100%', marginTop: 8 }}
              disabled={trimLoading}
            >
              {trimLoading ? '处理中...' : '修剪页面'}
            </button>
          </form>
        </div>

        {/* 删除指定页面 */}
        <div className="pixelated-border" style={{ marginBottom: 24, padding: 16 }}>
          <h4 style={{ color: '#b6c6e3', marginBottom: 8 }}>删除指定页面</h4>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>删除PDF文件中的特定页面（从0开始计数，用空格分隔）。</div>
          <form onSubmit={handleRemoveSpecificPages}>
            <div style={{ marginBottom: 8 }}>
              <label>页面编号：</label>
              <input
                type="text"
                value={pagesToDelete}
                onChange={e => setPagesToDelete(e.target.value)}
                className="pixelated-input"
                placeholder="例如：0 2 5"
                style={{ marginLeft: 8 }}
              />
            </div>
            <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
              输出目录：<span style={{ color: '#fff' }}>{outputDir}</span>
            </div>
            {deletePagesError && <div className="pixel-error">{deletePagesError}</div>}
            <button
              type="submit"
              className="pixelated-button"
              style={{ width: '100%', marginTop: 8 }}
              disabled={deletePagesLoading}
            >
              {deletePagesLoading ? '处理中...' : '删除页面'}
            </button>
          </form>
        </div>

        {/* 修复PDF */}
        <div className="pixelated-border" style={{ padding: 16 }}>
          <h4 style={{ color: '#b6c6e3', marginBottom: 8 }}>修复PDF</h4>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>通过重建PDF内部结构来修复损坏的PDF文件。</div>
          <form onSubmit={handleRepairPdfs}>
            <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
              输出目录：<span style={{ color: '#fff' }}>{outputDir}</span>
            </div>
            {repairError && <div className="pixel-error">{repairError}</div>}
            <button
              type="submit"
              className="pixelated-button"
              style={{ width: '100%', marginTop: 8 }}
              disabled={repairLoading}
            >
              {repairLoading ? '处理中...' : '修复PDF'}
            </button>
          </form>
        </div>
      </div>

      {/* PDF安全处理 */}
      <div className="pixelated-border" style={{ padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>PDF安全处理</h3>
        
        {/* PDF加密 */}
        <div className="pixelated-border" style={{ marginBottom: 32, padding: 24 }}>
          <h4 style={{ color: '#b6c6e3', marginBottom: 8 }}>PDF加密</h4>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>将目录下所有PDF文件加密。</div>
          <form onSubmit={handleEncodePdfs}>
            <div style={{ marginBottom: 8 }}>
              <label>密码：</label>
              <input
                type="password"
                value={encodePassword}
                onChange={e => setEncodePassword(e.target.value)}
                className="pixelated-input"
                placeholder="请输入加密密码"
                autoComplete="new-password"
                style={{ marginLeft: 8 }}
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
          <h4 style={{ color: '#b6c6e3', marginBottom: 8 }}>PDF解密</h4>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>将目录下所有加密PDF文件解密。</div>
          <form onSubmit={handleDecodePdfs}>
            <div style={{ marginBottom: 8 }}>
              <label>密码：</label>
              <input
                type="password"
                value={decodePassword}
                onChange={e => setDecodePassword(e.target.value)}
                className="pixelated-input"
                placeholder="请输入解密密码"
                autoComplete="current-password"
                style={{ marginLeft: 8 }}
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
    </div>
  );
};

export default PdfProcessor; 