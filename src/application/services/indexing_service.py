from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ...domain.interfaces.document_loader_service import DocumentLoaderService
from ...domain.interfaces.embedding_service import EmbeddingService
from ...domain.interfaces.vector_store_service import VectorStoreService
from ...domain.entities.document import Document
from ...domain.interfaces.document_splitter_service import DocumentSplitterService
from ...infrastructure.log.logger_service import LoggerService

class IndexingService:
    """索引服务 - 负责文档向量化和索引构建"""
    
    def __init__(
        self,
        document_loader_service: DocumentLoaderService,
        embedding_service: EmbeddingService,
        vector_store_service: VectorStoreService,
        document_splitter_service: DocumentSplitterService,
        logger: LoggerService
    ):
        self.document_loader_service = document_loader_service
        self.embedding_service = embedding_service
        self.vector_store_service = vector_store_service
        self.document_splitter_service = document_splitter_service
        self.logger = logger
    
    async def build_index(self, file_paths: List[str], force_rebuild: bool = False) -> Dict[str, Any]:
        """构建索引
        
        Args:
            file_paths: 要索引的文件路径列表
            force_rebuild: 是否强制重建索引
            
        Returns:
            索引构建结果
        """
        try:
            self.logger.info(f"开始构建索引，处理 {len(file_paths)} 个文件路径...")
            
            start_time = datetime.now()
            
            # 如果强制重建，先清空现有索引
            if force_rebuild:
                await self.vector_store_service.clear()
                self.logger.info("已清空现有索引")
            
            # 从文件路径加载文档
            documents = await self.__load_documents_from_paths(file_paths)
            self.logger.info(f"从文件路径加载了 {len(documents)} 个文档")
            
            if not documents:
                return {
                    "success": True,
                    "message": "没有找到需要索引的文档",
                    "documents_processed": 0,
                    "processing_time": 0
                }
            
            # 处理文档并构建索引
            processed_count = 0
            
            for document in documents:
                
                try:
                    # 切分文档
                    chunks = await self.__split_document(
                        content=document['content'],
                        metadata=document['metadata']
                    )

                    # 生成嵌入向量
                    embeddings = await self.__create_embeddings([chunk['content'] for chunk in chunks])
                    
                    # 存储到向量数据库
                    await self.__store_embeddings(
                        texts=[chunk['content'] for chunk in chunks],
                        embeddings=embeddings,
                        metadatas=[chunk['metadata'] for chunk in chunks]
                    )
                    
                    processed_count += len(chunks)
                    self.logger.info(f"已处理文档: {document['metadata']['filename']}，生成 {len(chunks)} 个片段")
                    
                except Exception as e:
                    self.logger.error(f"处理文档失败 {document['metadata']['filename']}: {str(e)}")
                    continue
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            self.logger.info(f"索引构建完成，处理了 {processed_count} 个文档片段，耗时 {processing_time:.2f} 秒")
            
            return {
                "success": True,
                "message": "索引构建成功",
                "documents_processed": processed_count,
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"索引构建失败: {str(e)}")
            return {
                "success": False,
                "message": f"索引构建失败: {str(e)}",
                "documents_processed": 0,
                "processing_time": 0
            }
    
    async def __load_documents_from_paths(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """从文件路径加载文档
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文档列表
        """
        documents = []
        
        for file_path in file_paths:
            try:
                # 使用DocumentLoaderService加载文档
                loaded_docs = self.document_loader_service.load_document(file_path)
               
                for doc in loaded_docs:
                    # 转换为字典格式以保持与现有代码的兼容性
                    document = {
                        'content': doc.content,
                        'metadata': {
                            'source': doc.metadata.get('source', file_path),
                            'filename': doc.metadata.get('file_name', Path(file_path).name),
                            'file_type': doc.metadata.get('file_extension', Path(file_path).suffix),
                            'file_size': doc.metadata.get('file_size', len(doc.content)),
                            **doc.metadata  # 包含其他元数据
                        }
                    }
                    documents.append(document)
                    self.logger.debug(f"加载文档: {document['metadata']['filename']}")
                
            except Exception as e:
                self.logger.error(f"加载文件失败 {file_path}: {str(e)}")
                continue
        
        return documents
    
    async def __split_document(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """切分文档
        
        Args:
            content: 文档内容
            metadata: 文档元数据
            
        Returns:
            文档片段列表
        """
        try:
            # 创建临时文档对象用于切分
            temp_doc = Document(
                content=content,
                metadata=metadata,
                doc_id=metadata.get('filename', 'temp'),
                doc_type=metadata.get('file_type', 'text')
            )
            
            # 检查是否需要切分
            should_split = await self.document_splitter_service.should_split_document(temp_doc)
            if should_split:
                # 切分文档
                chunks = await self.document_splitter_service.split_document(temp_doc)
                
                # 转换为字典格式
                result = []
                for chunk in chunks:
                    result.append({
                        'content': chunk.content,
                        'metadata': {
                            **metadata,
                            'chunk_id': chunk.chunk_id,
                            'chunk_index': chunk.chunk_index,
                            'start_position': chunk.start_char,
                            'end_position': chunk.end_char,
                            'chunk_size': chunk.chunk_size,
                            'is_chunk': True
                        }
                    })
                
                return result
            else:
                # 不需要切分，返回原文档
                return [{
                    'content': content,
                    'metadata': {
                        **metadata,
                        'is_chunk': False
                    }
                }]
                
        except Exception as e:
            self.logger.error(f"文档切分失败: {str(e)}")
            # 回退到原文档
            return [{
                'content': content,
                'metadata': {
                    **metadata,
                    'is_chunk': False,
                    'split_error': str(e)
                }
            }]
    
    async def __create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        try:
            # 检查并截断过长的文本（阿里云嵌入服务限制为2048字符）
            truncated_texts = []
            for text in texts:
                if len(text) > 2048:
                    truncated_text = text[:2048]
                    self.logger.warning(f"文本长度超过2048字符，已截断: {len(text)} -> 2048")
                    truncated_texts.append(truncated_text)
                elif len(text) == 0:
                    # 空文本用单个空格替代
                    truncated_texts.append(" ")
                else:
                    truncated_texts.append(text)
            embeddings = await self.embedding_service.embed_texts(truncated_texts)
            return embeddings
        except Exception as e:
            self.logger.error(f"生成嵌入向量失败: {str(e)}")
            raise
    
    async def __store_embeddings(self, texts: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]) -> None:
        """存储嵌入向量到向量数据库
        
        Args:
            texts: 文本列表
            embeddings: 嵌入向量列表
            metadatas: 元数据列表
        """
        try:
            # 创建文档对象列表
            documents = []
            for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
                doc = Document(
                    content=text,
                    metadata={
                        **metadata,
                        'indexed_at': datetime.now().isoformat()
                    },
                    doc_id=metadata.get('chunk_id', f"{metadata.get('filename', 'doc')}_{i}")
                )
                documents.append(doc)
            
            # 批量存储到向量数据库
            await self.vector_store_service.add_documents_with_vectors(documents, embeddings)
            
        except Exception as e:
            self.logger.error(f"存储嵌入向量失败: {str(e)}")
            raise
    
    