import React, { useState } from 'react';
import './styles/pixel.css';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Footer from './components/Footer';
import LogPanel from './components/LogPanel';
import MainContent from './components/MainContent';

const DEFAULT_INPUT_DIR = '';

const App: React.FC = () => {
  const [inputDir, setInputDir] = useState<string>(DEFAULT_INPUT_DIR);
  const [activeTab, setActiveTab] = useState<string>('file-organizer');
  const [logs, setLogs] = useState<string[]>([]);

  const handleLog = (msg: string) => setLogs((prev) => [...prev, msg]);

  // ocean-background 装饰（可后续替换为像素SVG）
  const oceanDecor = (
    <>
      <div className="pixel-fish" style={{ left: 40, top: 40, animationName: 'swimRight' }}>🐟</div>
      <div className="pixel-fish" style={{ left: 200, top: 80, animationName: 'swimLeft' }}>🐠</div>
      <div className="pixel-bubble" style={{ left: 120, bottom: 10, animationDuration: '6s' }}></div>
      <div className="pixel-bubble" style={{ left: 180, bottom: 20, animationDuration: '8s' }}></div>
      <div className="pixel-jellyfish" style={{ left: 320, top: 60, animationName: 'jellyfishFloat' }}>🪼</div>
      <div className="pixel-crab" style={{ left: 80, bottom: 0 }}>🦀</div>
    </>
  );

  return (
    <div className="pixel-app-layout" style={{ minHeight: '100vh', background: '#191a2a', display: 'flex', flexDirection: 'column' }}>
      <Header inputDir={inputDir} setInputDir={setInputDir} />
      <div className="pixel-main-area" style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <div className="pixelated-border" style={{ width: 220, minWidth: 180, margin: 16, marginRight: 0, background: 'rgba(30,32,60,0.95)' }}>
          <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
        </div>
        <main className="pixelated-border" style={{ flex: 1, margin: 16, marginLeft: 0, background: 'rgba(30,32,60,0.95)', minWidth: 0 }}>
          <MainContent activeTab={activeTab} inputDir={inputDir} onLog={handleLog} />
        </main>
      </div>
      <div className="pixelated-border" style={{ width: 'calc(100% - 32px)', margin: '0 16px 0 16px', background: 'rgba(30,32,60,0.95)' }}>
        <LogPanel logs={logs} />
      </div>
      <Footer />
    </div>
  );
};

export default App;
