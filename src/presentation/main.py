import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .container import ApplicationContainer,init_container
from .api import routes
from ..infrastructure.config.config_manager import get_config
from ..infrastructure.log.logger_service_impl import LoggerServiceImpl

# 创建日志服务
logger = LoggerServiceImpl("MainApplication")

# 全局容器
container: ApplicationContainer | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global container
    
    # 启动时初始化
    try:
        logger.info("正在启动RAG系统...")
        
        # 创建应用容器
        config = get_config()
        container = init_container(config,logger)
        yield  # 添加yield使其成为一个异步生成器

    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        raise
    
    finally:
        # 关闭时清理
        try:
            logger.info("正在关闭RAG系统...")
            if container:
                await container.cleanup()
            container = None
            logger.info("RAG系统已关闭")
        except Exception as e:
            logger.error(f"应用关闭时出错: {str(e)}")

# 创建FastAPI应用
app = FastAPI(
    title="RAG系统",
    description="基于DDD架构的RAG系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册query接口
app.include_router(
    routes.router,
)

@app.get("/", summary="根路径")
async def root():
    """根路径 - 返回系统信息"""
    return {
        "message": "RAG系统",
        "version": "1.0.0",
        "status": "running",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/health", summary="健康检查")
async def health_check():
    """健康检查接口"""
    try:
        if not container:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "系统未初始化"
                }
            )
        
        health_result = await container.health_check()
        
        if health_result["success"]:
            health_status = health_result["health_status"]
            status_code = 200 if health_status["overall"] == "healthy" else 503
            
            return JSONResponse(
                status_code=status_code,
                content={
                    "status": health_status["overall"],
                    "components": health_status["components"],
                    "timestamp": health_result.get("timestamp")
                }
            )
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": health_result.get("error", "健康检查失败")
                }
            )
    
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "message": "系统出现未知错误，请稍后重试"
        }
    )

def create_app() -> FastAPI:
    """创建FastAPI应用实例
    Returns:
        FastAPI: 配置好的FastAPI应用实例
    """
    
    return app