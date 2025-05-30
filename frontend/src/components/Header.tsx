import React, { useState } from 'react';

interface HeaderProps {
  inputDir: string;
  setInputDir: (dir: string) => void;
}

const Header: React.FC<HeaderProps> = ({ inputDir, setInputDir }) => {
  const [tempPath, setTempPath] = useState<string>(inputDir);
  const [setTip, setSetTip] = useState<string>('');

  const handleSetPath = () => {
    setInputDir(tempPath);
    setSetTip('目录已设置');
    setTimeout(() => setSetTip(''), 1500);
  };

  return (
    <header className="header-bar">
      <div className="header-left">
        <span className="header-icon">🐟</span>
        <span className="header-title">Tooools 像素工具箱</span>
        <input
          type="text"
          className="pixelated-input"
          style={{ marginLeft: 24, width: 320 }}
          value={tempPath}
          onChange={e => setTempPath(e.target.value)}
          placeholder="输入操作目录路径，如 /Users/xxx/Downloads ..."
        />
        <button
          className="pixelated-button"
          style={{ marginLeft: 8 }}
          onClick={handleSetPath}
        >
          Set Path
        </button>
        {setTip && <span style={{ color: '#7ee7ff', marginLeft: 12 }}>{setTip}</span>}
      </div>
      <div className="window-controls">
        <span>—</span>
        <span>□</span>
        <span className="text-red-400">×</span>
      </div>
    </header>
  );
};

export default Header; 