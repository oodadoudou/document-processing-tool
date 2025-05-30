import React from 'react';

const tabs = [
  { key: 'file-organizer', icon: '🗂️', label: '文件整理' },
  { key: 'text-converter', icon: '📝', label: '文本转换' },
  { key: 'image-converter', icon: '🖼️', label: '图片转换' },
  { key: 'folder-processor', icon: '📁', label: '文件夹处理' },
  { key: 'pdf-processor', icon: '📄', label: 'PDF处理' },
  { key: 'filename-manager', icon: '🔤', label: '文件名管理' },
  { key: 'file-combiner', icon: '➕', label: '文件合并' },
  { key: 'iso-creator', icon: '💿', label: 'ISO 创建' },
];

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => (
  <aside className="sidebar">
    <div className="sidebar-title">功能区</div>
    <ul className="sidebar-list">
      {tabs.map(tab => (
        <li key={tab.key}>
          <button
            className={`sidebar-btn${activeTab === tab.key ? ' pixel-button-active' : ''}`}
            onClick={() => onTabChange(tab.key)}
            aria-selected={activeTab === tab.key}
          >
            <span className="sidebar-icon">{tab.icon}</span> {tab.label}
          </button>
        </li>
      ))}
    </ul>
  </aside>
);

export default Sidebar; 