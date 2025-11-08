import re
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from langchain_community.document_loaders import UnstructuredMarkdownLoader
    from langchain.schema import Document as LangchainDocument
except ImportError:
    # 如果langchain未安装，提供备用实现
    UnstructuredMarkdownLoader = None
    LangchainDocument = None

from ...infrastructure.log.logger_service import LoggerService
from ..splitters.types import InfraDocument
from .base import InfraDocumentLoader


class MarkdownDocumentLoader(InfraDocumentLoader):
    """Markdown文档加载器
    
    使用langchain的UnstructuredMarkdownLoader来加载Markdown文件
    """
    
    def __init__(self, split_by_headers: bool = True, chunk_size: int = None):
        """
        初始化Markdown加载器
        
        Args:
            split_by_headers: 是否按标题分割文档
            chunk_size: 文档块大小，如果指定则按大小分割
        """
        super().__init__()
        self.split_by_headers = split_by_headers
        self.chunk_size = chunk_size
        self.logger = None  # 可以通过依赖注入设置
    
    def supports_file_type(self, file_path: str) -> bool:
        """检查是否支持Markdown文件"""
        extension = self.get_file_extension(file_path)
        return extension in ['md', 'markdown']
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return ['md', 'markdown']
    
    def load(self, file_path: str) -> List[InfraDocument]:
        """加载文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档列表
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持或内容无效
        """
        return self._load_documents(file_path)
    

    
    def _create_document(self, content: str, metadata: Dict[str, Any] = None) -> InfraDocument:
        """创建文档对象"""
        if metadata is None:
            metadata = {}
        return InfraDocument(content=content, metadata=metadata)
    
    def _clean_content(self, content: str) -> str:
        """清理文档内容"""
        if not content:
            return ""
        # 移除多余的空白字符
        content = content.strip()
        # 规范化换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        # 移除多余的空行
        lines = content.split('\n')
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append('')
                prev_empty = True
        return '\n'.join(cleaned_lines)
    
    def _load_documents(self, file_path: str) -> List[InfraDocument]:
        """加载Markdown文档
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            文档列表
        """
        if UnstructuredMarkdownLoader is not None:
            return self._load_with_langchain(file_path)
        else:
            return self._load_with_builtin(file_path)
    
    def _load_with_langchain(self, file_path: str) -> List[InfraDocument]:
        """使用langchain加载Markdown文档"""
        try:
            # 创建langchain加载器
            loader = UnstructuredMarkdownLoader(file_path)
            
            # 加载文档
            langchain_docs = loader.load()
            
            # 转换为我们的Document格式
            documents = []
            for i, lc_doc in enumerate(langchain_docs):
                # 提取元数据
                metadata = dict(lc_doc.metadata) if lc_doc.metadata else {}
                
                # 如果需要按标题分割，进行进一步处理
                if self.split_by_headers:
                    split_docs = self._split_by_headers(lc_doc.page_content, metadata)
                    documents.extend(split_docs)
                else:
                    # 创建单个文档
                    doc = self._create_document(
                        content=self._clean_content(lc_doc.page_content),
                        metadata=metadata
                    )
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"使用langchain加载Markdown失败: {e}")
            # 回退到内置实现
            return self._load_with_builtin(file_path)
    
    def _load_with_builtin(self, file_path: str) -> List[InfraDocument]:
        """使用内置方法加载Markdown文档"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 清理内容
            content = self._clean_content(content)
            
            documents = []
            
            if self.split_by_headers:
                # 按标题分割
                split_docs = self._split_by_headers(content)
                documents.extend(split_docs)
            elif self.chunk_size:
                # 按大小分割
                chunks = self._split_by_size(content, self.chunk_size)
                for i, chunk in enumerate(chunks):
                    metadata = {'chunk_index': i, 'total_chunks': len(chunks)}
                    doc = self._create_document(content=chunk, metadata=metadata)
                    documents.append(doc)
            else:
                # 作为单个文档
                doc = self._create_document(content=content)
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            raise ValueError(f"加载Markdown文件失败: {e}")
    
    def _split_by_headers(self, content: str, base_metadata: Dict[str, Any] = None) -> List[InfraDocument]:
        """按标题分割Markdown内容
        
        Args:
            content: Markdown内容
            base_metadata: 基础元数据
            
        Returns:
            分割后的文档列表
        """
        if base_metadata is None:
            base_metadata = {}
        
        documents = []
        
        # 使用正则表达式匹配标题
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = content.split('\n')
        
        current_section = {
            'title': '',
            'level': 0,
            'content': [],
            'line_start': 0
        }
        
        for i, line in enumerate(lines):
            header_match = re.match(header_pattern, line, re.MULTILINE)
            
            if header_match:
                # 保存当前section
                if current_section['content'] or current_section['title']:
                    doc = self._create_section_document(current_section, base_metadata, i)
                    if doc:
                        documents.append(doc)
                
                # 开始新section
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                current_section = {
                    'title': title,
                    'level': level,
                    'content': [],
                    'line_start': i
                }
            else:
                # 添加到当前section
                current_section['content'].append(line)
        
        # 保存最后一个section
        if current_section['content'] or current_section['title']:
            doc = self._create_section_document(current_section, base_metadata, len(lines))
            if doc:
                documents.append(doc)
        
        # 如果没有找到任何标题，将整个内容作为一个文档
        if not documents:
            doc = self._create_document(content=content, metadata=base_metadata)
            documents.append(doc)
        
        return documents
    
    def _create_section_document(self, section: Dict[str, Any], base_metadata: Dict[str, Any], line_end: int) -> Optional[InfraDocument]:
        """创建章节文档
        
        Args:
            section: 章节信息
            base_metadata: 基础元数据
            line_end: 结束行号
            
        Returns:
            文档对象（可能为空）
        """
        content_lines = [line for line in section['content'] if line.strip()]
        
        if not content_lines and not section['title']:
            return None
        
        # 构建内容
        content_parts = []
        if section['title']:
            content_parts.append(f"{'#' * section['level']} {section['title']}")
        
        if content_lines:
            content_parts.extend(content_lines)
        
        content = '\n'.join(content_parts)
        
        # 构建元数据
        metadata = dict(base_metadata)
        metadata.update({
            'section_title': section['title'],
            'section_level': section['level'],
            'line_start': section['line_start'],
            'line_end': line_end,
            'section_type': 'header_section'
        })
        
        return self._create_document(content=content, metadata=metadata)
    
    def _split_by_size(self, content: str, chunk_size: int) -> List[str]:
        """按大小分割内容
        
        Args:
            content: 内容
            chunk_size: 块大小
            
        Returns:
            内容块列表
        """
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # 如果不是最后一块，尝试在单词边界分割
            if end < len(content):
                # 向后查找空白字符
                while end > start and content[end] not in ' \n\t':
                    end -= 1
                
                # 如果没找到合适的分割点，使用原始位置
                if end == start:
                    end = start + chunk_size
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end
        
        return chunks
