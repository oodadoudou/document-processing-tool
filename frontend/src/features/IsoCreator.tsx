import React, { useState } from 'react';
import { formatDetails } from '../utils/formatDetails';

interface IsoCreatorProps {
  inputDir: string;
  onLog: (log: string) => void;
}

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5001';

const IsoCreator: React.FC<IsoCreatorProps> = ({ inputDir, onLog }) => {
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!inputDir || inputDir.trim() === '') {
      setError('操作目录不能为空');
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/iso/create_from_subfolders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parent_dirs_list: [inputDir],
          output_base_dir: inputDir,
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`ISO 创建失败: ${error}`);
    }
  };

  return (
    <div className="pixelated-border">
      <h2>ISO 创建</h2>
      <div style={{ color: '#b6c6e3', marginBottom: 16 }}>
        本功能用于将输入目录下的所有文件夹批量转换为 .iso 镜像文件。
      </div>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 12 }}>
          <label>输入目录：</label>
          <span style={{ color: '#7ee7ff', marginLeft: 8 }}>{inputDir || '（未设置）'}</span>
        </div>
        <div>
          <label>输出目录：</label>
          <span style={{ color: '#7ee7ff', marginLeft: 8 }}>{inputDir || '（未设置）'}</span>
        </div>
        {error && <div className="pixel-error">{error}</div>}
        <button type="submit" className="pixelated-button">开始创建 ISO</button>
      </form>
    </div>
  );
};

export default IsoCreator; 