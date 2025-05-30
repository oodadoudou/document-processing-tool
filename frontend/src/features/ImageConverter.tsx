import React, { useState } from 'react';
import { formatDetails } from '../utils/formatDetails';

interface ImageConverterProps {
  inputDir: string;
  onLog: (log: string) => void;
}

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5001';

const ImageConverter: React.FC<ImageConverterProps> = ({ inputDir, onLog }) => {
  // --- Compress Images to PDF ---
  const [compressPdfFilename, setCompressPdfFilename] = useState<string>('compressed_images');
  const [compressTargetWidth, setCompressTargetWidth] = useState<string>('1500');
  const [compressQuality, setCompressQuality] = useState<string>('90');
  const [compressDpi, setCompressDpi] = useState<string>('300');
  const [compressError, setCompressError] = useState<string | null>(null);

  // --- PDF to Images ---
  const [pdfToImgFmt, setPdfToImgFmt] = useState<'png' | 'jpg'>('png');
  const [pdfToImgDpi, setPdfToImgDpi] = useState<string>('300');
  const [pdfToImgQuality, setPdfToImgQuality] = useState<string>('90');
  const [pdfToImgError, setPdfToImgError] = useState<string | null>(null);

  // --- Images to PDF ---
  const [imgToPdfFilename, setImgToPdfFilename] = useState<string>('combined_images');
  const [imgToPdfTargetWidth, setImgToPdfTargetWidth] = useState<string>('1500');
  const [imgToPdfDpi, setImgToPdfDpi] = useState<string>('300');
  const [imgToPdfError, setImgToPdfError] = useState<string | null>(null);

  const outputDir = inputDir ? `${inputDir.replace(/\/$/, '')}/processed_files` : '';

  // --- Handlers ---
  // 1. Compress Images to PDF
  const handleCompressToPdf = async (e: React.FormEvent) => {
    e.preventDefault();
    setCompressError(null);
    if (!inputDir || inputDir.trim() === '') {
      setCompressError('操作目录不能为空');
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/image/compress_to_pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          output_dir: outputDir,
          output_pdf_filename: compressPdfFilename,
          target_width: parseInt(compressTargetWidth),
          quality: parseInt(compressQuality),
          dpi: parseInt(compressDpi),
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`图片压缩并合成PDF失败: ${error}`);
    }
  };

  // 2. PDF to Images
  const handlePdfToImages = async (e: React.FormEvent) => {
    e.preventDefault();
    setPdfToImgError(null);
    if (!inputDir || inputDir.trim() === '') {
      setPdfToImgError('操作目录不能为空');
      return;
    }
    if (pdfToImgFmt === 'jpg' && (parseInt(pdfToImgQuality) < 0 || parseInt(pdfToImgQuality) > 100)) {
      setPdfToImgError('JPG质量应在0-100之间');
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/image/pdf_to_images`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          output_dir: outputDir,
          fmt: pdfToImgFmt,
          dpi: parseInt(pdfToImgDpi),
          quality: parseInt(pdfToImgQuality),
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`PDF转图片失败: ${error}`);
    }
  };

  // 3. Images to PDF
  const handleImagesToPdf = async (e: React.FormEvent) => {
    e.preventDefault();
    setImgToPdfError(null);
    if (!inputDir || inputDir.trim() === '') {
      setImgToPdfError('操作目录不能为空');
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/image/images_to_pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_dir: inputDir,
          output_dir: outputDir,
          output_pdf_filename: imgToPdfFilename,
          target_width: parseInt(imgToPdfTargetWidth),
          dpi: parseInt(imgToPdfDpi),
        }),
      });
      const data = await response.json();
      onLog(
        `状态: ${data.status}\n` +
        `消息: ${data.message}\n` +
        (data.details ? formatDetails(data.details) : '')
      );
    } catch (error) {
      onLog(`图片合成PDF失败: ${error}`);
    }
  };

  return (
    <div className="pixelated-border" style={{ padding: 24 }}>
      <h2 className="pixel-main-title">图片转换</h2>
      {/* Compress Images to PDF */}
      <div className="pixelated-border" style={{ marginBottom: 32, padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>图片压缩并合成PDF</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>将目录下所有图片压缩后合成为一个PDF文件。</div>
        <form onSubmit={handleCompressToPdf}>
          <div style={{ marginBottom: 8 }}>
            <label>输出PDF文件名：</label>
            <input type="text" value={compressPdfFilename} onChange={e => setCompressPdfFilename(e.target.value)} className="pixelated-input" />
          </div>
          <div style={{ marginBottom: 8 }}>
            <label>目标宽度：</label>
            <input type="number" value={compressTargetWidth} onChange={e => setCompressTargetWidth(e.target.value)} className="pixelated-input" />
          </div>
          <div style={{ marginBottom: 8 }}>
            <label>质量：</label>
            <input type="number" value={compressQuality} onChange={e => setCompressQuality(e.target.value)} className="pixelated-input" />
          </div>
          <div style={{ marginBottom: 8 }}>
            <label>DPI：</label>
            <input type="number" value={compressDpi} onChange={e => setCompressDpi(e.target.value)} className="pixelated-input" />
          </div>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>输出目录：<span style={{ color: '#fff' }}>{outputDir}</span></div>
          {compressError && <div className="pixel-error">{compressError}</div>}
          <button type="submit" className="pixelated-button" style={{ width: '100%', marginTop: 8 }}>图片压缩并合成PDF</button>
        </form>
      </div>
      {/* PDF to Images */}
      <div className="pixelated-border" style={{ marginBottom: 32, padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>PDF转图片</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>将目录下所有PDF文件批量转换为图片。</div>
        <form onSubmit={handlePdfToImages}>
          <div style={{ marginBottom: 8 }}>
            <label>输出图片格式：</label>
            <select value={pdfToImgFmt} onChange={e => setPdfToImgFmt(e.target.value as any)} className="pixelated-input">
              <option value="png">PNG</option>
              <option value="jpg">JPG</option>
            </select>
          </div>
          <div style={{ marginBottom: 8 }}>
            <label>DPI：</label>
            <input type="number" value={pdfToImgDpi} onChange={e => setPdfToImgDpi(e.target.value)} className="pixelated-input" />
          </div>
          {pdfToImgFmt === 'jpg' && (
            <div style={{ marginBottom: 8 }}>
              <label>JPG质量：</label>
              <input type="number" value={pdfToImgQuality} onChange={e => setPdfToImgQuality(e.target.value)} className="pixelated-input" />
            </div>
          )}
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>输出目录：<span style={{ color: '#fff' }}>{outputDir}</span></div>
          {pdfToImgError && <div className="pixel-error">{pdfToImgError}</div>}
          <button type="submit" className="pixelated-button" style={{ width: '100%', marginTop: 8 }}>PDF转图片</button>
        </form>
      </div>
      {/* Images to PDF */}
      <div className="pixelated-border" style={{ padding: 24 }}>
        <h3 style={{ color: '#7ee7ff', marginBottom: 8 }}>图片合成PDF</h3>
        <div style={{ color: '#b6c6e3', marginBottom: 8 }}>将目录下所有图片合成为一个PDF文件。</div>
        <form onSubmit={handleImagesToPdf}>
          <div style={{ marginBottom: 8 }}>
            <label>输出PDF文件名：</label>
            <input type="text" value={imgToPdfFilename} onChange={e => setImgToPdfFilename(e.target.value)} className="pixelated-input" />
          </div>
          <div style={{ marginBottom: 8 }}>
            <label>目标宽度：</label>
            <input type="number" value={imgToPdfTargetWidth} onChange={e => setImgToPdfTargetWidth(e.target.value)} className="pixelated-input" />
          </div>
          <div style={{ marginBottom: 8 }}>
            <label>DPI：</label>
            <input type="number" value={imgToPdfDpi} onChange={e => setImgToPdfDpi(e.target.value)} className="pixelated-input" />
          </div>
          <div style={{ color: '#b6c6e3', marginBottom: 8 }}>输出目录：<span style={{ color: '#fff' }}>{outputDir}</span></div>
          {imgToPdfError && <div className="pixel-error">{imgToPdfError}</div>}
          <button type="submit" className="pixelated-button" style={{ width: '100%', marginTop: 8 }}>图片合成PDF</button>
        </form>
      </div>
    </div>
  );
};

export default ImageConverter; 