#!/usr/bin/env python3
"""
向量索引构建脚本

通过调用DDDServiceFactory创建IndexingService，完成文档加载、切分、向量化和存储的完整流程。
"""

import asyncio
from pathlib import Path
from loguru import logger

# 导入配置管理器
from src.infrastructure.config.config_manager import get_config_manager
# 导入DDD服务工厂
from src.presentation.service_factory import DDDServiceFactory


async def main():
    """主函数 - 执行向量索引构建流程"""
    try:
        logger.info("开始向量索引构建流程")
        
        # 步骤1：加载配置
        logger.info("步骤1：加载系统配置")
        config_manager = get_config_manager("config.yaml")
        config = config_manager.get_config()
        
        # 验证配置
        if not config_manager.validate_config():
            logger.error("配置验证失败，退出程序")
            return
            
        
        logger.info(f"配置加载成功 - 嵌入服务提供商: {config.ai_providers.embedding.provider}")
        logger.info(f"向量存储类型: {config.storage.vector_store.type}")
        logger.info(f"文档路径: {config.storage.documents.local.documents_path}")
        
        # 步骤2：初始化服务工厂和索引服务
        logger.info("步骤2：初始化DDD服务工厂")
        service_factory = DDDServiceFactory(config)
        
        # 通过工厂创建应用层索引服务
        logger.info("创建IndexingService实例")
        indexing_service = service_factory.create_application_indexing_service()
       
        # 步骤3：收集文档文件路径
        logger.info("步骤3：收集文档文件路径")
        
        # 定义数据目录
        data_dirs = [
            Path("d:/pythoncode/hhh/data/foods"),
            Path("d:/pythoncode/hhh/data/knowledge")
        ]
        
        # 收集所有文档文件路径
        file_paths = []
        supported_extensions = ['.txt', '.md', '.json']
        
        for data_dir in data_dirs:
            if not data_dir.exists():
                logger.warning(f"数据目录不存在: {data_dir}")
                continue
                
            logger.info(f"扫描目录: {data_dir}")
            
            # 获取目录下所有支持的文档文件
            for ext in supported_extensions:
                files = list(data_dir.glob(f"**/*{ext}"))
                file_paths.extend([str(f) for f in files])
                if files:
                    logger.info(f"找到 {len(files)} 个 {ext} 文件")
        
        if not file_paths:
            logger.error("未找到任何支持的文档文件")
            return
        
        logger.info(f"总共找到 {len(file_paths)} 个文档文件")
        
        # 步骤4：调用IndexingService构建索引
        logger.info("步骤4：开始构建向量索引")
        try:
            # 调用新的build_index方法
            result = await indexing_service.build_index(file_paths)
            # 检查结果
            if result['success']:
                logger.info("向量索引构建成功！")
                logger.info(f"处理文档数量: {result['documents_processed']}")
                logger.info(f"处理时间: {result['processing_time']:.2f} 秒")
                logger.info(f"索引存储路径: {config.storage.vector_store.index_path}")
            else:
                logger.error(f"向量索引构建失败: {result['message']}")
                return
                
        except Exception as e:
            logger.error(f"向量索引构建过程中发生错误: {e}")
            return
        
        # 完成统计
        logger.info("="*50)
        logger.info("向量索引构建完成！")
        logger.info(f"处理文档数量: {result['documents_processed']}")
        logger.info(f"处理时间: {result['processing_time']:.2f} 秒")
        logger.info(f"向量维度: {config.storage.vector_store.dimension}")
        logger.info(f"索引存储路径: {config.storage.vector_store.index_path}")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"向量索引构建过程中发生错误: {e}")
        raise


if __name__ == "__main__":
    # 配置日志
    logger.add(
        "logs/vector_index_construction.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    
    # 运行主程序
    asyncio.run(main())