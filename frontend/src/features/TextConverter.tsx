import React, { useState } from 'react';

interface TextConverterProps {
  inputDir: string;
  onLog: (log: string) => void;
}

const TextConverter: React.FC<TextConverterProps> = ({ inputDir, onLog }) => {
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5001';

  // EPUB转TXT
  const [epubError, setEpubError] = useState<string | null>(null);
  // PDF转TXT
  const [outputFormat, setOutputFormat] = useState<'standard' | 'compact' | 'clean'>('standard');
  const [pdfError, setPdfError] = useState<string | null>(null);

  const outputDir = inputDir ? `${inputDir.replace(/\/$/, '')}/processed_files` : '';

  // EPUB转TXT
  const handleEpubToTxt = async (e: React.FormEvent) => {
    e.preventDefault();
    setEpubError(null);
    if (!inputDir || inputDir.trim() === '') {
      setEpubError('操作目录不能为空');
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/text/epub_to_txt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          output_dir: outputDir,
        }),
      });
      const data = await response.json();
      onLog(`状态: ${data.status}\n消息: ${data.message}\n详情: ${JSON.stringify(data.details, null, 2)}`);
    } catch (error) {
      onLog(`EPUB转TXT失败: ${error}`);
    }
  };

  // PDF转TXT
  const handlePdfToTxt = async (e: React.FormEvent) => {
    e.preventDefault();
    setPdfError(null);
    if (!inputDir || inputDir.trim() === '') {
      setPdfError('操作目录不能为空');
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/text/pdf_to_txt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          output_dir: outputDir,
          output_format: outputFormat,
        }),
      });
      const data = await response.json();
      onLog(`状态: ${data.status}\n消息: ${data.message}\n详情: ${JSON.stringify(data.details, null, 2)}`);
    } catch (error) {
      onLog(`PDF转TXT失败: ${error}`);
    }
  };

  return (
    <div className="pixelated-border" style={{ padding: 24 }}>
      <h2 className="pixel-main-title">文本转换</h2>
      {/* EPUB转TXT */}
      <div className="pixelated-border" style={{ marginBottom: 32, padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>EPUB转TXT</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>将目录下所有EPUB文件批量转换为TXT文本。</div>
        {epubError && <div className="pixel-error">{epubError}</div>}
        <button type="button" className="pixelated-button" style={{ width: '100%', marginTop: 8 }} onClick={handleEpubToTxt}>
          EPUB转TXT
        </button>
      </div>
      {/* PDF转TXT */}
      <div className="pixelated-border" style={{ padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>PDF转TXT</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>将目录下所有PDF文件批量转换为TXT文本。</div>
        <div style={{ marginBottom: 8 }}>
          <label style={{ marginRight: 8 }}>输出格式：</label>
          <select value={outputFormat} onChange={e => setOutputFormat(e.target.value as any)} className="pixelated-input">
            <option value="standard">标准</option>
            <option value="compact">紧凑</option>
            <option value="clean">清洁</option>
          </select>
        </div>
        {pdfError && <div className="pixel-error">{pdfError}</div>}
        <button type="button" className="pixelated-button" style={{ width: '100%', marginTop: 8 }} onClick={handlePdfToTxt}>
          PDF转TXT
        </button>
      </div>
    </div>
  );
};

export default TextConverter; 