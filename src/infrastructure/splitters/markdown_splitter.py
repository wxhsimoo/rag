from typing import List, Dict, Any, Optional
import re
from pathlib import Path

try:
    from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Note: Langchain not available, using fallback implementation

from ...infrastructure.log.logger_service import LoggerService
from .types import InfraDocument, InfraDocumentChunk, InfraSplitterType, InfraSplitterConfig
from .base import InfraDocumentSplitter


class MarkdownSplitter(InfraDocumentSplitter):
    """Markdown文件切分器
    
    使用Langchain的MarkdownHeaderTextSplitter实现Markdown文档的智能切分
    按照Markdown标题层级进行结构化切分
    """
    
    def __init__(self, config: Optional[InfraSplitterConfig] = None, logger: Optional[LoggerService] = None):
        """初始化Markdown切分器
        
        Args:
            config: 切分器配置
            logger: 日志服务
        """
        self.logger = logger
        self.config = config
        # Markdown切分特定配置
        self.headers_to_split_on = getattr(config, 'headers_to_split_on', None) if config else None
        if not self.headers_to_split_on:
            # 默认按所有标题级别切分
            self.headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
                ("####", "Header 4"),
                ("#####", "Header 5"),
                ("######", "Header 6"),
            ]
        
        self.return_each_line = getattr(config, 'return_each_line', False) if config else False
        self.strip_headers = getattr(config, 'strip_headers', True) if config else True
        
        # 初始化Langchain切分器
        self._init_langchain_splitter()
    
    def _init_langchain_splitter(self) -> None:
        """初始化Langchain Markdown切分器"""
        if LANGCHAIN_AVAILABLE:
            try:
                # 初始化Markdown标题切分器
                self.markdown_splitter = MarkdownHeaderTextSplitter(
                    headers_to_split_on=self.headers_to_split_on,
                    return_each_line=self.return_each_line,
                    strip_headers=self.strip_headers
                )
                
                # 初始化递归字符切分器作为二级切分
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.config.chunk_size,
                    chunk_overlap=self.config.chunk_overlap,
                    separators=["\n\n", "\n", " ", ""],
                    keep_separator=self.config.keep_separator,
                    add_start_index=self.config.add_start_index,
                    strip_whitespace=self.config.strip_whitespace
                )
                
                if self.logger:
                    self.logger.info("Initialized Langchain MarkdownHeaderTextSplitter")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to initialize Langchain Markdown splitter: {str(e)}")
                self.markdown_splitter = None
                self.text_splitter = None
        else:
            self.markdown_splitter = None
            self.text_splitter = None
            if self.logger:
                self.logger.info("Using fallback Markdown splitter")
    
    def get_splitter_type(self) -> InfraSplitterType:
        """获取切分器类型
        
        Returns:
            切分器类型
        """
        return InfraSplitterType.MARKDOWN
    
    def split_document(self, document: InfraDocument) -> List[InfraDocumentChunk]:
        """切分单个文档
        
        Args:
            document: 要切分的文档
            
        Returns:
            文档块列表
        """
        metadata = {
            'source': document.source_path,
            'document_id': document.doc_id,
            'file_type': document.doc_type,
            'created_at': document.created_at.isoformat() if document.created_at else None,
        }
            
        return self.split_text(document.content, metadata)
    
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[InfraDocumentChunk]:
        """切分文本
        
        Args:
            text: 要切分的文本
            metadata: 元数据
            
        Returns:
            文档块列表
        """
        if metadata is None:
            metadata = {}
            
        return self._split_text_impl(text, metadata)
    
    def _split_text_impl(self, text: str, metadata: Dict[str, Any]) -> List[InfraDocumentChunk]:
        """具体的文本切分实现
        
        Args:
            text: 要切分的Markdown文本
            metadata: 基础元数据
            
        Returns:
            文档块列表
        """
        if LANGCHAIN_AVAILABLE and self.markdown_splitter:
            return self._split_with_langchain(text, metadata)
        else:
            return self._split_with_fallback(text, metadata)
    
    def _split_with_langchain(self, text: str, metadata: Dict[str, Any]) -> List[InfraDocumentChunk]:
        """使用Langchain进行Markdown切分
        
        Args:
            text: 要切分的Markdown文本
            metadata: 基础元数据
            
        Returns:
            文档块列表
        """
        try:
            # 使用Markdown标题切分器进行初步切分
            md_header_splits = self.markdown_splitter.split_text(text)
            
            chunks = []
            for i, doc in enumerate(md_header_splits):
                content = doc.page_content
                doc_metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                
                # 如果内容太长，使用递归字符切分器进一步切分
                if len(content) > self.config.chunk_size and self.text_splitter:
                    sub_docs = self.text_splitter.create_documents([content], [doc_metadata])
                    
                    for j, sub_doc in enumerate(sub_docs):
                        chunk = self._create_chunk_from_text(
                            content=sub_doc.page_content,
                            chunk_index=len(chunks),
                            start_char=0,  # Markdown切分不保留原始位置
                            metadata=metadata
                        )
                        
                        # 添加Markdown特定的元数据
                        chunk.set_metadata('markdown_method', 'langchain_header_split')
                        chunk.set_metadata('is_sub_chunk', j > 0)
                        
                        # 添加标题层级信息
                        if doc_metadata:
                            for key, value in doc_metadata.items():
                                chunk.set_metadata(f'header_{key.lower()}', value)
                        
                        chunks.append(chunk)
                else:
                    # 直接创建块
                    chunk = self._create_chunk_from_text(
                        content=content,
                        chunk_index=len(chunks),
                        start_char=0,
                        metadata=metadata
                    )
                    
                    # 添加Markdown特定的元数据
                    chunk.set_metadata('markdown_method', 'langchain_header_split')
                    chunk.set_metadata('is_sub_chunk', False)
                    
                    # 添加标题层级信息
                    if doc_metadata:
                        for key, value in doc_metadata.items():
                            chunk.set_metadata(f'header_{key.lower()}', value)
                    
                    chunks.append(chunk)
            
            if self.logger:
                self.logger.debug(f"Langchain split Markdown into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in Langchain Markdown splitting: {str(e)}")
            return self._split_with_fallback(text, metadata)
    
    def _split_with_fallback(self, text: str, metadata: Dict[str, Any]) -> List[InfraDocumentChunk]:
        """回退的Markdown切分实现
        
        Args:
            text: 要切分的Markdown文本
            metadata: 基础元数据
            
        Returns:
            文档块列表
        """
        if self.logger:
            self.logger.info("Using fallback Markdown splitting")
        
        # 按标题切分
        sections = self._split_by_headers(text)
        
        chunks = []
        for i, (header_info, content) in enumerate(sections):
            if content.strip():
                # 如果内容太长，进一步切分
                if len(content) > self.config.chunk_size:
                    sub_chunks = self._split_large_content(content, metadata, header_info, i)
                    chunks.extend(sub_chunks)
                else:
                    chunk = self._create_chunk_from_text(
                        content=content,
                        chunk_index=len(chunks),
                        start_char=0,
                        metadata=metadata
                    )
                    
                    # 添加标题信息
                    chunk.set_metadata('markdown_method', 'fallback_header_split')
                    if header_info:
                        chunk.set_metadata('header_level', header_info['level'])
                        chunk.set_metadata('header_text', header_info['text'])
                    
                    chunks.append(chunk)
        
        if self.logger:
            self.logger.debug(f"Fallback split Markdown into {len(chunks)} chunks")
        return chunks
    
    def _split_by_headers(self, text: str) -> List[tuple]:
        """按标题切分Markdown文本
        
        Args:
            text: Markdown文本
            
        Returns:
            (标题信息, 内容) 的列表
        """
        lines = text.split('\n')
        sections = []
        current_content = []
        current_header = None
        
        for line in lines:
            # 检查是否是标题
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            
            if header_match:
                # 保存之前的内容
                if current_content:
                    content = '\n'.join(current_content).strip()
                    if content:
                        sections.append((current_header, content))
                
                # 开始新的部分
                level = len(header_match.group(1))
                text_content = header_match.group(2)
                current_header = {
                    'level': level,
                    'text': text_content,
                    'raw': line.strip()
                }
                current_content = [line] if not self.strip_headers else []
            else:
                current_content.append(line)
        
        # 添加最后一个部分
        if current_content:
            content = '\n'.join(current_content).strip()
            if content:
                sections.append((current_header, content))
        
        return sections
    
    def _split_large_content(self, content: str, metadata: Dict[str, Any], header_info: Dict, base_index: int) -> List[InfraDocumentChunk]:
        """切分过大的内容
        
        Args:
            content: 内容
            metadata: 元数据
            header_info: 标题信息
            base_index: 基础索引
            
        Returns:
            子块列表
        """
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        # 尝试按段落切分
        paragraphs = re.split(r'\n\s*\n', content)
        
        if len(paragraphs) > 1:
            # 按段落组合
            current_chunk = ""
            
            for paragraph in paragraphs:
                potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
                
                if len(potential_chunk) <= chunk_size:
                    current_chunk = potential_chunk
                else:
                    # 保存当前块
                    if current_chunk.strip():
                        chunk = self._create_chunk_from_text(
                            content=current_chunk.strip(),
                            chunk_index=base_index * 100 + len(chunks),
                            start_char=0,
                            metadata=metadata
                        )
                        
                        chunk.set_metadata('markdown_method', 'fallback_paragraph_split')
                        chunk.set_metadata('is_sub_chunk', True)
                        if header_info:
                            chunk.set_metadata('header_level', header_info['level'])
                            chunk.set_metadata('header_text', header_info['text'])
                        
                        chunks.append(chunk)
                    
                    current_chunk = paragraph
            
            # 添加最后一个块
            if current_chunk.strip():
                chunk = self._create_chunk_from_text(
                    content=current_chunk.strip(),
                    chunk_index=base_index * 100 + len(chunks),
                    start_char=0,
                    metadata=metadata
                )
                
                chunk.set_metadata('markdown_method', 'fallback_paragraph_split')
                chunk.set_metadata('is_sub_chunk', True)
                if header_info:
                    chunk.set_metadata('header_level', header_info['level'])
                    chunk.set_metadata('header_text', header_info['text'])
                
                chunks.append(chunk)
        else:
            # 强制按字符切分
            start = 0
            while start < len(content):
                end = start + chunk_size
                chunk_content = content[start:end]
                
                if chunk_content.strip():
                    chunk = self._create_chunk_from_text(
                        content=chunk_content,
                        chunk_index=base_index * 100 + len(chunks),
                        start_char=start,
                        metadata=metadata
                    )
                    
                    chunk.set_metadata('markdown_method', 'fallback_character_split')
                    chunk.set_metadata('is_sub_chunk', True)
                    if header_info:
                        chunk.set_metadata('header_level', header_info['level'])
                        chunk.set_metadata('header_text', header_info['text'])
                    
                    chunks.append(chunk)
                
                start = end - overlap
                if start <= 0:
                    start = end
        
        return chunks
    
    def _create_chunk_from_text(
        self,
        content: str,
        chunk_index: int,
        start_char: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> InfraDocumentChunk:
        """从文本创建文档块
        
        Args:
            content: 块内容
            chunk_index: 块索引
            start_char: 起始字符位置
            metadata: 元数据
            
        Returns:
            文档块
        """
        # 使用父类的_create_chunk方法
        return self._create_chunk(
            content=content,
            chunk_index=chunk_index,
            start_char=start_char,
            metadata=metadata
        )
    
    def get_markdown_info(self) -> Dict[str, Any]:
        """获取Markdown切分器信息
        
        Returns:
            Markdown切分器信息
        """
        return {
            'type': self.get_splitter_type().value,
            'chunk_size': self.config.chunk_size,
            'chunk_overlap': self.config.chunk_overlap,
            'headers_to_split_on': self.headers_to_split_on,
            'return_each_line': self.return_each_line,
            'strip_headers': self.strip_headers,
            'langchain_available': LANGCHAIN_AVAILABLE,
            'using_langchain': LANGCHAIN_AVAILABLE and self.markdown_splitter is not None,
            'method': self._get_current_method()
        }
    
    def _get_current_method(self) -> str:
        """获取当前使用的方法
        
        Returns:
            方法名称
        """
        if self.markdown_splitter:
            return 'langchain_markdown_header'
        else:
            return 'fallback_markdown_header'
    
    def update_headers_to_split_on(self, headers: List[tuple]) -> None:
        """更新要切分的标题级别
        
        Args:
            headers: 标题级别列表，格式为 [("#", "Header 1"), ...]
        """
        self.headers_to_split_on = headers
        self._init_langchain_splitter()  # 重新初始化
        if self.logger:
            self.logger.info(f"Updated headers to split on: {headers}")
