import React from 'react';
import FileOrganizer from '../features/FileOrganizer';
import TextConverter from '../features/TextConverter';
import ImageConverter from '../features/ImageConverter';
import FolderProcessor from '../features/FolderProcessor';
import PdfProcessor from '../features/PdfProcessor';
import IsoCreator from '../features/IsoCreator';
import PdfSecurityProcessor from '../features/PdfSecurityProcessor';
import FileCombiner from '../features/FileCombiner';
import FilenameManager from '../features/FilenameManager';

interface MainContentProps {
  activeTab: string;
  inputDir: string;
  onLog: (log: string) => void;
}

const MainContent: React.FC<MainContentProps> = ({ activeTab, inputDir, onLog }) => {
  switch (activeTab) {
    case 'file-organizer':
      return <FileOrganizer inputDir={inputDir} onLog={onLog} />;
    case 'text-converter':
      return <TextConverter inputDir={inputDir} onLog={onLog} />;
    case 'image-converter':
      return <ImageConverter inputDir={inputDir} onLog={onLog} />;
    case 'folder-processor':
      return <FolderProcessor inputDir={inputDir} onLog={onLog} />;
    case 'pdf-processor':
      return <PdfProcessor inputDir={inputDir} onLog={onLog} />;
    case 'iso-creator':
      return <IsoCreator inputDir={inputDir} onLog={onLog} />;
    case 'pdf-security-processor':
      return <PdfSecurityProcessor inputDir={inputDir} onLog={onLog} />;
    case 'file-combiner':
      return <FileCombiner inputDir={inputDir} onLog={onLog} />;
    case 'filename-manager':
      return <FilenameManager inputDir={inputDir} onLog={onLog} />;
    default:
      return <div className="pixelated-border" style={{ padding: 32, textAlign: 'center' }}>请选择左侧功能区</div>;
  }
};

export default MainContent; 