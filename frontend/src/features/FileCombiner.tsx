import React, { useState } from 'react';
import { formatDetails } from '../utils/formatDetails';

interface FileCombinerProps {
  inputDir: string;
  onLog: (log: string) => void;
}

const FileCombiner: React.FC<FileCombinerProps> = ({ inputDir, onLog }) => {
  // --- States ---
  const [fileTypeChar, setFileTypeChar] = useState<string>('p');
  const [outputBaseName, setOutputBaseName] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const outputDir = inputDir ? `${inputDir.replace(/\/$/, '')}/processed_files` : '';

  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5001';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!inputDir || inputDir.trim() === '') {
      setError('操作目录不能为空');
      return;
    }
    if (!outputBaseName || outputBaseName.trim() === '') {
      setError('请输入输出文件名');
      return;
    }
    if (!fileTypeChar || !['p', 't'].includes(fileTypeChar)) {
      setError('请选择正确的文件类型');
      return;
    }
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/file/combine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          output_dir: outputDir,
          file_type_char: fileTypeChar,
          output_base_name: outputBaseName,
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`文件合并失败: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pixelated-border" style={{ padding: 24 }}>
      <h2 className="pixel-main-title">文件合并</h2>
      <div className="pixelated-border" style={{ padding: 16 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>合并文件</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>
          将指定目录下的所有PDF或TXT文件按文件名顺序合并为一个新文件。
        </div>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 8 }}>
            <label>输入目录：</label>
            <input
              type="text"
              value={inputDir}
              disabled
              className="pixelated-input"
              style={{ marginLeft: 8 }}
            />
          </div>
          <div style={{ marginBottom: 8 }}>
            <label>文件类型：</label>
            <select
              value={fileTypeChar}
              onChange={(e) => setFileTypeChar(e.target.value)}
              className="pixelated-input"
              style={{ marginLeft: 8 }}
            >
              <option value="p">PDF</option>
              <option value="t">TXT</option>
            </select>
          </div>
          <div style={{ marginBottom: 8 }}>
            <label>输出文件名：</label>
            <input
              type="text"
              value={outputBaseName}
              onChange={(e) => setOutputBaseName(e.target.value)}
              placeholder="例如：merged"
              className="pixelated-input"
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
            {loading ? '处理中...' : '开始合并'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default FileCombiner; 