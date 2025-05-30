import React, { useState } from 'react';
import { formatDetails } from '../utils/formatDetails';

interface FilenameManagerProps {
  inputDir: string;
  onLog: (log: string) => void;
}

const FilenameManager: React.FC<FilenameManagerProps> = ({ inputDir, onLog }) => {
  // --- States ---
  const [prefix, setPrefix] = useState<string>('');
  const [suffix, setSuffix] = useState<string>('');
  const [charPattern, setCharPattern] = useState<string>('');
  const [mode, setMode] = useState<string>('files');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const outputDir = inputDir ? `${inputDir.replace(/\/$/, '')}/processed_files` : '';

  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5001';

  // --- Handlers ---
  // 1. Add Prefix
  const handleAddPrefix = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!inputDir || inputDir.trim() === '' || !prefix) {
      setError('目录和前缀不能为空');
      return;
    }
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/filename/add_prefix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          directory_path: inputDir,
          prefix: prefix,
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`添加前缀失败: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  // 2. Add Suffix
  const handleAddSuffix = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!inputDir || inputDir.trim() === '' || !suffix) {
      setError('目录和后缀不能为空');
      return;
    }
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/filename/add_suffix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          directory_path: inputDir,
          suffix: suffix,
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`添加后缀失败: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  // 3. Delete Characters
  const handleDeleteChars = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!inputDir || inputDir.trim() === '' || !charPattern) {
      setError('目录和字符模式不能为空');
      return;
    }
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/filename/delete_chars`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          directory_path: inputDir,
          char_pattern: charPattern,
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`删除字符失败: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  // 4. Batch Rename
  const handleRenameItems = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!inputDir || inputDir.trim() === '') {
      setError('目录不能为空');
      return;
    }
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/filename/rename_items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          directory_path: inputDir,
          mode: mode,
        }),
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
      setLoading(false);
    }
  };

  // 5. Extract Numbers
  const handleExtractNumbers = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!inputDir || inputDir.trim() === '') {
      setError('目录不能为空');
      return;
    }
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/filename/extract_numbers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          directory_path: inputDir,
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`提取数字失败: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  // 6. Reverse Rename
  const handleReverseRename = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!inputDir || inputDir.trim() === '') {
      setError('目录不能为空');
      return;
    }
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/filename/reverse_rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          directory_path: inputDir,
        }),
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
      setLoading(false);
    }
  };

  return (
    <div className="pixelated-border" style={{ padding: 24 }}>
      <h2 className="pixel-main-title">文件名批量管理</h2>

      {/* 添加前缀 */}
      <div className="pixelated-border" style={{ marginBottom: 24, padding: 16 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>添加前缀</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>为文件名添加指定前缀。</div>
        <form onSubmit={handleAddPrefix}>
          <div style={{ marginBottom: 8 }}>
            <label>前缀：</label>
            <input
              type="text"
              value={prefix}
              onChange={e => setPrefix(e.target.value)}
              className="pixelated-input"
              placeholder="请输入前缀"
              style={{ marginLeft: 8 }}
            />
          </div>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
            输出目录：<span style={{ color: '#fff' }}>{outputDir}</span>
          </div>
          {error && <div className="pixel-error">{error}</div>}
          <button
            type="submit"
            className="pixelated-button"
            style={{ width: '100%', marginTop: 8 }}
            disabled={loading}
          >
            {loading ? '处理中...' : '添加前缀'}
          </button>
        </form>
      </div>

      {/* 添加后缀 */}
      <div className="pixelated-border" style={{ marginBottom: 24, padding: 16 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>添加后缀</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>为文件名添加指定后缀。</div>
        <form onSubmit={handleAddSuffix}>
          <div style={{ marginBottom: 8 }}>
            <label>后缀：</label>
            <input
              type="text"
              value={suffix}
              onChange={e => setSuffix(e.target.value)}
              className="pixelated-input"
              placeholder="请输入后缀"
              style={{ marginLeft: 8 }}
            />
          </div>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
            输出目录：<span style={{ color: '#fff' }}>{outputDir}</span>
          </div>
          {error && <div className="pixel-error">{error}</div>}
          <button
            type="submit"
            className="pixelated-button"
            style={{ width: '100%', marginTop: 8 }}
            disabled={loading}
          >
            {loading ? '处理中...' : '添加后缀'}
          </button>
        </form>
      </div>

      {/* 删除字符 */}
      <div className="pixelated-border" style={{ marginBottom: 24, padding: 16 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>删除字符</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>从文件名中删除指定的字符或正则表达式匹配的内容。</div>
        <form onSubmit={handleDeleteChars}>
          <div style={{ marginBottom: 8 }}>
            <label>字符模式：</label>
            <input
              type="text"
              value={charPattern}
              onChange={e => setCharPattern(e.target.value)}
              className="pixelated-input"
              placeholder="例如：[0-9] 或 特定字符"
              style={{ marginLeft: 8 }}
            />
          </div>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
            输出目录：<span style={{ color: '#fff' }}>{outputDir}</span>
          </div>
          {error && <div className="pixel-error">{error}</div>}
          <button
            type="submit"
            className="pixelated-button"
            style={{ width: '100%', marginTop: 8 }}
            disabled={loading}
          >
            {loading ? '处理中...' : '删除字符'}
          </button>
        </form>
      </div>

      {/* 批量重命名 */}
      <div className="pixelated-border" style={{ marginBottom: 24, padding: 16 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>批量重命名</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>根据文件名的首字符生成拼音前缀并重命名。</div>
        <form onSubmit={handleRenameItems}>
          <div style={{ marginBottom: 8 }}>
            <label>重命名类型：</label>
            <select
              value={mode}
              onChange={e => setMode(e.target.value)}
              className="pixelated-input"
              style={{ marginLeft: 8 }}
            >
              <option value="files">仅文件</option>
              <option value="folders">仅文件夹</option>
              <option value="both">文件和文件夹</option>
            </select>
          </div>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
            输出目录：<span style={{ color: '#fff' }}>{outputDir}</span>
          </div>
          {error && <div className="pixel-error">{error}</div>}
          <button
            type="submit"
            className="pixelated-button"
            style={{ width: '100%', marginTop: 8 }}
            disabled={loading}
          >
            {loading ? '处理中...' : '批量重命名'}
          </button>
        </form>
      </div>

      {/* 提取数字 */}
      <div className="pixelated-border" style={{ marginBottom: 24, padding: 16 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>提取数字</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>从文件名中提取数字部分作为新文件名。</div>
        <form onSubmit={handleExtractNumbers}>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
            输出目录：<span style={{ color: '#fff' }}>{outputDir}</span>
          </div>
          {error && <div className="pixel-error">{error}</div>}
          <button
            type="submit"
            className="pixelated-button"
            style={{ width: '100%', marginTop: 8 }}
            disabled={loading}
          >
            {loading ? '处理中...' : '提取数字'}
          </button>
        </form>
      </div>

      {/* 反向重命名 */}
      <div className="pixelated-border" style={{ padding: 16 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>反向重命名</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>移除文件名中的拼音前缀（格式：X-文件名）。</div>
        <form onSubmit={handleReverseRename}>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
            输出目录：<span style={{ color: '#fff' }}>{outputDir}</span>
          </div>
          {error && <div className="pixel-error">{error}</div>}
          <button
            type="submit"
            className="pixelated-button"
            style={{ width: '100%', marginTop: 8 }}
            disabled={loading}
          >
            {loading ? '处理中...' : '反向重命名'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default FilenameManager; 