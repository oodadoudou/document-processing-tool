import React from 'react';
import FileOrganizer from '../features/FileOrganizer';
import FilenameManager from '../features/FilenameManager';
import FolderProcessor from '../features/FolderProcessor';
import PdfProcessor from '../features/PdfProcessor';
import PdfSecurityProcessor from '../features/PdfSecurityProcessor';
import ImageConverter from '../features/ImageConverter';
import TextConverter from '../features/TextConverter';
import FileCombiner from '../features/FileCombiner';
import IsoCreator from '../features/IsoCreator';

interface FunctionAreaProps {
  activeTab: string;
  inputDir: string;
  onLog: (message: string) => void;
  onTabChange: (tabId: string) => void;
}

const tabConfiguration = [
  { id: 'file-organizer', label: '文件整理' },
  { id: 'filename-manager', label: '文件名管理' },
  { id: 'folder-processor', label: '文件夹处理' },
  { id: 'pdf-processor', label: 'PDF处理' },
  { id: 'image-converter', label: '图片转换' },
  { id: 'text-converter', label: '文本转换' },
  { id: 'file-combiner', label: '文件合并' },
  { id: 'iso-creator', label: 'ISO创建' },
];

const FunctionArea: React.FC<FunctionAreaProps> = ({ activeTab, inputDir, onLog, onTabChange }) => {
  let ContentComponent: React.ElementType | null = null;
  switch (activeTab) {
    case 'file-organizer': ContentComponent = FileOrganizer; break;
    case 'filename-manager': ContentComponent = FilenameManager; break;
    case 'folder-processor': ContentComponent = FolderProcessor; break;
    case 'pdf-processor': ContentComponent = PdfProcessor; break;
    case 'pdf-security-processor': ContentComponent = PdfSecurityProcessor; break;
    case 'image-converter': ContentComponent = ImageConverter; break;
    case 'text-converter': ContentComponent = TextConverter; break;
    case 'file-combiner': ContentComponent = FileCombiner; break;
    case 'iso-creator': ContentComponent = IsoCreator; break;
    default: ContentComponent = null;
  }

  return (
    <div className="main-layout" style={{ display: 'flex', minHeight: '80vh' }}>
      <aside style={{ minWidth: 180, borderRight: '2px solid #222', padding: 16 }}>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {tabConfiguration.map(tab => (
            <li key={tab.id} style={{ marginBottom: 8 }}>
              <button
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  background: activeTab === tab.id ? '#333' : '#eee',
                  color: activeTab === tab.id ? '#fff' : '#222',
                  border: '2px solid #222',
                  borderRadius: 4,
                  cursor: 'pointer',
                  fontWeight: activeTab === tab.id ? 'bold' : 'normal',
                }}
                onClick={() => onTabChange(tab.id)}
              >
                {tab.label}
              </button>
            </li>
          ))}
        </ul>
      </aside>
      <main style={{ flex: 1, padding: 24 }}>
        {ContentComponent
          ? <ContentComponent inputDir={inputDir} onLog={onLog} />
          : <div style={{ textAlign: 'center', padding: 32 }}>请选择功能</div>
        }
      </main>
    </div>
  );
};

export default FunctionArea; 