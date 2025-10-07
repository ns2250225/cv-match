import PyPDF2
import io

class PDFParser:
    @staticmethod
    def parse_pdf(file):
        """
        解析PDF文件并提取文本内容
        """
        try:
            # 读取PDF文件
            pdf_reader = PyPDF2.PdfReader(file)
            
            # 提取所有页面的文本
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            # 清理文本内容
            cleaned_content = PDFParser._clean_text(text_content)
            
            return cleaned_content
            
        except Exception as e:
            raise Exception(f"PDF解析失败: {str(e)}")
    
    @staticmethod
    def _clean_text(text):
        """
        清理和格式化文本内容
        """
        # 移除多余的空白字符
        cleaned = ' '.join(text.split())
        
        # 处理常见的PDF解析问题
        cleaned = cleaned.replace('\x00', '')  # 移除空字符
        cleaned = cleaned.replace('\ufeff', '')  # 移除BOM标记
        
        # 分段处理（基于常见的关键词）
        sections = []
        current_section = []
        
        # 常见简历分段关键词
        section_keywords = ['教育背景', '工作经历', '项目经验', '专业技能', '自我评价', 
                           'Education', 'Experience', 'Projects', 'Skills', 'Summary']
        
        lines = cleaned.split('.')
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in section_keywords):
                if current_section:
                    sections.append(' '.join(current_section))
                    current_section = []
            current_section.append(line)
        
        if current_section:
            sections.append(' '.join(current_section))
        
        return '\n\n'.join(sections) if sections else cleaned