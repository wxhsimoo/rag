from typing import List, Dict, Any, Optional
import json
from pathlib import Path

try:
    from langchain.text_splitter import RecursiveJsonSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Note: Langchain not available, using fallback implementation

from ...infrastructure.log.logger_service import LoggerService
from .types import InfraDocument, InfraDocumentChunk, InfraSplitterType, InfraSplitterConfig
from .base import InfraDocumentSplitter


class JsonSplitter(InfraDocumentSplitter):
    """JSON文件切分器
    
    使用Langchain的RecursiveJsonSplitter实现JSON文档的智能切分
    按照JSON结构递归地切分内容
    """
    
    def __init__(self, config: Optional[InfraSplitterConfig] = None, logger: Optional[LoggerService] = None):
        """初始化JSON切分器
        
        Args:
            config: 切分器配置
            logger: 日志服务
        """
        self.logger = logger
        self.config = config
        # JSON切分特定配置
        self.max_chunk_size = getattr(config, 'max_chunk_size', 4000) if config else 4000
        self.convert_lists = getattr(config, 'convert_lists', False) if config else False
        
        # 初始化Langchain切分器
        self._init_langchain_splitter()
    
    def _init_langchain_splitter(self) -> None:
        """初始化Langchain JSON切分器"""
        if LANGCHAIN_AVAILABLE:
            try:
                self.langchain_splitter = RecursiveJsonSplitter(
                    max_chunk_size=self.max_chunk_size,
                )
                if self.logger:
                    self.logger.info("Initialized Langchain RecursiveJsonSplitter")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to initialize Langchain JSON splitter: {str(e)}")
                self.langchain_splitter = None
        else:
            self.langchain_splitter = None
            if self.logger:
                self.logger.info("Using fallback JSON splitter")
    
    def get_splitter_type(self) -> InfraSplitterType:
        """获取切分器类型
        
        Returns:
            切分器类型
        """
        return InfraSplitterType.JSON
    
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
            text: 要切分的JSON文本
            metadata: 基础元数据
            
        Returns:
            文档块列表
        """
        if LANGCHAIN_AVAILABLE and self.langchain_splitter:
            return self._split_with_langchain(text, metadata)
        else:
            return self._split_with_fallback(text, metadata)
    
    def _split_with_langchain(self, text: str, metadata: Dict[str, Any]) -> List[InfraDocumentChunk]:
        """使用Langchain进行JSON切分
        
        Args:
            text: 要切分的JSON文本
            metadata: 基础元数据
            
        Returns:
            文档块列表
        """
        try:
           
            # 使用Langchain切分JSON
            json_chunks = self.langchain_splitter.split_json(json_data=metadata)
            
            # 转换为InfraDocumentChunk
            chunks = []
            for i, chunk_data in enumerate(json_chunks):
                # 将JSON数据转换为字符串
                chunk_content = json.dumps(chunk_data, ensure_ascii=False, indent=2)
                
                chunk = self._create_chunk_from_text(
                    content=chunk_content,
                    chunk_index=i,
                    start_char=0,  # JSON切分不保留原始位置
                    metadata=metadata
                )
                
                # 添加JSON特定的元数据
                chunk.set_metadata('json_method', 'langchain_recursive')
                chunk.set_metadata('json_keys', list(chunk_data.keys()) if isinstance(chunk_data, dict) else [])
                chunk.set_metadata('json_type', type(chunk_data).__name__)
                
                chunks.append(chunk)
            
            if self.logger:
                self.logger.debug(f"Langchain split JSON into {len(chunks)} chunks")
            return chunks
            
        except json.JSONDecodeError as e:
            if self.logger:
                self.logger.error(f"Invalid JSON format: {str(e)}")
            return self._split_with_fallback(text, metadata)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in Langchain JSON splitting: {str(e)}")
            return self._split_with_fallback(text, metadata)
    
    def _split_with_fallback(self, text: str, metadata: Dict[str, Any]) -> List[InfraDocumentChunk]:
        """回退的JSON切分实现
        
        Args:
            text: 要切分的JSON文本
            metadata: 基础元数据
            
        Returns:
            文档块列表
        """
        if self.logger:
            self.logger.info("Using fallback JSON splitting")
        
        try:
            # 尝试解析JSON
            json_data = json.loads(text)
            
            # 递归切分JSON对象
            chunks_data = self._recursive_split_json(json_data, max_size=self.max_chunk_size)
            
            # 转换为InfraDocumentChunk对象
            chunks = []
            for i, chunk_data in enumerate(chunks_data):
                chunk_content = json.dumps(chunk_data, ensure_ascii=False, indent=2)
                
                chunk = self._create_chunk_from_text(
                    content=chunk_content,
                    chunk_index=i,
                    start_char=0,
                    metadata=metadata
                )
                
                # 添加回退方法的元数据
                chunk.set_metadata('json_method', 'fallback_recursive')
                chunk.set_metadata('json_keys', list(chunk_data.keys()) if isinstance(chunk_data, dict) else [])
                chunk.set_metadata('json_type', type(chunk_data).__name__)
                
                chunks.append(chunk)
            
            if self.logger:
                self.logger.debug(f"Fallback split JSON into {len(chunks)} chunks")
            return chunks
            
        except json.JSONDecodeError:
            # 如果不是有效的JSON，按文本切分
            if self.logger:
                self.logger.warning("Invalid JSON, falling back to text splitting")
            return self._split_as_text(text, metadata)
    
    def _recursive_split_json(self, data: Any, max_size: int = 4000, current_path: str = "") -> List[Any]:
        """递归切分JSON数据
        
        Args:
            data: JSON数据
            max_size: 最大块大小
            current_path: 当前路径
            
        Returns:
            切分后的数据块列表
        """
        # 计算当前数据的大小
        data_str = json.dumps(data, ensure_ascii=False)
        if len(data_str) <= max_size:
            return [data]
        
        chunks = []
        
        if isinstance(data, dict):
            # 处理字典：按键值对切分
            current_chunk = {}
            current_size = 2  # 考虑 {}
            
            for key, value in data.items():
                value_str = json.dumps({key: value}, ensure_ascii=False)
                
                if current_size + len(value_str) <= max_size:
                    current_chunk[key] = value
                    current_size += len(value_str)
                else:
                    # 保存当前块
                    if current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = {}
                        current_size = 2
                    
                    # 如果单个值太大，递归切分
                    if len(value_str) > max_size:
                        sub_chunks = self._recursive_split_json(value, max_size, f"{current_path}.{key}")
                        chunks.extend(sub_chunks)
                    else:
                        current_chunk[key] = value
                        current_size = len(value_str)
            
            # 添加最后一个块
            if current_chunk:
                chunks.append(current_chunk)
        
        elif isinstance(data, list):
            # 处理列表：按元素切分
            current_chunk = []
            current_size = 2  # 考虑 []
            
            for i, item in enumerate(data):
                item_str = json.dumps(item, ensure_ascii=False)
                
                if current_size + len(item_str) <= max_size:
                    current_chunk.append(item)
                    current_size += len(item_str)
                else:
                    # 保存当前块
                    if current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = []
                        current_size = 2
                    
                    # 如果单个项太大，递归切分
                    if len(item_str) > max_size:
                        sub_chunks = self._recursive_split_json(item, max_size, f"{current_path}[{i}]")
                        chunks.extend(sub_chunks)
                    else:
                        current_chunk.append(item)
                        current_size = len(item_str)
            
            # 添加最后一个块
            if current_chunk:
                chunks.append(current_chunk)
        
        else:
            # 基本类型，直接返回
            chunks.append(data)
        
        return chunks
    
    def _split_as_text(self, text: str, metadata: Dict[str, Any]) -> List[InfraDocumentChunk]:
        """作为普通文本切分
        
        Args:
            text: 文本内容
            metadata: 元数据
            
        Returns:
            文档块列表
        """
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_content = text[start:end]
            
            if chunk_content.strip():
                chunk = self._create_chunk_from_text(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    start_char=start,
                    metadata=metadata
                )
                
                chunk.set_metadata('json_method', 'text_fallback')
                chunks.append(chunk)
                chunk_index += 1
            
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
    
    def get_json_info(self) -> Dict[str, Any]:
        """获取JSON切分器信息
        
        Returns:
            JSON切分器信息
        """
        return {
            'type': self.get_splitter_type().value,
            'max_chunk_size': self.max_chunk_size,
            'convert_lists': self.convert_lists,
            'langchain_available': LANGCHAIN_AVAILABLE,
            'using_langchain': LANGCHAIN_AVAILABLE and self.langchain_splitter is not None,
            'method': self._get_current_method()
        }
    
    def _get_current_method(self) -> str:
        """获取当前使用的方法
        
        Returns:
            方法名称
        """
        if self.langchain_splitter:
            return 'langchain_recursive_json'
        else:
            return 'fallback_recursive_json'
