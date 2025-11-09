#!/usr/bin/env python3
"""
RAG系统启动脚本

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

from src.presentation.main import create_app
from src.infrastructure.config.config_manager import get_config

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run.py                        # 默认配置启动
  python run.py --config custom.yaml   # 自定义配置启动
        """
    )
    parser.add_argument(
        "--config", 
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)"
    )

    args = parser.parse_args()
    
    try:
        config = get_config()

        # 创建FastAPI应用
        app = create_app()

        reload = getattr(config.server, 'reload', False)
        workers = getattr(config.server, 'workers', 1)
        # 在生产环境中禁用reload和多worker同时使用
        if reload and workers > 1:
            logger.warning("reload模式下不支持多worker，将使用单worker")
            workers = 1

        host =  getattr(config.server, 'host', '0.0.0.0')
        port = getattr(config.server, 'port', 8000)

        # 统一的uvicorn日志级别（优先环境变量，其次配置，默认INFO）
        uvicorn_log_level = (os.getenv("UVICORN_LOG_LEVEL") or os.getenv("LOG_LEVEL") or getattr(config.logging, 'level', 'INFO')).lower()
        
        if reload:
            # 使用导入字符串启用 reload 功能
            uvicorn.run(
                "src.presentation.main:create_app",
                host=host,
                port=port,
                reload=reload,
                log_level=uvicorn_log_level,
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
                log_level=uvicorn_log_level,
                access_log=True
            )
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()