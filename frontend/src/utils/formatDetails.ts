// 美化后端 details 日志输出
export function formatDetails(details: any): string {
  let out = '';
  if (details.messages) {
    out += '消息列表：\n';
    details.messages.forEach((msg: string) => {
      if (msg.startsWith('[SUCCESS]')) out += `  ✅ ${msg}\n`;
      else if (msg.startsWith('[INFO]')) out += `  ℹ️ ${msg}\n`;
      else if (msg.startsWith('[WARN]')) out += `  ⚠️ ${msg}\n`;
      else if (msg.startsWith('[ERROR]')) out += `  ❌ ${msg}\n`;
      else out += `  ${msg}\n`;
    });
  }
  if (details.moved_files_details && details.moved_files_details.length) {
    out += '\n移动文件明细：\n';
    details.moved_files_details.forEach((item: any) => {
      out += `  - ${item.file} → ${item.destination_folder}/${item.moved_to_file}\n`;
    });
  }
  if (details.skipped_files_details && details.skipped_files_details.length) {
    out += '\n跳过文件明细：\n';
    details.skipped_files_details.forEach((item: any) => {
      out += `  - ${item.file}，原因：${item.reason}\n`;
    });
  }
  if (details.error_details && details.error_details.length) {
    out += '\n错误明细：\n';
    details.error_details.forEach((item: any) => {
      out += `  - ${item.file}，错误：${item.error}\n`;
    });
  }
  // 其他统计字段
  Object.entries(details).forEach(([k, v]) => {
    if (typeof v === 'number' && !['success'].includes(k)) {
      out += `  ${k}: ${v}\n`;
    }
  });
  return out;
} 