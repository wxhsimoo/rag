import json
from typing import List, Dict, Any, Union

try:
    from langchain_community.document_loaders import JSONLoader
except ImportError:
    # 如果langchain未安装，提供备用实现
    JSONLoader = None
    LangchainDocument = None

from ..splitters.types import InfraDocument
from .base import InfraDocumentLoader
from pathlib import Path


class JsonDocumentLoader(InfraDocumentLoader):
    """JSON文档加载器
    
    使用langchain的JSONLoader来加载JSON文件
    """
    
    def __init__(self, jq_schema: str = None, content_key: str = None):
        """
        初始化JSON加载器
        
        Args:
            jq_schema: JQ查询模式，用于提取JSON中的特定字段
            content_key: 内容字段名，如果JSON是对象数组，指定哪个字段作为内容
        """
        super().__init__()
        self.jq_schema = jq_schema
        self.content_key = content_key
        self.logger = None  # 可以通过依赖注入设置
    
    def supports_file_type(self, file_path: str) -> bool:
        """检查是否支持JSON文件"""
        return self.get_file_extension(file_path) == 'json'
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return ['json']
    
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
        """加载JSON文档
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            文档列表
        """
        if JSONLoader is not None:
            return self._load_with_langchain(file_path)
        else:
            return self._load_with_builtin(file_path)
    
    def _load_with_langchain(self, file_path: str) -> List[InfraDocument]:
        """使用langchain加载JSON文档"""
        try:
            # 配置langchain JSONLoader
            loader_kwargs = {}
            if self.jq_schema:
                loader_kwargs['jq_schema'] = self.jq_schema
            if self.content_key:
                loader_kwargs['content_key'] = self.content_key
            
            # 创建langchain加载器
            loader = JSONLoader(file_path, **loader_kwargs)
            
            # 加载文档
            langchain_docs = loader.load()
            
            # 转换为我们的Document格式
            documents = []
            for i, lc_doc in enumerate(langchain_docs):
                # 提取元数据
                metadata = dict(lc_doc.metadata) if lc_doc.metadata else {}
                
                # 创建我们的Document对象
                doc = self._create_document(
                    content=self._clean_content(lc_doc.page_content),
                    metadata=metadata
                )
                
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"使用langchain加载JSON失败: {e}")
            # 回退到内置实现
            return self._load_with_builtin(file_path)
    
    def _load_with_builtin(self, file_path: str) -> List[InfraDocument]:
        """使用内置方法加载JSON文档"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            documents = []
            
            if isinstance(data, list):
                # 如果是数组，为每个元素创建一个文档
                for i, item in enumerate(data):
                    content, metadata = self._extract_content_and_metadata(item, i)
                    doc = self._create_document(content=content, metadata=metadata)
                    documents.append(doc)
            
            elif isinstance(data, dict):
                # 如果是单个对象，创建一个文档
                content, metadata = self._extract_content_and_metadata(data, 0)
                doc = self._create_document(content=content, metadata=metadata)
                documents.append(doc)
            
            else:
                # 如果是基本类型，直接作为内容
                content = str(data)
                doc = self._create_document(content=content)
                documents.append(doc)
            
            return documents
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON格式错误: {e}")
        except Exception as e:
            raise ValueError(f"加载JSON文件失败: {e}")
    
    def _extract_content_and_metadata(self, item: Union[Dict, Any], index: int) -> tuple[str, Dict[str, Any]]:
        """从JSON项目中提取内容和元数据
        
        Args:
            item: JSON项目
            index: 项目索引
            
        Returns:
            (内容, 元数据) 元组
        """
        if isinstance(item, dict):
            # 如果指定了内容字段，使用该字段作为内容
            if self.content_key and self.content_key in item:
                content = str(item[self.content_key])
                metadata = {k: v for k, v in item.items() if k != self.content_key}
            else:
                # 否则，尝试找到可能的内容字段
                content_fields = ['content', 'text', 'description', 'body', 'message']
                content = None
                
                for field in content_fields:
                    if field in item:
                        content = str(item[field])
                        break
                
                if content is None:
                    # 如果没有找到明显的内容字段，将整个对象序列化为内容
                    content = json.dumps(item, ensure_ascii=False, indent=2)
                    metadata = {'json_type': 'object'}
                else:
                    # 其他字段作为元数据
                    metadata = {k: v for k, v in item.items() if k not in content_fields}
            
            # 添加索引信息
            metadata['item_index'] = index
            
        else:
            # 非字典类型，直接作为内容
            content = str(item)
            metadata = {
                'item_index': index,
                'json_type': type(item).__name__
            }
        
        return content, metadata
