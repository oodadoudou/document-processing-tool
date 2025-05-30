import React, { useState } from 'react';

interface LogPanelProps {
  logs: string[];
}

const LogPanel: React.FC<LogPanelProps> = ({ logs }) => {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <div className="log-output" style={{ marginTop: 24 }}>
      <button className="pixelated-button" style={{ float: 'right', marginBottom: 8 }} onClick={() => setCollapsed(c => !c)}>
        {collapsed ? '展开日志' : '折叠日志'}
      </button>
      {!collapsed && (
        <div style={{ clear: 'both' }}>
          {logs.length === 0 ? <div>暂无日志</div> : logs.map((log, i) => <div key={i}>{log}</div>)}
        </div>
      )}
    </div>
  );
};

export default LogPanel; 