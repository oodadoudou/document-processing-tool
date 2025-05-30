import React, { useState } from 'react';
import { formatDetails } from '../utils/formatDetails';

interface FileOrganizerProps {
  inputDir: string;
  onLog: (log: string) => void;
}

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5001';

const FileOrganizer: React.FC<FileOrganizerProps> = ({ inputDir, onLog }) => {
  // 按组整理
  const [targetExtensions, setTargetExtensions] = useState<string>('.pdf .epub .txt');
  const [error, setError] = useState<string | null>(null);
  // 展平目录
  const [flattenError, setFlattenError] = useState<string | null>(null);
  // 批量重命名
  const [renameLoading, setRenameLoading] = useState(false);
  // 反向重命名
  const [reverseLoading, setReverseLoading] = useState(false);

  // 按组整理
  const handleGroupOrganize = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!inputDir || inputDir.trim() === '') {
      setError('操作目录不能为空');
      return;
    }
    let response;
    try {
      response = await fetch(`${API_BASE}/api/organizer/organize_by_group`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          target_extensions_str: targetExtensions,
        }),
      });
      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        onLog(`文件整理失败: 服务器返回非JSON内容：\n${text}`);
        return;
      }
      if (!response.ok || data.status !== 'success') {
        onLog(`文件整理失败: ${data.message}\n${data.details ? formatDetails(data.details) : ''}`);
      } else {
        onLog(
          `状态: ${data.status}\n` +
          `消息: ${data.message}\n` +
          (data.details ? formatDetails(data.details) : '')
        );
      }
    } catch (error) {
      onLog(`文件整理失败: ${error}`);
    }
  };

  // 展平目录
  const handleFlatten = async (e: React.FormEvent) => {
    e.preventDefault();
    setFlattenError(null);
    if (!inputDir || inputDir.trim() === '') {
      setFlattenError('操作目录不能为空');
      return;
    }
    let response;
    try {
      response = await fetch(`${API_BASE}/api/filename/flatten_dirs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ directory_path: inputDir }),
      });
      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        onLog(`扁平化目录失败: 服务器返回非JSON内容：\n${text}`);
        return;
      }
      if (!response.ok || data.status !== 'success') {
        onLog(`扁平化目录失败: ${data.message}\n${data.details ? formatDetails(data.details) : ''}`);
      } else {
        onLog(
          `状态: ${data.status}\n` +
          `消息: ${data.message}\n` +
          (data.details ? formatDetails(data.details) : '')
        );
      }
    } catch (error) {
      onLog(`扁平化目录失败: ${error}`);
    }
  };

  // 批量重命名
  const handleBatchRename = async () => {
    if (!inputDir || inputDir.trim() === '') {
      onLog('操作目录不能为空');
      return;
    }
    setRenameLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/filename/rename_items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ directory_path: inputDir, mode: 'both' }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`批量重命名失败: ${error}`);
    } finally {
      setRenameLoading(false);
    }
  };

  // 反向重命名
  const handleReverseRename = async () => {
    if (!inputDir || inputDir.trim() === '') {
      onLog('操作目录不能为空');
      return;
    }
    setReverseLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/filename/reverse_rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ directory_path: inputDir }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`反向重命名失败: ${error}`);
    } finally {
      setReverseLoading(false);
    }
  };

  return (
    <div className="pixelated-border" style={{ padding: 24 }}>
      <h2 className="pixel-main-title">文件整理</h2>
      {/* 按组整理 */}
      <div className="pixelated-border" style={{ marginBottom: 32, padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>按组整理</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>将目录下的文件按扩展名分组到对应文件夹。</div>
        <form onSubmit={handleGroupOrganize}>
          <div style={{ marginBottom: 8 }}>
            <label>目标扩展名：</label>
            <input
              type="text"
              value={targetExtensions}
              onChange={e => setTargetExtensions(e.target.value)}
              className="pixelated-input"
              placeholder="如 .pdf .epub .txt"
              style={{ marginLeft: 8 }}
            />
          </div>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
            操作目录：<span style={{ color: '#fff' }}>{inputDir}</span>
          </div>
          {error && <div className="pixel-error">{error}</div>}
          <button type="submit" className="pixelated-button" style={{ width: '100%', marginTop: 8 }}>
            按组整理
          </button>
        </form>
      </div>
      {/* 展平目录 */}
      <div className="pixelated-border" style={{ marginBottom: 32, padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>展平目录</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>将所有子文件夹中的文件移动到根目录，并删除空文件夹。</div>
        <form onSubmit={handleFlatten}>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
            操作目录：<span style={{ color: '#fff' }}>{inputDir}</span>
          </div>
          {flattenError && <div className="pixel-error">{flattenError}</div>}
          <button type="submit" className="pixelated-button" style={{ width: '100%', marginTop: 8 }}>
            展平目录
          </button>
        </form>
      </div>
      {/* 批量重命名与反向重命名 */}
      <div className="pixelated-border" style={{ padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>批量重命名/反向重命名</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>对目录下所有文件进行批量重命名或反向重命名（去除拼音/字母前缀）。</div>
        <div style={{ display: 'flex', gap: 16 }}>
          <button
            className="pixelated-button"
            style={{ flex: 1 }}
            onClick={handleBatchRename}
            disabled={renameLoading}
          >
            {renameLoading ? '处理中...' : '批量重命名'}
          </button>
          <button
            className="pixelated-button"
            style={{ flex: 1 }}
            onClick={handleReverseRename}
            disabled={reverseLoading}
          >
            {reverseLoading ? '处理中...' : '反向重命名'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FileOrganizer; 