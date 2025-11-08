#!/usr/bin/env python3
"""
婴幼儿营养RAG系统启动脚本

使用方法:
    python run.py                    # 使用默认配置启动
    python run.py --config custom.yaml  # 使用自定义配置启动
    python run.py --port 8080       # 指定端口启动
    python run.py --reload          # 开发模式启动（自动重载）
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import uvicorn
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.config.config_manager import ConfigManager
from src.presentation.main import create_app


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """配置日志系统"""
    # 移除默认的日志处理器
    logger.remove()
    
    # 添加控制台日志处理器
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 如果指定了日志文件，添加文件日志处理器
    if log_file:
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="7 days",
            compression="zip"
        )


def check_dependencies():
    """检查必要的依赖是否已安装"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "sentence_transformers",
        "faiss",
        "numpy"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"缺少必要的依赖包: {', '.join(missing_packages)}")
        logger.error("请运行: pip install -r requirements.txt")
        sys.exit(1)


async def initialize_system(config):
    """初始化系统组件"""
    logger.info("正在初始化系统组件...")
    
    try:
        # 这里可以添加系统初始化逻辑
        # 例如：预加载模型、初始化向量数据库等
        
        # 检查AI服务配置
        if config.ai_providers.embedding.provider == "openai":
            api_key = config.ai_providers.embedding.openai.api_key
            if not api_key or api_key == "your-openai-api-key-here":
                logger.warning("OpenAI API密钥未配置，某些功能可能无法正常工作")
        
        logger.info("系统组件初始化完成")
        
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")
        raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="婴幼儿营养RAG系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run.py                        # 默认配置启动
  python run.py --config custom.yaml   # 自定义配置启动
  python run.py --port 8080           # 指定端口
  python run.py --reload              # 开发模式
  python run.py --workers 4           # 指定worker数量
        """
    )
    
    parser.add_argument(
        "--config", 
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)"
    )
    parser.add_argument(
        "--host",
        default=None,
        help="服务器主机地址"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="服务器端口"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载（开发模式）"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Worker进程数量"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="日志级别"
    )
    parser.add_argument(
        "--log-file",
        help="日志文件路径"
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="检查依赖并退出"
    )
    
    args = parser.parse_args()
    
    # 检查依赖
    if args.check_deps:
        check_dependencies()
        logger.info("所有依赖检查通过")
        return
    
    try:
        # 加载配置
        config_manager = ConfigManager(args.config)
        config = config_manager.get_config()
        
        # 设置日志
        log_level = args.log_level or config.app.log_level
        setup_logging(log_level, args.log_file)
        
        # 检查依赖
        check_dependencies()
        
        
        # 初始化系统
        asyncio.run(initialize_system(config))
        
        # 创建FastAPI应用
        app = create_app()
        # 启动服务器
        # 确定服务器配置
        reload = args.reload or (config.server.reload if hasattr(config.server, 'reload') else False)
        workers = args.workers or (config.server.workers if hasattr(config.server, 'workers') else 1)
        # 在生产环境中禁用reload和多worker同时使用
        if reload and workers > 1:
            logger.warning("reload模式下不支持多worker，将使用单worker")
            workers = 1

        host = args.host or config.server.host
        port = args.port or config.server.port
        
        if reload:
            # 使用导入字符串启用 reload 功能
            uvicorn.run(
                "src.presentation.main:create_app",
                host=host,
                port=port,
                reload=reload,
                log_level=log_level.lower(),
                access_log=True,
                factory=True
            )
        else:
            # 直接使用应用实例
            uvicorn.run(
                app,
                host=host,
                port=port,
                workers=workers,
                log_level=log_level.lower(),
                access_log=True
            )
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()